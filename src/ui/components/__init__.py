"""
UI Components Package

Contains reusable UI components organized by functionality:
- chat.py: Chat interface components
- sidebar.py: Sidebar management components  
- upload.py: File upload components
- knowledge_base.py: Knowledge base management components

This structure will support the future multi-layer navigation system.
"""

from .chat import render_chat_messages, handle_chat_input
from .upload import (
    render_initial_upload_section,
    render_add_documents_section
)
from .knowledge_base import (
    render_knowledge_base_section,
    render_document_expander,
    render_reset_section
)

__all__ = [
    # Chat components
    'render_chat_messages',
    'handle_chat_input',
    
    # Upload components
    'render_initial_upload_section', 
    'render_add_documents_section',
    
    # Knowledge base components
    'render_knowledge_base_section',
    'render_document_expander', 
    'render_reset_section'
] 