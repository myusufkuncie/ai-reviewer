"""Tool registry for managing available tools"""

from typing import Dict, List, Optional
from .base import Tool


class ToolRegistry:
    """Registry for managing and discovering tools"""

    def __init__(self):
        """Initialize empty registry"""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        print(f"✓ Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools

        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def get_tool_schemas(self) -> List[Dict]:
        """Get schemas for all tools

        Returns:
            List of tool schemas for AI provider
        """
        return [tool.to_schema() for tool in self._tools.values()]

    def execute_tool(self, name: str, **kwargs):
        """Execute a tool by name

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            ToolResult from execution

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        return tool.execute(**kwargs)
