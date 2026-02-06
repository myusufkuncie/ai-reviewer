"""Cache management for review results"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class CacheManager:
    """Manages caching of review results"""

    def __init__(self, cache_dir: str = ".review_cache", ttl_days: int = 7):
        """Initialize cache manager

        Args:
            cache_dir: Directory for cache files
            ttl_days: Time-to-live for cache entries in days
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_days = ttl_days

    def get_cache_key(self, content: str) -> str:
        """Generate cache key from content

        Args:
            content: Content to hash

        Returns:
            MD5 hash of content
        """
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached review result

        Args:
            cache_key: Cache key to lookup

        Returns:
            Cached review data or None if not found/expired
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())

            # Check expiration
            if 'timestamp' in data:
                cached_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cached_time > timedelta(days=self.ttl_days):
                    print(f"⚠ Cache expired for key: {cache_key[:8]}...")
                    cache_file.unlink()  # Delete expired cache
                    return None

            print(f"✓ Cache hit for key: {cache_key[:8]}...")
            return data.get('review')

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠ Invalid cache file: {e}")
            cache_file.unlink()
            return None

    def set(self, cache_key: str, review_data: Dict[str, Any]) -> None:
        """Save review result to cache

        Args:
            cache_key: Cache key
            review_data: Review data to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        data = {
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key,
            'review': review_data
        }

        try:
            cache_file.write_text(json.dumps(data, indent=2))
            print(f"✓ Cached review for key: {cache_key[:8]}...")
        except Exception as e:
            print(f"⚠ Failed to save cache: {e}")

    def clear(self) -> None:
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        print("✓ Cache cleared")

    def clear_expired(self) -> int:
        """Remove expired cache entries

        Returns:
            Number of expired entries removed
        """
        removed = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                if 'timestamp' in data:
                    cached_time = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - cached_time > timedelta(days=self.ttl_days):
                        cache_file.unlink()
                        removed += 1
            except Exception:
                cache_file.unlink()
                removed += 1

        if removed > 0:
            print(f"✓ Removed {removed} expired cache entries")

        return removed
