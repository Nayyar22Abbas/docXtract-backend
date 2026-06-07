import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=API_KEY)  # type: ignore


async def generate_mcqs_gemini(context: str, total_mcqs: int = 10):
    """
    Generates MCQs using Gemini based on the provided context.
    Returns a list of MCQ objects with question, options, and correct_answer.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore

    prompt = f"""
You are DocXtract Academia, an expert educational assessment generator.

Your task is to generate {total_mcqs} Multiple Choice Questions (MCQs) STRICTLY based on the provided content.
Do not introduce information that is not present in the document.

--------------------------------------------------
RULES & CONSTRAINTS
--------------------------------------------------
- Use clear, academic language suitable for university students
- Focus on understanding, analysis, and application
- Avoid trivial or purely factual recall unless necessary
- Do NOT hallucinate facts
- Questions must be answerable using only the provided content

--------------------------------------------------
MCQ CONFIGURATION
--------------------------------------------------
Generate exactly {total_mcqs} MCQs with a mix of difficulty levels:
- Easy (concept understanding)
- Medium (section relationships, explanations)
- Hard (critical reasoning based on content)

--------------------------------------------------
MCQ RULES
--------------------------------------------------
- Each MCQ must have exactly 4 options
- Only ONE correct answer
- Options must be clearly distinguishable
- Avoid "All of the above" or "None of the above"
- Shuffle correct answer positions across questions

--------------------------------------------------
OUTPUT FORMAT (STRICT JSON)
--------------------------------------------------
Return the response as a JSON array ONLY. Do not include any other text.

[
  {{
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "difficulty": "Easy",
    "explanation": "Brief explanation why this is correct"
  }},
  ...
]

--------------------------------------------------
CONTENT TO ANALYZE
--------------------------------------------------
{context}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Try to extract JSON array from response
        # First, try to find a JSON array
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            json_str = match.group()
            mcqs = json.loads(json_str)
            
            # Validate and normalize each MCQ
            validated_mcqs = []
            for mcq in mcqs:
                if isinstance(mcq, dict) and mcq.get("question") and mcq.get("options"):
                    # Ensure options is a list
                    options = mcq.get("options")
                    if isinstance(options, dict):
                        options = list(options.values())
                    
                    if isinstance(options, list) and len(options) >= 2:
                        validated_mcqs.append({
                            "question": mcq.get("question"),
                            "options": options,
                            "correct_answer": mcq.get("correct_answer"),
                            "difficulty": mcq.get("difficulty", "Medium"),
                            "explanation": mcq.get("explanation", "")
                        })
            
            return validated_mcqs
        else:
            raise ValueError("No JSON array found in Gemini response.")
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in generate_mcqs_gemini: {e}")
        return []
    except Exception as e:
        import traceback
        print(f"Error in generate_mcqs_gemini: {e}")
        traceback.print_exc()
        return []
