"""Main code reviewer orchestrator"""

from typing import Dict, List, Optional
from .config import ConfigLoader
from .cache import CacheManager


class CodeReviewer:
    """Main orchestrator for code review process"""

    def __init__(
        self,
        platform_adapter,
        ai_provider,
        context_builder,
        config: Optional[ConfigLoader] = None,
        cache: Optional[CacheManager] = None
    ):
        """Initialize code reviewer

        Args:
            platform_adapter: Platform adapter (GitLab/GitHub)
            ai_provider: AI provider adapter
            context_builder: Context builder
            config: Configuration loader
            cache: Cache manager
        """
        self.platform = platform_adapter
        self.ai_provider = ai_provider
        self.context_builder = context_builder
        self.config = config or ConfigLoader()

        cache_settings = self.config.get_cache_settings()
        self.cache = cache or CacheManager(
            cache_dir=cache_settings.get('cache_location', '.review_cache'),
            ttl_days=cache_settings.get('ttl_days', 7)
        )

    def review_pull_request(self, pr_id: str) -> Dict:
        """Review a pull request/merge request

        Args:
            pr_id: PR/MR identifier

        Returns:
            Review statistics
        """
        print("=" * 80)
        print(f"Starting code review for PR/MR: {pr_id}")
        print("=" * 80)

        # Get changes from platform
        changes = self.platform.get_changes(pr_id)

        stats = {
            'files_reviewed': 0,
            'files_skipped': 0,
            'files_excluded': 0,
            'total_comments': 0,
            'cache_hits': 0
        }

        all_comments = []

        for change in changes:
            filepath = change['filepath']
            diff = change['diff']

            # Check exclusions
            if self._should_exclude(filepath):
                stats['files_excluded'] += 1
                print(f"⊘ Excluding: {filepath}")
                continue

            # Skip binary or large files
            if change.get('binary') or len(diff) > 10000:
                stats['files_skipped'] += 1
                print(f"⊘ Skipping: {filepath}")
                continue

            print(f"\n{'='*80}")
            print(f"Reviewing: {filepath}")
            print(f"{'='*80}")

            # Review file
            comments = self._review_file(filepath, diff, change)

            if comments:
                all_comments.extend(comments)
                stats['total_comments'] += len(comments)

            stats['files_reviewed'] += 1

        # Post comments to platform
        if all_comments:
            self.platform.post_comments(pr_id, all_comments)

        # Post summary
        self.platform.post_summary(pr_id, stats, all_comments)

        print(f"\n{'='*80}")
        print("Review complete!")
        print(f"Files reviewed: {stats['files_reviewed']}")
        print(f"Comments posted: {stats['total_comments']}")
        print(f"{'='*80}\n")

        return stats

    def _review_file(self, filepath: str, diff: str, change: Dict) -> List[Dict]:
        """Review a single file

        Args:
            filepath: Path to file
            diff: File diff
            change: Change data

        Returns:
            List of review comments
        """
        # Generate cache key
        cache_key = self.cache.get_cache_key(f"{filepath}:{diff}:v3")

        # Check cache
        cached_review = self.cache.get(cache_key)
        if cached_review:
            print(f"✓ Using cached review")
            return cached_review

        # Build context
        print("Building context...")
        context = self.context_builder.build_context(filepath, diff, change)

        # Get AI review
        print("Requesting AI review...")
        comments = self.ai_provider.review(context)

        # Cache result
        if comments:
            self.cache.set(cache_key, comments)

        return comments

    def _should_exclude(self, filepath: str) -> bool:
        """Check if file should be excluded

        Args:
            filepath: File path

        Returns:
            True if file should be excluded
        """
        exclusions = self.config.get_exclusions()

        # Check directories
        for excluded_dir in exclusions.get('directories', []):
            if excluded_dir in filepath:
                return True

        # Check file prefixes
        filename = filepath.split('/')[-1]
        for prefix in exclusions.get('file_prefixes', []):
            if filename.startswith(prefix):
                return True

        # Check file patterns
        for pattern in exclusions.get('file_patterns', []):
            if self._matches_pattern(filepath, pattern):
                return True

        return False

    def _matches_pattern(self, filepath: str, pattern: str) -> bool:
        """Check if filepath matches pattern

        Args:
            filepath: File path
            pattern: Pattern (e.g., *.lock)

        Returns:
            True if matches
        """
        if pattern.startswith('*.'):
            ext = pattern[1:]
            return filepath.endswith(ext)
        return pattern in filepath
