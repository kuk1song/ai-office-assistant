"""
Core Business Logic Package

This package contains the core business logic for the AI Office Assistant:
- AI Agent System (agent_system.py) - Unified AI agent interface and orchestration
- Document Parser (document_parser.py) - Multi-format document processing with OCR
- Session Management (session.py) - Application state and lifecycle management
"""

from .agent_system import AgentEngine, STORAGE_DIR
from .document_parser import DocumentParser
from .session import (
    initialize_app, 
    reset_knowledge_base, 
    ensure_session_state,
    get_chat_engine,
    get_chat_history,
    is_kb_initialized
)

__all__ = [
    'AgentEngine',
    'STORAGE_DIR', 
    'DocumentParser',
    'initialize_app',
    'reset_knowledge_base',
    'ensure_session_state',
    'get_chat_engine', 
    'get_chat_history',
    'is_kb_initialized'
] 