"""
Technical Specification Extraction Tool

This tool extracts specific technical parameters from documents using structured output.
"""
import json
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from pydantic.v1 import BaseModel, Field
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...engine import AgentEngine


class DocumentInput(BaseModel):
    file_name: str = Field(description="The exact file name of the document to process.")


class TechSpecInput(DocumentInput):
    parameters_to_extract: List[str] = Field(description="A list of specific technical parameters to extract from the document.")


def create_tech_spec_extractor_tool(engine: "AgentEngine"):
    """
    Factory function to create an extract_technical_specifications tool bound to a specific engine instance.
    
    Args:
        engine: The AgentEngine instance containing the raw texts and LLM
        
    Returns:
        The configured extract_technical_specifications tool
    """
    
    @tool(args_schema=TechSpecInput)
    def extract_technical_specifications(file_name: str, parameters_to_extract: List[str]) -> Dict[str, Any]:
        """
        Extracts specific numerical or textual technical parameters from a given document.
        Use this to gather the necessary data before performing calculations.
        For example, extract ['Transmitter Power (dBm)', 'Antenna Gain (dBi)'] from 'site_A_specs.pdf'.
        """
        if file_name not in engine.raw_texts:
            return {"error": f"The file '{file_name}' was not found. Available files: {', '.join(engine.file_names)}"}

        document_text = engine.raw_texts[file_name]
        
        # Using JSON mode for structured output
        json_llm = engine.llm.bind(response_format={"type": "json_object"})
        
        extraction_prompt = f"""
        Given the following document text for '{file_name}', extract the values for the following parameters:
        {', '.join(parameters_to_extract)}

        Please return the result as a JSON object where the keys are the parameter names and the values are the extracted values.
        If a parameter is not found, its value should be null.
        Only return the JSON object, with no other text.

        Document Text:
        ---
        {document_text[:16000]}
        ---
        """
        
        try:
            response = json_llm.invoke([HumanMessage(content=extraction_prompt)])
            extracted_data = json.loads(response.content)
            return extracted_data
        except Exception as e:
            return {"error": f"Failed to extract or parse data for {file_name}. Reason: {e}"}
    
    return extract_technical_specifications
