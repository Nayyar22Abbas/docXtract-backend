
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mocking dependencies
mock_llama = MagicMock()
sys.modules["llama_cpp"] = mock_llama

mock_pdfplumber = MagicMock()
sys.modules["pdfplumber"] = mock_pdfplumber

mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.mongo_client"] = MagicMock()

# Also mock config.db to avoid connection attempts
mock_config_db = MagicMock()
sys.modules["config.db"] = mock_config_db
mock_config_db.pdfconn = MagicMock()

from v2_model_services.summary_generation import generate_academic_summary_stream
from routes.v2.pdf_summary_model import pdfsummarymodel

class TestStreaming(unittest.TestCase):
    
    @patch("v2_model_services.summary_generation.llm")
    def test_generate_academic_summary_stream(self, mock_llm):
        # Mock LLM response
        mock_llm.return_value = {
            "choices": [{"text": " - Extracted Detail 1"}]
        }
        
        text = "This is a long text " * 500 # Enough to trigger chunking if chunk_size is small, or at least 1 chunk
        
        # Call the generator
        generator = generate_academic_summary_stream(text)
        
        # First item is header
        header = next(generator)
        print(f"Header: {header}")
        assert "Extracted Details" in header
        
        # Second item should be chunk 1
        chunk1 = next(generator)
        print(f"Chunk 1: {chunk1}")
        assert "Chunk 1" in chunk1
        assert "Extracted Detail 1" in chunk1
        
    @patch("routes.v2.pdf_summary_model.extract_text_from_pdf")
    @patch("routes.v2.pdf_summary_model.pdfconn")
    @patch("routes.v2.pdf_summary_model.StreamingResponse")
    @patch("v2_model_services.summary_generation.llm")
    @patch("routes.v2.pdf_summary_model.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_upload_route_structure(self, mock_open, mock_makedirs, mock_llm, mock_streaming_response, mock_pdfconn, mock_extract):
        try:
            print("Starting test_upload_route_structure")
            # Setup mocks
            mock_extract.return_value = "Mock PDF Content"
            mock_pdfconn.insert_one.return_value.inserted_id = "mock_id_123"
            
            # Mock UploadFile
            mock_file = MagicMock()
            mock_file.filename = "test.pdf"
            
            from routes.v2.pdf_summary_model import summarize_upload_pdf_model
            import asyncio
            
            # Run async function (basic workaround)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # We need to await the file read, so mock it
            mock_file.read = asyncio.coroutine(lambda: b"fake content")
            
            # Call the route
            response = loop.run_until_complete(summarize_upload_pdf_model(file=mock_file))
            
            # Check if StreamingResponse was called
            mock_streaming_response.assert_called()
        
        # Check if headers were set on the return value of StreamingResponse
            # mock_streaming_response returns an instance, so we check that instance
            resp_instance = response
            
            # In our code: response.headers["X-Pdf-Id"] = new_pdf_id
            # Since we mocked StreamingResponse class, response is the Mock object returned by the class constructor
            
            # Verification might be tricky if StreamingResponse is fully mocked, 
            # because the code does `response = StreamingResponse(...)` then `response.headers[...] = ...`
            # So we check if `response.headers.__setitem__` was called
            
            print("Headers set:", response.headers.__setitem__.call_args_list)
            
            # We expect calls for X-Pdf-Id and X-Filename
            calls = response.headers.__setitem__.call_args_list
            keys = [c[0][0] for c in calls]
            assert "X-Pdf-Id" in keys
            assert "X-Filename" in keys
        except Exception:
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    unittest.main()
