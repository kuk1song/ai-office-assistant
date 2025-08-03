"""
Knowledge Base Management Components

Contains all components related to knowledge base management:
- Document listing and management
- Document operations (summarize, delete)
- Reset functionality
"""

import streamlit as st
from langchain_core.messages import AIMessage
from typing import List

def render_document_expander(file_name: str, chat_engine, chat_history: List) -> bool:
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
                
                # Check if knowledge base is now empty and update session state
                if not chat_engine.file_names:
                    st.session_state.kb_initialized = False
                    chat_history.append(
                        AIMessage(content=f"🗑️ The document **{file_name}** has been deleted. The knowledge base is now empty.")
                    )
                else:
                    chat_history.append(
                        AIMessage(content=f"🗑️ The document **{file_name}** has been successfully deleted from the knowledge base.")
                    )
                
                st.rerun()
                return True
    return False

def render_knowledge_base_section(chat_engine, chat_history: List):
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

def render_reset_section():
    """Render the reset knowledge base section."""
    if st.session_state.get("confirming_reset", False):
        st.error("This will delete the entire knowledge base and cannot be undone.")
        col1, col2 = st.columns(2)
        
        if col1.button("✅ Yes, Confirm", use_container_width=True, type="primary"):
            from ...core.session import reset_knowledge_base
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