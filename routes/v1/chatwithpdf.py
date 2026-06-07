from fastapi import APIRouter, HTTPException, Body
from bson import ObjectId
from Services.pdfsummary import extract_text_from_pdf
import os
import google.generativeai as genai
from pymongo import MongoClient
from config.db import pdfconn

pdfchat = APIRouter()

# MongoDB connection


@pdfchat.post("/chat-pdf/{pdf_id}")
def chat_with_pdf(pdf_id: str, request_body: dict = Body(...)):
    """
    Chat with a specific PDF.
    Expects: {"question": "your question here"}
    """
    
    question = request_body.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Question field is required")
    
    doc = pdfconn.find_one({"_id": ObjectId(pdf_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = doc["saved_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

   
    pdf_text = extract_text_from_pdf(file_path)
    pdf_text = pdf_text[:15000]  

    
    model = genai.GenerativeModel(model_name="gemini-2.5-flash") # type: ignore
    prompt = f"You are an AI assistant. Answer the following question based on the PDF content.\n\nPDF Content:\n{pdf_text}\n\nQuestion:\n{question}"
    response = model.generate_content(prompt)

    return {"answer": response.text}
