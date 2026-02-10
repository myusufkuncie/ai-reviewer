"""Main code reviewer orchestrator"""

from typing import Dict, List, Optional
from .config import ConfigLoader
from .cache import CacheManager
from ..tools.registry import ToolRegistry
from ..tools.file_reader import FileReaderTool
from ..tools.git_history import GitHistoryTool
from ..tools.linter import LinterTool
from ..verification.verifier import DoubleCheckVerifier
from ..analyzers.language_detector import LanguageDetector


class CodeReviewer:
    """Main orchestrator for code review process"""

    def __init__(
        self,
        platform_adapter,
        ai_provider,
        context_builder,
        config: Optional[ConfigLoader] = None,
        cache: Optional[CacheManager] = None,
        enable_verification: bool = True
    ):
        """Initialize code reviewer

        Args:
            platform_adapter: Platform adapter (GitLab/GitHub)
            ai_provider: AI provider adapter
            context_builder: Context builder
            config: Configuration loader
            cache: Cache manager
            enable_verification: Enable 2-pass verification with linter (default: True)
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

        # Initialize language detector
        self.language_detector = LanguageDetector()

        # Initialize tool system for 2-pass verification
        self.enable_verification = enable_verification
        if self.enable_verification:
            self.tool_registry = ToolRegistry()
            self.tool_registry.register(FileReaderTool())
            self.tool_registry.register(GitHistoryTool())
            self.tool_registry.register(LinterTool())  # NEW: Linter tool!
            self.verifier = DoubleCheckVerifier(
                ai_provider=self.ai_provider,
                tool_registry=self.tool_registry,
                language_detector=self.language_detector,
                config=self.config
            )
            print("✓ Double-check verification enabled (with linter)")
        else:
            self.verifier = None
            print("⊘ Verification disabled")

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
        print(f"\n{'='*80}")
        print("Posting review comments...")
        print(f"{'='*80}")
        if all_comments:
            self.platform.post_comments(pr_id, all_comments)
        else:
            print("⊘ No comments to post")

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
        # Generate cache key (v6 for linter-first approach)
        cache_version = "v6-linter-first" if self.enable_verification else "v3"
        cache_key = self.cache.get_cache_key(
            f"{filepath}:{diff}:{cache_version}"
        )

        # Check cache
        cached_review = self.cache.get(cache_key)
        if cached_review:
            print("✓ Using cached review")
            return cached_review

        # Detect language for linter
        language = self.language_detector.detect_language(filepath)

        # Extract changed line numbers from diff
        changed_lines = self._extract_changed_lines(diff)

        # Pass 1: Run linter first (if enabled)
        linter_results = None
        if self.enable_verification and self.tool_registry:
            print("Pass 1: Running linter...")
            linter_tool = self.tool_registry.get_tool("run_linter")
            if linter_tool:
                result = linter_tool.execute(
                    filepath=filepath,
                    language=language,
                    changed_lines=changed_lines
                )
                if result.success and result.output:
                    linter_results = result.output
                    issue_count = linter_results.get('issue_count', 0)
                    if issue_count > 0:
                        print(f"  → Linter found {issue_count} issues on changed lines")
                    else:
                        print(f"  → Linter: no issues found")
                else:
                    print(f"  → Linter: {result.output.get('message', 'skipped')}")

        # Build context (including linter results if available)
        print("Building context...")
        context = self.context_builder.build_context(filepath, diff, change, linter_results=linter_results)

        # Pass 2: AI analyzes with linter context
        if linter_results and linter_results.get('issue_count', 0) > 0:
            print("Pass 2: AI analysis with linter context...")
        else:
            print("Pass 2: AI analysis...")
        comments = self.ai_provider.review(context)

        # Cache result
        if comments:
            self.cache.set(cache_key, comments)

        return comments

    def _extract_changed_lines(self, diff: str) -> List[int]:
        """Extract line numbers of changed lines from diff

        Args:
            diff: Git diff string

        Returns:
            List of changed line numbers
        """
        import re
        changed_lines = []

        # Parse diff to find changed lines
        # Format: @@ -old_start,old_count +new_start,new_count @@
        for line in diff.split('\n'):
            # Find hunk headers
            if line.startswith('@@'):
                match = re.search(r'\+(\d+),?(\d+)?', line)
                if match:
                    start = int(match.group(1))
                    count = int(match.group(2)) if match.group(2) else 1
                    # Add all lines in this hunk
                    changed_lines.extend(range(start, start + count))

        return changed_lines

    def _should_exclude(self, filepath: str) -> bool:
        """Check if file should be excluded

        Args:
            filepath: File path

        Returns:
            True if file should be excluded
        """
        # Hardcoded exclusion for config files (always exclude)
        filename = filepath.split('/')[-1]
        if filename.startswith('.ai-review-config') and filename.endswith('.json'):
            return True

        exclusions = self.config.get_exclusions()

        # Check directories
        for excluded_dir in exclusions.get('directories', []):
            if excluded_dir in filepath:
                return True

        # Check file prefixes
        for prefix in exclusions.get('file_prefixes', []):
            if filename.startswith(prefix):
                return True

        # Check file patterns
        for pattern in exclusions.get('file_patterns', []):
            if self._matches_pattern(filepath, pattern):
                return True

        return False

    def _matches_pattern(self, filepath: str, pattern: str) -> bool:
        """Check if filepath matches pattern using glob syntax

        Args:
            filepath: File path
            pattern: Pattern (e.g., *.lock, .ai-review-config*.json)

        Returns:
            True if matches
        """
        import fnmatch
        from pathlib import Path

        # Get just the filename for matching
        filename = Path(filepath).name

        # Use fnmatch for glob pattern matching
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filepath, pattern)
