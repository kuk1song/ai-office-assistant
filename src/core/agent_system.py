"""
This module contains the core Retrieval-Augmented Generation (RAG) engine.
"""
import os
import json
from typing import List, Dict
from .document_parser import DocumentParser
from .tools import create_all_tools
from .models import AIModelManager
from .knowledge import KnowledgeBaseManager
from .orchestration import OrchestrationManager

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
import shutil

# --- STORAGE CONFIGURATION ---
# Absolute path to the project root, ensuring that paths are always correct
# regardless of the script's execution directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# New standard location for variable data, following professional practices.
STORAGE_DIR = os.path.join(PROJECT_ROOT, "var", "persistent_storage")
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
        # Pass absolute storage directory to avoid accidental root-level paths
        self.knowledge_base = KnowledgeBaseManager(self.ai_models, STORAGE_DIR)
        
        # --- AI Orchestration (New Architecture) ---
        self.orchestration = OrchestrationManager(self.ai_models, self.knowledge_base)
        
        # Core components (Backward Compatibility)
        self.llm = self.ai_models.get_llm_provider().get_llm()
        self.embeddings = self.ai_models.get_embedding_provider().get_embeddings()
        
        # State variables (Backward Compatibility - delegated to specialized managers)
        self.vectorstore: FAISS = None
        self.rag_chain = None
        self.agent_executor: AgentExecutor = None
        self.file_names: List[str] = []
        self.raw_texts: Dict[str, str] = {}
        
        # Ensure storage directory exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
        # --- Initialize Tools (Backward Compatibility) ---
        self.tools = create_all_tools(self)
        
        # Expose summary tool for direct calls from UI (Backward Compatibility)
        self.summarize_document = self.tools[1] if len(self.tools) > 1 else None

    # --- New Architecture Methods ---
    
    def create_and_save(self, uploaded_files: List) -> List[str]:
        """Create knowledge base from uploaded files and save persistently."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        failed_files = self.knowledge_base.create_knowledge_base(uploaded_files)
        
        # --- Update backward compatibility state variables ---
        self._sync_state_from_knowledge_base()
        
        # --- Initialize orchestration manager (New Architecture) ---
        self.orchestration.initialize(self)
        
        # --- Build chains and agents (keep existing behavior) ---
        self._build_rag_chain()
        self._build_agent()
        
        return failed_files

    def add_documents(self, uploaded_files: List) -> List[str]:
        """Add new documents to existing knowledge base."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        failed_files = self.knowledge_base.add_documents(uploaded_files)
        
        # --- Update backward compatibility state variables ---
        self._sync_state_from_knowledge_base()
        
        # --- Refresh orchestration manager (New Architecture) ---
        self.orchestration.refresh_components()
        
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
        
        # --- Refresh orchestration manager (New Architecture) ---
        if self.vectorstore:  # Only rebuild if there are still documents
            self.orchestration.refresh_components()
        
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
        # Ensure new storage directory exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        self.knowledge_base.save_knowledge_base()

    def load(self) -> bool:
        """Load existing state from persistent storage. Returns True if successful."""
        # --- Delegate to new Knowledge Base Manager (New Architecture) ---
        success = self.knowledge_base.load_knowledge_base()
        
        if success:
            # --- Update backward compatibility state variables ---
            self._sync_state_from_knowledge_base()
            
            # --- Initialize orchestration manager (New Architecture) ---
            self.orchestration.initialize(self)
            
            # --- Rebuild chains and agents (keep existing behavior) ---
            self._build_rag_chain()
            self._build_agent()
        
        return success

    def get_summarize_tool(self):
        """Get the summarize tool for direct UI access."""
        # --- Try new architecture first ---
        if self.orchestration and self.orchestration.is_ready():
            exposed_tools = self.orchestration.get_exposed_tools()
            if "summarize_document" in exposed_tools:
                return exposed_tools["summarize_document"]["tool"]
        
        # --- Fallback to old architecture (Backward Compatibility) ---
        return self.summarize_document

    def invoke(self, query: str, chat_history: List = None) -> str:
        """Process a user query through the agent."""
        # --- Use new Orchestration Manager (New Architecture) ---
        if self.orchestration and self.orchestration.is_ready():
            return self.orchestration.process_query(query, chat_history)
        
        # --- Fallback to old behavior (Backward Compatibility) ---
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

    # --- Backward Compatibility Methods ---
    
    def _sync_state_from_knowledge_base(self):
        """Sync backward compatibility state variables from knowledge base manager."""
        self.file_names = self.knowledge_base.get_file_names()
        self.raw_texts = self.knowledge_base.get_all_raw_texts()
        self.vectorstore = self.knowledge_base.vector_store_manager.get_vector_store()

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

    def _build_agent(self):
        """Builds or rebuilds the agent executor with the current file list."""
        if not self.file_names:
            return
            
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
