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
    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = 0
    if "is_uploading" not in st.session_state:
        st.session_state.is_uploading = False

def check_document_status():
    """Check if documents are indexed and return status message"""
    try:
        response = requests.post(
            f"{API_URL}/ask/",
            data={"question": "test"}
        )
        
        if response.status_code == 200:
            if "no documents" in response.json().get("answer", "").lower():
                return "warning", "ℹ️ No documents indexed. The model will use its general knowledge."
            else:
                return "success", "✅ Documents are indexed and ready for Q&A"
        else:
            return "warning", "ℹ️ No documents indexed. The model will use its general knowledge."
    except Exception as e:
        return "warning", "ℹ️ No documents indexed. The model will use its general knowledge."

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
                try:
                    response = requests.post(
                        f"{API_URL}/chat/ask",
                        data={
                            "question": prompt,
                            "conversation_id": st.session_state.conversation_id
                        }
                    )
                    
                    if response.status_code == 200:
                        try:
                            answer = response.json()["answer"]
                        except (KeyError, requests.exceptions.JSONDecodeError) as e:
                            st.error(f"Error parsing response: {str(e)}")
                            st.error(f"Response content: {response.text}")
                            answer = "Sorry, there was an error processing your request."
                    else:
                        error_msg = f"Error {response.status_code}"
                        try:
                            error_detail = response.json().get("detail", "Unknown error")
                            error_msg += f": {error_detail}"
                        except:
                            error_msg += f": {response.text}"
                        st.error(error_msg)
                        answer = "Sorry, there was an error processing your request."
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")
                    answer = "Sorry, couldn't connect to the server. Please make sure the backend is running."

            # Display AI response
            display_message("assistant", answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    with col2:
        st.sidebar.title("📁 Document Management")
        
        # Document status indicator
        status_type, status_message = check_document_status()
        if status_type == "success":
            st.sidebar.success(status_message)
        else:
            st.sidebar.warning(status_message)
        
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
            help="Documents are indexed and preserved for future sessions",
            key=f"file_uploader_{st.session_state.file_uploader_key}"
        )

        if uploaded_file is not None and not st.session_state.is_uploading:
            st.session_state.is_uploading = True
            
            with st.sidebar.container():
                progress_text = st.empty()
                progress_text.text("Processing document...")
                
                try:
                    # Create form data with file
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    
                    # Set timeout to avoid indefinite waiting
                    response = requests.post(
                        f"{API_URL}/upload/",
                        files=files,
                        timeout=30  # 30 seconds timeout
                    )
                    
                    # Parse response
                    if response.status_code == 200:
                        result = response.json()
                        st.sidebar.success(f"✅ {result.get('message', 'Document processed successfully!')}")
                    else:
                        try:
                            error_detail = response.json().get('detail', 'Unknown error')
                            st.sidebar.error(f"❌ Error: {error_detail}")
                        except:
                            st.sidebar.error(f"❌ Error {response.status_code}: {response.text}")
                
                except requests.exceptions.Timeout:
                    st.sidebar.error("❌ Request timed out. The server took too long to respond.")
                    st.sidebar.error("Please try uploading a smaller document or check the server.")
                
                except requests.exceptions.ConnectionError:
                    st.sidebar.error("❌ Connection Error: Could not connect to the server.")
                    st.sidebar.error("Please check if the FastAPI server is running.")
                
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
                
                # Reset the uploader
                st.session_state.file_uploader_key += 1
                st.session_state.is_uploading = False
                st.rerun()

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
