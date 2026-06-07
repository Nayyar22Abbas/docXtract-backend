from fastapi import FastAPI, UploadFile, File, Form,APIRouter
from v2_model_services.Pdf_plumber_text_extraction import extract_text_from_pdf
from v2_model_services.text_chunking import chunk_text
from v2_model_services.mcq_generation.mcq_generation import generate_mcqs
import tempfile
import math
import json
import re
mcqs=APIRouter()


def parse_mcq_response(mcqs_json: str):
    """
    Parse MCQ response from model, handling both valid and malformed JSON.
    Returns list of properly formatted MCQs.
    """
    try:
        # Try direct JSON parsing first
        parsed = json.loads(mcqs_json)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "mcqs" in parsed:
            return parsed["mcqs"]
        return []
    except json.JSONDecodeError:
        # Try to extract individual MCQ objects from the response
        try:
            # Look for complete JSON objects with "question" field
            objects = re.findall(r'\{[^{}]*"question"[^{}]*\}', mcqs_json, re.DOTALL)
            if objects:
                mcqs_list = []
                for obj_str in objects:
                    try:
                        # Clean up the string - remove trailing commas, etc
                        obj_str = obj_str.rstrip(',').rstrip()
                        mcq = json.loads(obj_str)
                        if isinstance(mcq, dict):
                            mcqs_list.append(mcq)
                    except json.JSONDecodeError:
                        # Try to extract just the matching braces
                        pass
                if mcqs_list:
                    print(f"Extracted {len(mcqs_list)} MCQ objects from truncated JSON")
                    return mcqs_list
        except Exception as e:
            print(f"Error extracting MCQ objects: {e}")
        
        # If all parsing fails, return empty list (will be filtered out)
        print(f"Could not parse MCQ JSON: {mcqs_json[:300]}")
        return []


@mcqs.post("/generate-mcqs/")
async def generate_mcqs_from_pdf(
    file: UploadFile = File(...),
    total_mcqs: int = Form(default=10)
):
    """
    Generate MCQs from PDF with default limit of 10.
    total_mcqs defaults to 10 but can be overridden (kept low for resource optimization)
    """

    # Cap total_mcqs to a maximum of 20 for resource optimization (8GB RAM, CPU only)
    total_mcqs = min(total_mcqs, 20)

    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    # Extract & chunk text
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)

    # Determine MCQs per chunk
    num_chunks = len(chunks)
    mcqs_per_chunk = math.ceil(total_mcqs / num_chunks)

    # Generate MCQs
    all_mcqs = []
    for chunk in chunks:
        mcqs_json = generate_mcqs(chunk, mcqs_per_chunk)
        
        # Parse the response
        parsed_mcqs = parse_mcq_response(mcqs_json)
        
        # Normalize and validate each MCQ
        for mcq in parsed_mcqs:
            if isinstance(mcq, dict):
                try:
                    # Normalize options from object to array
                    if isinstance(mcq.get("options"), dict):
                        mcq["options"] = list(mcq["options"].values())
                    
                    # Ensure options is a list
                    if not isinstance(mcq.get("options"), list):
                        continue
                    
                    options = mcq["options"]
                    correct_answer = mcq.get("correct_answer")
                    
                    # Validate required fields
                    if (mcq.get("question") and 
                        len(options) >= 2):
                        
                        # Convert numeric correct_answer to string if needed
                        if isinstance(correct_answer, int) and 0 <= correct_answer < len(options):
                            mcq["correct_answer"] = correct_answer
                        elif isinstance(correct_answer, str) and correct_answer in options:
                            mcq["correct_answer"] = correct_answer
                        else:
                            # If no valid correct_answer, skip this MCQ
                            continue
                        
                        all_mcqs.append(mcq)
                except Exception as e:
                    print(f"Error processing MCQ: {e}")
                    continue

    # Trim to total_mcqs requested (capped at 20)
    all_mcqs = all_mcqs[:total_mcqs]

    return {
        "filename": file.filename,
        "requested_mcqs": total_mcqs,
        "requested_mcqs_per_chunk": mcqs_per_chunk,
        "total_chunks": len(chunks),
        "mcqs": all_mcqs,
        "total_generated": len(all_mcqs)
    }
