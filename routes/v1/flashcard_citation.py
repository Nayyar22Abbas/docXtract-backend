from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from Services.pdfsummary import extract_text_from_pdf
from datetime import datetime
import google.generativeai as genai
import os
import json
import re
import tempfile

flashcard_citation_router = APIRouter()

@flashcard_citation_router.post("/generate-flashcards/")
async def generate_flashcards_with_citation(
    file: UploadFile = File(...),
    max_cards: int = Form(default=10)
):
    """
    Generate flashcards with source citations from a PDF using Gemini.
    Each flashcard includes the exact text from the PDF that supports the answer.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        pdf_path = tmp.name
    
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from PDF")
        
        # Truncate for Gemini context limit
        truncated_text = pdf_text[:25000]
        
        # Generate flashcards using Gemini
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
You are an expert educational content creator. Generate {max_cards} flashcards from the following document.

RULES:
1. Each flashcard must have a clear question and concise answer
2. Include the EXACT source text from the document that supports the answer
3. Assign a difficulty level (Easy, Medium, Hard)
4. Questions should test understanding, not just recall
5. Source text must be a direct quote from the document

OUTPUT FORMAT (STRICT JSON):
{{
  "flashcards": [
    {{
      "question": "Clear, specific question",
      "answer": "Concise, accurate answer",
      "difficulty": "Easy | Medium | Hard",
      "source_text": "Exact quote from the document supporting this answer"
    }}
  ]
}}

DOCUMENT CONTENT:
{truncated_text}
"""
        
        response = model.generate_content(prompt)
        text = response.text
        
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="Failed to parse flashcard response")
        
        result = json.loads(match.group())
        flashcards = result.get("flashcards", [])
        
        return {
            "model": "Gemini-2.5-Flash",
            "total_flashcards": len(flashcards),
            "flashcards": flashcards
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse flashcard JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
