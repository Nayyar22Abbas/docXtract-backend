import os
import json
import re
import google.generativeai as genai
from v2_model_services.Pdf_plumber_text_extraction import extract_text_from_pdf
from v2_model_services.text_chunking import chunk_text
from v2_model_services.embeddding_faiss_index import build_index, retrieve
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

async def generate_quiz_mistral(pdf_path: str, document_type: str = "Research Paper"):
    """
    Generates a quiz using Gemini API based on the provided PDF.
    Function name kept for cross-file compatibility.
    Uses RAG to retrieve context from the document.
    """
    # 1. Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    # 2. Chunk text
    chunks = chunk_text(text, chunk_size=1000, overlap=100) # Gemini can handle larger chunks
    
    # 3. Build index
    index, _ = build_index(chunks)
    
    # 4. Retrieve context for quiz generation
    query = "The main concepts, section relationships, and critical reasoning details of the document for educational assessment."
    context = retrieve(query, chunks, index)

    # 5. Gemini Prompt
    prompt = f"""
You are DocXtract Academia, an expert educational assessment generator.
Your task is to generate a comprehension-focused quiz STRICTLY based on the provided context.
Do not introduce information that is not present in the document.

--------------------------------------------------
RULES & CONSTRAINTS
--------------------------------------------------
- Use clear, academic language suitable for university students
- Return EXACTLY 10 questions total (6 MCQs, 2 Short Answer, 2 True/False)
- Return EXACTLY in JSON format.

OUTPUT FORMAT (STRICT JSON):
{{
  "document_type": "{document_type}",
  "quiz": {{
    "mcqs": [
      {{
        "question": "Question text here",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "difficulty": "Easy",
        "explanation": "Why this is correct"
      }}
    ],
    "short_answer": [
      {{
        "question": "Question text here",
        "sample_answer": "Sample answer text",
        "difficulty": "Medium"
      }}
    ],
    "true_false": [
      {{
        "statement": "Statement text here",
        "answer": true,
        "explanation": "Why this is true/false"
      }}
    ]
  }}
}}

CONTEXT:
{context}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON from the response
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_str = match.group()
            return json.loads(json_str)
        else:
            print(f"Gemini response did not contain JSON: {response_text}")
            return None
    except Exception as e:
        print(f"Error in quiz generation (Gemini): {e}")
        return None
