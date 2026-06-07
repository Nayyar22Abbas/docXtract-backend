import google.generativeai as genai
from dotenv import load_dotenv
import os

def check_gemini():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in .env file.")
        return

    print(f"Attempting to connect with key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash as identified in the list_models diagnostic
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Gemini is working!' if you can read this.")
        
        if response and response.text:
            print(f"✅ Success! Response: {response.text.strip()}")
        else:
            print("❓ Connection established but response was empty.")
            
    except Exception as e:
        print(f"❌ Failed to connect to Gemini API.")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    check_gemini()
