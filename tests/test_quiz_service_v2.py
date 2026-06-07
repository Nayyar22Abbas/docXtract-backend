import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import asyncio

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules["llama_cpp"] = MagicMock()
sys.modules["pdfplumber"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["faiss"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.mongo_client"] = MagicMock()

# Mock config.db
mock_config_db = MagicMock()
sys.modules["config.db"] = mock_config_db
mock_config_db.quizconn = MagicMock()

# Import the service to test
# We need to mock the imports inside generate_quiz_mistral
with patch("v2_model_services.embeddding_faiss_index.SentenceTransformer"), \
     patch("v2_model_services.embeddding_faiss_index.faiss"), \
     patch("routes.v2.model_load.Llama"):
    from v2_model_services.quiz_generation_model import generate_quiz_mistral

class TestQuizServiceV2(unittest.TestCase):
    
    @patch("v2_model_services.quiz_generation_model.extract_text_from_pdf")
    @patch("v2_model_services.quiz_generation_model.build_index")
    @patch("v2_model_services.quiz_generation_model.retrieve")
    @patch("v2_model_services.quiz_generation_model.llm")
    def test_generate_quiz_mistral_success(self, mock_llm, mock_retrieve, mock_build, mock_extract):
        # Setup mocks
        mock_extract.return_value = "This is a test document about AI. AI is intelligence demonstrated by machines."
        mock_build.return_value = (MagicMock(), MagicMock())
        mock_retrieve.return_value = "AI is intelligence demonstrated by machines."
        
        # Mock Mistral JSON response
        mock_quiz_json = {
            "document_type": "Research Paper",
            "quiz": {
                "mcqs": [{"question": "What is AI?", "options": {"A": "Machine intelligence", "B": "Human intelligence", "C": "Animal intelligence", "D": "None"}, "correct_answer": "A", "difficulty": "Easy", "explanation": "AI is machine intelligence."}],
                "short_answer": [{"question": "Explain AI.", "sample_answer": "AI is machine intelligence.", "difficulty": "Medium"}],
                "true_false": [{"statement": "AI is intelligence.", "correct_answer": True, "justification": "Yes."}]
            }
        }
        mock_llm.return_value = {"choices": [{"text": "```json\n" + json.dumps(mock_quiz_json) + "\n```"}]}
        
        import json
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_quiz_mistral("mock_path.pdf"))
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["document_type"], "Research Paper")
        self.assertIn("quiz", result)
        self.assertEqual(len(result["quiz"]["mcqs"]), 1)
        
    @patch("v2_model_services.quiz_generation_model.extract_text_from_pdf")
    def test_generate_quiz_mistral_no_text(self, mock_extract):
        mock_extract.return_value = ""
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_quiz_mistral("mock_path.pdf"))
        
        self.assertNone(result)

if __name__ == "__main__":
    unittest.main()
