"""Tool for reading related files during verification"""

import os
from typing import Dict, Any
from .base import Tool, ToolResult


class FileReaderTool(Tool):
    """Tool to read file contents for verification"""

    def __init__(self, repo_path: str = "."):
        """Initialize file reader

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the complete contents of a file in the repository. Use this to examine related files, check imports, or understand context around an issue."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "filepath": {
                "type": "string",
                "description": "Relative path to the file from repository root (e.g., 'src/utils/auth.py')",
                "required": True
            }
        }

    def execute(self, **kwargs) -> ToolResult:
        """Read file contents

        Args:
            filepath: Path to file

        Returns:
            ToolResult with file contents or error
        """
        filepath = kwargs.get("filepath")
        if not filepath:
            return ToolResult(
                success=False,
                data=None,
                error="filepath parameter is required"
            )

        try:
            full_path = os.path.join(self.repo_path, filepath)

            if not os.path.exists(full_path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {filepath}"
                )

            # Check file size (limit to 50KB)
            file_size = os.path.getsize(full_path)
            if file_size > 50000:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File too large: {file_size} bytes (max 50KB)"
                )

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return ToolResult(
                success=True,
                data={
                    "filepath": filepath,
                    "content": content,
                    "lines": len(content.split('\n')),
                    "size": file_size
                }
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data=None,
                error="File is binary or not UTF-8 encoded"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error reading file: {str(e)}"
            )
