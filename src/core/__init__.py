"""
Core Business Logic Package

This package contains the core business logic for the AI Office Assistant:
- RAG Engine (engine.py)
- Document Parser (parser.py) 
- Session Management (session.py)
"""

from .engine import AgentEngine, STORAGE_DIR
from .parser import DocumentParser
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