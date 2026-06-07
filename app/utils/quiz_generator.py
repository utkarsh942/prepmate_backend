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
def generate_quiz(note_text):
    prompt = f"""
    Generate 5 MCQ quiz questions
    from the following notes.

    Notes:
    {note_text}
     Format:

    Question:
    Options:
    Correct Answer:

    """
    response = model.generate_content(prompt)
    return response.text
