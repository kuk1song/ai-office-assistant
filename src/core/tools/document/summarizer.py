"""
Document Summarization Tool

This tool provides multi-language document summarization capabilities.
"""
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic.v1 import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...agent_system import AgentEngine


class SummarizeInput(BaseModel):
    file_name: str = Field(description="The exact file name of the document to summarize.")
    language: str = Field(description="The language for the summary (e.g., 'English', '中文', 'italiano').", default="English")


def create_summarize_document_tool(engine: "AgentEngine"):
    """
    Factory function to create a summarize_document tool bound to a specific engine instance.
    
    Args:
        engine: The AgentEngine instance containing the raw texts and LLM
        
    Returns:
        The configured summarize_document tool
    """
    
    @tool(args_schema=SummarizeInput)
    def summarize_document(file_name: str, language: str = "English") -> str:
        """
        Use this tool to generate a detailed summary of a SINGLE, SPECIFIC document in a specified language.
        The first input MUST be the exact file name.
        The second, optional input is the language for the summary (defaults to English).
        """
        # Debug output to verify language parameter
        print(f"[DEBUG] Summarize tool called with: file_name='{file_name}', language='{language}'")
        
        if file_name not in engine.raw_texts:
            return f"Error: The file '{file_name}' was not found in the knowledge base. Please use one of the available files: {', '.join(engine.file_names)}"
        
        text_to_summarize = engine.raw_texts[file_name]
        
        # Enhanced language-specific prompt with stronger enforcement
        language_instruction = f"""
ABSOLUTE CRITICAL LANGUAGE REQUIREMENT: 
The user has specifically requested the summary in "{language}". You MUST strictly comply.

LANGUAGE RULES:
- If language is "中文", "Chinese", or "chinese": Write EVERYTHING in Chinese characters only (中文).
- If language is "italiano", "Italian", or "italian": Write EVERYTHING in Italian only.
- If language is "English" or "english": Write EVERYTHING in English only.
- For any other language: Write EVERYTHING in that specified language only.

STRICT PROHIBITIONS:
- NEVER write in English if another language is requested
- NEVER mix languages in the same response
- NEVER provide translations or bilingual content
- NEVER add English explanations after non-English content

COMPLIANCE CHECK: Before responding, verify that your ENTIRE response is written in "{language}".
"""
        
        system_prompt = f"""You are a professional document summarization expert. {language_instruction}

Your task is to create a comprehensive yet concise summary of the provided document. Focus on:
1. Main topics and key points
2. Important data, numbers, and technical details
3. Conclusions and findings
4. Overall document purpose and context

FINAL REMINDER: Your response must be written entirely in "{language}". Do not write in any other language."""
        
        human_prompt = f"""Please summarize this document in {language} ONLY. 
Do not use any other language in your response.

Document: {file_name}

Content:
{text_to_summarize[:16000]}

Remember: Respond entirely in {language}."""
        
        response = engine.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        return response.content
    
    return summarize_document
