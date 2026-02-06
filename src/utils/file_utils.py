"""File utility functions"""

from pathlib import Path
from typing import Tuple, Optional
import fnmatch


def should_exclude_file(filepath: str, exclusions: dict) -> Tuple[bool, Optional[str]]:
    """Check if file should be excluded from review

    Args:
        filepath: Path to file
        exclusions: Exclusion rules

    Returns:
        Tuple of (should_exclude, reason)
    """
    path = Path(filepath)

    # Check directories
    for excluded_dir in exclusions.get('directories', []):
        if excluded_dir in path.parts:
            return True, f"in excluded directory: {excluded_dir}"

    # Check file prefixes
    filename = path.name
    for prefix in exclusions.get('file_prefixes', []):
        if filename.startswith(prefix):
            return True, f"matches excluded prefix: {prefix}"

    # Check file patterns
    for pattern in exclusions.get('file_patterns', []):
        if matches_pattern(filepath, pattern):
            return True, f"matches excluded pattern: {pattern}"

    return False, None


def matches_pattern(filepath: str, pattern: str) -> bool:
    """Check if filepath matches pattern using glob syntax

    Args:
        filepath: File path
        pattern: Pattern (e.g., *.lock, .ai-review-config*.json)

    Returns:
        True if matches
    """
    # Get just the filename for matching
    filename = Path(filepath).name

    # Use fnmatch for glob pattern matching
    return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filepath, pattern)
