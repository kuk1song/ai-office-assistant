"""
Chat Interface Components

Contains all components related to chat functionality:
- Message rendering
- Chat input handling
- Message history management
"""

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from typing import Optional, List

def render_chat_messages(chat_history: List):
    """Render the chat message history."""
    for message in chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("ai", avatar="🤖"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(message.content)

def handle_chat_input(prompt: str, chat_engine, chat_history: List) -> Optional[str]:
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