
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

for env_file in (Path(__file__).resolve().parent.parent / ".env", Path(__file__).resolve().parent.parent / ".env.txt"):
    if env_file.exists():
        load_dotenv(env_file)


class GeminiDocumentGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add the key to a .env file or environment variable.")

        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate_document(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        prompt = (
            f"Generate a comprehensive legal document titled '{document_type}'.\n"
            f"Involved parties: {parties}\n"
            f"Effective Date: {dates}\n"
            f"Terms and conditions: {terms}\n"
            "Ensure formal legal structure with multiple sections and legal clauses."
        )
        response = self.model.generate_content(prompt)
        return response.text