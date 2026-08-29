"""
GitHub Statistics Collector
Dynamic statistics querying using GitHub REST and GraphQL APIs with pagination,
caching, exponential backoff, rate limit handling, and offline fallback.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

from src.cache_manager import CacheManager

logger = logging.getLogger("github_stats")


@dataclass
class GithubStats:
    repositories: int = 0
    stars: int = 0
    contributions: int = 0
    followers: int = 0
    commits: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    net_lines: int = 0
    last_updated: str = ""
    is_mock: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositories": self.repositories,
            "stars": self.stars,
            "contributions": self.contributions,
            "followers": self.followers,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "net_lines": self.net_lines,
            "last_updated": self.last_updated,
            "is_mock": self.is_mock,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GithubStats:
        return cls(
            repositories=int(data.get("repositories", 0)),
            stars=int(data.get("stars", 0)),
            contributions=int(data.get("contributions", 0)),
            followers=int(data.get("followers", 0)),
            commits=int(data.get("commits", 0)),
            lines_added=int(data.get("lines_added", 0)),
            lines_deleted=int(data.get("lines_deleted", 0)),
            net_lines=int(data.get("net_lines", 0)),
            last_updated=str(data.get("last_updated", "")),
            is_mock=bool(data.get("is_mock", False)),
        )


class GithubStatsCollector:
    API_BASE = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(
        self,
        username: str,
        token: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None,
        session: Optional[requests.Session] = None,
    ):
        self.username = username
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("PAT")
        self.cache_manager = cache_manager or CacheManager()
        self.session = session or requests.Session()
        
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Original-Profile-Generator/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

    def _safe_request(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> Optional[requests.Response]:
        for attempt in range(max_retries):
            try:
                res = self.session.get(url, params=params, timeout=12)
                if res.status_code == 200:
                    return res
                if res.status_code == 202:
                    # GitHub computing stats, wait and retry
                    time.sleep(1.2 * (attempt + 1))
                    continue
                if res.status_code == 403:
                    logger.warning(f"Rate limited or forbidden accessing {url}: {res.text[:120]}")
                    return None
                if res.status_code == 404:
                    return None
                logger.warning(f"Unexpected status {res.status_code} from {url}")
            except Exception as e:
                logger.warning(f"Request exception for {url} (attempt {attempt + 1}): {e}")
                time.sleep(1.0)
        return None

    def fetch_graphql_stats(self) -> Optional[Dict[str, Any]]:
        """Queries GitHub GraphQL API for contributions calendar and user data if token is provided."""
        if not self.token:
            return None

        query = """
        query($username: String!) {
          user(login: $username) {
            repositories(first: 100, ownerAffiliations: [OWNER], isFork: false) {
              totalCount
              nodes {
                name
                stargazerCount
                isPrivate
                pushedAt
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history {
                        totalCount
                      }
                    }
                  }
                }
              }
            }
            followers {
              totalCount
            }
            contributionsCollection {
              contributionCalendar {
                totalContributions
              }
              totalCommitContributions
              totalIssueContributions
              totalPullRequestContributions
              totalPullRequestReviewContributions
              restrictedContributionsCount
            }
          }
        }
        """
        try:
            res = self.session.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": {"username": self.username}},
                timeout=12,
            )
            if res.status_code == 200:
                data = res.json()
                if "data" in data and data["data"].get("user"):
                    return data["data"]["user"]
                if "errors" in data:
                    logger.warning(f"GraphQL errors: {data['errors']}")
            else:
                logger.warning(f"GraphQL request failed with status {res.status_code}")
        except Exception as e:
            logger.warning(f"GraphQL query exception: {e}")
        return None

    def fetch_rest_user(self) -> Optional[Dict[str, Any]]:
        res = self._safe_request(f"{self.API_BASE}/users/{self.username}")
        if res and res.status_code == 200:
            return res.json()
        return None

    def fetch_all_owned_repos(self) -> List[Dict[str, Any]]:
        """Fetches all non-fork owned repositories using pagination."""
        repos = []
        page = 1
        while page <= 10:  # Safety cap at 1000 repositories
            res = self._safe_request(
                f"{self.API_BASE}/users/{self.username}/repos",
                params={"type": "owner", "per_page": 100, "page": page, "sort": "pushed"},
            )
            if not res or res.status_code != 200:
                break
            page_data = res.json()
            if not isinstance(page_data, list) or len(page_data) == 0:
                break
            for r in page_data:
                # Exclude forks to accurately reflect owned original work
                if not r.get("fork", False):
                    repos.append(r)
            if len(page_data) < 100:
                break
            page += 1
        return repos

    def fetch_repo_loc_stats(self, repo_name: str, pushed_at: Optional[str]) -> Dict[str, int]:
        """
        Fetches additions and deletions for a repository using GitHub's code frequency stats.
        Uses local cache if pushed_at has not changed.
        """
        cached = self.cache_manager.get_repo_cache(repo_name, pushed_at)
        if cached:
            return {
                "additions": cached.get("additions", 0),
                "deletions": cached.get("deletions", 0),
                "commits": cached.get("commits", 0),
            }

        # Query code_frequency stats endpoint
        # Response is an array of [timestamp, additions, deletions(negative)]
        url = f"{self.API_BASE}/repos/{self.username}/{repo_name}/stats/code_frequency"
        res = self._safe_request(url, max_retries=3)
        additions = 0
        deletions = 0
        weekly_data = []

        if res and res.status_code == 200:
            stats = res.json()
            if isinstance(stats, list):
                weekly_data = stats
                for week in stats:
                    if isinstance(week, list) and len(week) >= 3:
                        additions += max(0, int(week[1]))
                        deletions += abs(int(week[2]))

        # Commit count estimate from contributor stats or default branch
        commits = 0
        contrib_url = f"{self.API_BASE}/repos/{self.username}/{repo_name}/stats/contributors"
        contrib_res = self._safe_request(contrib_url, max_retries=2)
        if contrib_res and contrib_res.status_code == 200:
            contributors = contrib_res.json()
            if isinstance(contributors, list):
                for c in contributors:
                    if isinstance(c, dict) and c.get("author", {}).get("login", "").lower() == self.username.lower():
                        commits += int(c.get("total", 0))

        # Save to cache
        self.cache_manager.set_repo_cache(
            repo_name=repo_name,
            pushed_at=pushed_at,
            commits=commits,
            additions=additions,
            deletions=deletions,
            weekly_stats=weekly_data,
        )

        return {"additions": additions, "deletions": deletions, "commits": commits}

    def collect(self, force_refresh: bool = False) -> GithubStats:
        """
        Collects comprehensive statistics across GitHub GraphQL and REST endpoints.
        Falls back gracefully to cache or mock if offline or unauthenticated.
        """
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # 1. Attempt GraphQL collection first if token available
        gql_user = self.fetch_graphql_stats()
        
        # 2. Base metrics
        total_repos = 0
        total_stars = 0
        total_followers = 0
        total_contributions = 0
        total_commits = 0
        total_additions = 0
        total_deletions = 0

        repos_to_inspect = []

        if gql_user:
            repos_data = gql_user.get("repositories", {})
            total_repos = repos_data.get("totalCount", 0)
            total_followers = gql_user.get("followers", {}).get("totalCount", 0)
            
            contrib_col = gql_user.get("contributionsCollection", {})
            cal = contrib_col.get("contributionCalendar", {})
            total_contributions = cal.get("totalContributions", 0)
            
            # Sum commits from contribution summary
            commit_contribs = contrib_col.get("totalCommitContributions", 0)
            restricted = contrib_col.get("restrictedContributionsCount", 0)
            total_commits += commit_contribs + restricted

            for node in repos_data.get("nodes", []):
                total_stars += node.get("stargazerCount", 0)
                branch_ref = node.get("defaultBranchRef") or {}
                target = branch_ref.get("target") or {}
                history = target.get("history") or {}
                repo_commits = history.get("totalCount", 0)
                if repo_commits > 0:
                    total_commits = max(total_commits, total_commits + repo_commits)
                
                repos_to_inspect.append({
                    "name": node.get("name"),
                    "pushed_at": node.get("pushedAt"),
                })
        else:
            # REST Fallback
            user_data = self.fetch_rest_user()
            if user_data:
                total_repos = user_data.get("public_repos", 0)
                total_followers = user_data.get("followers", 0)

            all_repos = self.fetch_all_owned_repos()
            if all_repos:
                total_repos = max(total_repos, len(all_repos))
                for r in all_repos:
                    total_stars += r.get("stargazers_count", 0)
                    repos_to_inspect.append({
                        "name": r.get("name"),
                        "pushed_at": r.get("pushed_at"),
                    })

        # 3. Calculate Lines of Code (Additions / Deletions) across repos
        if repos_to_inspect:
            for repo_info in repos_to_inspect:
                r_name = repo_info.get("name")
                r_pushed = repo_info.get("pushed_at")
                if r_name:
                    loc = self.fetch_repo_loc_stats(r_name, r_pushed)
                    total_additions += loc["additions"]
                    total_deletions += loc["deletions"]
                    if loc["commits"] > 0 and not gql_user:
                        total_commits += loc["commits"]
            
            # If total_contributions wasn't populated from GraphQL, approximate from commits
            if total_contributions == 0:
                total_contributions = total_commits

        # Check if we got zero or failed due to missing token / offline
        if total_repos == 0 and total_followers == 0 and total_additions == 0:
            cached_global = self.cache_manager.get_global_stats()
            if cached_global:
                logger.info("Using cached global statistics.")
                cached_stats = GithubStats.from_dict(cached_global)
                cached_stats.last_updated = now_str
                return cached_stats

            # Fallback to realistic mock statistics if nothing is available
            logger.info("Falling back to mock statistics for demonstration/offline build.")
            return self.get_mock_stats(self.username)

        net_loc = total_additions - total_deletions

        stats = GithubStats(
            repositories=total_repos,
            stars=total_stars,
            contributions=total_contributions,
            followers=total_followers,
            commits=total_commits,
            lines_added=total_additions,
            lines_deleted=total_deletions,
            net_lines=net_loc,
            last_updated=now_str,
            is_mock=False,
        )

        # Update cache
        self.cache_manager.set_global_stats(stats.to_dict())
        self.cache_manager.save()

        return stats

    @staticmethod
    def get_mock_stats(username: str) -> GithubStats:
        """Generates realistic mock metrics for testing or offline environment."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return GithubStats(
            repositories=18,
            stars=47,
            contributions=682,
            followers=34,
            commits=1240,
            lines_added=94520,
            lines_deleted=28340,
            net_lines=66180,
            last_updated=now_str,
            is_mock=True,
        )
