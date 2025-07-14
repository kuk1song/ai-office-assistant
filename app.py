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
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = []


def restart_session():
    """Clears the session state to start over."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Clean up the temp directory
    temp_dir = "temp_uploads"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# --- Main App Logic ---
def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")

    with st.sidebar:
        st.title("📄 Document Knowledge Base")
        st.write("Upload a collection of documents and ask questions about their combined content.")
        
        st.button("Start New Session", on_click=restart_session, use_container_width=True)
        st.markdown("---")

        if not st.session_state.chat_engine:
            uploaded_files = st.file_uploader(
                "Upload your documents here", 
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True
            )

            if st.button("Create Knowledge Base", use_container_width=True) and uploaded_files:
                # Check for API key
                if not openai_api_key:
                    st.error("OPENAI_API_KEY is not set. Please add it to your environment.")
                    return

                temp_file_paths = []
                # Ensure temp dir exists
                if not os.path.exists(st.session_state.temp_dir):
                    os.makedirs(st.session_state.temp_dir)

                for uploaded_file in uploaded_files:
                    temp_file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_file_paths.append(temp_file_path)

                with st.spinner(f"Creating knowledge base from {len(uploaded_files)} documents..."):
                    try:
                        st.session_state.chat_engine = ChatEngine(temp_file_paths, openai_api_key)
                        st.session_state.processed_files = [f.name for f in uploaded_files]
                        
                        file_list_str = "\n".join([f"- `{name}`" for name in st.session_state.processed_files])
                        st.session_state.chat_history = [
                            AIMessage(content=f"Knowledge base created successfully from:\n{file_list_str}\n\nAsk me anything!"),
                        ]
                        st.rerun() # Rerun to update the main view
                    except Exception as e:
                        st.error(f"Failed to create knowledge base: {e}")
                        st.session_state.chat_engine = None
        else:
            st.success("Knowledge Base is active!")
            st.markdown("##### Loaded Documents:")
            for file_name in st.session_state.processed_files:
                st.markdown(f"- `{file_name}`")
    
    # --- Chat Interface ---
    st.title("🤖 Knowledge Base Assistant")
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
    user_query = st.chat_input("Ask a question about your documents...")
    if user_query:
        if st.session_state.chat_engine is None:
            st.error("Please create a knowledge base first using the sidebar.")
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