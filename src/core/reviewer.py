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
            enable_verification: Enable 2-pass verification with linter
                (default: True)
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

        # Separate cached files from files that need AI review
        pending_items = []  # items to batch-review via AI

        for change in changes:
            filepath = change['filepath']
            diff = change['diff']

            if self._should_exclude(filepath):
                stats['files_excluded'] += 1
                print(f"⊘ Excluding: {filepath}")
                continue

            if change.get('binary') or len(diff) > 10000:
                stats['files_skipped'] += 1
                print(f"⊘ Skipping: {filepath}")
                continue

            # Check cache first — no API call needed
            cache_version = (
                "v6-linter-first" if self.enable_verification else "v3"
            )
            cache_key = self.cache.get_cache_key(
                f"{filepath}:{diff}:{cache_version}"
            )
            cached = self.cache.get(cache_key)
            if cached:
                print(f"✓ Cache hit: {filepath}")
                all_comments.extend(cached)
                stats['total_comments'] += len(cached)
                stats['files_reviewed'] += 1
                stats['cache_hits'] += 1
                continue

            # Run linter (Pass 1) before batching
            language = self.language_detector.detect_language(filepath)
            changed_lines = self._extract_changed_lines(diff)
            linter_results = None

            if self.enable_verification and self.tool_registry:
                linter_tool = self.tool_registry.get_tool("run_linter")
                if linter_tool:
                    result = linter_tool.execute(
                        filepath=filepath,
                        language=language,
                        changed_lines=changed_lines,
                    )
                    if result.success and result.data:
                        linter_results = result.data
                        count = linter_results.get('filtered_issues', 0)
                        if count > 0:
                            print(
                                f"  → Linter: {count} issues in {filepath}"
                            )
                        else:
                            print(f"  → Linter: no issues in {filepath}")

            pending_items.append({
                'filepath': filepath,
                'diff': diff,
                'change': change,
                'linter_results': linter_results,
                'cache_key': cache_key,
            })

        # Batch-review pending files in chunks
        if pending_items:
            batch_size = self.config.get('batch_size', 7)
            total = len(pending_items)
            chunks = [
                pending_items[i:i + batch_size]
                for i in range(0, total, batch_size)
            ]
            print(f"\n{'='*80}")
            print(
                f"AI review: {total} file(s) in"
                f" {len(chunks)} batch(es) of up to {batch_size}"
            )
            print(f"{'='*80}")

            for chunk_idx, chunk in enumerate(chunks, 1):
                filenames = ', '.join(item['filepath'] for item in chunk)
                print(f"\nBatch {chunk_idx}/{len(chunks)}: {filenames}")

                batch_context = self.context_builder.build_batch_context(
                    chunk
                )
                comments = self.ai_provider.review_batch(batch_context)

                # Map comments back to their files and cache each
                comments_by_file: Dict[str, list] = {}
                for c in (comments or []):
                    fp = c.get('filepath', '')
                    comments_by_file.setdefault(fp, []).append(c)

                for item in chunk:
                    fp = item['filepath']
                    file_comments = comments_by_file.get(fp, [])
                    if file_comments:
                        self.cache.set(item['cache_key'], file_comments)
                        all_comments.extend(file_comments)
                        stats['total_comments'] += len(file_comments)
                    stats['files_reviewed'] += 1

        # Clear previous bot comments before posting new ones
        print(f"\n{'='*80}")
        print("Clearing previous bot comments...")
        print(f"{'='*80}")
        self.platform.clear_bot_comments(pr_id)

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
        config_check = (
            filename.startswith('.ai-review-config') and
            filename.endswith('.json')
        )
        if config_check:
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
            pattern: Pattern
                (e.g., *.lock, .ai-review-config*.json)

        Returns:
            True if matches
        """
        import fnmatch
        from pathlib import Path

        # Get just the filename for matching
        filename = Path(filepath).name

        # Use fnmatch for glob pattern matching
        return (
            fnmatch.fnmatch(filename, pattern)
            or fnmatch.fnmatch(filepath, pattern)
        )
