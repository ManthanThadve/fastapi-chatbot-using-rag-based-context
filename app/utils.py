# FILE: app/utils.py

import fitz
import requests

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])

def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def ask_ollama(prompt, model="mistral:latest"):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        return response.json().get("response", "[No response from model]")
    except Exception as e:
        return f"[LLM error: {e}]"

def save_chunks(chunks, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("|||CHUNK|||\n".join(chunks))

def load_chunks(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().split("|||CHUNK|||")
