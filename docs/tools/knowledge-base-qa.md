# Knowledge Base Q&A Tool

## Overview

The knowledge base Q&A tool is the primary interface for retrieving information from uploaded documents. It uses Retrieval-Augmented Generation (RAG) to provide contextually relevant answers based on document content.

## Purpose

- **Primary use case**: Answering questions about document content
- **Technology**: RAG with FAISS vector store and OpenAI embeddings
- **Retrieval strategy**: Semantic similarity search (k=8 chunks)

## How It Works

1. **User Query**: User asks a natural language question
2. **Vector Search**: System finds most relevant document chunks using semantic similarity
3. **Context Generation**: Retrieved chunks are formatted as context
4. **LLM Response**: GPT-4o-mini generates an answer based on the context

## Tool Signature

```python
def knowledge_base_qa(query: str) -> str
```

### Parameters

- **query** (str): The user's question in natural language

### Returns

- **str**: A comprehensive answer based on the document content, or an error message if the knowledge base is not initialized

## Usage Examples

### Good Queries
- "What is the maximum transmission power mentioned in the specifications?"
- "Summarize the key findings from the antenna measurement report"
- "What are the frequency bands supported by this device?"

### System Responses
- **Success**: Detailed answer with relevant information from documents
- **No KB**: "Error: The knowledge base is not initialized. Please load documents first."
- **No Answer**: "I could not find an answer in the documents."

## Implementation Details

- **Location**: `src/core/tools/knowledge_base/qa.py`
- **Factory Function**: `create_knowledge_base_qa_tool(engine)`
- **Dependencies**: Requires initialized RAG chain in AgentEngine
- **Error Handling**: Graceful handling of uninitialized knowledge base

## Best Practices

1. **Specific Questions**: More specific questions yield better results
2. **Document Context**: Questions should relate to uploaded document content
3. **Natural Language**: Use conversational, natural language queries
4. **Follow-up**: Can be used for follow-up questions in conversation

## Related Tools

- **summarize_document**: For comprehensive document summaries
- **extract_technical_specifications**: For extracting specific data points
