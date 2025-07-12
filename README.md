# RAG Q&A System

A Retrieval-Augmented Generation (RAG) based question-answering system with chat capabilities. This system allows users to upload documents and ask questions about them while maintaining conversation context.

## Features

- Document upload and indexing with FAISS
- Conversational Q&A with history
- Streaming responses
- Web-based UI using Streamlit
- RESTful API using FastAPI
- Persistent document storage
- Fall-back to general knowledge when no documents are uploaded

## Project Structure

```
fast-answer-with-context/
├── app/
│   ├── __init__.py
│   ├── main.py      # FastAPI application
│   ├── rag.py       # RAG implementation
│   └── utils.py     # Utility functions
├── streamlit_ui/
│   └── ui.py        # Streamlit UI
├── uploads/         # Document upload directory
└── faiss_store/     # FAISS index storage
```

## Setup

1. Create a virtual environment:
```bash
python -m venv rag-env
source rag-env/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the FastAPI backend:
```bash
uvicorn app.main:app --reload
```

4. Run the Streamlit UI:
```bash
streamlit run streamlit_ui/ui.py
```

## Usage

1. Upload PDF documents through the web interface
2. Start asking questions about the documents
3. The system will maintain conversation context
4. If no documents are uploaded, the system will use its general knowledge with appropriate disclaimers

## API Endpoints

- `POST /upload/`: Upload a document
- `POST /chat/start`: Start a new conversation
- `POST /chat/ask`: Ask a question in conversation context
- `GET /chat/{conversation_id}/history`: Get conversation history
