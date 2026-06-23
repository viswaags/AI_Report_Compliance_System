import os
import requests

from dotenv import load_dotenv

load_dotenv()

'''
class OpenRouterClient:

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def generate(
        self,
        prompt: str
    ) -> str:

        response = requests.post(

            self.BASE_URL,

            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },

            json={

                "model": os.getenv(
                    "OPENROUTER_MODEL"
                ),

                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

        response = requests.post(...)

        if response.status_code != 200:

            return (
                f"AI generation failed. "
                f"Status Code: {response.status_code}. "
                f"Response: {response.text}"
            )

        #response.raise_for_status()

        data = response.json()

        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )
'''

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        # Retrieve configuration safely
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

        if not api_key:
            return "Configuration Error: OPENROUTER_API_KEY is missing."

        # Send the payload to OpenRouter
        try:
            response = requests.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=60
            )

            # Error handling for network issues or credit walls
            if response.status_code != 200:
                return (
                    f"AI generation failed. "
                    f"Status Code: {response.status_code}. "
                    f"Response: {response.text}"
                )

            # Extract the content from the standard OpenRouter structure
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            return f"An application error occurred: {str(e)}"
