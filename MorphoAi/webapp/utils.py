import requests
import json

GOOGLE_GEMINI_API_KEY = "AIzaSyA3F__YWfcfjLiH8fB_LA1moMVAXUxXQok"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateText"

def detect_morphemes(text):
    """Send input text to Google Gemini API for morpheme analysis."""
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": {
            "text": f"Analyze the following Dutch text and extract its morphemes: '{text}'"
        }
    }

    response = requests.post(f"{GEMINI_ENDPOINT}?key={GOOGLE_GEMINI_API_KEY}", 
                             headers=headers, 
                             json=data)

    if response.status_code == 200:
        result = response.json()
        return result.get("candidates", [{}])[0].get("output", "No response")
    else:
        return f"Error: {response.status_code} - {response.text}"
