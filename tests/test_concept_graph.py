import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules["llama_cpp"] = MagicMock()
sys.modules["pdfplumber"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

class TestConceptGraph(unittest.TestCase):

    @patch("routes.v2.insight_generation.extract_text_from_pdf")
    @patch("routes.v2.insight_generation.llm")
    @patch("routes.v2.insight_generation.genai.GenerativeModel")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("routes.v2.insight_generation.shutil.copyfileobj")
    def test_generate_concept_graph_mistral(self, mock_copy, mock_open, mock_genai, mock_llm, mock_extract):
        import asyncio
        from routes.v2.insight_generation import generate_concept_graph
        
        # Setup mocks
        mock_extract.return_value = "AI is a branch of computer science. Neural networks are used in AI."
        mock_llm.return_value = {
            "choices": [{
                "text": json.dumps({
                    "nodes": [
                        {"id": "ai", "label": "AI", "type": "topic"},
                        {"id": "nn", "label": "Neural Networks", "type": "topic"}
                    ],
                    "links": [
                        {"source": "nn", "target": "ai", "relation": "used in"}
                    ]
                })
            }]
        }
        
        # Mock UploadFile
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Call the route (Mistral)
        response = loop.run_until_complete(generate_concept_graph(
            file=mock_file,
            use_api=False,
            max_concepts=5
        ))
        
        # Assertions
        self.assertEqual(response["engine"], "Local Mistral")
        self.assertEqual(len(response["graph"]["nodes"]), 2)
        self.assertEqual(response["graph"]["links"][0]["relation"], "used in")

    @patch("routes.v2.insight_generation.extract_text_from_pdf")
    @patch("routes.v2.insight_generation.llm")
    @patch("routes.v2.insight_generation.genai.GenerativeModel")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("routes.v2.insight_generation.shutil.copyfileobj")
    @patch("routes.v2.insight_generation.API_KEY", "mock_key")
    def test_generate_concept_graph_gemini(self, mock_copy, mock_open, mock_genai_model, mock_llm, mock_extract):
        import asyncio
        from routes.v2.insight_generation import generate_concept_graph
        
        # Setup mocks
        mock_extract.return_value = "Large Language Models are powerful. GPT-4 is an LLM."
        
        mock_model_instance = MagicMock()
        mock_genai_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "nodes": [
                {"id": "llm", "label": "LLM", "type": "topic"},
                {"id": "gpt4", "label": "GPT-4", "type": "entity"}
            ],
            "links": [
                {"source": "gpt4", "target": "llm", "relation": "is a"}
            ]
        })
        mock_model_instance.generate_content.return_value = mock_response
        
        # Mock UploadFile
        mock_file = MagicMock()
        mock_file.filename = "test_gemini.pdf"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Call the route (Gemini)
        response = loop.run_until_complete(generate_concept_graph(
            file=mock_file,
            use_api=True,
            max_concepts=5
        ))
        
        # Assertions
        self.assertEqual(response["engine"], "Gemini API")
        self.assertEqual(len(response["graph"]["nodes"]), 2)
        self.assertEqual(response["graph"]["links"][0]["source"], "gpt4")

if __name__ == "__main__":
    unittest.main()
