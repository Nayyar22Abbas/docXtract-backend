from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from Services.pdfsummary import extract_text_from_pdf
from Services.mcq_service_gemini import generate_mcqs_gemini
import tempfile
import os

mcqs_gemini_router = APIRouter()


@mcqs_gemini_router.post("/generate-mcqs/")
async def generate_mcqs_from_pdf_gemini(
    file: UploadFile = File(...),
    total_mcqs: int = Form(default=10)
):
    """
    Generate MCQs from PDF using Gemini API.
    total_mcqs defaults to 10 but can be overridden (max 20 for optimization)
    """

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Cap total_mcqs to a reasonable maximum
    total_mcqs = min(total_mcqs, 20)

    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Insufficient content in PDF to generate MCQs")

        # Limit context size for Gemini (approximately 20k characters)
        truncated_context = text[:20000]

        # Generate MCQs using Gemini
        mcqs_result = await generate_mcqs_gemini(truncated_context, total_mcqs)

        if not mcqs_result:
            raise HTTPException(status_code=500, detail="Failed to generate MCQs using Gemini")

        return {
            "filename": file.filename,
            "requested_mcqs": total_mcqs,
            "total_generated": len(mcqs_result),
            "mcqs": mcqs_result,
            "model": "gemini-2.5-flash"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating MCQs: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
