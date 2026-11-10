
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from google import genai
from google.genai import types

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.8-flash"

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
DATABASE_DIR = ROOT / "database"

OUTPUT_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATABASE_DIR / "history.json"

# Load previous topics
if HISTORY_FILE.exists():
    history = json.loads(HISTORY_FILE.read_text())
else:
    history = []

recent_topics = [
    item["topic"] for item in history[-30:]
]

client = genai.Client(api_key=API_KEY)

prompt = f"""
You are an educational YouTube Shorts content producer.

CHANNEL:
Faceless educational videos.
Language: English.
Audience: General learners.
Duration: 30 to 60 seconds.

YOUR TASK:

1. Choose one fascinating educational topic.
2. Avoid topics used recently.
3. Choose something scientifically or historically
   interesting and suitable for a short video.
4. Create a powerful opening hook.
5. Write original narration of 85-125 words.
6. Keep the language clear and engaging.
7. Suggest 5-7 visual scenes.
8. Give a suitable YouTube title and description.
9. Do not invent scientific facts or quotations.
10. Clearly flag any claims requiring verification.

Recently used topics:
{json.dumps(recent_topics)}

Return ONLY valid JSON in this structure:

{{
  "topic": "Topic name",
  "category": "Science or history etc",
  "hook": "Opening hook",
  "narration": "Complete narration",
  "scenes": [
    "Scene 1 description",
    "Scene 2 description",
    "Scene 3 description",
    "Scene 4 description",
    "Scene 5 description"
  ],
  "title": "YouTube title",
  "description": "Video description",
  "hashtags": ["#science", "#education"],
  "verification_notes": [
    "Claims that need external verification"
  ]
}}
"""

print("Starting AI topic generation...")

response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.8
    )
)

result = json.loads(response.text)

required = [
    "topic", "narration", "scenes",
    "title", "description", "hashtags"
]

for field in required:
    if field not in result:
        raise ValueError(f"Missing field: {field}")

if not 85 <= len(result["narration"].split()) <= 125:
    raise ValueError("Narration word count is outside the target range.")

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

output_file = OUTPUT_DIR / f"{today}.json"

# Save generated content
output_file.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# Save topic history
history.append({
    "date": today,
    "topic": result["topic"]
})

HISTORY_FILE.write_text(
    json.dumps(history, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("AI CONTENT GENERATED SUCCESSFULLY")
print("Topic:", result["topic"])
print("Title:", result["title"])
print("Word count:", len(result["narration"].split()))
print("Saved:", output_file)
