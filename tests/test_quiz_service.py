import asyncio
import os
import sys

# Add the current directory to sys.path to resolve 'Services'
sys.path.append(os.getcwd())

from Services.quiz_service import generate_quiz_content
from dotenv import load_dotenv
import google.generativeai as genai

# Load env for API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def test_service():
    context = "SpaceX is a private aerospace manufacturer and space transportation services company headquartered in Hawthorne, California. It was founded in 2002 by Elon Musk with the goal of reducing space transportation costs to enable the colonization of Mars."
    print("Testing generate_quiz_content...")
    quiz = await generate_quiz_content(context, "Fact Sheet")
    if quiz:
        print("Quiz generated successfully!")
        # print(quiz)
        # Check structure
        q = quiz.get("quiz", {})
        print(f"MCQs: {len(q.get('mcqs', []))}")
        print(f"Short Answer: {len(q.get('short_answer', []))}")
        print(f"True/False: {len(q.get('true_false', []))}")
    else:
        print("Failed to generate quiz.")

if __name__ == "__main__":
    asyncio.run(test_service())
