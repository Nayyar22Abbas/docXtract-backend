from fastapi import APIRouter, UploadFile, File, HTTPException
from Services.pdfsummary import extract_text_from_pdf
from Services.chapterwisesum import split_into_chapters_smart
from datetime import datetime
import google.generativeai as genai
import os
from config.db import pdfconn

pdf_summary_combined = APIRouter()

# --- Upload folder ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@pdf_summary_combined.post("/summarize-pdf-combined/")
async def summarize_pdf_combined(file: UploadFile = File(...), user_id: str = "ahsan"):
    """
    Receive a PDF, save permanently, store metadata, and generate a combined summary
    (General Summary + Chapter-wise Summary).
    """

    if not file.filename.lower().endswith(".pdf"): #type: ignore
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 1️⃣ Save PDF permanently
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = file.filename.replace(" ", "_")#type: ignore
    saved_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename}")

    try:
        content = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 2️⃣ Store metadata in MongoDB
    doc = {
        "user_id": user_id,
        "original_name": file.filename,
        "saved_path": saved_path,
        "upload_time": datetime.utcnow(),
    }
    pdfconn.insert_one(doc)

    # 3️⃣ Extract text from PDF
    pdf_text = extract_text_from_pdf(saved_path)
    if not pdf_text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")

    # 4️⃣ Generate General Summary using Gemini
    model = genai.GenerativeModel(model_name="gemini-2.5-flash") # type: ignore
    
    # Truncate text for general summary if too long
    general_summary_text = pdf_text[:15000] 
    general_prompt = f"Summarize the following PDF content in clear and concise paragraphs. Provide a comprehensive overview of the entire document:\n\n{general_summary_text}"
    
    try:
        general_response = model.generate_content(general_prompt)
        general_summary = general_response.text
    except Exception as e:
        general_summary = f"Error generating general summary: {str(e)}"

    # 5️⃣ Split into chapters and generate chapter-wise summaries
    chapters = split_into_chapters_smart(pdf_text)
    chapter_summaries = {}

    for title, content in chapters:
        # Truncate per chapter if needed, though split_into_chapters_smart handles chunks
        content_snippet = content[:15000]
        chapter_prompt = f"Summarize the following chapter/section content in clear and concise paragraphs. Maintain the context of the overall document:\n\nSection: {title}\n\nContent: {content_snippet}"
        try:
            chapter_response = model.generate_content(chapter_prompt)
            chapter_summaries[title] = chapter_response.text
        except Exception as e:
            chapter_summaries[title] = f"Error generating summary for this section: {str(e)}"

    # 6️⃣ Compile the final response string as requested
    # "that will be a summary with heading summary and chapter-wise/section-wise summary below it with appropriate headings"
    
    combined_response_text = f"# Summary\n\n{general_summary}\n\n"
    combined_response_text += "## Chapter-wise / Section-wise Summary\n\n"
    
    for title, summary in chapter_summaries.items():
        combined_response_text += f"### {title}\n\n{summary}\n\n"

    # 7️⃣ Return combined result + file info
    return {
        "file_info": {
            "filename": file.filename,
            "saved_path": saved_path,
        },
        "combined_summary": combined_response_text,
        "structured_data": {
            "general_summary": general_summary,
            "chapters": chapter_summaries
        }
    }
