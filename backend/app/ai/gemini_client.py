import os

import requests
from dotenv import load_dotenv


load_dotenv()


class GeminiClient:

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError(
                "Gemini API key is not configured. Set GEMINI_API_KEY."
            )

        url = f"{self.BASE_URL}/{self.model}:generateContent"
        response = requests.post(
            url,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Gemini generation failed with status {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )
        return "\n".join(
            part.get("text", "")
            for part in parts
            if part.get("text")
        ).strip()
