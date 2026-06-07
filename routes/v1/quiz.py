from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from Services.pdfsummary import extract_text_from_pdf
from Services.quiz_service import generate_quiz_content
from config.db import quizconn
from datetime import datetime
from bson import ObjectId
import os

quiz_router = APIRouter()

# --- Upload folder ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@quiz_router.post("/generate")
async def generate_quiz(
    file: UploadFile = File(None),
    text_content: str = Form(None),
    document_type: str = Form("Research Paper"),
    user_id: str = Form("ahsan")
):
    """
    Generate a quiz from a PDF file or raw text.
    Stores the quiz in MongoDB and returns the questions.
    """
    context = ""
    
    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save temp file to extract text
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")
        saved_path = os.path.join(UPLOAD_DIR, f"{timestamp}_quiz_{safe_filename}")
        
        try:
            content = await file.read()
            with open(saved_path, "wb") as f:
                f.write(content)
            context = extract_text_from_pdf(saved_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    elif text_content:
        context = text_content
    else:
        raise HTTPException(status_code=400, detail="Either file or text_content must be provided")

    if not context or len(context.strip()) < 100:
        raise HTTPException(status_code=400, detail="Insufficient content to generate a quiz")

    # Limit context size for Gemini if necessary
    truncated_context = context[:20000] 

    quiz_data = await generate_quiz_content(truncated_context, document_type)
    
    if not quiz_data:
        raise HTTPException(status_code=500, detail="Failed to generate quiz content")

    # Store in MongoDB
    quiz_record = {
        "user_id": user_id,
        "document_type": quiz_data.get("document_type", document_type),
        "quiz": quiz_data.get("quiz"),
        "created_at": datetime.utcnow()
    }
    
    result = quizconn.insert_one(quiz_record)
    quiz_id = str(result.inserted_id)

    # Return quiz without solutions for the initial display if needed
    # But often front-end wants everything and just hides the solution.
    # However, the user specifically asked for a request to API when solution button is pressed.
    # So I will return the quiz ID and questions (MCQs without correct_answer, etc.)?
    # No, usually in these apps we return the whole thing and FE handles it, 
    # but I'll stick to the "request to api" requirement.

    # Prepare "clean" quiz for front-end
    full_quiz = quiz_data.get("quiz", {})
    
    # We will return the quiz_id so FE can ask for solutions later.
    return {
        "quiz_id": quiz_id,
        "document_type": quiz_record["document_type"],
        "questions": {
            "mcqs": [
                {
                    "question": m["question"],
                    "options": m["options"],
                    "difficulty": m["difficulty"]
                } for m in full_quiz.get("mcqs", [])
            ],
            "short_answer": [
                {
                    "question": s["question"],
                    "difficulty": s["difficulty"]
                } for s in full_quiz.get("short_answer", [])
            ],
            "true_false": [
                {
                    "statement": t["statement"]
                } for t in full_quiz.get("true_false", [])
            ]
        }
    }

@quiz_router.get("/solution/{quiz_id}")
async def get_quiz_solution(quiz_id: str):
    """
    Retrieve the solution for a specific quiz.
    """
    try:
        quiz = quizconn.find_one({"_id": ObjectId(quiz_id)})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        return {
            "quiz_id": quiz_id,
            "solutions": quiz["quiz"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
