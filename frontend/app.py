import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import time

st.set_page_config(
    page_title="Calendar Booking Agent",
    page_icon="✮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<script>
    // Force light theme
    document.documentElement.setAttribute('data-theme', 'light');
</script>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>☆</text></svg>">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Global text color fix */
    .stApp {
        color: #333333 !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4 !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid;
        color: #333333 !important;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
        color: #333333 !important;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
        color: #333333 !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 20px;
        color: #333333 !important;
    }
    
    .stButton > button {
        border-radius: 20px;
        background-color: #1f77b4;
        color: white !important;
        border: none;
        padding: 0.5rem 2rem;
    }
    
    .stButton > button:hover {
        background-color: #1565c0;
    }
    
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333333 !important;
    }
    
    .example-button {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        cursor: pointer;
        text-align: left;
        width: 100%;
        color: #333333 !important;
    }
    
    .example-button:hover {
        background-color: #e0e0e0;
    }
    
    /* Fix for Streamlit text elements */
    .stMarkdown, .stText, .stMarkdown p {
        color: #333333 !important;
    }
    
    /* Fix for sidebar text */
    .css-1d391kg {
        color: #333333 !important;
    }
    
    /* Fix for input labels */
    .stTextInput label {
        color: #333333 !important;
    }
    
    /* Fix for form submit button text */
    .stFormSubmitButton button {
        border-radius: 20px;
        background-color: #1f77b4 !important;
        color: #fff !important;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stFormSubmitButton button:hover {
        background-color: #1565c0 !important;
        color: #fff !important;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

def send_message(message: str, chat_history: List[Dict] = None) -> str:
    
    try:
        
        payload = {
            "message": message,
            "chat_history": chat_history or []
        }
        
        response = requests.post(
            f"{st.session_state.api_url}/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the backend server. Please make sure the backend is running."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def check_backend_health() -> bool:
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    st.markdown('<h1 class="main-header">Calendar Booking Agent</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
        api_url = st.text_input(
            "Backend API URL",
            value=st.session_state.api_url,
            help="URL of the FastAPI backend server"
        )
        
        if api_url != st.session_state.api_url:
            st.session_state.api_url = api_url
            st.rerun()
       
        backend_healthy = check_backend_health()
        status_color = "🟢" if backend_healthy else "🔴"
        st.markdown(f"{status_color} Backend Status: {'Connected' if backend_healthy else 'Disconnected'}")
        
        st.markdown("---")
        
        st.markdown('<div class="sidebar-header">💡 Example Messages</div>', unsafe_allow_html=True)
        examples = [
            "Book a meeting for tomorrow at 3 PM",
            "Do I have time next Wednesday afternoon?",
            "Schedule a call with John on Friday at 2 PM",
            "What's my availability next week?",
            "I want to book a 30-minute meeting",
            "Show me my schedule for today"
        ]
        for example in examples:
            if st.button(example, key=f"example_{example}", help="Click to use this example"):
                st.session_state.user_input = example
                st.session_state.suggestion_submitted = True
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('<div class="sidebar-header">ℹ️ About</div>', unsafe_allow_html=True)
        st.markdown("""
        This AI agent helps you:
        - Check your calendar availability
        - ⏰ Suggest available time slots
        - ✅ Book appointments and meetings
        - 📋 View your daily schedule
        
        Just chat naturally with the agent!
        """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True) as form:
            user_input = st.text_input(
                "Type your message here...",
                key="user_input",
                placeholder="e.g., 'Book a meeting for tomorrow at 3 PM'",
                label_visibility="collapsed"
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("Send", use_container_width=True)
        if submitted and user_input.strip():
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            })
            with st.spinner("🤔 Thinking..."):
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    chat_history.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"].isoformat() if msg["timestamp"] else None
                    })
                response = send_message(user_input, chat_history)
                if not (st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.messages[-1]["content"] == response):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    })
            st.rerun()
        
        if st.session_state.get("suggestion_submitted", False):
            st.session_state.suggestion_submitted = False
            suggestion = st.session_state.get("user_input", "")
            if suggestion.strip():
                st.session_state.messages.append({
                    "role": "user",
                    "content": suggestion,
                    "timestamp": datetime.now()
                })
                with st.spinner("🤔 Thinking..."):
                    chat_history = []
                    for msg in st.session_state.messages[:-1]:
                        chat_history.append({
                            "role": msg["role"],
                            "content": msg["content"],
                            "timestamp": msg["timestamp"].isoformat() if msg["timestamp"] else None
                        })
                    response = send_message(suggestion, chat_history)
                    if not (st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.messages[-1]["content"] == response):
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now()
                        })
                st.rerun()
        for message in reversed(st.session_state.messages):
            with st.container():
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Assistant:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 