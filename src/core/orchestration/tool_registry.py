"""
Tool Registry - Tool Registration and Management

Responsible for:
- Centralized tool registration and discovery
- Tool lifecycle management and validation
- Providing unified tool access for agents
- Managing tool metadata and capabilities
"""

from typing import List, Dict, Callable, Optional, Any
from ..tools import create_all_tools


class ToolRegistry:
    """
    Centralized registry for managing and accessing AI agent tools.
    
    This class provides a unified interface for tool registration, discovery,
    and execution, ensuring consistent tool management across the conversation system.
    """
    
    def __init__(self, engine_instance=None):
        """
        Initialize the tool registry.
        
        Args:
            engine_instance: Optional AgentEngine instance for tool creation
        """
        self.engine_instance = engine_instance
        self.tools: List = []
        self.tool_metadata: Dict[str, Dict] = {}
        self._is_initialized = False
    
    def initialize_tools(self, engine_instance) -> None:
        """
        Initialize tools using the provided engine instance.
        
        Args:
            engine_instance: AgentEngine instance containing tool dependencies
        """
        if not engine_instance:
            print("❌ Cannot initialize tools without engine instance")
            return
        
        try:
            self.engine_instance = engine_instance
            
            # Create all tools using existing tool factory
            self.tools = create_all_tools(engine_instance)
            
            # Build tool metadata for discovery and validation
            self._build_tool_metadata()
            
            self._is_initialized = True
            print(f"✅ Tool registry initialized with {len(self.tools)} tools")
            
        except Exception as e:
            print(f"❌ Error initializing tools: {str(e)}")
            self.tools = []
            self.tool_metadata = {}
            self._is_initialized = False
    
    def _build_tool_metadata(self) -> None:
        """
        Build metadata for registered tools for discovery and validation.
        """
        self.tool_metadata = {}
        
        for i, tool in enumerate(self.tools):
            tool_name = getattr(tool, 'name', f'tool_{i}')
            tool_description = getattr(tool, 'description', 'No description available')
            
            # Extract tool schema if available
            tool_schema = None
            if hasattr(tool, 'args_schema') and tool.args_schema:
                try:
                    tool_schema = tool.args_schema.schema()
                except:
                    tool_schema = None
            
            self.tool_metadata[tool_name] = {
                "name": tool_name,
                "description": tool_description,
                "schema": tool_schema,
                "index": i,
                "available": True
            }
    
    def get_tools(self) -> List:
        """
        Get all registered tools.
        
        Returns:
            List of all available tools
        """
        return self.tools.copy() if self.tools else []
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance if found, None otherwise
        """
        if tool_name in self.tool_metadata:
            tool_index = self.tool_metadata[tool_name]["index"]
            if tool_index < len(self.tools):
                return self.tools[tool_index]
        
        return None
    
    def get_tool_metadata(self, tool_name: str = None) -> Dict:
        """
        Get metadata for tools.
        
        Args:
            tool_name: Optional specific tool name. If None, returns all metadata
            
        Returns:
            Tool metadata dictionary
        """
        if tool_name:
            return self.tool_metadata.get(tool_name, {})
        
        return self.tool_metadata.copy()
    
    def list_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return [
            name for name, metadata in self.tool_metadata.items()
            if metadata.get("available", False)
        ]
    
    def validate_tool(self, tool_name: str) -> bool:
        """
        Validate that a tool exists and is callable.
        
        Args:
            tool_name: Name of the tool to validate
            
        Returns:
            True if tool is valid and available
        """
        if tool_name not in self.tool_metadata:
            return False
        
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return False
        
        # Check if tool is callable
        return callable(getattr(tool, 'run', None)) or callable(tool)
    
    def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Execute a tool by name with provided arguments.
        
        Args:
            tool_name: Name of the tool to execute
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found or invalid
            Exception: Any tool execution errors
        """
        if not self.validate_tool(tool_name):
            raise ValueError(f"Tool '{tool_name}' not found or invalid")
        
        tool = self.get_tool_by_name(tool_name)
        
        try:
            # Try to call the tool's run method first
            if hasattr(tool, 'run') and callable(tool.run):
                return tool.run(*args, **kwargs)
            # Fall back to calling the tool directly
            elif callable(tool):
                return tool(*args, **kwargs)
            else:
                raise ValueError(f"Tool '{tool_name}' is not callable")
                
        except Exception as e:
            print(f"❌ Error executing tool '{tool_name}': {str(e)}")
            raise
    
    def get_registry_status(self) -> Dict:
        """
        Get status information about the tool registry.
        
        Returns:
            Dictionary with registry status information
        """
        return {
            "initialized": self._is_initialized,
            "total_tools": len(self.tools),
            "available_tools": len(self.list_available_tools()),
            "tool_names": self.list_available_tools(),
            "engine_available": self.engine_instance is not None
        }
    
    def refresh_tools(self) -> bool:
        """
        Refresh tools by reinitializing them.
        
        Returns:
            True if refresh was successful
        """
        if not self.engine_instance:
            print("❌ Cannot refresh tools without engine instance")
            return False
        
        print("🔄 Refreshing tool registry...")
        self.tools = []
        self.tool_metadata = {}
        self._is_initialized = False
        
        self.initialize_tools(self.engine_instance)
        return self._is_initialized
    
    def register_external_tool(self, tool_name: str, tool_instance: Any, 
                             description: str = None) -> bool:
        """
        Register an external tool to the registry.
        
        Args:
            tool_name: Name for the tool
            tool_instance: The tool instance to register
            description: Optional description of the tool
            
        Returns:
            True if registration was successful
        """
        try:
            # Validate tool instance
            if not callable(tool_instance) and not hasattr(tool_instance, 'run'):
                print(f"❌ Tool '{tool_name}' must be callable or have a 'run' method")
                return False
            
            # Add to tools list
            self.tools.append(tool_instance)
            tool_index = len(self.tools) - 1
            
            # Add metadata
            self.tool_metadata[tool_name] = {
                "name": tool_name,
                "description": description or "External tool",
                "schema": None,  # External tools may not have schema
                "index": tool_index,
                "available": True,
                "external": True
            }
            
            print(f"✅ External tool '{tool_name}' registered successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error registering external tool '{tool_name}': {str(e)}")
            return False
    
    def is_initialized(self) -> bool:
        """
        Check if the tool registry is initialized.
        
        Returns:
            True if registry is initialized and ready
        """
        return self._is_initialized and len(self.tools) > 0
