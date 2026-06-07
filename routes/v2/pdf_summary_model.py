from fastapi import APIRouter, Body, HTTPException, UploadFile, File
from bson import ObjectId
import os
from datetime import datetime

from config.db import pdfconn
from v2_model_services.Pdf_plumber_text_extraction import extract_text_from_pdf
from v2_model_services.text_chunking import chunk_text
from v2_model_services.embeddding_faiss_index import build_index, retrieve
from v2_model_services.summary_generation import ask_mistral

from v2_model_services.chapter_service import split_into_chapters_smart

pdfsummarymodel = APIRouter()

@pdfsummarymodel.post("/summarize-upload-pdf-model/")
async def summarize_upload_pdf_model(file: UploadFile = File(...), user_id: str = "ahsan"):
    """
    Upload a PDF, save it, and generate both a global RAG summary 
    and detailed chapter-wise summaries in one response.
    """
    if not file.filename.lower().endswith(".pdf"): #type: ignore
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 1️⃣ Save PDF permanently
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = file.filename.replace(" ", "_") #type: ignore
    saved_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_filename}")

    with open(saved_path, "wb") as f:
        f.write(await file.read())

    # 2️⃣ Save metadata and get pdf_id
    doc = {
        "user_id": user_id,
        "original_name": file.filename,
        "saved_path": saved_path,
        "upload_time": datetime.utcnow()
    }
    result = pdfconn.insert_one(doc)
    new_pdf_id = str(result.inserted_id)

    # 3️⃣ Extraction
    text = extract_text_from_pdf(saved_path)

    # 4️⃣ Global RAG Pipeline for High-level Summary
    chunks = chunk_text(text)
    index, _ = build_index(chunks)
    global_query = "Summarize this document comprehensively, highlighting key points and main takeaways."
    context = retrieve(global_query, chunks, index)
    global_summary = ask_mistral(context, global_query)

    # 5️⃣ Detailed Chapter-wise Summaries
    chapters = split_into_chapters_smart(text)
    chapter_summaries = {}
    
    for title, content in chapters:
        # Gemini handles larger content safely
        chapter_query = f"Provide a detailed summary for the section titled '{title}'."
        summary = ask_mistral(content, chapter_query)
        chapter_summaries[title] = summary

    return {
        "summary": global_summary,
        "chapter_summaries": chapter_summaries,
        "pdf_id": new_pdf_id,
        "engine": "Gemini API",
        "file_info": {
            "filename": file.filename,
            "saved_path": saved_path
        }
    }


