import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def generate_quiz(note_text, num_questions=5, difficulty="medium"):
    prompt = f"""Generate exactly {num_questions} multiple-choice quiz questions at {difficulty} difficulty level from the following study notes.

You MUST respond with ONLY a valid JSON array. No markdown, no code fences, no explanation — ONLY the JSON array.

Each question object must have exactly these fields:
- "question": the question text (string)
- "options": exactly 4 answer choices (array of 4 strings)
- "correct_answer": the correct option text, must exactly match one of the options (string)
- "explanation": brief explanation of why the answer is correct (string)

Example format:
[{{
  "question": "What is X?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": "Option A",
  "explanation": "Because X is defined as..."
}}]

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
        questions = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse quiz JSON from AI response: {e}")

    if not isinstance(questions, list):
        raise ValueError("AI response is not a JSON array")

    # Validate and normalize each question
    validated = []
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            continue
        question_text = q.get("question", "").strip()
        options = q.get("options", [])
        correct_answer = q.get("correct_answer", "").strip()
        explanation = q.get("explanation", "").strip()

        # Basic validation
        if not question_text or not isinstance(options, list) or len(options) < 2:
            continue

        # Ensure correct_answer is in options
        if correct_answer and correct_answer not in options:
            # Try to find a close match
            correct_answer = options[0]  # Fallback

        validated.append({
            "question": question_text,
            "options": [str(o) for o in options[:4]],
            "correct_answer": correct_answer or options[0],
            "explanation": explanation or "No explanation provided."
        })

    if not validated:
        raise ValueError("No valid questions could be parsed from AI response")

    return validated
