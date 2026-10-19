import os
import json
from datetime import datetime

from dotenv import load_dotenv
from google import genai

load_dotenv()

_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=_key) if _key else None
MODEL = "gemini-flash-lite-latest"


def _ask(prompt):
    if client is None:
        return None
    try:
        r = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(r.text)
    except Exception as e:
        print("AI error:", e)
        return None


def analyze_call(transcript):
    prompt = (
        "You analyse a short phone-call transcript for an appointment booking agent. "
        "The transcript may be in English, Hindi or Marathi. "
        'Reply ONLY with JSON like {"summary": "...", "sentiment": "..."}. '
        "summary: one short English sentence. "
        "sentiment: exactly one of happy, neutral, angry, urgent.\n"
        "Transcript: " + transcript
    )
    data = _ask(prompt)
    if not data:
        return None, None
    return data.get("summary"), data.get("sentiment")


def extract_booking(transcript):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = (
        "Extract appointment details from the sentence below. "
        "It may be in English, Hindi, Marathi or a mix. "
        "Current date and time: " + now + ". "
        'Reply ONLY with JSON like {"name": "...", "datetime": "YYYY-MM-DDTHH:MM:00"}. '
        "Use null for anything that is not clearly said. "
        "Resolve words like tomorrow or day after tomorrow using the current date. "
        "Evening or shaam or sandhyakal means PM.\n"
        "Sentence: " + transcript
    )
    data = _ask(prompt)
    if not data:
        return None, None
    return data.get("name"), data.get("datetime")