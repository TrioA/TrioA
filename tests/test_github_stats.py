import unittest
from unittest.mock import MagicMock
from src.cache_manager import CacheManager
from src.github_stats import GithubStats, GithubStatsCollector


class TestGithubStats(unittest.TestCase):
    def test_github_stats_serialization(self):
        stats = GithubStats(
            repositories=10,
            stars=25,
            contributions=100,
            followers=5,
            commits=50,
            lines_added=2000,
            lines_deleted=500,
            net_lines=1500,
            last_updated="2026-08-29 12:00 UTC",
            is_mock=False,
        )
        d = stats.to_dict()
        self.assertEqual(d["repositories"], 10)
        self.assertEqual(d["net_lines"], 1500)

        reconstructed = GithubStats.from_dict(d)
        self.assertEqual(reconstructed.repositories, stats.repositories)
        self.assertEqual(reconstructed.stars, stats.stars)
        self.assertEqual(reconstructed.net_lines, stats.net_lines)

    def test_get_mock_stats(self):
        mock_stats = GithubStatsCollector.get_mock_stats("TrioA")
        self.assertGreater(mock_stats.repositories, 0)
        self.assertGreater(mock_stats.stars, 0)
        self.assertGreater(mock_stats.commits, 0)
        self.assertGreater(mock_stats.lines_added, mock_stats.lines_deleted)
        self.assertEqual(mock_stats.net_lines, mock_stats.lines_added - mock_stats.lines_deleted)
        self.assertTrue(mock_stats.is_mock)

    def test_github_collector_with_mocked_rest(self):
        session_mock = MagicMock()
        cache_mock = MagicMock(spec=CacheManager)
        cache_mock.get_repo_cache.return_value = None
        cache_mock.get_global_stats.return_value = None

        user_res = MagicMock()
        user_res.status_code = 200
        user_res.json.return_value = {"public_repos": 2, "followers": 10}

        repos_res = MagicMock()
        repos_res.status_code = 200
        repos_res.json.return_value = [
            {"name": "repo1", "fork": False, "stargazers_count": 5, "pushed_at": "2026-01-01T00:00:00Z"},
            {"name": "repo2", "fork": False, "stargazers_count": 3, "pushed_at": "2026-01-02T00:00:00Z"},
        ]

        code_freq_res = MagicMock()
        code_freq_res.status_code = 200
        code_freq_res.json.return_value = [
            [1700000000, 100, -20],
            [1700086400, 200, -30],
        ]

        contrib_res = MagicMock()
        contrib_res.status_code = 200
        contrib_res.json.return_value = [
            {"author": {"login": "testuser"}, "total": 12}
        ]

        def mock_get(url, **kwargs):
            if "/users/testuser/repos" in url:
                if kwargs.get("params", {}).get("page", 1) == 1:
                    return repos_res
                empty_res = MagicMock()
                empty_res.status_code = 200
                empty_res.json.return_value = []
                return empty_res
            elif "/users/testuser" in url:
                return user_res
            elif "/stats/code_frequency" in url:
                return code_freq_res
            elif "/stats/contributors" in url:
                return contrib_res
            return None

        session_mock.get.side_effect = mock_get

        collector = GithubStatsCollector(
            username="testuser",
            token=None,
            cache_manager=cache_mock,
            session=session_mock,
        )
        stats = collector.collect()

        self.assertEqual(stats.repositories, 2)
        self.assertEqual(stats.followers, 10)
        self.assertEqual(stats.stars, 8)
        self.assertEqual(stats.lines_added, 600)
        self.assertEqual(stats.lines_deleted, 100)
        self.assertEqual(stats.net_lines, 500)
        self.assertEqual(stats.commits, 24)

    def test_github_collector_empty_repos_and_failures(self):
        session_mock = MagicMock()
        cache_mock = MagicMock(spec=CacheManager)
        cache_mock.get_repo_cache.return_value = None
        cache_mock.get_global_stats.return_value = None

        fail_res = MagicMock()
        fail_res.status_code = 404
        session_mock.get.return_value = fail_res

        collector = GithubStatsCollector(
            username="ghost_user",
            token=None,
            cache_manager=cache_mock,
            session=session_mock,
        )
        stats = collector.collect()
        self.assertTrue(stats.is_mock)
        self.assertGreater(stats.repositories, 0)


if __name__ == "__main__":
    unittest.main()
