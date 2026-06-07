"""
Triplet System Usage Examples with Gemini API
All examples use Gemini API for LLM operations
"""

import os
from dotenv import load_dotenv
from v2_model_services.triplet_storage import TripletStorage
from v2_model_services.triplet_retrieval import TripletRetriever

# Load environment variables (ensures GOOGLE_API_KEY is available)
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Set GOOGLE_API_KEY environment variable")


# ============================================================================
# EXAMPLE 1: Save Data from Model as Triplets
# ============================================================================
def example_save_triplets():
    """Save model-generated data as RDF triplets with indexing"""
    
    print("=" * 70)
    print("EXAMPLE 1: Saving Model Data as Triplets")
    print("=" * 70)
    
    # Initialize storage
    storage = TripletStorage("example_storage")
    
    # Your model generates this data
    model_output_triples = [
        {
            "subject": "Document Analysis",
            "predicate": "uses technique",
            "object": "Natural Language Processing"
        },
        {
            "subject": "Natural Language Processing",
            "predicate": "enables feature",
            "object": "Named Entity Recognition"
        },
    ]
    
    # Save with metadata
    file_path = storage.save_triples(
        doc_id="document_analysis_paper",
        triples=model_output_triples,
        metadata={
            "source": "Model Output",
            "model_version": "v2 with Gemini API"
        }
    )
    
    print(f"\n✓ Saved {len(model_output_triples)} triplets")
    print(f"✓ File: {file_path}")
    print(f"✓ Indexed for fast retrieval with Gemini")
    

# ============================================================================
# EXAMPLE 2: Query Triplets Using Table of Contents
# ============================================================================
def example_query_with_index():
    """Query triplets using the index (table of contents)"""
    
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Query Using Index (Table of Contents)")
    print("=" * 70)
    
    storage = TripletStorage("example_storage")
    
    # Query - the index directs us to only relevant documents
    keywords = ["nlp", "analysis"]
    
    index_results = storage.get_relevant_triples_for_query(keywords)
    
    print(f"\nKeywords: {keywords}")
    print(f"✓ Index found relevant concepts")
    print(f"✓ Only relevant docs need to be loaded")
    

# ============================================================================
# EXAMPLE 3: Use Gemini to Answer Questions About Triplets (GEMINI API)
# ============================================================================
def example_answer_question_with_gemini():
    """Use Gemini API to answer questions based on triplets"""
    
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Ask Gemini Questions About Your Data")
    print("=" * 70)
    print("🔐 Using Gemini API (not local model)")
    
    storage = TripletStorage("example_storage")
    retriever = TripletRetriever("example_storage", api_key=GEMINI_API_KEY)
    
    # Ask a question about the stored triplets
    question = "What techniques are used in document analysis?"
    
    print(f"\nQuestion: {question}\n")
    print("Retrieving relevant triplets...")
    print("Using Gemini API for intelligent keyword extraction...")
    
    retrieval = retriever.retrieve_relevant_triples(
        query=question,
        use_llm_extraction=True  # Uses Gemini for smart keyword extraction
    )
    
    print(f"\n✓ Keywords extracted by Gemini: {retrieval['keywords_used']}")
    print(f"✓ Relevant triplets found: {len(retrieval['relevant_triples'])}")
    

# ============================================================================
# EXAMPLE 4: Full Workflow - Save, Query, Answer
# ============================================================================
def example_full_workflow():
    """Complete workflow: Save model data → Index → Query → Answer with Gemini"""
    
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Full Workflow with Gemini API")
    print("=" * 70)
    
    # Step 1: Initialize with Gemini API key
    storage = TripletStorage("workflow_storage")
    retriever = TripletRetriever("workflow_storage", api_key=GEMINI_API_KEY)
    
    # Step 2: Save triplets from model
    print("\nStep 1: Saving model-generated triplets...")
    triplets = [
        {"subject": "Machine Learning", "predicate": "includes", "object": "Neural Networks"},
        {"subject": "Neural Networks", "predicate": "used in", "object": "Image Recognition"},
    ]
    storage.save_triples("ml_doc", triplets)
    print(f"   ✓ Saved {len(triplets)} triplets")
    
    # Step 3: Use Gemini to answer
    print("\nStep 2: Using Gemini API to answer question...")
    question = "What is machine learning used for?"
    
    retrieval = retriever.retrieve_relevant_triples(question, use_llm_extraction=True)
    print(f"   ✓ Found {len(retrieval['relevant_triples'])} relevant triplets")
    print(f"   ✓ Gemini extracted keywords: {retrieval['keywords_used']}")
    

# ============================================================================
# Setup Instructions
# ============================================================================
SETUP_GUIDE = """
SETUP GUIDE - Using Triplet System with Gemini API
===================================================

1. Set Environment Variable:
   - Windows: set GOOGLE_API_KEY=your_key_here
   - Linux/Mac: export GOOGLE_API_KEY=your_key_here

2. Or create .env file in backend/:
   GOOGLE_API_KEY=your_gemini_key_here

3. All functions automatically use Gemini API
   - No local model needed
   - Gemini handles all NLP tasks
   - Gemini extracts keywords from queries
   - Gemini answers questions about triplets

4. Integration points with Gemini:
   - extract_keywords_from_query() → Uses Gemini
   - answer_question_with_triples() → Uses Gemini
   - LLM-based triplet generation → Uses Gemini
"""

# ============================================================================
# RUN EXAMPLES
# ============================================================================
if __name__ == "__main__":
    print(SETUP_GUIDE)
    print("\n" + "="*70)
    print("Running Examples...")
    print("="*70)
    
    try:
        example_save_triplets()
        example_query_with_index()
        example_answer_question_with_gemini()
        example_full_workflow()
        
        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("✓ All operations used Gemini API")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

query_response = requests.post(
    f"{BASE_URL}/insight/v2/triplets/query/",
    json={
        "query": "neural networks learning",
        "doc_id": "sample-doc-001",
        "use_api": False
    }
)
query_result = query_response.json()

print(f"Query executed efficiently:")
print(f"  - Concepts found: {query_result['index_lookup_results']['concepts_matched']}")
print(f"  - Retrieved {query_result['retrieval_stats']['total_triples_found']} triples")
print(f"  - Efficiency: {query_result['retrieval_stats']['efficiency']}")


# ============================================================================
# EXAMPLE 3: Expert Mode - Ask Natural Language Questions
# ============================================================================

# Ask a natural language question - system will answer using the triples
question_response = requests.post(
    f"{BASE_URL}/insight/v2/triplets/answer-question/",
    json={
        "query": "How do artificial neural networks simulate biological learning?",
        "doc_id": "sample-doc-001",
        "use_api": True,  # Use Gemini API for better answers
        "use_llm_extraction": True  # Smart keyword extraction
    }
)
answer_result = question_response.json()

print("\nQuestion Asked:")
print(f"  Q: {answer_result['question']}")
print("\nSystem Answer:")
print(f"  A: {answer_result['answer']}")
print("\nConfidence Metrics:")
print(f"  - Used {len(answer_result['source_triples'])} source triples")
print(f"  - Searched {answer_result['retrieval_efficiency']['documents_searched']} document(s)")
print(f"  - Engine: {answer_result['engine']}")


# ============================================================================
# EXAMPLE 4: Explore the Table of Contents
# ============================================================================

# Get overview of all stored data
toc_response = requests.get(f"{BASE_URL}/insight/v2/triplets/table-of-contents/")
toc = toc_response.json()["table_of_contents"]

print("\n=== TABLE OF CONTENTS ===")
print(f"Total Documents: {toc['summary']['total_documents']}")
print(f"Total Concepts: {toc['summary']['total_concepts']}")
print(f"Total Relations: {toc['summary']['total_relations']}")

print("\nTop Concepts by Frequency:")
concepts_by_freq = sorted(
    toc['concepts_index'].items(),
    key=lambda x: x[1]['frequency'],
    reverse=True
)[:5]
for concept, info in concepts_by_freq:
    print(f"  - {concept}: appears in {info['frequency']} document(s)")

print("\nRelations found:")
for relation in list(toc['relations_index'].keys())[:5]:
    print(f"  - {relation}")


# ============================================================================
# EXAMPLE 5: Deep Dive - Explore a Concept
# ============================================================================

# See everything connected to a concept
concept_response = requests.post(
    f"{BASE_URL}/insight/v2/triplets/concept-context/",
    json={
        "concept": "Neural Networks",
        "doc_id": "sample-doc-001"
    }
)
concept_context = concept_response.json()

print(f"\n=== Exploring Concept: Neural Networks ===")
context = concept_context['context_info']

print("What Neural Networks connects to:")
for relation in context['outgoing']:
    print(f"  - {relation['predicate']} → {relation['target']}")

print("What connects to Neural Networks:")
for relation in context['incoming']:
    print(f"  - {relation['source']} → {relation['predicate']}")

print(f"Neighboring concepts: {context['neighboring_concepts']['outgoing']}")


# ============================================================================
# EXAMPLE 6: Export Data in Various Formats
# ============================================================================

# Export as JSON (default)
export_json = requests.post(
    f"{BASE_URL}/insight/v2/triplets/export/",
    json={
        "query": "machine learning",
        "doc_id": "sample-doc-001",
        "format": "json"
    }
).json()

# Export as CSV for spreadsheet
export_csv = requests.post(
    f"{BASE_URL}/insight/v2/triplets/export/",
    json={
        "query": "machine learning",
        "doc_id": "sample-doc-001",
        "format": "csv"
    }
).json()

# Save to file
with open("export_data.csv", "w") as f:
    f.write(export_csv["data"])

print("Exported data to export_data.csv")


# ============================================================================
# EXAMPLE 7: Multi-Document Workflow
# ============================================================================

# Upload multiple documents
documents = [
    "ml_basics.pdf",
    "deep_learning.pdf",
    "nlp_guide.pdf"
]

doc_ids = []
for doc_name in documents:
    # Generate triples
    with open(doc_name, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/insight/v2/concept-graph/",
            files={"file": f},
            data={"use_api": True, "max_concepts": 20}
        )
    
    # Save to storage
    doc_id = f"doc-{doc_name.replace('.pdf', '')}"
    requests.post(
        f"{BASE_URL}/insight/v2/triplets/save/",
        json={"pdf_name": doc_name, "doc_id": doc_id}
    )
    doc_ids.append(doc_id)
    print(f"Processed: {doc_name} (ID: {doc_id})")

# Now query across all documents
cross_doc_query = requests.post(
    f"{BASE_URL}/insight/v2/triplets/query/",
    json={
        "query": "transformer attention mechanism",
        "doc_id": None,  # Search all documents
        "use_llm_extraction": True
    }
)
result = cross_doc_query.json()
print(f"\nCross-document search found {result['retrieval_stats']['total_triples_found']} triples")
print(f"From {result['retrieval_stats']['documents_searched']} documents")


# ============================================================================
# EXAMPLE 8: Batch Question Answering
# ============================================================================

questions = [
    "What is machine learning?",
    "How do neural networks learn?",
    "What are transformers used for?",
    "Explain backpropagation"
]

print("\n=== Batch Q&A ===")
for question in questions:
    response = requests.post(
        f"{BASE_URL}/insight/v2/triplets/answer-question/",
        json={
            "query": question,
            "doc_id": None,  # Search all
            "use_api": True
        }
    )
    result = response.json()
    print(f"\nQ: {question}")
    print(f"A: {result['answer'][:150]}...")  # First 150 chars


# ============================================================================
# EXAMPLE 9: Performance Monitoring
# ============================================================================

import time

questions = [
    "neural networks",
    "deep learning optimization",
    "convolutional layers",
    "recurrent networks"
]

print("\n=== Performance Metrics ===")
for question in questions:
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/insight/v2/triplets/query/",
        json={
            "query": question,
            "use_llm_extraction": True
        }
    )
    elapsed = time.time() - start
    
    result = response.json()
    triples = result['retrieval_stats']['total_triples_found']
    
    print(f"Query: '{question}'")
    print(f"  Time: {elapsed*1000:.0f}ms")
    print(f"  Triples: {triples}")
    print(f"  Efficiency: {result['retrieval_stats']['efficiency']}")


# ============================================================================
# EXAMPLE 10: Integration with Frontend Component
# ============================================================================

"""
JavaScript/React example for frontend:

// Component for searching the knowledge graph
function KnowledgeGraphSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  
  const searchGraph = async (question) => {
    const response = await fetch(
      "http://localhost:8000/insight/v2/triplets/answer-question/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          use_api: true,
          use_llm_extraction: true
        })
      }
    );
    const result = await response.json();
    setResults({
      answer: result.answer,
      triples: result.source_triples,
      metrics: result.retrieval_efficiency
    });
  };
  
  return (
    <div>
      <input 
        type="text" 
        value={query} 
        onChange={e => setQuery(e.target.value)}
        placeholder="Ask about the concept graph..."
      />
      <button onClick={() => searchGraph(query)}>Search</button>
      
      {results.answer && (
        <div>
          <h3>Answer:</h3>
          <p>{results.answer}</p>
          
          <h3>Source Triples ({results.triples.length}):</h3>
          <ul>
            {results.triples.map((triple, i) => (
              <li key={i}>
                {triple.subject} 
                <strong> {triple.predicate} </strong>
                {triple.object}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
"""


# ============================================================================
# EXAMPLE 11: Error Handling
# ============================================================================

def safe_query(query, doc_id=None):
    """Wrapper for safe querying with error handling"""
    try:
        response = requests.post(
            f"{BASE_URL}/insight/v2/triplets/query/",
            json={
                "query": query,
                "doc_id": doc_id,
                "use_llm_extraction": True
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Query timed out. Try being more specific."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to server. Is it running?"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"Server error: {e.response.status_code}"}


# ============================================================================
# TESTING THE SYSTEM
# ============================================================================

if __name__ == "__main__":
    print("Testing Triplet Storage System...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/insight/v2/triplets/table-of-contents/")
        print("✓ Server is running")
    except:
        print("✗ Server is not running. Start it with: python index.py")
        exit()
    
    # Test 2: Simple query
    result = safe_query("test query")
    if "error" not in result:
        print("✓ Query system working")
    else:
        print(f"✗ Query failed: {result['error']}")
    
    print("\nAll tests completed!")
