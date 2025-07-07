import os
import base64
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
from typing import List

def analyze_document(text_content: str, image_paths: List[str]) -> str:
    """
    Analyzes a document's text and images in a single call using a multimodal model.

    Args:
        text_content: The textual content of the document, potentially including markdown tables.
        image_paths: A list of paths to image files extracted from the document.

    Returns:
        A comprehensive analysis combining insights from both text and images.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    # We use gpt-4o-mini for its multimodal capabilities and cost-effectiveness.
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        api_key=api_key,
        base_url=api_base,
        temperature=0.1,
        max_tokens=2048,
    )

    # Construct the multimodal message
    message_content = []

    # Add the text part
    # For very long documents, we might need to chunk the text.
    # For this MVP, we'll analyze the first 16000 characters to be safe.
    max_chars = 16000
    truncated_text = text_content[:max_chars]
    if len(text_content) > max_chars:
        print(f"Warning: Document text is very long. Analyzing the first {max_chars} characters.")

    prompt_template = f"""
You are a highly skilled AI assistant specializing in comprehensive document analysis. You will be given the full text of a document (including tables in Markdown format) and all the images contained within it.

Your task is to create a single, cohesive analysis that synthesizes information from ALL provided sources (text, tables, and images). Do not analyze each component separately. Instead, weave them together into a unified report.

Please perform two tasks:
1.  **Provide a concise executive summary** that integrates the main message from the text with key insights derived from the visual data (charts, graphs, images).
2.  **Extract and list the key points** as a bulleted list. These points should be critical pieces of information, drawing from and correlating between the text, tables, and images.

Please structure your response clearly. Use '### Summary' as the heading for the summary, and '### Key Points' as the heading for the bulleted list.

---
Here is the document's text content:
{truncated_text}
---
The following images are also part of this document. Please analyze them in conjunction with the text.
"""
    message_content.append({"type": "text", "text": prompt_template})

    # Add the image parts
    for image_path in image_paths:
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
                message_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    }
                )
        except Exception as e:
            print(f"Warning: Could not read or encode image {image_path}. Skipping. Reason: {e}")

    messages = [
        SystemMessage(content="You are a professional assistant skilled at synthesizing text and visual information into a single, comprehensive analysis."),
        HumanMessage(content=message_content),
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error analyzing document: {e}" 