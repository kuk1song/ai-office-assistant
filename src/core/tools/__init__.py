"""
Agent Tools Registry

This module provides centralized access to all agent tools and manages their instantiation.
"""
from typing import TYPE_CHECKING, List

from .knowledge_base.qa import create_knowledge_base_qa_tool
from .document.summarizer import create_summarize_document_tool
from .technical.spec_extractor import create_tech_spec_extractor_tool
from .calculations.link_budget import calculate_link_budget

if TYPE_CHECKING:
    from ..engine import AgentEngine


def create_all_tools(engine: "AgentEngine") -> List:
    """
    Creates and returns all agent tools bound to the given engine instance.
    
    Args:
        engine: The AgentEngine instance to bind tools to
        
    Returns:
        List of all configured tools ready for use with the agent
    """
    return [
        create_knowledge_base_qa_tool(engine),
        create_summarize_document_tool(engine),
        create_tech_spec_extractor_tool(engine),
        calculate_link_budget  # This tool is stateless, no binding needed
    ]


# Export individual tool creators for advanced use cases
__all__ = [
    'create_all_tools',
    'create_knowledge_base_qa_tool',
    'create_summarize_document_tool', 
    'create_tech_spec_extractor_tool',
    'calculate_link_budget'
]
