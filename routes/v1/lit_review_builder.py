from fastapi import APIRouter, UploadFile, File, HTTPException
from Services.pdfsummary import extract_text_from_pdf
from datetime import datetime
import google.generativeai as genai
import os
from typing import List
from config.db import pdfconn

lit_review_router = APIRouter()

# --- Upload folder ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@lit_review_router.post("/generate-lit-review/")
async def generate_lit_review(files: List[UploadFile] = File(...), user_id: str = "ahsan"):
    """
    Receive multiple PDFs, save them, store metadata, and generate a synthesized literature review
    including themes, gaps, and future work using Gemini 2.5 Flash.
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    all_file_info = []
    combined_text = ""

    for file in files:
        if not file.filename.lower().endswith(".pdf"): #type: ignore
            continue # Skip non-pdf files
            
        # 1️⃣ Save PDF permanently
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")#type: ignore
        saved_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename}")

        try:
            content = await file.read()
            with open(saved_path, "wb") as f:
                f.write(content)
        except Exception as e:
            continue # Or handle as needed

        # 2️⃣ Store metadata in MongoDB
        doc = {
            "user_id": user_id,
            "original_name": file.filename,
            "saved_path": saved_path,
            "upload_time": datetime.utcnow(),
            "type": "literature_review_input"
        }
        pdfconn.insert_one(doc)

        # 3️⃣ Extract text from PDF
        pdf_text = extract_text_from_pdf(saved_path)
        if pdf_text:
            combined_text += f"\n\n--- Paper: {file.filename} ---\n\n" + pdf_text[:10000] # Truncate per paper to fit context
            
        all_file_info.append({
            "filename": file.filename,
            "saved_path": saved_path
        })

    if not combined_text:
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded PDFs.")

    # 4️⃣ Generate Literature Review Synthesis using Gemini 2.5 Flash
    model = genai.GenerativeModel(model_name="gemini-2.5-flash") # type: ignore
    
    prompt = f"""
    You are an academic research assistant. Based on the following extracted text from multiple research papers, provide a comprehensive literature review synthesis.
    
    Your response should include:
    1. **Thematic Analysis**: Identify and discuss major themes and trends across all papers.
    2. **Synthesis of Papers**: Briefly synthesize how each paper contributes to these themes.
    3. **Research Gaps**: Identify clear gaps in the current research presented.
    4. **Future Work**: Suggest specific directions for future research based on these gaps.
    
    Format the output with clear Markdown headings.
    
    Extracted Text:
    {combined_text}
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Check if the response was blocked
        if not response.candidates or len(response.candidates) == 0:
            # Check if there's feedback about blocking
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                    return {
                        "files_processed": all_file_info,
                        "literature_review": f"⚠️ **Content Blocked**: The Gemini API blocked this request due to safety filters. This may happen with certain document content. Please try:\n1. Using a different document\n2. Try again (sometimes it works on retry)\n\nOriginal block reason: {response.prompt_feedback.block_reason}"
                    }
            
            return {
                "files_processed": all_file_info,
                "literature_review": "⚠️ **Error**: The API returned no response. This may be due to content safety filters or rate limiting. Please try again in a moment."
            }
        
        lit_review_result = response.text
    except Exception as e:
        error_msg = str(e)
        if "empty" in error_msg.lower() and "candidates" in error_msg.lower():
            return {
                "files_processed": all_file_info,
                "literature_review": f"⚠️ **Content Blocked**: The Gemini API safety filters blocked this request. This may happen with certain document content. Please try:\n1. Using a different document\n2. Try generating again\n\nError details: {error_msg}"
            }
        
        lit_review_result = f"⚠️ **Error generating literature review**: {error_msg}"

    # 5️⃣ Return result + file info
    return {
        "files_processed": all_file_info,
        "literature_review": lit_review_result
    }
