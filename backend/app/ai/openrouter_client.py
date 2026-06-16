import os
import requests

from dotenv import load_dotenv

load_dotenv()


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