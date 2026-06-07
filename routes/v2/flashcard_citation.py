import google.generativeai as genai
import os
import re
import logging
import pdfplumber
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from v2_model_services.Pdf_plumber_text_extraction import extract_text_from_pdf
from v2_model_services.text_chunking import chunk_text
from v2_model_services.embeddding_faiss_index import build_index, retrieve
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

flashcardWithcitation = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Generate flashcards using Gemini API ---
async def generate_flashcards_gemini(pdf_path: str, max_cards: int = 5):
    """
    Generates flashcards with source citations using Gemini API.
    """
    # 1. Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    # 2. Chunk text
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    
    # 3. Build index
    index, _ = build_index(chunks)
    
    # 4. Context retrieval
    query = "Important concepts, definitions, and facts for learning."
    context_chunks = retrieve(query, chunks, index)

    # 5. Gemini Prompt
    prompt = f"""
You are DocXtract Academia. Extract {max_cards} flashcards from the context.
Each flashcard MUST have a specific citation string from the context.

FORMAT:
Q: <question>
A: <answer>
Source: <exact quote or sentence from context>

CONTEXT:
{context_chunks}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        response_text = response.text
        return parse_flashcards_gemini_output(response_text) # Renamed to avoid conflict and clarify purpose
    except Exception as e:
        print(f"Error in Gemini flashcards: {e}")
        return []

def parse_flashcards_gemini_output(output):
    """
    Parses Gemini LLM output into structured flashcards with difficulty and source line using Regex.
    Expected format:
    Q: <question>
    A: <answer>
    Source: <exact quote or sentence from context>
    """
    cards = []
    
    pattern = re.compile(
        r"(?:Q|Question):\s*(?P<question>.*?)\s*(?:A|Answer):\s*(?P<answer>.*?)\s*(?:Source|Source Line):\s*(?P<source>.*?)(?=\n(?:Q|Question):|\Z)", 
        re.IGNORECASE | re.DOTALL
    )
    
    matches = pattern.finditer(output)
    
    for match in matches:
        try:
            question = match.group("question").strip()
            answer = match.group("answer").strip()
            source_text = match.group("source").strip()

            # Difficulty logic based on answer length
            word_count = len(answer.split())
            if word_count <= 8:
                difficulty = "Easy"
            elif word_count <= 20:
                difficulty = "Medium"
            else:
                difficulty = "Hard"

            cards.append({
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "source_text": source_text # Changed from source_line to source_text for Gemini output
            })
        except Exception as e:
            logger.error(f"Failed to parse match: {match.group(0)} | Error: {e}")
            continue

    if not cards:
        logger.warning("No flashcards parsed. Raw LLM output:")
        logger.warning(output)

    return cards

# --- API Endpoint ---
@flashcardWithcitation.post("/generate-flashcards/")
async def generate_flashcards_api(
    file: UploadFile = File(...),
    max_cards: int = Form(...)
):
    """
    Upload a PDF and get AI-generated flashcards with source lines.
    """
    # Save uploaded PDF
    path = f"{UPLOAD_DIR}/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Generate flashcards
    flashcards = await generate_flashcards_gemini(path, max_cards=max_cards)

    return {
        "model": "Gemini-2.5-Flash",
        "total_flashcards": len(flashcards),
        "flashcards": flashcards
    }

# --- Optional: Integrate Router with FastAPI App ---
# app = FastAPI()
# app.include_router(flashcard, prefix="/flashcard")
