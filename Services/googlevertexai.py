import google.generativeai as genai
from dotenv import load_dotenv
import os


# Load .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure the client
model=genai.configure(api_key=API_KEY) # type: ignore

# Create model
def contentcreation(text:str | None=None):

        model = genai.GenerativeModel("gemini-2.5-flash") # type: ignore

        # Send prompt
        response = model.generate_content(text)
        print(response.text)
        return response.text
        # this will return the response as text so that it can be saved 
        
       

if __name__ == "__main__":
       contentcreation("what is ai")
