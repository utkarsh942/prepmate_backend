import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

import json
import re

def generate_flashcards(note_text, num_cards=5):
    prompt = f"""Generate {num_cards} study flashcards from the following notes. 
Each flashcard must have a "front" (Question or Concept) and a "back" (Answer or Explanation).

You MUST respond with ONLY a valid JSON array. No markdown, no code fences, no explanation — ONLY the JSON array.

Example format:
[
  {{
    "front": "What is Photosynthesis?",
    "back": "The process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar."
  }}
]

Notes:
{note_text}
"""
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Strip markdown code fences if present
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
    raw_text = re.sub(r'\s*```$', '', raw_text)
    raw_text = raw_text.strip()

    try:
        flashcards = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse flashcards JSON from AI response: {e}")

    if not isinstance(flashcards, list):
        raise ValueError("AI response is not a JSON array")

    return flashcards