# FILE: app/utils.py

import fitz
import requests
import os

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])

def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def ask_ollama(prompt, model="mistral:latest"):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60  # Add timeout
        )
        
        if response.status_code != 200:
            error_msg = f"Ollama server error (Status {response.status_code})"
            try:
                error_detail = response.json().get("error", "Unknown error")
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {response.text}"
            raise Exception(error_msg)
            
        try:
            return response.json().get("response", "[No response from model]")
        except requests.exceptions.JSONDecodeError:
            raise Exception(f"Invalid JSON response from Ollama: {response.text}")
            
    except requests.exceptions.ConnectionError:
        raise Exception("Cannot connect to Ollama server. Is it running?")
    except requests.exceptions.Timeout:
        raise Exception("Request to Ollama server timed out")
    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")

def save_chunks(chunks, file_path):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save chunks with proper handling of empty list
    content = "|||CHUNK|||\n".join(chunk.strip() for chunk in chunks if chunk.strip())
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def load_chunks(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return []
            return [chunk.strip() for chunk in content.split("|||CHUNK|||") if chunk.strip()]
    except FileNotFoundError:
        return []
