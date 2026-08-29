"""
Persistent Cache Manager for GitHub Statistics and LOC History
Prevents unnecessary API requests and rate limit exhaustion by caching repository metrics.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class CacheManager:
    def __init__(self, cache_file_path: str = "cache/stats_cache.json"):
        self.cache_file_path = cache_file_path
        self.data: Dict[str, Any] = {
            "version": 1,
            "last_updated": None,
            "repos": {},
            "global_stats": None,
        }
        self.load()

    def load(self) -> None:
        """Loads cache from disk if available and valid."""
        if not os.path.exists(self.cache_file_path):
            return

        try:
            with open(self.cache_file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "repos" in content:
                    self.data = content
        except Exception:
            # If cache file is corrupted or unreadable, initialize clean cache
            self.data = {
                "version": 1,
                "last_updated": None,
                "repos": {},
                "global_stats": None,
            }

    def get_repo_cache(self, repo_name: str, pushed_at: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Returns cached repo metrics if available.
        If pushed_at timestamp is provided, only returns cache if repo hasn't been modified since cached.
        """
        repos = self.data.get("repos", {})
        repo_data = repos.get(repo_name)
        if not repo_data:
            return None

        # Check if pushed_at timestamp matches
        if pushed_at and repo_data.get("pushed_at") != pushed_at:
            return None

        return repo_data

    def set_repo_cache(
        self,
        repo_name: str,
        pushed_at: Optional[str],
        commits: int,
        additions: int,
        deletions: int,
        weekly_stats: Optional[list] = None,
    ) -> None:
        """Updates cache for a specific repository."""
        if "repos" not in self.data:
            self.data["repos"] = {}

        self.data["repos"][repo_name] = {
            "pushed_at": pushed_at,
            "commits": commits,
            "additions": additions,
            "deletions": deletions,
            "weekly_stats": weekly_stats or [],
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_global_stats(self) -> Optional[Dict[str, Any]]:
        """Returns cached global summary stats."""
        return self.data.get("global_stats")

    def set_global_stats(self, stats: Dict[str, Any]) -> None:
        """Sets cached global summary stats."""
        self.data["global_stats"] = stats

    def save(self) -> None:
        """Persists cache to disk atomically."""
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        cache_dir = os.path.dirname(self.cache_file_path)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        # Write to temporary file in the same directory then atomic replace
        temp_dir = cache_dir if cache_dir else "."
        try:
            with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
                json.dump(self.data, tf, indent=2)
                temp_name = tf.name
            
            # Atomic replace
            os.replace(temp_name, self.cache_file_path)
        except Exception:
            # Fallback simple write
            try:
                with open(self.cache_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2)
            except Exception:
                pass
