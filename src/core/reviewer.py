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

            language = self.language_detector.detect_language(filepath)
            changed_lines = self._extract_changed_lines(diff)

            pending_items.append({
                'filepath': filepath,
                'diff': diff,
                'change': change,
                'language': language,
                'changed_lines': changed_lines,
                'linter_results': None,
                'cache_key': cache_key,
            })

        # Run linter (Pass 1) in a single batched subprocess per language
        if self.enable_verification and self.tool_registry and pending_items:
            self._run_batched_linters(pending_items)

        # Batch-review pending files in chunks
        if pending_items:
            # Token budget for a single batch's input context.
            # Keep well below the model's 1M limit to leave room for
            # output tokens and prompt overhead.
            max_input_tokens = self.config.get('max_input_tokens', 800000)
            total = len(pending_items)
            initial_chunks = self._pack_batches(
                pending_items, max_input_tokens
            )
            print(f"\n{'='*80}")
            print(
                f"AI review: {total} file(s) in"
                f" {len(initial_chunks)} batch(es)"
                f" (token budget: {max_input_tokens})"
            )
            print(f"{'='*80}")

            # Process chunks as a queue so oversized chunks can be split
            # in half and re-queued.
            queue = list(initial_chunks)
            processed = 0
            while queue:
                chunk = queue.pop(0)
                batch_context = self.context_builder.build_batch_context(
                    chunk
                )
                # Rough estimate: ~4 chars per token.
                estimated_tokens = len(batch_context) // 4

                if estimated_tokens > max_input_tokens and len(chunk) > 1:
                    mid = len(chunk) // 2
                    print(
                        f"\n⚠ Batch of {len(chunk)} file(s) estimated at"
                        f" ~{estimated_tokens} tokens exceeds budget"
                        f" ({max_input_tokens}). Splitting into"
                        f" {mid} + {len(chunk) - mid}."
                    )
                    queue.insert(0, chunk[mid:])
                    queue.insert(0, chunk[:mid])
                    continue

                if estimated_tokens > max_input_tokens:
                    print(
                        f"\n⚠ Single file exceeds token budget"
                        f" (~{estimated_tokens} tokens):"
                        f" {chunk[0]['filepath']}. Sending anyway;"
                        f" API may reject."
                    )

                processed += 1
                filenames = ', '.join(item['filepath'] for item in chunk)
                print(
                    f"\nBatch {processed} ({len(chunk)} file(s),"
                    f" ~{estimated_tokens} tokens): {filenames}"
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

    def _pack_batches(
        self,
        items: List[Dict],
        max_input_tokens: int,
    ) -> List[List[Dict]]:
        """Greedy-pack files into batches by estimated token count.

        No hard file-count cap: if everything fits under the budget, we
        send one batch. Only split when adding the next file would push
        the estimated batch over the budget.

        The chunk queue in review_pull_request() will still re-split any
        batch that turns out oversized once context is actually built,
        so this estimate can be approximate.
        """
        # ~4 chars per token; reserve room for shared context
        # (README, Dockerfile, architecture, prompt scaffolding).
        chars_per_token = 4
        shared_context_tokens = 20000
        budget_chars = (
            max_input_tokens - shared_context_tokens
        ) * chars_per_token

        batches: List[List[Dict]] = []
        current: List[Dict] = []
        current_chars = 0
        for item in items:
            # Per-file overhead: headers, linter block, filepath, etc.
            item_chars = len(item['diff']) + 2000
            if current and current_chars + item_chars > budget_chars:
                batches.append(current)
                current = [item]
                current_chars = item_chars
            else:
                current.append(item)
                current_chars += item_chars
        if current:
            batches.append(current)
        return batches

    def _run_batched_linters(self, pending_items: List[Dict]) -> None:
        """Run linter once per language across all pending items.

        Mutates each item in-place to attach linter_results.
        """
        linter_tool = self.tool_registry.get_tool("run_linter")
        if not linter_tool:
            return

        by_language: Dict[str, List[Dict]] = {}
        for item in pending_items:
            by_language.setdefault(item['language'], []).append(item)

        for language, items in by_language.items():
            batch_input = [
                {
                    'filepath': i['filepath'],
                    'changed_lines': i['changed_lines'],
                }
                for i in items
            ]
            results = linter_tool.execute_batch(
                files=batch_input,
                language=language,
            )
            if not results:
                continue

            for item in items:
                data = results.get(item['filepath'])
                if not data:
                    continue
                item['linter_results'] = data
                count = data.get('filtered_issues', 0)
                if count > 0:
                    print(f"  → Linter: {count} issues in {item['filepath']}")
                else:
                    print(f"  → Linter: no issues in {item['filepath']}")

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
