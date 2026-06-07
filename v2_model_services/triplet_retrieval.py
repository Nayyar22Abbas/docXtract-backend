"""
Triplet Retrieval System
Efficiently retrieves relevant triplets from storage to answer user queries
Uses the index to avoid loading unnecessary data
"""

import json
from typing import List, Dict, Optional
import google.generativeai as genai  # type: ignore
from dotenv import load_dotenv
import os
from v2_model_services.triplet_storage import TripletStorage

# Load environment variables for Gemini API key
load_dotenv()

class TripletRetriever:
    """
    Retrieves relevant triplets for user queries using an intelligent lookup system.
    Minimizes data transfer by using the table of contents to fetch only needed triples.
    """
    
    def __init__(self, storage_dir: str = "triplet_storage", api_key: Optional[str] = None):
        """
        Initialize the retriever using Gemini API
        
        Args:
            storage_dir: Directory containing triplet storage
            api_key: Optional Gemini API key (uses GOOGLE_API_KEY env var if not provided)
        """
        self.storage = TripletStorage(storage_dir)
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
        try:
            genai.configure(api_key=self.api_key)  # type: ignore
        except Exception:
            # If configure fails, set it directly on the module
            pass
    
    def extract_keywords_from_query(self, query: str, use_llm: bool = False) -> List[str]:
        """
        Extract relevant keywords from user query
        
        Args:
            query: User's natural language query
            use_llm: Whether to use LLM for intelligent keyword extraction
            
        Returns:
            List of keywords to search for
        """
        if not use_llm:
            # Simple keyword extraction
            return [word.strip() for word in query.split() 
                   if len(word) > 3 and word.lower() not in 
                   ['what', 'when', 'where', 'which', 'about', 'does', 'through']]
        
        # LLM-based extraction using Gemini
        prompt = f"""Extract the main keywords from this query that would help find relevant concepts in a knowledge graph.
        Return as a JSON list of keywords.
        Query: {query}
        Return format: ["keyword1", "keyword2", ...]"""
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore
            response = model.generate_content(prompt)  # type: ignore
            keywords = json.loads(response.text)
            return keywords if isinstance(keywords, list) else []
        except Exception as e:
            print(f"Warning: LLM extraction failed ({e}), using simple extraction")
            return [word.strip() for word in query.split() if len(word) > 3]
    
    def retrieve_relevant_triples(self, query: str, doc_id: Optional[str] = None, use_llm_extraction: bool = False) -> Dict:
        """
        Main retrieval function: use index to find relevant triples efficiently
        
        Args:
            query: User's question/query
            doc_id: Optional specific document to search
            use_llm_extraction: Use LLM for keyword extraction
            
        Returns:
            {
                "query": original query,
                "keywords_used": extracted keywords,
                "index_results": table of contents lookup results,
                "relevant_triples": filtered triples,
                "retrieval_summary": statistics about retrieval
            }
        """
        # Step 1: Extract keywords from query
        keywords = self.extract_keywords_from_query(query, use_llm_extraction)
        
        # Step 2: Use table of contents to find relevant documents and concepts
        index_results = self.storage.get_relevant_triples_for_query(keywords, doc_id)
        
        relevant_docs = index_results["relevant_docs"]
        relevant_triples = []
        
        # Step 3: Load only relevant triples from index-identified documents
        for doc_id_iter in relevant_docs:
            doc_triples = self.storage.load_triples(doc_id_iter)
            # Filter by keywords
            filtered = self.storage.filter_triples_by_keywords(doc_triples, keywords)
            relevant_triples.extend(filtered)
        
        return {
            "query": query,
            "keywords_used": keywords,
            "index_lookup": {
                "docs_searched": relevant_docs,
                "concepts_found": index_results["relevant_concepts"],
                "relations_found": index_results["relevant_relations"],
                "total_candidates": index_results["index_metadata"]
            },
            "relevant_triples": relevant_triples,
            "retrieval_summary": {
                "total_triples_retrieved": len(relevant_triples),
                "documents_searched": len(relevant_docs),
                "concepts_matched": len(index_results["relevant_concepts"]),
                "relations_matched": len(index_results["relevant_relations"])
            }
        }
    
    def answer_question_with_triples(self, question: str, doc_id: Optional[str] = None,
                                    use_api: bool = False) -> Dict:
        """
        Answer a user question by retrieving relevant triples and using LLM reasoning
        
        Args:
            question: User's question about the graph
            doc_id: Optional document to search within
            use_api: Whether to use Gemini API (True) or local LLM (False)
            
        Returns:
            {
                "question": original question,
                "answer": LLM-generated answer,
                "source_triples": triples used to generate answer,
                "reasoning": brief explanation of how answer was derived
            }
        """
        # Retrieve relevant triples
        retrieval = self.retrieve_relevant_triples(question, doc_id, use_llm_extraction=True)
        relevant_triples = retrieval["relevant_triples"]
        
        if not relevant_triples:
            return {
                "question": question,
                "answer": "No relevant information found in the knowledge graph to answer your question.",
                "source_triples": [],
                "reasoning": "No triples matched the query keywords."
            }
        
        # Prepare context for LLM
        triples_context = json.dumps(relevant_triples, indent=2)
        
        prompt = f"""You are an expert at answering questions using knowledge graphs represented as RDF triples.

User Question: {question}

Relevant Knowledge Graph Triples (already filtered for relevance):
{triples_context}

Based on these triples, provide a clear and concise answer to the user's question.
Focus on using the information from the triples provided.
If the triples don't contain enough information to fully answer, state what information is available and what is missing."""
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore
            response = model.generate_content(prompt)  # type: ignore
            answer = response.text
            engine = "Gemini API"
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"
            engine = "Error"
        
        return {
            "question": question,
            "answer": answer,
            "engine": engine,
            "source_triples": relevant_triples,
            "retrieval_stats": retrieval["retrieval_summary"],
            "reasoning": f"Retrieved {len(relevant_triples)} relevant triples from {retrieval['retrieval_summary']['documents_searched']} document(s) using index lookup."
        }
    
    def get_concept_context(self, concept: str, doc_id: str) -> Dict:
        """
        Get full context around a concept (all connected triples)
        
        Args:
            concept: The concept to explore
            doc_id: The document containing the concept
            
        Returns:
            Complete context around the concept
        """
        neighbors = self.storage.get_concept_neighbors(concept, doc_id)
        
        return {
            "concept": concept,
            "context": neighbors,
            "neighboring_concepts": {
                "outgoing": [r["target"] for r in neighbors["outgoing"]],
                "incoming": [r["source"] for r in neighbors["incoming"]]
            }
        }
    
    def explain_triple(self, subject: str, predicate: str, obj: str,
                      doc_id: str, use_api: bool = False) -> str:
        """
        Generate a natural language explanation for a specific triple
        
        Args:
            subject: Subject of the triple
            predicate: Predicate/relation
            obj: Object of the triple
            doc_id: The document containing this triple
            use_api: Whether to use Gemini API
            
        Returns:
            Natural language explanation of the triple
        """
        prompt = f"""Explain this knowledge graph relationship in clear, simple language:
Subject: {subject}
Relation: {predicate}
Object: {obj}

Provide a 1-2 sentence explanation of what this relationship means."""
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore
            response = model.generate_content(prompt)  # type: ignore
            explanation = response.text
        except:
            explanation = f"{subject} {predicate} {obj}"
        
        return explanation
    
    def export_retrieved_triples(self, query: str, doc_id: Optional[str] = None,
                                format: str = "json") -> str:
        """
        Export retrieved triples in various formats
        
        Args:
            query: The query to use for retrieval
            doc_id: Optional document filter
            format: Output format ('json', 'csv', 'ttl' for turtle RDF)
            
        Returns:
            Formatted string of triples
        """
        retrieval = self.retrieve_relevant_triples(query, doc_id)
        triples = retrieval["relevant_triples"]
        
        if format == "json":
            return json.dumps(triples, indent=2)
        
        elif format == "csv":
            lines = ["Subject,Predicate,Object"]
            for triple in triples:
                subject = triple.get("subject", "").replace(",", "\\,")
                predicate = triple.get("predicate", "").replace(",", "\\,")
                obj = triple.get("object", "").replace(",", "\\,")
                lines.append(f'"{subject}","{predicate}","{obj}"')
            return "\n".join(lines)
        
        elif format == "ttl":
            lines = [f"# Triples for: {query}\n"]
            for triple in triples:
                subject = f":{triple.get('subject', '').replace(' ', '_')}"
                predicate = f":{triple.get('predicate', '').replace(' ', '_')}"
                obj = f":{triple.get('object', '').replace(' ', '_')}"
                lines.append(f"{subject} {predicate} {obj} .")
            return "\n".join(lines)
        
        else:
            return json.dumps(triples, indent=2)
