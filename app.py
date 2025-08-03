import streamlit as st
import os
import shutil
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.rag_engine import AgentEngine, STORAGE_DIR

# Load environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# --- App Configuration ---
st.set_page_config(page_title="AI Office Assistant", page_icon="🤖", layout="wide")

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
    
    /* Center align the text in st.info */
    .stAlert {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- Session State and Engine Initialization ---
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


# --- Main App Logic ---
def main():
    """Main function to run the Streamlit app."""
    initialize_app()
    
    # --- Sidebar Layout ---
    with st.sidebar:
        # --- UI for managing the knowledge base ---
        if st.session_state.get("kb_initialized"):
            # --- KB EXISTS: SHOW MANAGEMENT UI ---
            st.markdown("### Knowledge Base")
            
            if not st.session_state.chat_engine.file_names:
                st.info("Your knowledge base is empty. Add some documents below.")
            else:
                # Create scrollable container that shows exactly 4 files
                # Calculate height: show max 4 files, each file takes roughly 80-100px
                num_files = len(st.session_state.chat_engine.file_names)
                container_height = min(num_files, 4) * 95  # 95px per file, max 4 files visible
                
                with st.container(height=container_height):
                    for file_name in st.session_state.chat_engine.file_names:
                        with st.expander(f"📄 {file_name}"):
                            language = st.text_input("Summary Language", value="English", key=f"lang_{file_name}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Summarize", key=f"summary_{file_name}", use_container_width=True):
                                    with st.spinner(f"Generating summary in {language}..."):
                                        summary = st.session_state.chat_engine.summarize_document.invoke({"file_name": file_name, "language": language})
                                        summary_message = f"**Summary for `{file_name}` (in {language}):**\n\n{summary}"
                                        st.session_state.chat_history.append(AIMessage(content=summary_message))
                                        st.rerun()
                            with col2:
                                if st.button("Delete", key=f"delete_{file_name}", use_container_width=True, type="primary"):
                                    with st.spinner(f"Deleting {file_name} and rebuilding knowledge base..."):
                                        st.session_state.chat_engine.delete_document(file_name)
                                    
                                    # Add a confirmation message to the chat
                                    st.session_state.chat_history.append(
                                        AIMessage(content=f"🗑️ The document **{file_name}** has been successfully deleted from the knowledge base.")
                                    )
                                    st.rerun()
            
            st.divider()

            # --- Add New Documents Section ---
            st.markdown("### Add More Documents")
            
            # Use a dynamic key to force recreation of file uploader when needed
            if "uploader_key" not in st.session_state:
                st.session_state.uploader_key = 0
                
            new_uploaded_files = st.file_uploader(
                "Upload more documents",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key=f"new_files_uploader_{st.session_state.uploader_key}",
                label_visibility="collapsed"
            )
            
            def handle_add_documents():
                """Handle adding new documents with comprehensive error handling and user feedback."""
                # Get the current uploader key to access the right session state
                current_key = f"new_files_uploader_{st.session_state.uploader_key}"
                uploaded_files = st.session_state.get(current_key, [])
                
                if not uploaded_files:
                    return
                
                try:
                    # Check for duplicates
                    existing_files = set(st.session_state.chat_engine.file_names)
                    files_to_add = []
                    duplicate_files = []
                    
                    for uploaded_file in uploaded_files:
                        if uploaded_file.name in existing_files:
                            duplicate_files.append(uploaded_file.name)
                        else:
                            files_to_add.append(uploaded_file)
                    
                    # Show duplicate warnings
                    if duplicate_files:
                        for duplicate_file in duplicate_files:
                            st.warning(f"📁 {duplicate_file} is already in the knowledge base")
                    
                    # Process new files if any
                    if files_to_add:
                        temp_dir = "temp_uploads_add"
                        if not os.path.exists(temp_dir): 
                            os.makedirs(temp_dir)
                        
                        temp_file_paths = []
                        successful_files = []
                        
                        # Save files to temp directory
                        for file in files_to_add:
                            temp_path = os.path.join(temp_dir, file.name)
                            try:
                                with open(temp_path, "wb") as f:
                                    f.write(file.getbuffer())
                                temp_file_paths.append(temp_path)
                                successful_files.append(file.name)
                            except Exception as e:
                                st.error(f"❌ Failed to process {file.name}: File may be corrupted")
                        
                        # Add documents to knowledge base
                        if temp_file_paths:
                            try:
                                with st.spinner(f"Adding {len(successful_files)} new document(s)..."):
                                    st.session_state.chat_engine.add_documents(temp_file_paths)
                                
                                # Success message
                                file_list = ", ".join(successful_files)
                                st.session_state.chat_history.append(
                                    AIMessage(content=f"✅ Successfully added to Knowledge Base: {file_list}")
                                )
                                
                                # Increment uploader key to create a new uploader (effectively clearing it)
                                st.session_state.uploader_key += 1
                                
                            except Exception as e:
                                st.error("❌ Some files couldn't be processed. They may be empty, corrupted, or in an unsupported format.")
                                
                        # Cleanup
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                    
                    elif not duplicate_files:
                        st.info("No files were selected for upload.")
                        
                except Exception as e:
                    st.error("❌ An unexpected error occurred. Please try again or contact support.")
            
            st.button(
                "Add to Knowledge Base", 
                on_click=handle_add_documents,
                use_container_width=True, 
                disabled=not new_uploaded_files
            )

        else:
            # --- NO KB: SHOW CREATE_KB_UI ---
            st.info(
                """
                **💡 Welcome to your AI Office Assistant!**
                
                To get started, please upload one or more documents to create your knowledge base.
                """
            )
            initial_uploaded_files = st.file_uploader(
                "Documents", 
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="initial_uploader",
                label_visibility="collapsed"
            )

            if st.button("Create Knowledge Base", use_container_width=True, disabled=not initial_uploaded_files):
                try:
                    # Remove duplicates from initial upload
                    unique_files = {}
                    duplicate_count = 0
                    
                    for uploaded_file in initial_uploaded_files:
                        if uploaded_file.name not in unique_files:
                            unique_files[uploaded_file.name] = uploaded_file
                        else:
                            duplicate_count += 1
                    
                    if duplicate_count > 0:
                        st.warning(f"⚠️ Removed {duplicate_count} duplicate file(s) from your selection")
                    
                    temp_dir = "temp_uploads_create"
                    if not os.path.exists(temp_dir): 
                        os.makedirs(temp_dir)
                    
                    temp_file_paths = []
                    successful_files = []
                    
                    # Save unique files to temp directory
                    for file_name, file in unique_files.items():
                        temp_path = os.path.join(temp_dir, file_name)
                        try:
                            with open(temp_path, "wb") as f:
                                f.write(file.getbuffer())
                            temp_file_paths.append(temp_path)
                            successful_files.append(file_name)
                        except Exception as e:
                            st.error(f"❌ Failed to process {file_name}: File may be corrupted")
                    
                    # Create knowledge base
                    if temp_file_paths:
                        try:
                            with st.spinner(f"Creating knowledge base from {len(successful_files)} document(s)...\n(This may take a moment for large files)"):
                                st.session_state.chat_engine.create_and_save(temp_file_paths)
                            
                            st.session_state.kb_initialized = True
                            
                            # Success message
                            file_list = ", ".join(successful_files)
                            st.session_state.chat_history.append(
                                AIMessage(content=f"✅ Knowledge Base created successfully with: {file_list}")
                            )
                            
                        except Exception as e:
                            st.error("❌ Failed to create knowledge base. Some files may be empty, corrupted, or in an unsupported format.")
                    else:
                        st.error("❌ No valid files could be processed.")
                    
                    # Cleanup
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        
                except Exception as e:
                    st.error("❌ An unexpected error occurred while creating the knowledge base. Please try again.")
                
                st.rerun()
        
        # Reset button (naturally placed, not forced to bottom)
        st.divider()
        if st.session_state.get("confirming_reset", False):
            st.error("This will delete the entire knowledge base and cannot be undone.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Yes, Confirm", use_container_width=True, type="primary"):
                reset_knowledge_base()
                st.rerun()
            if col2.button("❌ Cancel", use_container_width=True):
                st.session_state.confirming_reset = False
                st.rerun()
        else:
            if st.button("Reset Knowledge Base", on_click=lambda: st.session_state.update(confirming_reset=True), use_container_width=True):
                pass

    # --- Chat Interface ---
    st.title("🤖 AI Office Assistant")
    # st.markdown(
    #     "**Welcome!** Use the sidebar to manage your documents. "
    #     "Use this main chat area for complex, open-ended questions that require cross-document analysis."
    # )

    # Display chat messages
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("ai", avatar="🤖"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(message.content)

    # User input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        if not st.session_state.get("kb_initialized"):
            st.error("Please create a knowledge base first using the sidebar.")
            return
            
        st.session_state.chat_history.append(HumanMessage(content=prompt))
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(prompt)

        with st.chat_message("AI", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_engine.invoke(prompt, st.session_state.chat_history)
                st.write(response)
                st.session_state.chat_history.append(AIMessage(content=response))

if __name__ == '__main__':
    main() 