"""
Agent Executor - AI Agent Execution and Coordination

Responsible for:
- Creating and managing LangChain agent executors
- Coordinating tool usage and agent reasoning
- Managing agent prompts and behavior
- Executing agent workflows and conversations
"""

from typing import List, Dict, Optional, Any
from langchain.agents import AgentExecutor as LangChainAgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate


class AgentExecutor:
    """
    Manages AI agent execution and tool coordination.
    
    This class provides a high-level interface for creating and executing
    AI agents that can use tools and maintain conversational context.
    """
    
    def __init__(self, ai_model_manager, tool_registry):
        """
        Initialize the agent executor.
        
        Args:
            ai_model_manager: AI model manager for LLM access
            tool_registry: Tool registry for agent tools
        """
        self.ai_model_manager = ai_model_manager
        self.tool_registry = tool_registry
        self.agent_executor: Optional[LangChainAgentExecutor] = None
        self.file_list: List[str] = []
        self._is_initialized = False
    
    def build_agent(self, file_list: List[str] = None) -> None:
        """
        Build the agent executor with tools and prompt configuration.
        
        Args:
            file_list: List of files in the knowledge base for context
        """
        if not self.tool_registry.is_initialized():
            print("❌ Cannot build agent without initialized tool registry")
            return
        
        try:
            # Update file list
            self.file_list = file_list or []
            
            # Get LLM and tools
            llm = self.ai_model_manager.get_llm_provider().get_llm()
            tools = self.tool_registry.get_tools()
            
            if not tools:
                print("❌ No tools available for agent")
                return
            
            # Create agent prompt with file list context
            agent_prompt = self._create_agent_prompt(self.file_list)
            
            # Create OpenAI tools agent
            agent = create_openai_tools_agent(llm, tools, agent_prompt)
            
            # Create agent executor
            self.agent_executor = LangChainAgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=True
            )
            
            self._is_initialized = True
            print(f"✅ Agent executor built with {len(tools)} tools")
            
        except Exception as e:
            print(f"❌ Error building agent: {str(e)}")
            self.agent_executor = None
            self._is_initialized = False
    
    def _create_agent_prompt(self, file_list: List[str]) -> ChatPromptTemplate:
        """
        Create the agent system prompt with file list context.
        
        Args:
            file_list: List of files in the knowledge base
            
        Returns:
            ChatPromptTemplate for the agent
        """
        # Format file list for prompt
        file_list_str = ", ".join(file_list) if file_list else "No files uploaded yet"
        
        # Create system prompt with operational guide
        system_prompt = f"""
You are an expert AI assistant specializing in Communication Engineering.
Your primary goal is to assist users by analyzing technical documents and performing relevant calculations.
You have access to a specialized set of tools to help you. The user has uploaded the following files: {file_list_str}

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
        
        # Create prompt template
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def execute(self, query: str, chat_history: List = None) -> str:
        """
        Execute a query through the agent.
        
        Args:
            query: User query to process
            chat_history: Optional chat history for context
            
        Returns:
            Agent response string
        """
        if not self._is_initialized or not self.agent_executor:
            return "❌ Agent executor not initialized. Please ensure tools and knowledge base are available."
        
        try:
            # Prepare input for agent
            agent_input = {
                "input": query,
                "chat_history": chat_history or []
            }
            
            # Execute agent
            response = self.agent_executor.invoke(agent_input)
            
            # Extract output from response
            if isinstance(response, dict) and "output" in response:
                return response["output"]
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            print(f"❌ Error in agent execution: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def is_ready(self) -> bool:
        """
        Check if agent executor is ready for queries.
        
        Returns:
            True if agent is initialized and ready
        """
        return (self._is_initialized and 
                self.agent_executor is not None and 
                self.tool_registry.is_initialized())
    
    def rebuild_agent(self, file_list: List[str] = None) -> bool:
        """
        Rebuild the agent executor (useful after tool or knowledge base updates).
        
        Args:
            file_list: Updated list of files in the knowledge base
            
        Returns:
            True if rebuild was successful
        """
        print("🔄 Rebuilding agent executor...")
        self.agent_executor = None
        self._is_initialized = False
        
        self.build_agent(file_list)
        return self.is_ready()
    
    def get_agent_info(self) -> Dict:
        """
        Get information about the current agent configuration.
        
        Returns:
            Dictionary with agent configuration info
        """
        tool_info = self.tool_registry.get_registry_status()
        
        return {
            "initialized": self._is_initialized,
            "ready": self.is_ready(),
            "file_count": len(self.file_list),
            "files": self.file_list,
            "tools": tool_info,
            "agent_executor_available": self.agent_executor is not None
        }
    
    def update_file_list(self, file_list: List[str]) -> bool:
        """
        Update the file list and rebuild agent if necessary.
        
        Args:
            file_list: New list of files in the knowledge base
            
        Returns:
            True if update was successful
        """
        if self.file_list == file_list:
            # No change needed
            return True
        
        print(f"📝 Updating file list: {len(file_list)} files")
        return self.rebuild_agent(file_list)
    
    def execute_with_streaming(self, query: str, chat_history: List = None):
        """
        Execute a query with streaming response (if supported).
        
        Args:
            query: User query to process
            chat_history: Optional chat history for context
            
        Yields:
            Response chunks as they become available
        """
        if not self._is_initialized or not self.agent_executor:
            yield "❌ Agent executor not initialized. Please ensure tools and knowledge base are available."
            return
        
        try:
            # Prepare input for agent
            agent_input = {
                "input": query,
                "chat_history": chat_history or []
            }
            
            # Check if agent supports streaming
            if hasattr(self.agent_executor, 'stream'):
                for chunk in self.agent_executor.stream(agent_input):
                    if isinstance(chunk, dict) and "output" in chunk:
                        yield chunk["output"]
                    else:
                        yield str(chunk)
            else:
                # Fall back to regular execution
                response = self.execute(query, chat_history)
                yield response
                
        except Exception as e:
            yield f"❌ Error processing query: {str(e)}"
    
    def get_tool_usage_stats(self) -> Dict:
        """
        Get statistics about tool usage (if available).
        
        Returns:
            Dictionary with tool usage statistics
        """
        # This would require implementing tool usage tracking
        # For now, return basic information
        return {
            "available_tools": self.tool_registry.list_available_tools(),
            "total_tools": len(self.tool_registry.get_tools()),
            "agent_ready": self.is_ready()
        }
