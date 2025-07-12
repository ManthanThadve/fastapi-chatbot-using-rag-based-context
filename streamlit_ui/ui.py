# FILE: streamlit_ui/ui.py

import streamlit as st
import requests
from typing import List, Dict
import time

API_URL = "http://localhost:8000"

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        # Start a new conversation
        response = requests.post(f"{API_URL}/chat/start")
        st.session_state.conversation_id = response.json()["conversation_id"]

def display_message(role: str, content: str):
    """Display a message in the chat interface"""
    with st.chat_message(role):
        st.markdown(content)

def clear_chat():
    """Clear the chat history and start a new conversation"""
    st.session_state.messages = []
    response = requests.post(f"{API_URL}/chat/start")
    st.session_state.conversation_id = response.json()["conversation_id"]

def main():
    st.set_page_config(
        page_title="RAG Chatbot",
        page_icon="📚",
        layout="wide"
    )

    # Initialize session state
    init_session_state()

    # Create two columns for layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("📚 RAG Q&A System")
        
        # Chat interface
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about the document..."):
            # Display user message
            display_message("user", prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get AI response
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{API_URL}/chat/ask",
                    data={
                        "question": prompt,
                        "conversation_id": st.session_state.conversation_id
                    }
                )
                answer = response.json()["answer"]

            # Display AI response
            display_message("assistant", answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    with col2:
        st.sidebar.title("📁 Document Management")
        
        # Document status indicator
        try:
            # Check if any documents are indexed
            response = requests.get(f"{API_URL}/chat/{st.session_state.conversation_id}/history")
            has_documents = response.status_code == 200
            if has_documents:
                st.sidebar.success("✅ Documents are indexed and ready for Q&A")
            else:
                st.sidebar.warning("ℹ️ No documents indexed. The model will use its general knowledge.")
        except:
            st.sidebar.warning("ℹ️ No documents indexed. The model will use its general knowledge.")
        
        # Information about response reliability
        st.sidebar.info("""
        💡 **How responses work:**
        - With indexed documents: Responses are based on the content of uploaded documents
        - Without documents: Responses come from the model's general knowledge and may not be fully accurate
        - For best results, upload relevant documents
        """)
        
        # File upload
        uploaded_file = st.sidebar.file_uploader(
            "Upload a PDF Document",
            type="pdf",
            help="Documents are indexed and preserved for future sessions"
        )

        if uploaded_file is not None:
            with st.sidebar.spinner("Processing document..."):
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(
                    f"{API_URL}/upload/",
                    files={"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                )
                if response.status_code == 200:
                    st.sidebar.success("✅ Document processed and indexed successfully!")
                else:
                    st.sidebar.error("❌ Error processing document")

        # Chat controls
        st.sidebar.title("💬 Chat Controls")
        if st.sidebar.button("🔄 Clear Chat"):
            clear_chat()
            st.rerun()

        # Display conversation ID
        st.sidebar.title("🔑 Session Info")
        st.sidebar.text(f"Conversation ID: {st.session_state.conversation_id}")

        # Get and display chat history
        st.sidebar.title("📜 Chat History")
        try:
            history = requests.get(
                f"{API_URL}/chat/{st.session_state.conversation_id}/history"
            ).json()["history"]
            
            if history:
                for msg in history:
                    role_icon = "👤" if msg["role"] == "human" else "🤖"
                    st.sidebar.text(f"{role_icon} {msg['role']}: {msg['content'][:50]}...")
        except Exception as e:
            st.sidebar.error("Unable to load chat history")

if __name__ == "__main__":
    main()
