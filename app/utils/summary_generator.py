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

def generate_summary(note_text):
    prompt = f"""
    Provide a clear, concise summary of the following study notes. 
    Break it down into simple, easy-to-read bullet points.

    Notes:
    {note_text}
    """
    
    response = model.generate_content(prompt)
    return response.text