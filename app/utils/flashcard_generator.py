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

def generate_flashcards(note_text):
    prompt = f"""
    Generate 5 study flashcards from the following notes. 
    Each flashcard must have a Front (Question or Concept) and a Back (Answer or Explanation).

    Notes:
    {note_text}

    Format exactly like this:
    Front: [Insert question/concept here]
    Back: [Insert answer/explanation here]
    """
    
    response = model.generate_content(prompt)
    return response.text