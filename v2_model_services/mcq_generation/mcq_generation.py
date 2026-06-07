import os
import google.generativeai as genai
from v2_model_services.mcq_generation.mcq_prompt import mcq_prompt
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def generate_mcqs(chunk, mcq_count):
    prompt = mcq_prompt(chunk, mcq_count)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return json.dumps({"error": f"Gemini API failure: {str(e)}", "mcqs": []})