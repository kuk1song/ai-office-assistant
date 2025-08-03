"""
Main Layout Management

This module handles the overall layout structure of the application.
Designed to support future multi-layer navigation system.

Current Implementation:
- Single layer with sidebar and main chat
- Prepared for future Hub/Detail layer system

Future Implementation:
- Hub Layer: KB selection and management
- Detail Layer: Individual KB chat interface
- Navigation breadcrumbs and layer switching
"""

import streamlit as st
from .components.chat import render_chat_messages, handle_chat_input
from .components.upload import render_initial_upload_section, render_add_documents_section
from .components.knowledge_base import render_knowledge_base_section, render_reset_section
from ..core.session import ensure_session_state, get_chat_engine, get_chat_history, is_kb_initialized

def render_sidebar():
    """
    Render the complete sidebar layout.
    
    Current: Single KB management
    Future: Will include layer navigation and KB selection
    """
    with st.sidebar:
        # Ensure session state is properly initialized
        ensure_session_state()
        
        chat_engine = get_chat_engine()
        chat_history = get_chat_history()
        
        # FUTURE: Layer navigation will be added here
        # render_layer_navigation()
        
        if is_kb_initialized():
            # --- KB EXISTS: SHOW MANAGEMENT UI ---
            render_knowledge_base_section(chat_engine, chat_history)
            st.divider()
            render_add_documents_section(chat_engine, chat_history)
            
            # Reset button - only show when there's a KB to reset
            st.divider()
            render_reset_section()
        else:
            # --- NO KB: SHOW CREATE_KB_UI ---
            render_initial_upload_section(chat_engine, chat_history)

def render_main_chat():
    """
    Render the main chat interface.
    
    Current: Direct chat with single KB
    Future: Will adapt based on current layer (Hub vs Detail)
    """
    # FUTURE: Layer-specific title and content
    # if current_layer == "hub":
    #     render_hub_interface()
    # else:
    #     render_kb_detail_interface()
    
    st.title("🤖 AI Office Assistant")
    
    chat_history = get_chat_history()
    chat_engine = get_chat_engine()
    
    # Display chat messages
    render_chat_messages(chat_history)

    # User input - will be adapted for layer-specific functionality
    if prompt := st.chat_input("Ask me anything about your documents..."):
        handle_chat_input(prompt, chat_engine, chat_history)

# FUTURE: Layer-specific rendering functions
def render_hub_interface():
    """
    Render the Knowledge Base Hub interface.
    
    Will include:
    - KB cards/list
    - Create new KB option
    - KB management options
    """
    pass

def render_kb_detail_interface():
    """
    Render the individual KB detail interface.
    
    Will include:
    - Current KB name and info
    - Chat interface specific to this KB
    - KB-specific actions
    """
    pass

def render_layer_navigation():
    """
    Render navigation between layers.
    
    Will include:
    - Breadcrumb navigation
    - Back/forward buttons
    - Layer switching controls
    """
    pass 