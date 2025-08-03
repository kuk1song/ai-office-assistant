import streamlit as st
import os
from dotenv import load_dotenv
from src.core.session import initialize_app
from src.ui.styles import inject_custom_css
from src.ui.layout import render_sidebar, render_main_chat

# Load environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# --- App Configuration ---
st.set_page_config(page_title="AI Office Assistant", page_icon="🤖", layout="wide")

# --- Apply Custom Styling ---
inject_custom_css()

def main():
    """Main function to run the Streamlit app."""
    # Initialize application state
    initialize_app()
    
    # Render UI components
    render_sidebar()
    render_main_chat()

if __name__ == '__main__':
    main() 