"""
Session Management for AI Office Assistant

This module handles application state initialization, session management, and cleanup operations.
"""

import streamlit as st
import os
import shutil
from langchain_core.messages import AIMessage
from .engine import AgentEngine, STORAGE_DIR

def initialize_app():
    """Initializes the engine and session state. Ensures UI updates correctly."""
    if "app_initialized" not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY is not set. Please add it to your environment and refresh.")
            st.stop()
            
        st.session_state.chat_engine = AgentEngine(api_key)
        
        if st.session_state.chat_engine.load_from_disk():
            st.session_state.kb_initialized = True
            st.session_state.chat_history = [AIMessage(content="Welcome back! Your knowledge base is loaded and ready.")]
        else:
            st.session_state.kb_initialized = False
            st.session_state.chat_history = [AIMessage(content="Hello! I'm your AI Office Assistant. Please create a knowledge base to get started.")]
        
        st.session_state.app_initialized = True

def reset_knowledge_base():
    """Clears chat history and deletes the persistent knowledge base."""
    st.session_state.clear()
    
    # Delete the persistent storage directory
    if os.path.exists(STORAGE_DIR):
        shutil.rmtree(STORAGE_DIR)
    
    # A rerun will be triggered automatically by Streamlit after the callback.

def ensure_session_state():
    """Ensure all required session state variables are initialized."""
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    
    if "confirming_reset" not in st.session_state:
        st.session_state.confirming_reset = False

def get_chat_engine():
    """Get the chat engine from session state."""
    return st.session_state.get("chat_engine")

def get_chat_history():
    """Get the chat history from session state."""
    return st.session_state.get("chat_history", [])

def is_kb_initialized():
    """Check if knowledge base is initialized."""
    session_initialized = st.session_state.get("kb_initialized", False)
    chat_engine = st.session_state.get("chat_engine")
    
    # Double check: session state says initialized but engine has no files
    if session_initialized and chat_engine and not chat_engine.file_names:
        # Sync session state with actual engine state
        st.session_state.kb_initialized = False
        return False
    
    # Double check: session state says not initialized but engine has files
    if not session_initialized and chat_engine and chat_engine.file_names:
        # Sync session state with actual engine state
        st.session_state.kb_initialized = True
        return True
    
    return session_initialized 