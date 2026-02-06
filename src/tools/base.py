"""Base tool interface for AI-augmented reviews"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any
    error: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for AI consumption"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }


class Tool(ABC):
    """Abstract base class for all tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for AI to reference"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Parameter schema for the tool

        Example:
        {
            "filepath": {
                "type": "string",
                "description": "Path to file to read",
                "required": True
            }
        }
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution results
        """
        pass

    def to_schema(self) -> Dict:
        """Convert tool to schema for AI provider

        Returns schema in Anthropic tool format
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    param_name: {
                        "type": param_def.get("type", "string"),
                        "description": param_def.get("description", "")
                    }
                    for param_name, param_def in self.parameters.items()
                },
                "required": [
                    param_name
                    for param_name, param_def in self.parameters.items()
                    if param_def.get("required", False)
                ]
            }
        }
