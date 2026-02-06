"""Tool for analyzing git history during verification"""

import subprocess
from typing import Dict, Any
from .base import Tool, ToolResult


class GitHistoryTool(Tool):
    """Tool to analyze git history for a file"""

    def __init__(self, repo_path: str = "."):
        """Initialize git history tool

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path

    @property
    def name(self) -> str:
        return "git_history"

    @property
    def description(self) -> str:
        return "Get recent git commit history for a file. Shows who changed it, when, and why. Useful for understanding the context and intent behind existing code."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "filepath": {
                "type": "string",
                "description": "Relative path to the file from repository root",
                "required": True
            },
            "max_commits": {
                "type": "integer",
                "description": "Maximum number of recent commits to return (default: 5)",
                "required": False
            }
        }

    def execute(self, **kwargs) -> ToolResult:
        """Get git history for file

        Args:
            filepath: Path to file
            max_commits: Max number of commits (default: 5)

        Returns:
            ToolResult with commit history or error
        """
        filepath = kwargs.get("filepath")
        max_commits = kwargs.get("max_commits", 5)

        if not filepath:
            return ToolResult(
                success=False,
                data=None,
                error="filepath parameter is required"
            )

        try:
            # Get commit history with format: hash|author|date|message
            cmd = [
                "git", "log",
                f"-{max_commits}",
                "--pretty=format:%H|%an|%ar|%s",
                "--", filepath
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Git command failed: {result.stderr}"
                )

            if not result.stdout.strip():
                return ToolResult(
                    success=True,
                    data={
                        "filepath": filepath,
                        "commits": [],
                        "message": "No commit history found (new file or not tracked)"
                    }
                )

            # Parse commits
            commits = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],  # Short hash
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })

            return ToolResult(
                success=True,
                data={
                    "filepath": filepath,
                    "commits": commits,
                    "count": len(commits)
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data=None,
                error="Git command timed out"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting git history: {str(e)}"
            )
