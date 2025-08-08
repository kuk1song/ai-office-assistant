"""
Orchestration Manager - Unified AI Orchestration Lifecycle Management

Responsible for:
- Orchestrating all AI components (RAG, Agent, Tools)
- Managing interaction flow and context
- Coordinating between different processing modes
- Providing unified API for AI orchestration operations
"""

from typing import List, Dict, Optional, Any
from .rag_retriever import RAGRetriever
from .agent_executor import AgentExecutor
from .tool_registry import ToolRegistry


class OrchestrationManager:
    """
    Unified manager for all AI orchestration operations.
    
    This class provides a single point of access for all AI processing
    functionality and coordinates between RAG retrieval, agent execution,
    and tool management components.
    """
    
    def __init__(self, ai_model_manager, knowledge_base_manager):
        """
        Initialize the orchestration manager.
        
        Args:
            ai_model_manager: AI model manager for LLM operations
            knowledge_base_manager: Knowledge base manager for data access
        """
        self.ai_model_manager = ai_model_manager
        self.knowledge_base_manager = knowledge_base_manager
        
        # Initialize component managers
        self.rag_retriever = RAGRetriever(ai_model_manager, knowledge_base_manager)
        self.tool_registry = ToolRegistry()
        self.agent_executor = AgentExecutor(ai_model_manager, self.tool_registry)
        
        # State management
        self._is_initialized = False
        self._conversation_mode = "agent"  # "agent" or "rag"
    
    def initialize(self, engine_instance) -> bool:
        """
        Initialize all conversation components.
        
        Args:
            engine_instance: AgentEngine instance for tool initialization
            
        Returns:
            True if initialization was successful
        """
        try:
            print("🚀 Initializing orchestration manager...")
            
            # Initialize tool registry first
            self.tool_registry.initialize_tools(engine_instance)
            if not self.tool_registry.is_initialized():
                print("❌ Failed to initialize tool registry")
                return False
            
            # Initialize RAG retriever
            if self.knowledge_base_manager.is_initialized():
                self.rag_retriever.build_rag_chain()
                if not self.rag_retriever.is_ready():
                    print("⚠️ RAG retriever not ready - knowledge base may be empty")
            
            # Initialize agent executor
            file_list = self.knowledge_base_manager.get_file_names()
            self.agent_executor.build_agent(file_list)
            if not self.agent_executor.is_ready():
                print("❌ Failed to initialize agent executor")
                return False
            
            self._is_initialized = True
            print("✅ Orchestration manager initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing orchestration manager: {str(e)}")
            return False
    
    def process_query(self, query: str, chat_history: List = None, 
                     mode: str = None) -> str:
        """
        Process a user query through the orchestration system.
        
        Args:
            query: User query to process
            chat_history: Optional chat history for context
            mode: Optional processing mode ("agent" or "rag")
            
        Returns:
            Processed response string
        """
        if not self._is_initialized:
            return "❌ Orchestration system not initialized. Please check configuration."
        
        # Determine processing mode
        processing_mode = mode or self._conversation_mode
        
        try:
            if processing_mode == "rag":
                # Use RAG-only mode for direct knowledge retrieval
                return self._process_rag_query(query, chat_history)
            else:
                # Use agent mode for full tool access and reasoning
                return self._process_agent_query(query, chat_history)
                
        except Exception as e:
            print(f"❌ Error processing query in {processing_mode} mode: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def _process_rag_query(self, query: str, chat_history: List = None) -> str:
        """
        Process query using RAG retrieval only.
        
        Args:
            query: User query
            chat_history: Optional chat history
            
        Returns:
            RAG response string
        """
        if not self.rag_retriever.is_ready():
            return "❌ RAG system not available. Please ensure knowledge base is initialized."
        
        return self.rag_retriever.query(query, chat_history)
    
    def _process_agent_query(self, query: str, chat_history: List = None) -> str:
        """
        Process query using full agent capabilities.
        
        Args:
            query: User query
            chat_history: Optional chat history
            
        Returns:
            Agent response string
        """
        if not self.agent_executor.is_ready():
            return "❌ Agent system not available. Please ensure tools and knowledge base are initialized."
        
        return self.agent_executor.execute(query, chat_history)
    
    def search_knowledge_base(self, query: str, k: int = 8) -> List[Dict]:
        """
        Perform direct search on knowledge base.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        return self.rag_retriever.search_knowledge_base(query, k)
    
    def execute_tool_directly(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Execute a tool directly by name.
        
        Args:
            tool_name: Name of the tool to execute
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
            
        Returns:
            Tool execution result
        """
        return self.tool_registry.execute_tool(tool_name, *args, **kwargs)
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return self.tool_registry.list_available_tools()
    
    def set_conversation_mode(self, mode: str) -> bool:
        """
        Set the default conversation mode.
        
        Args:
            mode: Conversation mode ("agent" or "rag")
            
        Returns:
            True if mode was set successfully
        """
        if mode not in ["agent", "rag"]:
            print(f"❌ Invalid conversation mode: {mode}. Use 'agent' or 'rag'")
            return False
        
        self._conversation_mode = mode
        print(f"✅ Conversation mode set to: {mode}")
        return True
    
    def get_conversation_mode(self) -> str:
        """
        Get the current conversation mode.
        
        Returns:
            Current conversation mode
        """
        return self._conversation_mode
    
    def refresh_components(self) -> bool:
        """
        Refresh all conversation components after knowledge base updates.
        
        Returns:
            True if refresh was successful
        """
        print("🔄 Refreshing conversation components...")
        
        try:
            # Refresh RAG retriever
            if self.knowledge_base_manager.is_initialized():
                self.rag_retriever.rebuild_chain()
            
            # Refresh agent executor with updated file list
            file_list = self.knowledge_base_manager.get_file_names()
            self.agent_executor.rebuild_agent(file_list)
            
            print("✅ Conversation components refreshed")
            return True
            
        except Exception as e:
            print(f"❌ Error refreshing components: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict:
        """
        Get comprehensive status of the conversation system.
        
        Returns:
            Dictionary with system status information
        """
        return {
            "orchestrator": {
                "initialized": self._is_initialized,
                "conversation_mode": self._conversation_mode
            },
            "rag_retriever": self.rag_retriever.get_retrieval_info(),
            "agent_executor": self.agent_executor.get_agent_info(),
            "tool_registry": self.tool_registry.get_registry_status(),
            "knowledge_base": self.knowledge_base_manager.get_knowledge_base_info()
        }
    
    def is_ready(self) -> bool:
        """
        Check if the conversation orchestrator is ready for queries.
        
        Returns:
            True if system is initialized and ready
        """
        return (self._is_initialized and 
                self.tool_registry.is_initialized() and
                (self.agent_executor.is_ready() or self.rag_retriever.is_ready()))
    
    def stream_response(self, query: str, chat_history: List = None, 
                       mode: str = None):
        """
        Process query with streaming response (if supported).
        
        Args:
            query: User query to process
            chat_history: Optional chat history for context
            mode: Optional conversation mode
            
        Yields:
            Response chunks as they become available
        """
        if not self._is_initialized:
            yield "❌ Conversation system not initialized. Please check configuration."
            return
        
        conversation_mode = mode or self._conversation_mode
        
        try:
            if conversation_mode == "agent" and self.agent_executor.is_ready():
                # Use agent streaming if available
                for chunk in self.agent_executor.execute_with_streaming(query, chat_history):
                    yield chunk
            else:
                # Fall back to regular processing
                response = self.process_query(query, chat_history, conversation_mode)
                yield response
                
        except Exception as e:
            yield f"❌ Error processing query: {str(e)}"
    
    def get_exposed_tools(self) -> Dict:
        """
        Get tools that should be exposed for direct UI access.
        
        Returns:
            Dictionary of exposed tools with their metadata
        """
        # Return specific tools that UI needs direct access to
        exposed_tools = {}
        
        # Get summarization tool if available
        if self.tool_registry.validate_tool("summarize_document"):
            summarize_tool = self.tool_registry.get_tool_by_name("summarize_document")
            if summarize_tool:
                exposed_tools["summarize_document"] = {
                    "tool": summarize_tool,
                    "metadata": self.tool_registry.get_tool_metadata("summarize_document")
                }
        
        return exposed_tools
