import os
import tempfile
import unittest
from src.cache_manager import CacheManager


class TestCacheManager(unittest.TestCase):
    def test_cache_manager_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "test_cache.json")
            cm = CacheManager(cache_file)
            
            # Test empty state
            self.assertIsNone(cm.get_repo_cache("my-repo"))
            self.assertIsNone(cm.get_global_stats())

            # Set repo cache
            cm.set_repo_cache(
                repo_name="my-repo",
                pushed_at="2026-01-01T00:00:00Z",
                commits=15,
                additions=500,
                deletions=100,
                weekly_stats=[[1700000000, 500, -100]],
            )
            cm.set_global_stats({"total_repos": 1, "stars": 5})
            cm.save()

            # Load in new instance
            cm2 = CacheManager(cache_file)
            cached_repo = cm2.get_repo_cache("my-repo", pushed_at="2026-01-01T00:00:00Z")
            self.assertIsNotNone(cached_repo)
            self.assertEqual(cached_repo["commits"], 15)
            self.assertEqual(cached_repo["additions"], 500)
            self.assertEqual(cached_repo["deletions"], 100)

            # Invalidation test when pushed_at changes
            invalidated = cm2.get_repo_cache("my-repo", pushed_at="2026-02-01T00:00:00Z")
            self.assertIsNone(invalidated)

            # Global stats test
            gstats = cm2.get_global_stats()
            self.assertEqual(gstats, {"total_repos": 1, "stars": 5})

    def test_cache_manager_corrupted_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "corrupt.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json")

            cm = CacheManager(cache_file)
            self.assertEqual(cm.data["repos"], {})
            self.assertIsNone(cm.get_global_stats())


if __name__ == "__main__":
    unittest.main()
