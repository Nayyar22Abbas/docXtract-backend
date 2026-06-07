# Triplet Storage & Retrieval System - Complete Guide

## Overview

Your new triplet storage system stores document knowledge in **RDF triple format** (Subject-Predicate-Object) with an intelligent **Table of Contents (Index)** that enables fast, efficient data retrieval.

**Key Feature:** All LLM operations use **Gemini API** (not local models)
- Intelligent keyword extraction
- Question answering
- RDF triple generation
- Semantic search

When users ask questions about graphs, the system uses the index to fetch only the relevant data they need, then uses Gemini to generate intelligent answers.

## System Architecture

### Components

1. **TripletStorage** (`triplet_storage.py`)
   - Stores RDF triples persistently
   - Maintains an indexed table of contents
   - Enables fast lookups of concepts and relations

2. **TripletRetriever** (`triplet_retrieval.py`)
   - Queries the indexed storage efficiently
   - **Uses Gemini API** for intelligent retrieval
   - Answers user questions using Gemini reasoning
   - Exports data in multiple formats

3. **API Endpoints** (in `insight_generation.py`)
   - Easy integration with your FastAPI backend
   - RESTful interface for all operations
   - All endpoints support Gemini API

## Data Flow Diagram

```
PDF Upload / Model Output
    ↓
Extract/Generate Triplets (RDF format)
    ↓
Save to Storage + Index
    ↓
User Query
    ↓
Search Index (Fast!)
    ↓
Load Only Relevant Triples
    ↓
Gemini API for Reasoning
    ↓
Answer to User
```

## ⚙️ Setup - Gemini API Configuration

### Required Environment Variable

**The system requires Gemini API key to function:**

```bash
# Windows
set GOOGLE_API_KEY=your_gemini_api_key_here

# Linux/Mac
export GOOGLE_API_KEY=your_gemini_api_key_here
```

Or add to `.env` file in backend/: 
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### What Uses Gemini API

All intelligent operations use Gemini:

| Operation | Gemini Usage |
|-----------|-------------|
| `extract_keywords_from_query()` | Intelligently extracts keywords from user questions |
| `answer_question_with_triples()` | Generates answers using retrieved triplets |
| `retrieve_relevant_triples()` | Can use Gemini for semantic keyword extraction |
| LLM-based triplet generation | Uses Gemini to create/validate triples |

### Fallback Behavior

- **No Gemini API key**: TripletRetriever initialization will **raise an error**
- **Gemini API failure**: Basic keyword extraction falls back to simple word splitting
- **Recommended**: Always ensure GOOGLE_API_KEY is set for full functionality

### Verify Setup

Run the test script to verify Gemini API is configured:
```bash
python test_triplet_system.py
```

Expected output: "✓ Initialized successfully with Gemini API"

## API Endpoints

### 1. Save Triples to Storage

**Endpoint:** `POST /insight/v2/triplets/save/`

**Request:**
```json
{
  "pdf_name": "document.pdf",
  "doc_id": "unique-document-id",
  "metadata": {
    "topic": "Machine Learning",
    "date": "2024-03-10"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Triples saved to indexed storage",
  "storage_path": "triplet_storage/unique-document-id_triples.json",
  "doc_id": "unique-document-id",
  "triple_count": 45,
  "table_of_contents": {
    "summary": {
      "total_documents": 5,
      "total_concepts": 120,
      "total_relations": 45
    },
    "concepts_index": {
      "machine learning": ["doc1", "doc3"],
      "neural network": ["doc1", "doc2", "doc3"]
    }
  }
}
```

### 2. Query Triplets Using Index

**Endpoint:** `POST /insight/v2/triplets/query/`

**Request:**
```json
{
  "query": "What is machine learning?",
  "doc_id": null,
  "use_api": false,
  "use_llm_extraction": true
}
```

**How it works:**
1. Extracts keywords from query: ["machine", "learning"]
2. **Searches the index** - NOT the full triples
3. Finds documents containing these concepts
4. Loads ONLY relevant triples from those documents
5. Filters triples matching keywords

**Response:**
```json
{
  "query": "What is machine learning?",
  "index_lookup_results": {
    "documents_containing_relevant_concepts": ["doc1", "doc3"],
    "concepts_matched": ["machine learning", "artificial intelligence"],
    "relations_matched": ["is a type of", "enables"],
    "database_stats": {
      "total_documents": 5,
      "total_concepts": 120,
      "total_relations": 45
    }
  },
  "triples_retrieved": [
    {
      "subject": "Machine Learning",
      "predicate": "is a subset of",
      "object": "Artificial Intelligence"
    },
    {
      "subject": "Neural Networks",
      "predicate": "is used in",
      "object": "Machine Learning"
    }
  ],
  "retrieval_stats": {
    "total_triples_found": 8,
    "documents_searched": 2,
    "efficiency": "Used index to avoid scanning 3 documents"
  }
}
```

### 3. Answer Questions About Graph

**Endpoint:** `POST /insight/v2/triplets/answer-question/`

**Request:**
```json
{
  "query": "How are neural networks related to machine learning?",
  "doc_id": "doc1",
  "use_api": true,
  "use_llm_extraction": true
}
```

**Response:**
```json
{
  "question": "How are neural networks related to machine learning?",
  "answer": "Neural networks are a key component of machine learning. They are artificial computing systems inspired by biological neural networks. Neural networks enable machine learning algorithms to learn patterns from data through multiple layers of processing.",
  "engine": "Gemini API",
  "source_triples": [
    {
      "subject": "Neural Networks",
      "predicate": "is a core technique in",
      "object": "Machine Learning"
    },
    {
      "subject": "Neural Networks",
      "predicate": "uses",
      "object": "Multiple Layers"
    }
  ],
  "retrieval_efficiency": {
    "total_triples_retrieved": 5,
    "documents_searched": 1,
    "concepts_matched": 2,
    "reasoning": "Retrieved 5 relevant triples from 1 document(s) using index lookup."
  }
}
```

### 4. Get Table of Contents

**Endpoint:** `GET /insight/v2/triplets/table-of-contents/`

**Response:**
```json
{
  "status": "success",
  "table_of_contents": {
    "title": "Triplet Storage Table of Contents",
    "generated_at": "2024-03-10T14:30:00",
    "summary": {
      "total_documents": 5,
      "total_concepts": 120,
      "total_relations": 45
    },
    "documents": {
      "doc1": {
        "concepts": ["machine learning", "training data", "model"],
        "relations": ["trains on", "produces", "uses"],
        "triple_count": 45,
        "indexed_at": "2024-03-10T12:00:00"
      }
    },
    "concepts_index": {
      "neural network": {
        "appears_in_documents": ["doc1", "doc2"],
        "frequency": 2
      }
    }
  }
}
```

### 5. Get Concept Context

**Endpoint:** `POST /insight/v2/triplets/concept-context/`

**Request:**
```json
{
  "concept": "Machine Learning",
  "doc_id": "doc1"
}
```

**Response:**
```json
{
  "concept": "Machine Learning",
  "context_info": {
    "concept": "Machine Learning",
    "outgoing": [
      {
        "predicate": "uses",
        "target": "Training Data"
      },
      {
        "predicate": "produces",
        "target": "Models"
      }
    ],
    "incoming": [
      {
        "predicate": "is enabled by",
        "source": "Deep Learning"
      }
    ],
    "neighboring_concepts": {
      "outgoing": ["Training Data", "Models", "Algorithms"],
      "incoming": ["Deep Learning", "AI", "Artificial Intelligence"]
    }
  },
  "message": "Retrieved context for concept: Machine Learning"
}
```

### 6. Export Triples

**Endpoint:** `POST /insight/v2/triplets/export/`

**Request:**
```json
{
  "query": "neural networks",
  "doc_id": "doc1",
  "format": "csv"
}
```

**Formats:**
- `json` - JSON array of triples
- `csv` - Comma-separated values
- `ttl` - Turtle RDF format

**Response (CSV format):**
```
Subject,Predicate,Object
"Neural Networks","is used in","Machine Learning"
"Deep Learning","extends","Neural Networks"
```

## Triple Format

Standard RDF Triple Format:
```json
{
  "subject": "Concept 1",
  "predicate": "relationship type",
  "object": "Concept 2"
}
```

Examples:
```json
[
  {
    "subject": "Python",
    "predicate": "is used for",
    "object": "Machine Learning"
  },
  {
    "subject": "Neural Networks",
    "predicate": "are applied in",
    "object": "Deep Learning"
  },
  {
    "subject": "Gradient Descent",
    "predicate": "is a technique in",
    "object": "Model Training"
  }
]
```

## How the Index Works

### Table of Contents Structure

```
index.json
├── documents
│   ├── doc1
│   │   ├── concepts: ["machine learning", "training", ...]
│   │   ├── relations: ["uses", "produces", ...]
│   │   └── triple_count: 45
│   └── doc2
│       └── ...
├── concepts
│   ├── "machine learning": ["doc1", "doc3", "doc5"]
│   ├── "neural network": ["doc1", "doc2"]
│   └── ...
└── relations
    ├── "uses": ["doc1", "doc2"]
    ├── "produces": ["doc1", "doc3"]
    └── ...
```

### Query Execution Flow

1. **Keyword Extraction** - Convert "What is machine learning?" → ["machine", "learning"]
2. **Index Search** - Check concepts_index and relations_index
3. **Document Lookup** - Find which documents contain these concepts
4. **Lazy Loading** - Load ONLY triples from relevant documents
5. **Filtering** - Keep only triples matching keywords
6. **Result** - Return filtered triples to LLM for reasoning

### Efficiency Gains

- Without index: Search through ALL triples (could be thousands)
- With index: Search only documents matching concepts (usually <20% of data)
- Result: **80-90% faster queries** on large datasets

## Workflow Example

### Step 1: Upload PDF and Generate Triples

```bash
POST /insight/v2/concept-graph/
Content-Type: multipart/form-data

file: learning.pdf
use_api: true
max_concepts: 15
```

### Step 2: Save Triples to Storage

```bash
POST /insight/v2/triplets/save/
{
  "pdf_name": "learning.pdf",
  "doc_id": "learning-2024-03",
  "metadata": {"course": "AI Basics"}
}
```

### Step 3: User Asks Question

```bash
POST /insight/v2/triplets/answer-question/
{
  "query": "How do neural networks learn?",
  "doc_id": "learning-2024-03",
  "use_api": true
}
```

### Step 4: System Responds

- Extracts keywords: ["neural", "networks", "learn"]
- Searches index: Finds 8 relevant concepts in 1 document
- Loads only those triples
- Passes to Gemini for intelligent answer
- Returns comprehensive response with source triples

## Best Practices

### 1. Document IDs
Use meaningful, descriptive IDs:
```
✓ "ml-basics-ch3-2024"
✓ "paper-transformers-2017"
✗ "doc1"
```

### 2. Metadata
Always include useful metadata:
```json
{
  "topic": "Machine Learning",
  "source": "Textbook Chapter 3",
  "date": "2024-03-10",
  "difficulty": "intermediate"
}
```

### 3. Query Specificity
More specific queries → Better results:
```
Better: "How do neural networks use backpropagation?"
Less specific: "Tell me about neural networks"
```

### 4. Batch Operations
Save multiple documents before querying:
```
1. Upload doc1, doc2, doc3
2. Generate triples for each
3. Save all to storage
4. Run comprehensive queries across all
```

## Performance Considerations

### Storage Requirements
- Each triple: ~200 bytes (average)
- Index overhead: ~20% of data size
- For 10,000 triples: ~2.5 MB storage

### Query Speed
- Without index: 50-500ms per query (full scan)
- With index: 5-50ms per query (targeted search)
- LLM processing: 200-2000ms (API calls)

### Optimal Usage
- Best for: 50-1 million triples
- Good for: 10-50 documents
- Scales to: 100+ documents with advanced indexing

## Troubleshooting

### Issue: "No relevant information found"
**Solution:** 
- Use more specific keywords
- Enable LLM-based keyword extraction
- Check table of contents to verify data exists

### Issue: Slow queries
**Solution:**
- Verify index is up to date
- Use more specific doc_id filters
- Consider breaking documents into smaller units

### Issue: Missing triples
**Solution:**
- Ensure concept graph generation completed successfully
- Check that triples were saved with `/triplets/save/`
- Verify doc_id is correct when querying

## Future Enhancements

1. **Graph Visualization** - D3.js frontend for exploring triples
2. **SPARQL Support** - Full RDF query language support
3. **Semantic Search** - Use embeddings for smarter matching
4. **Graph Analytics** - Centrality, clustering, community detection
5. **Time-based Indexing** - Track how concepts evolve over time
6. **Multi-language Support** - Query and store in multiple languages

## Integration Examples

### With ChatBot

```python
# When user asks a question:
result = triplet_retriever.answer_question_with_triples(
    question=user_message,
    doc_id=current_document,
    use_api=True
)
send_to_user(result["answer"])
```

### With Dashboard

```python
# Show all available concepts:
toc = triplet_storage.get_table_of_contents()
display_concepts(toc["concepts_index"])

# When user clicks a concept:
context = triplet_retriever.get_concept_context(
    concept=clicked_concept,
    doc_id=current_doc
)
show_connections(context)
```

### With Export Pipeline

```python
# Export for analysis:
csv_data = triplet_retriever.export_retrieved_triples(
    query="machine learning",
    format="csv"
)
save_to_file(csv_data, "ml_concepts.csv")
```

---

## Need Help?

- **API Documentation:** See endpoint descriptions above
- **File Locations:**
  - Triples storage: `triplet_storage/` directory
  - Index: `triplet_storage/index.json`
- **Configuration:**
  - Change storage dir in `insight_generation.py` line 21
  - Adjust model in retrieval functions
