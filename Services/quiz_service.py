import google.generativeai as genai
import os
import json
import re

async def generate_quiz_content(context: str, document_type: str = "Research Paper"):
    """
    Generates a quiz using Gemini based on the provided context.
    """
    model = genai.GenerativeModel("gemini-2.5-flash") # Use flash for speed and reliability

    prompt = f"""
You are DocXtract Academia, an expert educational assessment generator.

Your task is to generate a comprehension-focused quiz STRICTLY based on the provided content.
Do not introduce information that is not present in the document.

--------------------------------------------------
RULES & CONSTRAINTS
--------------------------------------------------
- Use clear, academic language suitable for university students
- Focus on understanding, analysis, and application
- Avoid trivial or purely factual recall unless necessary
- Do NOT hallucinate facts
- If information is insufficient, skip that question type
- Questions must be answerable using only the provided content

--------------------------------------------------
QUIZ CONFIGURATION
--------------------------------------------------
Generate:
- 10 questions total
- Mix of difficulty levels:
  - Easy (concept understanding)
  - Medium (section relationships, explanations)
  - Hard (critical reasoning based on content)

Question types:
- Multiple Choice Questions (MCQs)
- Short Answer Questions
- True / False Questions

--------------------------------------------------
QUESTION DISTRIBUTION
--------------------------------------------------
- 6 MCQs
- 2 Short Answer
- 2 True/False

--------------------------------------------------
MCQ RULES
--------------------------------------------------
- Each MCQ must have exactly 4 options
- Only ONE correct answer
- Options must be clearly distinguishable
- Avoid "All of the above" or "None of the above"
- Shuffle correct answer positions

--------------------------------------------------
SHORT ANSWER RULES
--------------------------------------------------
- Questions should require explanation in 2–4 sentences
- Answers must be concise and document-grounded

--------------------------------------------------
TRUE / FALSE RULES
--------------------------------------------------
- Statements must be unambiguous
- Clearly indicate correct answer (True or False)
- Provide a one-sentence justification

--------------------------------------------------
OUTPUT FORMAT (STRICT JSON)
--------------------------------------------------
Return the response in the following JSON structure:

{{
  "document_type": "{document_type}",
  "quiz": {{
    "mcqs": [
      {{
        "question": "",
        "options": {{
          "A": "",
          "B": "",
          "C": "",
          "D": ""
        }},
        "correct_answer": "A | B | C | D",
        "difficulty": "Easy | Medium | Hard",
        "explanation": ""
      }}
    ],
    "short_answer": [
      {{
        "question": "",
        "sample_answer": "",
        "difficulty": "Medium | Hard"
      }}
    ],
    "true_false": [
      {{
        "statement": "",
        "correct_answer": true,
        "justification": ""
      }}
    ]
  }}
}}

--------------------------------------------------
CONTENT TO ANALYZE
--------------------------------------------------
{context}
"""

    try:
        response = model.generate_content(prompt)
        # Extract JSON from the response
        text = response.text
        # Use regex to find the first '{' and last '}'
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group()
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in Gemini response.")
    except Exception as e:
        import traceback
        print(f"Error in generate_quiz_content: {e}")
        traceback.print_exc()
        return None
