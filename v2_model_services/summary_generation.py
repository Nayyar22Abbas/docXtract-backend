import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def ask_mistral(context, question):
    """
    Generate summaries using Gemini API for v2 routes.
    """
    prompt = f"""
    You are an intelligent document assistant.
    Context:
    {context}
    
    Question:
    {question}
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary with Gemini: {str(e)}"
