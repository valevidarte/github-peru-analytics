"""
Repository extraction and detailed data collection.
"""

import base64
from loguru import logger
from tqdm import tqdm
from .github_client import GitHubClient


class RepoExtractor:
    """Extract repository data from GitHub API."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    def get_repo_details(self, owner: str, repo: str) -> dict:
        """Get detailed information for a repository."""
        logger.debug(f"Fetching details for {owner}/{repo}")
        return self.client.make_request(f"repos/{owner}/{repo}")

    def search_repos_by_stars(
        self,
        location_users: list[str],
        min_stars: int = 1,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Search top repositories by stars from a list of users.

        Args:
            location_users: usernames associated with Peru locations
            min_stars: minimum stars to include
            limit: maximum repositories to return

        Returns:
            Sorted list of repositories by stargazers_count desc
        """
        repos = []

        for username in location_users:
            try:
                user_repos = self.client.make_request(
                    f"users/{username}/repos",
                    params={"sort": "stars", "direction": "desc", "per_page": 100},
                )
            except Exception as e:
                logger.warning(f"Could not fetch repos by stars for {username}: {e}")
                continue

            for repo in user_repos:
                if repo.get("stargazers_count", 0) >= min_stars:
                    repos.append(repo)

        repos.sort(key=lambda repo: repo.get("stargazers_count", 0), reverse=True)
        return repos[:limit]
    
    def get_repo_readme(self, owner: str, repo: str) -> str:
        """
        Get the README content of a repository.
        Returns empty string if not found.
        """
        try:
            result = self.client.make_request(f"repos/{owner}/{repo}/readme")
            content = base64.b64decode(result["content"]).decode("utf-8")
            return content[:5000]  # Limit to 5000 chars for API costs
        except Exception as e:
            logger.debug(f"No README found for {owner}/{repo}: {e}")
            return ""
    
    def get_repo_languages(self, owner: str, repo: str) -> dict:
        """Get the language breakdown of a repository."""
        try:
            return self.client.make_request(f"repos/{owner}/{repo}/languages")
        except Exception as e:
            logger.debug(f"Error fetching languages for {owner}/{repo}: {e}")
            return {}
    
    def get_repo_contributors(self, owner: str, repo: str) -> list[dict]:
        """Get the contributors of a repository."""
        try:
            return self.client.make_request(
                f"repos/{owner}/{repo}/contributors",
                params={"per_page": 100}
            )
        except Exception as e:
            logger.debug(f"Error fetching contributors for {owner}/{repo}: {e}")
            return []

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        max_repositories: int = 300,
    ) -> list[dict]:
        """
        Search repositories using GitHub Search API.

        Args:
            query: GitHub search query string
            sort: stars, forks, updated
            order: asc or desc
            max_repositories: maximum repos to return

        Returns:
            List of repository dictionaries
        """
        repos = []
        page = 1
        per_page = 100

        logger.info(
            f"Searching repositories with query='{query}', sort='{sort}', order='{order}'"
        )

        while len(repos) < max_repositories:
            try:
                result = self.client.make_request(
                    "search/repositories",
                    params={
                        "q": query,
                        "sort": sort,
                        "order": order,
                        "per_page": per_page,
                        "page": page,
                    },
                )
            except Exception as e:
                logger.error(f"Repository search failed for query='{query}': {e}")
                break

            items = result.get("items", [])
            if not items:
                break

            repos.extend(items)
            page += 1

            # Search API only supports first 1000 results window.
            if page * per_page >= 1000:
                logger.warning("Reached GitHub repository search window limit (1000)")
                break

        logger.info(f"Found {len(repos)} repositories for query='{query}'")
        return repos[:max_repositories]
    
    def enrich_repositories(self, repos: list[dict], fetch_details: bool = True) -> list[dict]:
        """
        Enrich repository data with README, languages, etc.
        
        Args:
            repos: List of basic repository data
            fetch_details: Whether to call repos/{owner}/{repo} for full details
            
        Returns:
            List of enriched repository data
        """
        enriched = []
        
        for repo in tqdm(repos, desc="Enriching repository data"):
            try:
                owner = repo["owner"]["login"]
                name = repo["name"]

                details = {}
                if fetch_details:
                    # Get detailed repository payload (source of canonical fields).
                    details = self.get_repo_details(owner, name)

                # Get additional data
                readme = self.get_repo_readme(owner, name)
                languages = self.get_repo_languages(owner, name)

                # Add/override with canonical details and enrichment.
                repo_enriched = repo.copy()
                repo_enriched.update(details)
                repo_enriched["readme"] = readme
                repo_enriched["languages"] = languages
                repo_enriched["has_readme"] = bool(readme)
                
                enriched.append(repo_enriched)
                
            except Exception as e:
                logger.error(f"Error enriching {repo.get('full_name')}: {e}")
                enriched.append(repo)  # Add without enrichment
        
        return enriched
