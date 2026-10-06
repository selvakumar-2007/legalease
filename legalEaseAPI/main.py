from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
for env_file in (BASE_DIR / ".env", BASE_DIR / ".env.txt"):
    if env_file.exists():
        load_dotenv(env_file)

app = FastAPI(title="LegalEase AI Legal Document Generator")
router = APIRouter()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
else:
    model = None


class DocumentRequest(BaseModel):
    document_type: str
    parties: str
    terms: str
    dates: str


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set. Add the key to a .env file or environment variable before generating a document.",
        )

    prompt = (
        f"Generate a comprehensive legal document titled '{request.document_type}'.\n"
        f"Involved parties: {request.parties}\n"
        f"Effective Date: {request.dates}\n"
        f"Terms and conditions: {request.terms}\n"
        "Ensure formal legal structure with multiple sections and legal clauses."
    )

    try:
        response = model.generate_content(prompt)
        document_text = getattr(response, "text", None)
        if not document_text:
            raise ValueError("No document content returned by the model.")
        return {"document": document_text}
    except Exception as exc:
        error_text = str(exc)
        if "API_KEY_INVALID" in error_text.upper() or "API KEY NOT VALID" in error_text.upper():
            raise HTTPException(
                status_code=401,
                detail=(
                    "The Gemini API key is invalid or unauthorized. Create a valid key "
                    "in Google AI Studio and update GEMINI_API_KEY in the .env file."
                ),
            ) from exc

        status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if (
            str(status_code) == "429"
            or "RESOURCE_EXHAUSTED" in error_text.upper()
            or "429" in error_text
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota is exhausted for this key/project. "
                    "Wait for the quota to reset, or use a key/project with available quota "
                    "and billing enabled."
                ),
            ) from exc

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate document: {exc}",
        ) from exc


app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase API"}