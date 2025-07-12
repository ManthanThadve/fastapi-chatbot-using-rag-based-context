# FILE: app/rag.py (updated with persistence and conversation history)

import faiss
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils import extract_text_from_pdf, chunk_text, ask_ollama, save_chunks, load_chunks
from typing import List, Dict
import time

INDEX_FILE = "faiss_store/index.faiss"
CHUNKS_FILE = "faiss_store/chunks.txt"

model = SentenceTransformer("all-MiniLM-L6-v2")
index = None
chunks = []

# Add conversation management
conversations: Dict[str, List[Dict]] = {}

def create_conversation() -> str:
    conversation_id = str(int(time.time()))
    conversations[conversation_id] = []
    return conversation_id

def get_conversation_history(conversation_id: str) -> List[Dict]:
    return conversations.get(conversation_id, [])

def add_to_conversation(conversation_id: str, role: str, content: str):
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    conversations[conversation_id].append({"role": role, "content": content})

def process_document(file_path):
    global index, chunks
    
    # Load existing chunks if available
    if os.path.exists(CHUNKS_FILE):
        existing_chunks = load_chunks(CHUNKS_FILE)
    else:
        existing_chunks = []
    
    # Process new document
    text = extract_text_from_pdf(file_path)
    new_chunks = chunk_text(text)
    
    # Combine existing and new chunks
    chunks = existing_chunks + new_chunks
    save_chunks(chunks, CHUNKS_FILE)
    
    # Create embeddings for all chunks
    embeddings = model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, INDEX_FILE)

def load_index():
    global index, chunks
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        chunks = load_chunks(CHUNKS_FILE)
        return True
    return False

def query_faiss(question, top_k=3):
    question_embedding = model.encode([question])
    _, indices = index.search(question_embedding, top_k)
    return [chunks[i] for i in indices[0]]

def get_default_response(question: str) -> str:
    """Generate a response when no documents are uploaded"""
    disclaimer = (
        "⚠️ Note: This response is based on the model's general knowledge as no documents "
        "have been uploaded for context. The information provided may not be accurate or "
        "up-to-date. Please upload relevant documents for more accurate answers."
    )
    
    # Use the base model to generate a response
    response = ask_ollama(
        f"Please answer this question based on your general knowledge: {question}\n\n"
        "Keep the answer concise and factual."
    )
    
    return f"{disclaimer}\n\n{response}"

def answer_query(question: str) -> str:
    """Answer a question with or without document context"""
    if index is None:
        # Try to load existing index
        if not load_index():
            return get_default_response(question)
    
    # Use RAG if documents are available
    context_chunks = query_faiss(question)
    context = "\n".join(context_chunks)
    prompt = f"Answer the following question based on the context.\n\nContext:\n{context}\n\nQuestion: {question}"
    return ask_ollama(prompt)

def answer_query_with_history(question: str, conversation_id: str) -> str:
    """Answer a question with conversation history and optional document context"""
    # Get conversation history
    history = get_conversation_history(conversation_id)
    conversation_context = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in history[-5:]  # Include last 5 messages for context
    ])
    
    if index is None:
        # Try to load existing index
        if not load_index():
            response = get_default_response(question)
            add_to_conversation(conversation_id, "human", question)
            add_to_conversation(conversation_id, "assistant", response)
            return response
    
    # Use RAG with conversation history
    context_chunks = query_faiss(question)
    context = "\n".join(context_chunks)
    
    prompt = f"""Answer the following question based on the available context and previous conversation.

Context:
{context}

Previous Conversation:
{conversation_context}

Question: {question}

Please provide a clear and concise answer, maintaining context from our previous conversation."""
    
    answer = ask_ollama(prompt)
    
    # Update conversation history
    add_to_conversation(conversation_id, "human", question)
    add_to_conversation(conversation_id, "assistant", answer)
    
    return answer
