import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v2_model_services.mcq_generation.mcq_prompt import mcq_prompt
from routes.v2.model_load import llm
import json
import re

# Sample text for testing
sample_text = """
Machine learning is a subset of artificial intelligence (AI) that provides systems the ability 
to automatically learn and improve from experience without being explicitly programmed. 
Machine learning focuses on developing algorithms that can access data and use it to learn for themselves. 
The process begins with observations or data to look for patterns and make better decisions based on 
what we learn. The primary aim is to allow computers to learn automatically without human intervention or assistance.
"""

def test_mcq_generation():
    """Test MCQ generation"""
    print("Testing MCQ generation...")
    
    prompt = mcq_prompt(sample_text, 3)
    print("Prompt sent to model:")
    print(prompt[:200] + "...")
    print("\n" + "="*50 + "\n")
    
    response = llm(
        prompt,
        max_tokens=500,
        temperature=0.2,
        top_p=0.9,
        stop=["</s>"]
    )
    
    mcqs_json = response["choices"][0]["text"]
    print("Raw model response:")
    print(mcqs_json)
    print("\n" + "="*50 + "\n")
    
    # Try to parse
    try:
        parsed = json.loads(mcqs_json)
        print("Successfully parsed as JSON!")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print("Attempting to extract JSON array...")
        match = re.search(r'\[\s*\{.*?\}\s*\]', mcqs_json, re.DOTALL)
        if match:
            try:
                extracted = json.loads(match.group(0))
                print("Successfully extracted JSON!")
                print(json.dumps(extracted, indent=2))
            except:
                print("Could not extract valid JSON")
        else:
            print("No JSON array pattern found")

if __name__ == "__main__":
    test_mcq_generation()
