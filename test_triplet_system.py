#!/usr/bin/env python
"""
Test & Demo Script for Triplet Storage System
Run this to verify the system is working correctly with Gemini API
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v2_model_services.triplet_storage import TripletStorage
from v2_model_services.triplet_retrieval import TripletRetriever

def demo_triplet_system():
    """Demonstrate the triplet storage and retrieval system"""
    
    print("=" * 70)
    print("TRIPLET STORAGE SYSTEM - DEMO")
    print("=" * 70)
    
    # Initialize
    print("\n1. Initializing Triplet Storage System with Gemini API...")
    storage = TripletStorage("triplet_storage_demo")
    
    # Get Gemini API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   ❌ Error: GOOGLE_API_KEY not found in environment")
        print("   Please set GOOGLE_API_KEY environment variable")
        return
    
    retriever = TripletRetriever("triplet_storage_demo", api_key=api_key)
    print("   ✓ Initialized successfully with Gemini API")
    
    # Create sample triples
    print("\n2. Creating sample triples...")
    sample_triples = [
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
            "subject": "Deep Learning",
            "predicate": "is a subset of",
            "object": "Machine Learning"
        },
        {
            "subject": "TensorFlow",
            "predicate": "is a library for",
            "object": "Deep Learning"
        },
        {
            "subject": "Gradient Descent",
            "predicate": "is used in",
            "object": "Neural Network Training"
        },
        {
            "subject": "Backpropagation",
            "predicate": "is used in",
            "object": "Neural Network Training"
        },
        {
            "subject": "Convolutional Networks",
            "predicate": "are used for",
            "object": "Image Processing"
        },
        {
            "subject": "Recurrent Networks",
            "predicate": "are used for",
            "object": "Sequence Processing"
        },
        {
            "subject": "Transformers",
            "predicate": "revolutionized",
            "object": "Natural Language Processing"
        },
        {
            "subject": "BERT",
            "predicate": "is built on",
            "object": "Transformers"
        }
    ]
    print(f"   ✓ Created {len(sample_triples)} sample triples")
    
    # Save triples
    print("\n3. Saving triples to indexed storage...")
    storage.save_triples(
        doc_id="ml-basics-2024",
        triples=sample_triples,
        metadata={"topic": "Machine Learning Basics", "date": "2024-03"}
    )
    print("   ✓ Triples saved with index")
    
    # Query index
    print("\n4. Testing Index-Based Retrieval...")
    keywords = ["neural", "networks"]
    index_results = storage.get_relevant_triples_for_query(keywords)
    print(f"   Keywords: {keywords}")
    print(f"   Concepts found: {index_results['relevant_concepts']}")
    print(f"   Relations found: {index_results['relevant_relations']}")
    print(f"   Documents to search: {index_results['relevant_docs']}")
    
    # Load and filter triples
    print("\n5. Loading and filtering triples...")
    doc_triples = storage.load_triples("ml-basics-2024")
    filtered = storage.filter_triples_by_keywords(doc_triples, keywords)
    print(f"   Found {len(filtered)} relevant triples:")
    for i, triple in enumerate(filtered, 1):
        print(f"   {i}. {triple['subject']} → {triple['predicate']} → {triple['object']}")
    
    # Get table of contents
    print("\n6. Viewing Table of Contents...")
    toc = storage.get_table_of_contents()
    print(f"   Total documents: {toc['summary']['total_documents']}")
    print(f"   Total concepts: {toc['summary']['total_concepts']}")
    print(f"   Total relations: {toc['summary']['total_relations']}")
    print(f"   \n   Concepts index sample:")
    for concept in list(toc['concepts_index'].keys())[:3]:
        freq = toc['concepts_index'][concept]['frequency']
        print(f"     - {concept}: appears in {freq} document(s)")
    
    # Test retriever
    print("\n7. Testing TripletRetriever...")
    retrieval = retriever.retrieve_relevant_triples(
        query="How are neural networks used in deep learning?"
    )
    print(f"   Query: '{retrieval['query']}'")
    print(f"   Keywords extracted: {retrieval['keywords_used']}")
    print(f"   Concepts matched: {retrieval['index_lookup']['concepts_found']}")
    print(f"   Triples retrieved: {retrieval['retrieval_summary']['total_triples_retrieved']}")
    
    # Concept neighbors
    print("\n8. Exploring Concept Context...")
    concept = "Machine Learning"
    neighbors = retriever.get_concept_context(concept, "ml-basics-2024")
    print(f"   Concept: {concept}")
    print(f"   Outgoing relationships:")
    for rel in neighbors['context']['outgoing']:
        print(f"     • {rel['predicate']} → {rel['target']}")
    print(f"   Incoming relationships:")
    for rel in neighbors['context']['incoming']:
        print(f"     • {rel['source']} → {rel['predicate']}")
    
    # Export formats
    print("\n9. Testing Export Formats...")
    
    # JSON export
    json_export = retriever.export_retrieved_triples(
        query="neural networks",
        doc_id="ml-basics-2024",
        format="json"
    )
    print(f"   JSON export (first 100 chars): {json_export[:100]}...")
    
    # CSV export
    csv_export = retriever.export_retrieved_triples(
        query="neural networks",
        doc_id="ml-basics-2024",
        format="csv"
    )
    print(f"   CSV export:")
    for line in csv_export.split('\n')[:3]:
        print(f"     {line}")
    
    # Get system statistics
    print("\n10. System Statistics")
    print(f"   Storage directory: triplet_storage_demo/")
    print(f"   Index file: triplet_storage_demo/index.json")
    import glob
    triplet_files = glob.glob("triplet_storage_demo/*_triples.json")
    print(f"   Triplet files: {len(triplet_files)}")
    
    # Performance test
    print("\n11. Performance Test")
    import time
    
    queries = [
        "machine learning",
        "neural networks",
        "deep learning training",
        "image processing"
    ]
    
    print("   Query time measurements:")
    for query in queries:
        start = time.time()
        result = retriever.retrieve_relevant_triples(query)
        elapsed = (time.time() - start) * 1000
        triples = result['retrieval_summary']['total_triples_retrieved']
        print(f"   Query: '{query:30s}' → {elapsed:6.1f}ms ({triples} triples)")
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Check triplet_storage_demo/ directory for stored data")
    print("2. Review TRIPLET_SYSTEM_GUIDE.md for detailed documentation")
    print("3. Check TRIPLET_USAGE_EXAMPLES.py for API usage patterns")
    print("4. Run the backend and test the REST API endpoints")
    print("\nAPI Endpoints available:")
    print("  • POST /insight/v2/triplets/save/")
    print("  • POST /insight/v2/triplets/query/")
    print("  • POST /insight/v2/triplets/answer-question/")
    print("  • GET  /insight/v2/triplets/table-of-contents/")
    print("  • POST /insight/v2/triplets/concept-context/")
    print("  • POST /insight/v2/triplets/export/")
    print("\n")

if __name__ == "__main__":
    try:
        demo_triplet_system()
    except Exception as e:
        print(f"\n✗ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
