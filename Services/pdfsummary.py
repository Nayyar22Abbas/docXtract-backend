import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File
import os
import fitz

# Load .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure the client
model=genai.configure(api_key=API_KEY) # type: ignore
  # PyMuPDF for PDF text extraction



def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF file."""
    text: str = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text")  # type: ignore
    return text