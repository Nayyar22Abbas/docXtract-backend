
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

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
mock_config_db.pdfconn = MagicMock()

from v2_model_services.embeddding_faiss_index import build_index, retrieve
from v2_model_services.summary_generation import ask_mistral
from routes.v2.pdf_summary_model import summarize_upload_pdf_model

class TestRAG(unittest.TestCase):
    
    @patch("v2_model_services.embeddding_faiss_index.embedder")
    @patch("v2_model_services.embeddding_faiss_index.faiss")
    def test_build_index_and_retrieve(self, mock_faiss, mock_embedder):
        # Setup mocks
        mock_embedder.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_index = MagicMock()
        mock_faiss.IndexFlatL2.return_value = mock_index
        mock_index.search.return_value = (None, np.array([[0, 1]])) # Return indices 0 and 1
        
        chunks = ["chunk1", "chunk2"]
        
        # Test Build
        index, embeddings = build_index(chunks)
        mock_embedder.encode.assert_called()
        mock_index.add.assert_called()
        
        # Test Retrieve
        result = retrieve("query", chunks, index)
        assert "chunk1" in result
        assert "chunk2" in result

    @patch("routes.v2.pdf_summary_model.extract_text_from_pdf")
    @patch("routes.v2.pdf_summary_model.pdfconn")
    @patch("routes.v2.pdf_summary_model.split_into_chapters_smart")
    @patch("v2_model_services.summary_generation.llm")
    @patch("routes.v2.pdf_summary_model.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_upload_route_structure(self, mock_open, mock_makedirs, mock_llm, mock_split, mock_pdfconn, mock_extract):
        try:
            # Setup mocks
            mock_extract.return_value = "Mock PDF Content"
            mock_pdfconn.insert_one.return_value.inserted_id = "mock_id_123"
            mock_llm.return_value = {"choices": [{"text": "Summary Content"}]}
            mock_split.return_value = [("Chapter 1", "Content 1")]
            
            # Mock UploadFile
            mock_file = MagicMock()
            mock_file.filename = "test.pdf"
            
            from routes.v2.pdf_summary_model import summarize_upload_pdf_model
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            mock_file.read = asyncio.coroutine(lambda: b"fake content")
            
            # Call the route
            response = loop.run_until_complete(summarize_upload_pdf_model(file=mock_file))
            
            # Check structure
            assert "summary" in response
            assert "chapter_summaries" in response
            assert "pdf_id" in response
            assert response["summary"] == "Summary Content"
            assert "Chapter 1" in response["chapter_summaries"]
        except Exception as e:
            with open("error.log", "w") as f:
                import traceback
                f.write(traceback.format_exc())
            raise


if __name__ == "__main__":
    unittest.main()
