"""Base classes for adapters"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class PlatformAdapter(ABC):
    """Base class for platform adapters (GitHub, GitLab, etc.)"""

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with platform

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def get_changes(self, pr_id: str) -> List[Dict]:
        """Get list of changed files in PR/MR

        Args:
            pr_id: Pull/Merge request ID

        Returns:
            List of changes with filepath, diff, etc.
        """
        pass

    @abstractmethod
    def get_file_content(self, filepath: str, ref: str) -> Optional[str]:
        """Get file content at specific commit

        Args:
            filepath: Path to file
            ref: Git reference (commit SHA, branch, etc.)

        Returns:
            File content or None if not found
        """
        pass

    @abstractmethod
    def post_comments(self, pr_id: str, comments: List[Dict]) -> None:
        """Post review comments to PR/MR

        Args:
            pr_id: Pull/Merge request ID
            comments: List of comments with line, message, severity
        """
        pass

    @abstractmethod
    def post_summary(self, pr_id: str, stats: Dict, comments: List[Dict]) -> None:
        """Post review summary comment

        Args:
            pr_id: Pull/Merge request ID
            stats: Review statistics
            comments: All review comments
        """
        pass

    @abstractmethod
    def clear_bot_comments(self, pr_id: str) -> int:
        """Delete all previous comments posted by this bot on the PR/MR.

        Args:
            pr_id: Pull/Merge request ID

        Returns:
            Number of comments deleted
        """
        pass

    @abstractmethod
    def get_directory_tree(self, directory: str, ref: str) -> List[Dict]:
        """Get directory tree (list of files in directory)

        Args:
            directory: Directory path
            ref: Git reference (commit SHA, branch, etc.)

        Returns:
            List of file/directory items
        """
        pass


class AIProviderAdapter(ABC):
    """Base class for AI provider adapters"""

    @abstractmethod
    def review(self, context: str) -> List[Dict]:
        """Get AI review for given context

        Args:
            context: Review context (code, diff, metadata)

        Returns:
            List of review comments
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to AI provider

        Returns:
            True if connection successful
        """
        pass
