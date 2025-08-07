"""
Knowledge Base Q&A Tool

This tool provides question-answering capabilities over the knowledge base using RAG.
"""
from langchain.tools import tool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...engine import AgentEngine


def create_knowledge_base_qa_tool(engine: "AgentEngine"):
    """
    Factory function to create a knowledge_base_qa tool bound to a specific engine instance.
    
    Args:
        engine: The AgentEngine instance containing the RAG chain
        
    Returns:
        The configured knowledge_base_qa tool
    """
    
    @tool
    def knowledge_base_qa(query: str) -> str:
        """
        Use this tool to answer any questions about the content of the uploaded documents.
        The input should be a user's full question.
        This is your primary tool for information retrieval.
        """
        if not engine.rag_chain:
            return "Error: The knowledge base is not initialized. Please load documents first."
        response = engine.rag_chain.invoke({"input": query})
        return response.get("answer", "I could not find an answer in the documents.")
    
    return knowledge_base_qa
