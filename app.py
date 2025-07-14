import streamlit as st
import os
import shutil
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.rag_engine import ChatEngine

# Load environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# --- App Configuration ---
st.set_page_config(page_title="Conversational Document AI", page_icon="🤖", layout="wide")

# --- CSS for styling ---
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f0f2f6;
    }
    /* Chat bubbles styling */
    .st-emotion-cache-1c7y2kd {
        border-radius: 20px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    /* User message */
    .st-emotion-cache-1c7y2kd[data-testid="stChatMessage"]:has(.st-emotion-cache-1f1d6gn) {
        background-color: #dcf8c6;
    }
    /* AI message */
    .st-emotion-cache-1c7y2kd[data-testid="stChatMessage"]:not(:has(.st-emotion-cache-1f1d6gn)) {
        background-color: #ffffff;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
def initialize_session_state():
    """Initializes the session state variables."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="Hello! I'm your AI Office Assistant. Please upload a document to get started."),
        ]
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = None
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = "temp_uploads"
        # Ensure temp dir is clean on new session
        if os.path.exists(st.session_state.temp_dir):
            shutil.rmtree(st.session_state.temp_dir)
        os.makedirs(st.session_state.temp_dir)

# --- Main App Logic ---
def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")

    with st.sidebar:
        st.title("📄 Document Chat")
        st.write("Upload a document and ask questions about its content.")
        
        uploaded_file = st.file_uploader("Choose a document...", type=["pdf", "docx", "txt"])

        if uploaded_file:
            # Check for API key
            if not openai_api_key:
                st.error("OPENAI_API_KEY is not set. Please add it to your .env file or environment variables.")
                return

            # Save the file and initialize the engine
            temp_file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Analyzing document... This may take a moment."):
                try:
                    st.session_state.chat_engine = ChatEngine(temp_file_path, openai_api_key)
                    st.success(f"Ready to chat with `{uploaded_file.name}`!")
                    # Reset chat history for the new document
                    st.session_state.chat_history = [
                        AIMessage(content=f"I'm ready! Ask me anything about `{uploaded_file.name}`."),
                    ]
                except Exception as e:
                    st.error(f"Failed to initialize the chat engine: {e}")
                    st.session_state.chat_engine = None
    
    # --- Chat Interface ---
    st.title("🤖 Conversational AI Assistant")
    st.write("This is an interactive chat interface. Ask me anything about your uploaded document.")

    # Display chat history
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI", avatar="🤖"):
                st.write(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human", avatar="👤"):
                st.write(message.content)

    # User input
    user_query = st.chat_input("Ask a question about your document...")
    if user_query:
        if st.session_state.chat_engine is None:
            st.error("Please upload a document first to start the chat.")
            return
            
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        with st.chat_message("Human", avatar="👤"):
            st.write(user_query)

        with st.chat_message("AI", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_engine.ask(user_query, st.session_state.chat_history)
                st.write(response)
                st.session_state.chat_history.append(AIMessage(content=response))

if __name__ == '__main__':
    main() 