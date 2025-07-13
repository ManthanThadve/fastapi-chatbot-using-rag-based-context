## FILE: app/main.py

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.rag import process_document, answer_query, create_conversation, answer_query_with_history, get_conversation_history
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # Process document
        try:
            process_document(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

        return {
            "message": f"File {file.filename} processed successfully",
            "status": "success",
            "file_path": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    answer = answer_query(question)
    return {"answer": answer}

@app.post("/chat/start")
async def start_chat():
    """Start a new chat conversation and return the conversation ID"""
    conversation_id = create_conversation()
    return {"conversation_id": conversation_id}

@app.post("/chat/ask", response_model=ChatResponse)
async def chat_question(
    question: str = Form(...),
    conversation_id: str = Form(...)
):
    """Ask a question in the context of an existing conversation"""
    try:
        answer = answer_query_with_history(question, conversation_id)
        return ChatResponse(answer=answer, conversation_id=conversation_id)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to process question",
                "detail": str(e)
            }
        )

@app.get("/chat/{conversation_id}/history")
async def get_chat_history(conversation_id: str):
    """Get the history of a specific conversation"""
    history = get_conversation_history(conversation_id)
    return {"history": history}
