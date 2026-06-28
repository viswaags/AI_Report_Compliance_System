import os
import requests
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

# Setup URL, headers, and payload
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}
PAYLOAD = {
    "model": os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    "messages": [{"role": "user", "content": "Respond with only the word 'Success'."}]
}

# Run the request
print("Sending request to OpenRouter...")
response = requests.post(URL, headers=HEADERS, json=PAYLOAD)

# Check the result
if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print(f"✅ Connection successful! AI says: {reply}")
else:
    print(f"❌ Failed! Status: {response.status_code}")
    print(f"Error details: {response.text}")
