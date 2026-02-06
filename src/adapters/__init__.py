"""Platform and AI provider adapters"""

from .base import PlatformAdapter, AIProviderAdapter
from .gitlab_adapter import GitLabAdapter
from .github_adapter import GitHubAdapter
from .openrouter_provider import OpenRouterProvider

__all__ = [
    "PlatformAdapter",
    "AIProviderAdapter",
    "GitLabAdapter",
    "GitHubAdapter",
    "OpenRouterProvider"
]
