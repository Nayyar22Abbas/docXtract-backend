from fastapi import APIRouter, UploadFile, File, Form
import shutil
import os
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

flashcard = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:3]:  # first 3 pages for speed
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def generate_flashcards(text, max_cards):
    prompt = f"""
You are an intelligent AI tutor.

Extract {max_cards} important concepts from the text below and
convert each into a flashcard in this format:

Q: <question>
A: <concise answer>

TEXT:
{text}
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text
        return parse_flashcards(raw_text)
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

def parse_flashcards(output):
    cards = []
    blocks = output.split("Q:")

    for block in blocks[1:]:
        try:
            q, a = block.split("A:")
            answer = a.strip()

            # Difficulty logic
            if len(answer.split()) <= 8:
                difficulty = "Easy"
                
            elif len(answer.split()) <= 20:
                difficulty = "Medium"
                
            else:
                difficulty = "Hard"
                

            cards.append({
                "question": q.strip(),
                "answer": answer,
                "difficulty": difficulty,
                
            })
        except:
            continue

    return cards


@flashcard.post("/generate-flashcards/")
async def generate_flashcards_api(file: UploadFile = File(...), max_cards: int =Form(...)):
    path = f"{UPLOAD_DIR}/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(path)
    flashcards = generate_flashcards(text, max_cards=max_cards)

    return {
        "model": "Gemini-2.5-Flash",
        "total_flashcards": len(flashcards),
        "flashcards": flashcards
    }
