from fastapi import APIRouter, UploadFile, File, HTTPException
from Services.pdfsummary import extract_text_from_pdf
from Services.chapterwisesum import split_into_chapters_smart
from datetime import datetime
import os
import google.generativeai as genai

pdfcompare = APIRouter()

# --- Upload folder ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@pdfcompare.post("/compare-pdfs/")
async def compare_pdfs(file1: UploadFile = File(...), file2: UploadFile = File(...), user_id: str = "ahsan"):
    """
    Compare two PDFs using Gemini 2.5 Flash and return a smart comparison summary.
    """

    # Validate files
    for f in [file1, file2]:
        if not f.filename.lower().endswith(".pdf"): #type: ignore
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save PDFs
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    saved_paths = []
    for f in [file1, file2]:
        safe_name = f"{timestamp}_{f.filename.replace(' ', '_')}" #type: ignore
        path = os.path.join(UPLOAD_DIR, safe_name)
        with open(path, "wb") as out_file:
            out_file.write(await f.read())
        saved_paths.append(path)

    # Extract text
    text1 = extract_text_from_pdf(saved_paths[0])
    text2 = extract_text_from_pdf(saved_paths[1])

    # Optional: split into chapters (if you want chapter-level comparison)
    chapters1 = split_into_chapters_smart(text1)
    chapters2 = split_into_chapters_smart(text2)

    # Initialize Gemini model
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")  # type: ignore

    # Build prompt for comparison
    prompt = f"""
    You are an AI expert in comparing documents. 
    Compare the following two PDFs and generate a concise summary of differences, similarities, and major changes.
    
    PDF 1 content:
    {text1[:15000]}
    
    PDF 2 content:
    {text2[:15000]}
    
    Provide the output in clear paragraphs highlighting added, removed, or modified content.
    """

    # Call Gemini
    try:
        response = model.generate_content(prompt)
        comparison_summary = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

    # Return JSON
    return {
        "files_info": [
            {"filename": file1.filename, "saved_path": saved_paths[0]},
            {"filename": file2.filename, "saved_path": saved_paths[1]},
        ],
        "comparison_summary": comparison_summary
    }
