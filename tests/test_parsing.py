import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routes.v2.flashcard_citation import parse_flashcards_with_source

def test_parsing():
    print("Testing Flashcard Parsing...")

    # Case 1: Perfect Format
    good_output = """
Q: What is AI?
A: Artificial Intelligence.
Source Line: 5

Q: What is ML?
A: Machine Learning.
Source Line: 10
"""
    results = parse_flashcards_with_source(good_output)
    print(f"Good Input: Expected 2, Got {len(results)}")
    if len(results) != 2:
        print("FAILED: Good Input")
        print(results)

    # Case 2: Missing whitespace or slight variations (Common LLM quirks)
    quirky_output = """
Q:Define Python.
A: A programming language.
Source Line: 20

Q:   What is Rust?  
A:Systems language.
Source Line:25
"""
    # Current code expects "Q: " (split by Q:) but inside loop splits by "A:" and "Source Line:"
    # If the LLM omits space after colon, does it fail? 
    results = parse_flashcards_with_source(quirky_output)
    print(f"Quirky Input: Expected 2, Got {len(results)}")
    
    # Case 3: Messy but parsable (Now works with Regex!)
    messy_output = """
Here are your flashcards:
1. Question: Foo? Answer: Bar. Source: 1
"""
    results = parse_flashcards_with_source(messy_output)
    print(f"Messy Input: Expected 1, Got {len(results)}")
    
    # Case 4: True Garbage (No keywords)
    true_garbage = """
    This is just a summary of the text.
    The text talks about AI and ML.
    It does not follow the format at all.
    """
    results = parse_flashcards_with_source(true_garbage)
    print(f"True Garbage: Expected 0, Got {len(results)}")

if __name__ == "__main__":
    test_parsing()
