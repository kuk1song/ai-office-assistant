"""
RAG Retriever - Retrieval-Augmented Generation Query Processing

Responsible for:
- Managing RAG chains and retrieval operations
- Providing semantic search capabilities for knowledge base
- Integrating vector retrieval with LLM generation
- Handling retrieval-augmented responses
"""

from typing import List, Dict, Optional
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class RAGRetriever:
    """
    Manages Retrieval-Augmented Generation operations for conversation flow.
    
    This class handles the creation and execution of RAG chains that combine
    knowledge base retrieval with LLM generation for contextually accurate responses.
    """
    
    def __init__(self, ai_model_manager, knowledge_base_manager):
        """
        Initialize the RAG retriever.
        
        Args:
            ai_model_manager: AI model manager for LLM access
            knowledge_base_manager: Knowledge base manager for retrieval
        """
        self.ai_model_manager = ai_model_manager
        self.knowledge_base_manager = knowledge_base_manager
        self.rag_chain = None
        self._is_initialized = False
    
    def build_rag_chain(self) -> None:
        """
        Build the RAG chain for retrieval-augmented generation.
        
        Creates a chain that combines vector store retrieval with LLM generation
        to provide contextually accurate responses based on knowledge base content.
        """
        if not self.knowledge_base_manager.is_initialized():
            print("Knowledge base not initialized, cannot build RAG chain")
            return
        
        try:
            # Get retriever from knowledge base
            retriever = self.knowledge_base_manager.get_vector_store_retriever(
                search_kwargs={"k": 8}
            )
            
            # Create QA prompt template
            qa_prompt = ChatPromptTemplate.from_template("""
Answer the user's question based only on the following context:
{context}

Question: {input}
""")
            
            # Get LLM from AI model manager
            llm = self.ai_model_manager.get_llm_provider().get_llm()
            
            # Create document combination chain
            question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
            
            # Create retrieval chain
            self.rag_chain = create_retrieval_chain(retriever, question_answer_chain)
            self._is_initialized = True
            
            print("✅ RAG chain built successfully")
            
        except Exception as e:
            print(f"❌ Error building RAG chain: {str(e)}")
            self.rag_chain = None
            self._is_initialized = False
    
    def query(self, question: str, chat_history: List = None) -> str:
        """
        Execute a RAG query to get contextually augmented response.
        
        Args:
            question: User question to answer
            chat_history: Optional chat history for context
            
        Returns:
            RAG-augmented response string
        """
        if not self._is_initialized or not self.rag_chain:
            return "❌ RAG system not initialized. Please ensure knowledge base is available."
        
        try:
            # Prepare input for RAG chain
            rag_input = {"input": question}
            
            # Add chat history if provided
            if chat_history:
                # Convert chat history to string context if needed
                history_context = self._format_chat_history(chat_history)
                rag_input["chat_history"] = history_context
            
            # Execute RAG chain
            response = self.rag_chain.invoke(rag_input)
            
            # Extract answer from response
            if isinstance(response, dict) and "answer" in response:
                return response["answer"]
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            print(f"❌ Error in RAG query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def _format_chat_history(self, chat_history: List) -> str:
        """
        Format chat history for RAG context.
        
        Args:
            chat_history: List of chat messages
            
        Returns:
            Formatted chat history string
        """
        if not chat_history:
            return ""
        
        formatted_history = []
        for message in chat_history[-5:]:  # Keep last 5 messages for context
            if hasattr(message, 'content'):
                role = getattr(message, 'type', 'unknown')
                content = message.content
                formatted_history.append(f"{role}: {content}")
            elif isinstance(message, dict):
                role = message.get('type', 'unknown')
                content = message.get('content', '')
                formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history)
    
    def get_retrieval_info(self) -> Dict:
        """
        Get information about the current retrieval setup.
        
        Returns:
            Dictionary with retrieval configuration info
        """
        if not self._is_initialized:
            return {"initialized": False, "status": "Not initialized"}
        
        kb_info = self.knowledge_base_manager.get_knowledge_base_info()
        
        return {
            "initialized": True,
            "status": "Ready",
            "knowledge_base": kb_info,
            "rag_chain_available": self.rag_chain is not None
        }
    
    def is_ready(self) -> bool:
        """
        Check if RAG retriever is ready for queries.
        
        Returns:
            True if RAG system is initialized and ready
        """
        return (self._is_initialized and 
                self.rag_chain is not None and 
                self.knowledge_base_manager.is_initialized())
    
    def rebuild_chain(self) -> bool:
        """
        Rebuild the RAG chain (useful after knowledge base updates).
        
        Returns:
            True if rebuild was successful
        """
        print("🔄 Rebuilding RAG chain...")
        self.rag_chain = None
        self._is_initialized = False
        
        self.build_rag_chain()
        return self.is_ready()
    
    def search_knowledge_base(self, query: str, k: int = 8) -> List[Dict]:
        """
        Perform direct search on knowledge base without generation.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.knowledge_base_manager.is_initialized():
            return []
        
        try:
            # Use knowledge base manager's search functionality
            documents = self.knowledge_base_manager.search_documents(query, k)
            
            # Format documents for return
            formatted_docs = []
            for doc in documents:
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    formatted_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", "unknown")
                    })
                else:
                    formatted_docs.append({"content": str(doc), "metadata": {}, "source": "unknown"})
            
            return formatted_docs
            
        except Exception as e:
            print(f"❌ Error searching knowledge base: {str(e)}")
            return []
