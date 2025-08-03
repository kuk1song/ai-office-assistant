import streamlit as st
import os
from dotenv import load_dotenv
from src.session_manager import initialize_app, ensure_session_state, get_chat_engine, get_chat_history, is_kb_initialized
from src.ui_components import (
    inject_custom_css,
    render_knowledge_base_section,
    render_add_documents_section,
    render_reset_section,
    render_initial_upload_section,
    render_chat_messages,
    handle_chat_input
)

# Load environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# --- App Configuration ---
st.set_page_config(page_title="AI Office Assistant", page_icon="🤖", layout="wide")

# --- Apply Custom Styling ---
inject_custom_css()

def render_sidebar():
    """Render the complete sidebar layout."""
    with st.sidebar:
        # Ensure session state is properly initialized
        ensure_session_state()
        
        chat_engine = get_chat_engine()
        chat_history = get_chat_history()
        
        if is_kb_initialized():
            # --- KB EXISTS: SHOW MANAGEMENT UI ---
            render_knowledge_base_section(chat_engine, chat_history)
            st.divider()
            render_add_documents_section(chat_engine, chat_history)
        else:
            # --- NO KB: SHOW CREATE_KB_UI ---
            render_initial_upload_section(chat_engine, chat_history)
        
        # Reset button (naturally placed, not forced to bottom)
        st.divider()
        render_reset_section()

def render_main_chat():
    """Render the main chat interface."""
    st.title("🤖 AI Office Assistant")
    
    chat_history = get_chat_history()
    chat_engine = get_chat_engine()
    
    # Display chat messages
    render_chat_messages(chat_history)

    # User input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        handle_chat_input(prompt, chat_engine, chat_history)

def main():
    """Main function to run the Streamlit app."""
    # Initialize application state
    initialize_app()
    
    # Render UI components
    render_sidebar()
    render_main_chat()

if __name__ == '__main__':
    main() 