import requests
import json
import os

BASE_URL = "http://localhost:8000" # Adjust if your server runs on a different port

def test_quiz_generation_text():
    url = f"{BASE_URL}/v1/quiz/generate"
    data = {
        "text_content": """
        Artificial Intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. 
        Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. 
        As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect.
        For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. 
        Modern machine learning involves using statistical techniques to enable systems to "learn" (e.g., progressively improve performance on a specific task) with data, without being explicitly programmed.
        """,
        "document_type": "Research Paper",
        "user_id": "tester"
    }
    
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Quiz Generated Successfully!")
        print(f"Quiz ID: {result['quiz_id']}")
        return result['quiz_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_quiz_solution(quiz_id):
    url = f"{BASE_URL}/v1/quiz/solution/{quiz_id}"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Solution Retrieved Successfully!")
        # print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    # Note: Ensure the server is running before executing this test
    quiz_id = test_quiz_generation_text()
    if quiz_id:
        test_quiz_solution(quiz_id)
    print("Test script ready. Run it manually or check if server is up.")
