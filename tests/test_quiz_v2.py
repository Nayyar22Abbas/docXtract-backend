import requests
import os

BASE_URL = "http://localhost:8000"

def test_quiz_generation_v2():
    url = f"{BASE_URL}/v2/quiz/generate-model"
    # Create a dummy PDF or use an existing one from uploads if available
    # For testing, we'll assume there's a test.pdf in the current dir or we'll skip if not
    pdf_path = "test.pdf" 
    if not os.path.exists(pdf_path):
        # Create a simple PDF using fpdf if available, or just mock the call if we can't
        print(f"Please place a {pdf_path} in the tests directory or adjust the path.")
        return None

    files = {'file': open(pdf_path, 'rb')}
    data = {
        'document_type': 'Research Paper',
        'user_id': 'v2_tester'
    }
    
    print("Requesting v2 quiz generation (Mistral + RAG)... this might take a while.")
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("v2 Quiz Generated Successfully!")
        print(f"Quiz ID: {result['quiz_id']}")
        return result['quiz_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_quiz_solution_v2(quiz_id):
    url = f"{BASE_URL}/v2/quiz/solution/{quiz_id}"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("v2 Solution Retrieved Successfully!")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    # quiz_id = test_quiz_generation_v2()
    # if quiz_id:
    #     test_quiz_solution_v2(quiz_id)
    print("v2 Test script ready. Note: Local model inference will be slow on CPU.")
