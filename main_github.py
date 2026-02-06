#!/usr/bin/env python3
"""Main entry point for GitHub Actions"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import ConfigLoader, CacheManager, CodeReviewer
from src.adapters import GitHubAdapter, OpenRouterProvider
from src.analyzers import ContextBuilder


def main():
    """Main function for GitHub Actions"""
    print("=" * 80)
    print("AI Code Reviewer - GitHub Edition")
    print("=" * 80)

    # Load configuration
    config = ConfigLoader()

    if not config.is_enabled():
        print("⚠ AI Reviewer is disabled in configuration")
        sys.exit(0)

    # Initialize components
    platform = GitHubAdapter()
    if not platform.authenticate():
        print("✗ Failed to authenticate with GitHub")
        sys.exit(1)

    # Get PR number
    pr_number = os.getenv("GITHUB_PR_NUMBER")
    if not pr_number:
        print("✗ GITHUB_PR_NUMBER not set")
        sys.exit(1)

    # Initialize AI provider
    ai_provider = OpenRouterProvider(
        model=config.get_model(),
        max_tokens=config.get('max_tokens', 4000),
        temperature=config.get('temperature', 0.3)
    )

    # Initialize context builder
    context_builder = ContextBuilder(platform, config)

    # Initialize cache
    cache_settings = config.get_cache_settings()
    cache = CacheManager(
        cache_dir=cache_settings.get('cache_location', '.review_cache'),
        ttl_days=cache_settings.get('ttl_days', 7)
    )

    # Create reviewer
    reviewer = CodeReviewer(
        platform_adapter=platform,
        ai_provider=ai_provider,
        context_builder=context_builder,
        config=config,
        cache=cache
    )

    # Run review
    try:
        stats = reviewer.review_pull_request(pr_number)
        print(f"\n✓ Review completed successfully")
        print(f"Files reviewed: {stats['files_reviewed']}")
        print(f"Comments posted: {stats['total_comments']}")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Review failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
