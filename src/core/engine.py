"""
This module contains the core Retrieval-Augmented Generation (RAG) engine.
"""
import os
import json
from typing import List, Dict
from .parser import DocumentParser
from .tools import create_all_tools
from .models import AIModelManager
from .knowledge import KnowledgeBaseManager

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
import shutil

# --- STORAGE CONFIGURATION ---
STORAGE_DIR = "persistent_storage"
FAISS_INDEX_PATH = os.path.join(STORAGE_DIR, "vector_store")
METADATA_PATH = os.path.join(STORAGE_DIR, "metadata.json")


# --- AGENT SYSTEM PROMPT ---
AGENT_SYSTEM_PROMPT = """
You are an expert AI assistant specializing in Communication Engineering.
Your primary goal is to assist users by analyzing technical documents and performing relevant calculations.
You have access to a specialized set of tools to help you. The user has uploaded the following files: {file_list}

Here is your operational guide:

1.  **For General Questions**: Use the `knowledge_base_qa` tool to answer questions about the contents of the documents. This is your primary tool for information retrieval.

2.  **For Summarization**: Use the `summarize_document` tool ONLY when the user explicitly asks for a summary of a specific file.

3.  **For Calculations (e.g., Link Budget)**: This is a multi-step process.
    *   **Step A: Identify Parameters**: First, understand what parameters are needed for the calculation (e.g., for a link budget, you need distance, power, gain, loss, frequency).
    *   **Step B: Gather Data**: If the user has not provided all parameters, use the `extract_technical_specifications` tool to find the missing information from the uploaded documents. You may need to call this tool multiple times for different documents.
    *   **Step C: Execute Calculation**: Once you have all the necessary parameters, use the `calculate_link_budget` tool to perform the calculation.
    *   **Step D: Present Results**: Clearly present the final calculated results to the user and, if helpful, list the parameters used to get there.

Always be professional, concise, and when possible, cite the source document for any data you extract.
"""


class AgentEngine:
    """
    An AI Agent that can use tools to interact with a knowledge base of documents.
    This engine supports persistence, allowing it to load, save, and update the knowledge base.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        os.environ["OPENAI_API_KEY"] = api_key
        
        # --- AI Model Management (New Architecture) ---
        self.ai_models = AIModelManager(api_key)
        
        # --- Knowledge Base Management (New Architecture) ---
        self.knowledge_base = KnowledgeBaseManager(self.ai_models)
        
        # Core components (Backward Compatibility)
        self.llm = self.ai_models.get_llm_provider().get_llm()
        self.embeddings = self.ai_models.get_embedding_provider().get_embeddings()
        
        # State variables (Backward Compatibility - delegated to KnowledgeBaseManager)
        self.vectorstore: FAISS = None
        self.rag_chain = None
        self.agent_executor: AgentExecutor = None
        self.file_names: List[str] = []
        self.raw_texts: Dict[str, str] = {}
        
        # Ensure storage directory exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
        # --- Initialize Tools ---
        self.tools = create_all_tools(self)
        
        # Expose summary tool for direct calls from UI
        self.summarize_document = self.tools[1]  # summarize_document is the second tool

    def _get_text_splitter(self, docs_for_rag: List = None):
        """
        Creates an optimal text splitter based on document characteristics.
        """
        if not docs_for_rag:
            # Default configuration for unknown content
            return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            
        # Smart text splitting based on content size
        # For OCR content, extract the actual text without the prefix
        actual_texts = []
        for i, doc in enumerate(docs_for_rag):
            text = doc[0] if isinstance(doc, tuple) else doc
            
            print(f"  - Document {i+1}: Total length = {len(text)} chars")
            
            # Remove OCR prefix for length calculation
            if text.startswith("=== Text extracted from images using OCR ===\n"):
                actual_text = text.replace("=== Text extracted from images using OCR ===\n", "")
                actual_texts.append(actual_text)
                print(f"    OCR document: Prefix removed, actual length = {len(actual_text)} chars")
            else:
                actual_texts.append(text)
                print(f"    Regular document: Using full length = {len(text)} chars")
        
        total_text_length = sum(len(text) for text in actual_texts)
        avg_text_length = total_text_length / len(actual_texts) if actual_texts else 0
        
        print(f"  - Total actual text length: {total_text_length}")
        print(f"  - Average text length: {int(avg_text_length)}")
        
        # Adjust chunk size based on document size
        if avg_text_length < 200:
            # Very tiny documents - don't chunk, use as single piece
            chunk_size = max(avg_text_length, 50)  # Minimum 50 chars for FAISS
            overlap = 0
            print(f"  - Strategy: TINY documents (< 200 chars) - minimal chunking")
        elif avg_text_length < 500:
            # Small documents - use smaller chunks
            chunk_size = max(200, int(avg_text_length * 0.8))
            overlap = min(50, chunk_size // 4)
            print(f"  - Strategy: SMALL documents (200-500 chars)")
        elif avg_text_length < 2000:
            # Medium documents
            chunk_size = 500
            overlap = 100
            print(f"  - Strategy: MEDIUM documents (500-2000 chars)")
        else:
            # Large documents - use default settings
            chunk_size = 1000
            overlap = 200
            print(f"  - Strategy: LARGE documents (> 2000 chars)")
            
        print(f"Using chunk_size={chunk_size}, overlap={overlap} for {len(docs_for_rag)} document(s) (avg_length={int(avg_text_length)})")
        return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        
    def _create_valid_chunks(self, text_splitter, docs_for_rag):
        """
        Creates and validates document chunks, filtering out empty or meaningless ones.
        """
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        # Ensure we have meaningful chunks
        valid_chunks = [doc for doc in split_docs if len(doc.page_content.strip()) > 10]
        
        if not valid_chunks:
            raise ValueError("No meaningful content chunks could be created from the documents.")
        
        if len(valid_chunks) < len(split_docs):
            print(f"Filtered out {len(split_docs) - len(valid_chunks)} empty or very small chunks")
            
        return valid_chunks

    def _build_agent(self):
        """Builds or rebuilds the agent executor with the current file list."""
        print("Rebuilding agent with updated file list...")
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT.format(file_list=", ".join(self.file_names))),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        agent = create_openai_tools_agent(self.llm, self.tools, agent_prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        print("Agent is ready.")

    def _build_rag_chain(self):
        """Builds the RAG chain from the current vectorstore."""
        if not self.vectorstore:
            return
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 8})
        qa_prompt = ChatPromptTemplate.from_template("""
Answer the user's question based only on the following context:
{context}

Question: {input}
""")
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    def create_and_save(self, uploaded_files: List) -> List[str]:
        """Create knowledge base from uploaded files and save persistently."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        failed_files = self.knowledge_base.create_knowledge_base(uploaded_files)
        
        # --- Update backward compatibility state variables ---
        self._sync_state_from_knowledge_base()
        
        # --- Build chains and agents (keep existing behavior) ---
        self._build_rag_chain()
        self._build_agent()
        
        return failed_files

    def _sync_state_from_knowledge_base(self):
        """Sync backward compatibility state variables from knowledge base manager."""
        self.file_names = self.knowledge_base.get_file_names()
        self.raw_texts = self.knowledge_base.get_all_raw_texts()
        self.vectorstore = self.knowledge_base.vector_store_manager.get_vector_store()

    def add_documents(self, uploaded_files: List) -> List[str]:
        """Add new documents to existing knowledge base."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        failed_files = self.knowledge_base.add_documents(uploaded_files)
        
        # --- Update backward compatibility state variables ---
        self._sync_state_from_knowledge_base()
        
        # --- Rebuild chains and agents (keep existing behavior) ---
        self._build_rag_chain()
        self._build_agent()
        
        return failed_files

    def delete_document(self, file_name_to_delete: str):
        """Delete a specific document from the knowledge base."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        success = self.knowledge_base.delete_document(file_name_to_delete)
        
        if not success:
            raise ValueError(f"Document '{file_name_to_delete}' not found in knowledge base.")
        
        # --- Update backward compatibility state variables ---
        self._sync_state_from_knowledge_base()
        
        # --- Rebuild chains and agents (keep existing behavior) ---
        if self.vectorstore:  # Only rebuild if there are still documents
            self._build_rag_chain()
            self._build_agent()
        else:
            # Clear chains if no documents remain
            self.rag_chain = None
            self.agent_executor = None

    def save(self):
        """Save the current state to persistent storage."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        self.knowledge_base.save_knowledge_base()

    def load(self) -> bool:
        """Load existing state from persistent storage. Returns True if successful."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        success = self.knowledge_base.load_knowledge_base()
        
        if success:
            # --- Update backward compatibility state variables ---
            self._sync_state_from_knowledge_base()
            
            # --- Rebuild chains and agents (keep existing behavior) ---
            self._build_rag_chain()
            self._build_agent()
        
        return success

    def invoke(self, query: str, chat_history: List = None) -> str:
        """Process a user query through the agent."""
        if not self.agent_executor:
            return "❌ Knowledge base not initialized. Please upload documents first."
        
        try:
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": chat_history or []
            })
            return response["output"]
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

    def reset_storage(self):
        """Delete all persistent storage."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        self.knowledge_base.clear_knowledge_base()
        
        # --- Reset backward compatibility state variables ---
        self.vectorstore = None
        self.rag_chain = None
        self.agent_executor = None
        self.file_names = []
        self.raw_texts = {}
