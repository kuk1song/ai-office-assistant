"""
UI Components for AI Office Assistant

This module contains reusable UI components and layouts for the Streamlit application.
"""

import streamlit as st
import os
import shutil
from langchain_core.messages import AIMessage, HumanMessage
from typing import Optional

def inject_custom_css():
    """Inject custom CSS for styling the application."""
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

def render_welcome_message():
    """Render the welcome message for new users."""
    st.info(
        """
        **💡 Welcome to your AI Office Assistant!**
        
        To get started, please upload one or more documents to create your knowledge base.
        """
    )

def render_document_expander(file_name: str, chat_engine, chat_history: list) -> bool:
    """
    Render an expandable document item with summarize and delete buttons.
    
    Args:
        file_name: Name of the document file
        chat_engine: The AgentEngine instance
        chat_history: Current chat history
        
    Returns:
        bool: True if the document was deleted, False otherwise
    """
    with st.expander(f"📄 {file_name}"):
        language = st.text_input("Summary Language", value="English", key=f"lang_{file_name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Summarize", key=f"summary_{file_name}", use_container_width=True):
                with st.spinner(f"Generating summary in {language}..."):
                    summary = chat_engine.summarize_document.invoke({"file_name": file_name, "language": language})
                    summary_message = f"**Summary for `{file_name}` (in {language}):**\n\n{summary}"
                    chat_history.append(AIMessage(content=summary_message))
                    st.rerun()
        
        with col2:
            if st.button("Delete", key=f"delete_{file_name}", use_container_width=True, type="primary"):
                with st.spinner(f"Deleting {file_name} and rebuilding knowledge base..."):
                    chat_engine.delete_document(file_name)
                
                # Add confirmation message to chat
                chat_history.append(
                    AIMessage(content=f"🗑️ The document **{file_name}** has been successfully deleted from the knowledge base.")
                )
                st.rerun()
                return True
    return False

def render_knowledge_base_section(chat_engine, chat_history: list):
    """Render the knowledge base management section."""
    st.markdown("### Knowledge Base")
    
    if not chat_engine.file_names:
        st.info("Your knowledge base is empty. Add some documents below.")
    else:
        # Create scrollable container that shows exactly 4 files
        num_files = len(chat_engine.file_names)
        container_height = min(num_files, 4) * 95  # 95px per file, max 4 files visible
        
        with st.container(height=container_height):
            for file_name in chat_engine.file_names:
                render_document_expander(file_name, chat_engine, chat_history)

def handle_file_upload(uploaded_files: list, temp_dir: str) -> tuple[list, list]:
    """
    Handle file upload and save to temporary directory.
    
    Args:
        uploaded_files: List of uploaded file objects
        temp_dir: Temporary directory path
        
    Returns:
        tuple: (temp_file_paths, successful_files)
    """
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    temp_file_paths = []
    successful_files = []
    
    for file in uploaded_files:
        temp_path = os.path.join(temp_dir, file.name)
        try:
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            temp_file_paths.append(temp_path)
            successful_files.append(file.name)
        except Exception as e:
            st.error(f"❌ Failed to process {file.name}: File may be corrupted")
    
    return temp_file_paths, successful_files

def create_add_documents_handler(chat_engine, chat_history: list):
    """Create the handler function for adding new documents."""
    def handle_add_documents():
        """Handle adding new documents with comprehensive error handling and user feedback."""
        # Get the current uploader key to access the right session state
        current_key = f"new_files_uploader_{st.session_state.uploader_key}"
        uploaded_files = st.session_state.get(current_key, [])
        
        if not uploaded_files:
            return
        
        try:
            # Check for duplicates
            existing_files = set(chat_engine.file_names)
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
                temp_file_paths, successful_files = handle_file_upload(files_to_add, temp_dir)
                
                # Add documents to knowledge base
                if temp_file_paths:
                    try:
                        with st.spinner(f"Adding {len(successful_files)} new document(s)..."):
                            chat_engine.add_documents(temp_file_paths)
                        
                        # Success message
                        file_list = ", ".join(successful_files)
                        chat_history.append(
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
    
    return handle_add_documents

def render_add_documents_section(chat_engine, chat_history: list):
    """Render the section for adding new documents."""
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
    
    handle_add_documents = create_add_documents_handler(chat_engine, chat_history)
    
    st.button(
        "Add to Knowledge Base", 
        on_click=handle_add_documents,
        use_container_width=True, 
        disabled=not new_uploaded_files
    )

def render_reset_section():
    """Render the reset knowledge base section."""
    if st.session_state.get("confirming_reset", False):
        st.error("This will delete the entire knowledge base and cannot be undone.")
        col1, col2 = st.columns(2)
        
        if col1.button("✅ Yes, Confirm", use_container_width=True, type="primary"):
            from .session_manager import reset_knowledge_base
            reset_knowledge_base()
            st.rerun()
            
        if col2.button("❌ Cancel", use_container_width=True):
            st.session_state.confirming_reset = False
            st.rerun()
    else:
        if st.button(
            "Reset Knowledge Base", 
            on_click=lambda: st.session_state.update(confirming_reset=True), 
            use_container_width=True
        ):
            pass

def create_knowledge_base_handler(chat_engine, chat_history: list):
    """Create the handler function for initial knowledge base creation."""
    def handle_create_kb():
        """Handle the creation of initial knowledge base."""
        initial_uploaded_files = st.session_state.get("initial_uploader", [])
        
        if not initial_uploaded_files:
            return
            
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
            temp_file_paths, successful_files = handle_file_upload(unique_files.values(), temp_dir)
            
            # Create knowledge base
            if temp_file_paths:
                try:
                    with st.spinner(f"Creating knowledge base from {len(successful_files)} document(s)...\n(This may take a moment for large files)"):
                        chat_engine.create_and_save(temp_file_paths)
                    
                    st.session_state.kb_initialized = True
                    
                    # Success message
                    file_list = ", ".join(successful_files)
                    chat_history.append(
                        AIMessage(content=f"✅ Knowledge Base created successfully with: {file_list}")
                    )
                    
                except ValueError as ve:
                    # Handle specific errors from create_and_save
                    error_message = str(ve)
                    if "No readable content found" in error_message:
                        st.error("❌ Unable to create knowledge base: The uploaded files contain no readable text.")
                        st.error("Possible causes:")
                        st.error("• Image-only PDFs with poor quality images that OCR cannot process")
                        st.error("• Empty or corrupted files") 
                        st.error("• Files in unsupported formats")
                        st.error("• Very small files with insufficient content")
                        
                        # Show which files failed if available
                        if "Failed files:" in error_message:
                            failed_part = error_message.split("Failed files:")[1].strip()
                            st.error(f"• Failed files: {failed_part}")
                    else:
                        st.error(f"❌ Failed to create knowledge base: {error_message}")
                        
                    # Add chat message for failed creation
                    chat_history.append(
                        AIMessage(content=f"❌ Failed to create knowledge base: {error_message}")
                    )
                except Exception as e:
                    st.error("❌ An unexpected error occurred while creating the knowledge base. Please try again.")
            else:
                st.error("❌ No valid files could be processed.")
            
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            st.error("❌ An unexpected error occurred while creating the knowledge base. Please try again.")
    
    return handle_create_kb

def render_initial_upload_section(chat_engine, chat_history: list):
    """Render the initial file upload section for creating knowledge base."""
    render_welcome_message()
    
    initial_uploaded_files = st.file_uploader(
        "Documents", 
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="initial_uploader",
        label_visibility="collapsed"
    )
    
    handle_create_kb = create_knowledge_base_handler(chat_engine, chat_history)
    
    if st.button("Create Knowledge Base", use_container_width=True, disabled=not initial_uploaded_files):
        handle_create_kb()
        st.rerun()

def render_chat_messages(chat_history: list):
    """Render the chat message history."""
    for message in chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("ai", avatar="🤖"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(message.content)

def handle_chat_input(prompt: str, chat_engine, chat_history: list) -> Optional[str]:
    """
    Handle user chat input and return AI response.
    
    Args:
        prompt: User input text
        chat_engine: The AgentEngine instance
        chat_history: Current chat history
        
    Returns:
        str: AI response or None if knowledge base not initialized
    """
    if not st.session_state.get("kb_initialized"):
        st.error("Please create a knowledge base first using the sidebar.")
        return None
        
    chat_history.append(HumanMessage(content=prompt))
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)

    with st.chat_message("AI", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = chat_engine.invoke(prompt, chat_history)
            st.write(response)
            chat_history.append(AIMessage(content=response))
            
    return response 