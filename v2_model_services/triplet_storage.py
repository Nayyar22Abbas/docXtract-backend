"""
Triplet Storage System with Table of Contents Index
Stores RDF triples in structured format with indexing for fast retrieval
"""

import json
import os
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime

class TripletStorage:
    """
    Manages storage and indexing of RDF triples.
    Stores triples and maintains an index (table of contents) for fast lookup.
    """
    
    def __init__(self, storage_dir: str = "triplet_storage"):
        """
        Initialize triplet storage system
        
        Args:
            storage_dir: Directory to store triplet files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.index_file = os.path.join(storage_dir, "index.json")
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load the table of contents index"""
        if os.path.exists(self.index_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "documents": {},
            "concepts": {},  # concept -> list of doc_ids
            "relations": {},  # predicate -> list of doc_ids
            "created_at": datetime.now().isoformat()
        }
    
    def _save_index(self):
        """Save the updated index"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2)
    
    def save_triples(self, doc_id: str, triples: List[Dict], metadata: Optional[Dict] = None) -> str:
        """
        Save RDF triples for a document with indexing
        
        Args:
            doc_id: Unique document identifier
            triples: List of triples [{"subject": "...", "predicate": "...", "object": "..."}]
            metadata: Optional metadata about the document
            
        Returns:
            File path where triples are stored
        """
        # Create document triplet file
        triplet_file = os.path.join(self.storage_dir, f"{doc_id}_triples.json")
        
        # Prepare document data
        doc_data = {
            "doc_id": doc_id,
            "triples": triples,
            "metadata": metadata or {},
            "saved_at": datetime.now().isoformat(),
            "triple_count": len(triples)
        }
        
        # Save triplets
        with open(triplet_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, indent=2)
        
        # Update index
        self._update_index(doc_id, triples)
        
        return triplet_file
    
    def _update_index(self, doc_id: str, triples: List[Dict]):
        """Update the table of contents index with new triples"""
        
        # Extract all concepts and relations
        concepts = set()
        relations = set()
        
        for triple in triples:
            subject = triple.get("subject", "").lower().strip()
            predicate = triple.get("predicate", "").lower().strip()
            obj = triple.get("object", "").lower().strip()
            
            if subject:
                concepts.add(subject)
            if obj:
                concepts.add(obj)
            if predicate:
                relations.add(predicate)
        
        # Add document to index
        self.index["documents"][doc_id] = {
            "concepts": list(concepts),
            "relations": list(relations),
            "triple_count": len(triples),
            "indexed_at": datetime.now().isoformat()
        }
        
        # Update concept index
        for concept in concepts:
            if concept not in self.index["concepts"]:
                self.index["concepts"][concept] = []
            if doc_id not in self.index["concepts"][concept]:
                self.index["concepts"][concept].append(doc_id)
        
        # Update relation index
        for relation in relations:
            if relation not in self.index["relations"]:
                self.index["relations"][relation] = []
            if doc_id not in self.index["relations"][relation]:
                self.index["relations"][relation].append(doc_id)
        
        self._save_index()
    
    def get_relevant_triples_for_query(self, query_keywords: List[str], doc_id: Optional[str] = None) -> Dict:
        """
        Use table of contents to quickly find relevant triples for a query
        
        Args:
            query_keywords: List of keywords from the user query
            doc_id: Optional specific document to search within
            
        Returns:
            {
                "relevant_docs": [...],
                "relevant_concepts": [...],
                "relevant_relations": [...],
                "triples_to_fetch": [list of doc_ids to load and search]
            }
        """
        relevant_docs = set()
        relevant_concepts = set()
        relevant_relations = set()
        
        query_keywords_lower = [kw.lower() for kw in query_keywords]
        
        # If specific doc requested, only search that doc
        if doc_id:
            if doc_id in self.index["documents"]:
                relevant_docs.add(doc_id)
        else:
            # Search across all concepts and relations in index
            for concept in self.index["concepts"]:
                for keyword in query_keywords_lower:
                    if keyword in concept or concept in keyword:
                        relevant_concepts.add(concept)
                        relevant_docs.update(self.index["concepts"][concept])
                        break
            
            for relation in self.index["relations"]:
                for keyword in query_keywords_lower:
                    if keyword in relation or relation in keyword:
                        relevant_relations.add(relation)
                        relevant_docs.update(self.index["relations"][relation])
                        break
        
        return {
            "relevant_docs": list(relevant_docs),
            "relevant_concepts": list(relevant_concepts),
            "relevant_relations": list(relevant_relations),
            "index_metadata": {
                "total_documents": len(self.index["documents"]),
                "total_concepts": len(self.index["concepts"]),
                "total_relations": len(self.index["relations"])
            }
        }
    
    def load_triples(self, doc_id: str) -> List[Dict]:
        """Load triples for a specific document"""
        triplet_file = os.path.join(self.storage_dir, f"{doc_id}_triples.json")
        
        if not os.path.exists(triplet_file):
            return []
        
        with open(triplet_file, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        
        return doc_data.get("triples", [])
    
    def filter_triples_by_keywords(self, triples: List[Dict], keywords: List[str]) -> List[Dict]:
        """
        Filter triples that match any of the keywords
        
        Args:
            triples: List of triples to filter
            keywords: Keywords to match
            
        Returns:
            Filtered list of triples
        """
        keywords_lower = [kw.lower() for kw in keywords]
        filtered = []
        
        for triple in triples:
            subject = triple.get("subject", "").lower()
            predicate = triple.get("predicate", "").lower()
            obj = triple.get("object", "").lower()
            
            # Check if any keyword matches subject, predicate, or object
            for keyword in keywords_lower:
                if keyword in subject or keyword in predicate or keyword in obj:
                    filtered.append(triple)
                    break
        
        return filtered
    
    def get_table_of_contents(self) -> Dict:
        """
        Get a comprehensive table of contents of all stored data
        
        Returns:
            Structured table of contents with all concepts, relations, and documents
        """
        return {
            "title": "Triplet Storage Table of Contents",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_documents": len(self.index["documents"]),
                "total_concepts": len(self.index["concepts"]),
                "total_relations": len(self.index["relations"])
            },
            "documents": self.index["documents"],
            "concepts_index": {
                concept: {
                    "appears_in_documents": docs,
                    "frequency": len(docs)
                }
                for concept, docs in self.index["concepts"].items()
            },
            "relations_index": {
                relation: {
                    "appears_in_documents": docs,
                    "frequency": len(docs)
                }
                for relation, docs in self.index["relations"].items()
            }
        }
    
    def get_concept_neighbors(self, concept: str, doc_id: str) -> Dict:
        """
        Get all triples where a concept is subject or object
        
        Args:
            concept: The concept to find neighbors for
            doc_id: The document containing the concept
            
        Returns:
            Dictionary with connected concepts and relations
        """
        triples = self.load_triples(doc_id)
        concept_lower = concept.lower()
        
        outgoing_relations = []  # concept is subject
        incoming_relations = []  # concept is object
        
        for triple in triples:
            subject = triple.get("subject", "").lower()
            predicate = triple.get("predicate", "")
            obj = triple.get("object", "").lower()
            
            if subject == concept_lower:
                outgoing_relations.append({
                    "predicate": predicate,
                    "target": triple.get("object", "")
                })
            elif obj == concept_lower:
                incoming_relations.append({
                    "predicate": predicate,
                    "source": triple.get("subject", "")
                })
        
        return {
            "concept": concept,
            "outgoing": outgoing_relations,
            "incoming": incoming_relations
        }
    
    def search_triples(self, query: str, doc_id: Optional[str] = None) -> List[Dict]:
        """
        Search triples by exact match on any field
        
        Args:
            query: Search query
            doc_id: Optional document to limit search to
            
        Returns:
            List of matching triples
        """
        query_lower = query.lower()
        results = []
        
        docs_to_search = [doc_id] if doc_id else self.index["documents"].keys()
        
        for search_doc_id in docs_to_search:
            triples = self.load_triples(search_doc_id)
            for triple in triples:
                if (query_lower in triple.get("subject", "").lower() or
                    query_lower in triple.get("predicate", "").lower() or
                    query_lower in triple.get("object", "").lower()):
                    results.append({
                        **triple,
                        "source_doc": search_doc_id
                    })
        
        return results
