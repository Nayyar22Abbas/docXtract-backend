from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from Services.pdfsummary import extract_text_from_pdf
import google.generativeai as genai
import os
import json
import re
import tempfile

insight_router = APIRouter()

@insight_router.post("/concept-graph/")
async def generate_concept_graph(
    file: UploadFile = File(...),
    use_api: bool = Form(default=True),
    max_concepts: int = Form(default=15)
):
    """
    Generate a concept graph from a PDF using Gemini.
    Returns nodes (concepts/entities) and links (relationships) for visualization.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        pdf_path = tmp.name
    
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from PDF")
        
        # Truncate for Gemini context limit
        truncated_text = pdf_text[:20000]
        
        # Generate concept graph using Gemini
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
You are an expert knowledge graph generator. Analyze the following document and extract key concepts and their relationships.

RULES:
1. Extract {max_concepts} most important concepts/entities from the document
2. Identify relationships between these concepts
3. Each node should have a unique ID, label, and type (topic or entity)
4. Each link should have source, target, and relation description
5. Focus on the main themes and their connections

OUTPUT FORMAT (STRICT JSON):
{{
  "nodes": [
    {{
      "id": "unique_id_1",
      "label": "Concept Name",
      "type": "topic"
    }},
    {{
      "id": "unique_id_2", 
      "label": "Entity Name",
      "type": "entity"
    }}
  ],
  "links": [
    {{
      "source": "unique_id_1",
      "target": "unique_id_2",
      "relation": "describes relationship"
    }}
  ]
}}

Node types:
- "topic": Abstract concepts, themes, methodologies
- "entity": Concrete things like people, places, technologies, tools

DOCUMENT CONTENT:
{truncated_text}
"""
        
        response = model.generate_content(prompt)
        text = response.text
        
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="Failed to parse concept graph response")
        
        graph = json.loads(match.group())
        
        return {
            "pdf_name": file.filename,
            "engine": "Gemini API",
            "graph": graph
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse graph JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
