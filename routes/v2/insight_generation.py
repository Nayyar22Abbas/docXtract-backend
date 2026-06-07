from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import json
import re
import google.generativeai as genai  # type: ignore
from dotenv import load_dotenv

from routes.v2.model_load import llm
from v2_model_services.Pdf_plumber_text_extraction import extract_text_from_pdf
from v2_model_services.triplet_storage import TripletStorage
from v2_model_services.triplet_retrieval import TripletRetriever

load_dotenv()

insight_router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize Triplet Storage and Retrieval
TRIPLET_STORAGE_DIR = "triplet_storage"
triplet_storage = TripletStorage(TRIPLET_STORAGE_DIR)
triplet_retriever = TripletRetriever(TRIPLET_STORAGE_DIR, api_key=None)

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)  # type: ignore
    except Exception:
        pass
    triplet_retriever.api_key = API_KEY

def clean_json_response(raw_text):
    """
    Cleans LLM response to ensure it's valid JSON.
    Removes markdown code blocks if present.
    """
    clean_text = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Fallback: find something that looks like a JSON object
        json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        return {"error": "Invalid JSON format from LLM", "raw": raw_text}

@insight_router.post("/concept-graph/")
async def generate_concept_graph(
    file: UploadFile = File(...),
    use_api: bool = Form(False),
    max_concepts: int = Form(10)
):
    """
    Upload a PDF and identify key concepts and relationships.
    Returns a graph-ready JSON (nodes and links).
    """
    # 1. Save file
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Extract and Truncate text
    try:
        text = extract_text_from_pdf(file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        
        # Limit text size for the prompt
        truncated_text = text[:4000]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

    # 3. Construct Prompt for RDF Triples
    prompt = f"""
    Analyze the following document text and extract the most important information as a knowledge graph using RDF Triples (Subject, Predicate, Object).
    Extract up to {max_concepts * 2} unique triples that capture the core concepts and their relationships.
    
    Return the result STRICTLY as a JSON list of objects, where each object represents a single triple:
    [
      {{"subject": "Concept 1", "predicate": "relates to", "object": "Concept 2"}},
      {{"subject": "Concept A", "predicate": "is part of", "object": "Concept B"}}
    ]
    
    TEXT:
    {truncated_text}
    """

    # 4. Model Execution
    try:
        if use_api:
            if not API_KEY:
                raise HTTPException(status_code=500, detail="Google API Key missing in environment.")
            
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore
            response = model.generate_content(prompt)
            raw_response = response.text
        else:
            # Local Mistral
            output = llm(prompt, max_tokens=1000, temperature=0.1)
            raw_response = output["choices"][0]["text"] # type: ignore

        # 5. Parse Triples
        triples_data = clean_json_response(raw_response)
        
        if isinstance(triples_data, dict) and "error" in triples_data:
             raise HTTPException(status_code=500, detail=triples_data["error"])

        # Ensure triples_data is a list
        if not isinstance(triples_data, list):
            triples_data = []

        # 6. Save Triples Locally
        triples_file_path = os.path.join(UPLOAD_DIR, f"{file.filename}_triples.json")
        with open(triples_file_path, "w", encoding="utf-8") as tf:
            json.dump(triples_data, tf, indent=2)

        # 7. Convert Triples to Nodes & Links for Frontend compatibility
        nodes_dict = {}
        links = []
        
        for idx, triple in enumerate(triples_data):  # type: ignore
            subj = triple.get("subject", "").strip()
            pred = triple.get("predicate", "").strip()
            obj = triple.get("object", "").strip()
            
            if not subj or not obj:
                continue
                
            # Create nodes (if they don't exist)
            if subj not in nodes_dict:
                nodes_dict[subj] = {"id": subj, "label": subj, "type": "concept"}
            if obj not in nodes_dict:
                nodes_dict[obj] = {"id": obj, "label": obj, "type": "concept"}
                
            # Create link
            links.append({
                "source": subj,
                "target": obj,
                "relation": pred
            })
            
        graph_data = {
            "nodes": list(nodes_dict.values()),
            "links": links
        }

        return {
            "pdf_name": file.filename,
            "engine": "Gemini API" if use_api else "Local Mistral",
            "graph": graph_data,
            "message": "Concept graph generated from stored RDF triples."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")


class GraphQueryRequest(BaseModel):
    pdf_name: str
    query: str
    use_api: bool = False

@insight_router.post("/concept-graph/query/")
async def query_concept_graph(request: GraphQueryRequest):
    """
    Search the stored RDF triples using a natural language query
    and return a filtered subset of the graph.
    """
    triples_file_path = os.path.join(UPLOAD_DIR, f"{request.pdf_name}_triples.json")
    
    if not os.path.exists(triples_file_path):
        raise HTTPException(status_code=404, detail="No stored concept graph found for this document.")
        
    # 1. Load stored triples
    with open(triples_file_path, "r", encoding="utf-8") as f:
        stored_triples = json.load(f)
        
    # 2. Construct Prompt for filtering
    prompt = f"""
    You are given a list of RDF Triples representing the knowledge graph of a document.
    A user has asked the following query: "{request.query}"
    
    Filter the provided list of triples and return ONLY the triples that are relevant to answering or exploring the user's query.
    If no triples are strictly relevant, return an empty list: []
    
    Return the result STRICTLY as a JSON list of triple objects.
    
    STORED TRIPLES:
    {json.dumps(stored_triples, indent=2)}
    """
    
    # 3. Model Execution
    try:
        if request.use_api:
            if not API_KEY:
                raise HTTPException(status_code=500, detail="Google API Key missing in environment.")
            
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore
            response = model.generate_content(prompt)
            raw_response = response.text
        else:
            # Local Mistral
            output = llm(prompt, max_tokens=1000, temperature=0.1)
            raw_response = output["choices"][0]["text"] # type: ignore
            
        # 4. Parse Query Results
        filtered_triples = clean_json_response(raw_response)
        
        if not isinstance(filtered_triples, list):
            # Fallback if the LLM completely fails
            filtered_triples = []
            
        # 5. Convert Filtered Triples to Nodes & Links
        nodes_dict = {}
        links = []
        
        for idx, triple in enumerate(filtered_triples):
            subj = triple.get("subject", "").strip()
            pred = triple.get("predicate", "").strip()
            obj = triple.get("object", "").strip()
            
            if not subj or not obj:
                continue
                
            if subj not in nodes_dict:
                nodes_dict[subj] = {"id": subj, "label": subj, "type": "concept"}
            if obj not in nodes_dict:
                nodes_dict[obj] = {"id": obj, "label": obj, "type": "concept"}
                
            links.append({
                "source": subj,
                "target": obj,
                "relation": pred
            })
            
        graph_data = {
            "nodes": list(nodes_dict.values()),
            "links": links
        }

        return {
            "pdf_name": request.pdf_name,
            "query": request.query,
            "graph": graph_data,
            "message": f"Found {len(links)} relevant relationships."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# ==================== ENHANCED TRIPLET STORAGE ENDPOINTS ====================

class TripletSaveRequest(BaseModel):
    pdf_name: str
    doc_id: str
    metadata: Optional[dict] = None

@insight_router.post("/triplets/save/")
async def save_triples_to_storage(request: TripletSaveRequest):
    """
    Save extracted triples to the triplet storage system with table of contents indexing.
    Automatically creates an index for efficient retrieval.
    Returns: table of contents information
    """
    try:
        # Load triples from the file saved earlier
        triples_file = os.path.join(UPLOAD_DIR, f"{request.pdf_name}_triples.json")
        if not os.path.exists(triples_file):
            raise HTTPException(status_code=404, detail="Triples file not found. Please generate concept graph first.")
        
        with open(triples_file, "r", encoding="utf-8") as f:
            triples_data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(triples_data, dict):
            triples_list = triples_data.get("triples", [])
        else:
            triples_list = triples_data
        
        # Save to triplet storage with indexing
        metadata = {**(request.metadata or {}), "pdf_name": request.pdf_name}
        storage_path = triplet_storage.save_triples(
            doc_id=request.doc_id,
            triples=triples_list,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "message": "Triples saved to indexed storage",
            "storage_path": storage_path,
            "doc_id": request.doc_id,
            "triple_count": len(triples_list),
            "table_of_contents": triplet_storage.get_table_of_contents()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving triples: {str(e)}")


class TripletQueryRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    use_api: bool = False
    use_llm_extraction: bool = True

@insight_router.post("/triplets/query/")
async def query_triplet_storage(request: TripletQueryRequest):
    """
    Query the triplet storage using intelligent indexing.
    Retrieves ONLY relevant triples based on the query keywords using table of contents.
    Minimizes data loading for efficiency.
    """
    try:
        # Use index to quickly find relevant triples
        index_results = triplet_storage.get_relevant_triples_for_query(
            query_keywords=request.query.split(),
            doc_id=request.doc_id
        )
        
        # Load only relevant triples
        relevant_triples = []
        for doc_id_iter in index_results["relevant_docs"]:
            doc_triples = triplet_storage.load_triples(doc_id_iter)
            filtered = triplet_storage.filter_triples_by_keywords(doc_triples, request.query.split())
            relevant_triples.extend(filtered)
        
        return {
            "query": request.query,
            "index_lookup_results": {
                "documents_containing_relevant_concepts": index_results["relevant_docs"],
                "concepts_matched": index_results["relevant_concepts"],
                "relations_matched": index_results["relevant_relations"],
                "database_stats": index_results["index_metadata"]
            },
            "triples_retrieved": relevant_triples,
            "retrieval_stats": {
                "total_triples_found": len(relevant_triples),
                "documents_searched": len(index_results["relevant_docs"]),
                "efficiency": f"Used index to avoid scanning {index_results['index_metadata']['total_documents'] - len(index_results['relevant_docs'])} documents"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying triplets: {str(e)}")


@insight_router.post("/triplets/answer-question/")
async def answer_question_with_graph(request: TripletQueryRequest):
    """
    Answer a user's question by retrieving relevant triples and using LLM reasoning.
    Uses table of contents for efficient retrieval, then generates intelligent answers.
    """
    try:
        # Configure retriever with API key if available
        if request.use_api and API_KEY:
            triplet_retriever.api_key = API_KEY
        
        # Answer the question using retrieved triples
        answer_result = triplet_retriever.answer_question_with_triples(
            question=request.query,
            doc_id=request.doc_id,
            use_api=request.use_api
        )
        
        return {
            "question": request.query,
            "answer": answer_result["answer"],
            "engine": answer_result.get("engine", "Local LLM"),
            "source_triples": answer_result["source_triples"],
            "retrieval_efficiency": {
                "total_triples_retrieved": answer_result["retrieval_stats"]["total_triples_retrieved"],
                "documents_searched": answer_result["retrieval_stats"]["documents_searched"],
                "concepts_matched": answer_result["retrieval_stats"]["concepts_matched"],
                "reasoning": answer_result["reasoning"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@insight_router.get("/triplets/table-of-contents/")
async def get_table_of_contents():
    """
    Get the complete table of contents of all stored triplets.
    Shows all concepts, relations, and documents indexed in the system.
    Useful for data exploration and navigation.
    """
    try:
        toc = triplet_storage.get_table_of_contents()
        return {
            "status": "success",
            "table_of_contents": toc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving table of contents: {str(e)}")


class ConceptContextRequest(BaseModel):
    concept: str
    doc_id: str

@insight_router.post("/triplets/concept-context/")
async def get_concept_context(request: ConceptContextRequest):
    """
    Get complete context around a specific concept.
    Shows all incoming and outgoing relationships for a concept.
    """
    try:
        context = triplet_retriever.get_concept_context(
            concept=request.concept,
            doc_id=request.doc_id
        )
        
        return {
            "concept": request.concept,
            "context_info": context,
            "message": f"Retrieved context for concept: {request.concept}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving concept context: {str(e)}")


class ExportTripletsRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    format: str = "json"  # json, csv, ttl

@insight_router.post("/triplets/export/")
async def export_retrieved_triples(request: ExportTripletsRequest):
    """
    Export retrieved triples in different formats (JSON, CSV, or Turtle RDF).
    Useful for integration with other systems or for data analysis.
    """
    try:
        exported_data = triplet_retriever.export_retrieved_triples(
            query=request.query,
            doc_id=request.doc_id,
            format=request.format
        )
        
        return {
            "query": request.query,
            "format": request.format,
            "data": exported_data,
            "message": f"Triples exported as {request.format.upper()}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting triplets: {str(e)}")

