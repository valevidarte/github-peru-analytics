"""
GitHub API client with rate limiting and error handling.
"""

import os
import time
import requests
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from loguru import logger

load_dotenv()


class GitHubClient:
    """GitHub API client with authentication and rate limiting."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        logger.info("GitHubClient initialized")
    
    def check_rate_limit(self) -> dict:
        """Check current rate limit status."""
        response = requests.get(
            f"{self.base_url}/rate_limit",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        
        core = data["resources"]["core"]
        logger.info(f"Rate limit: {core['remaining']}/{core['limit']} remaining")
        
        return core

    def _handle_rate_limit_wait(self, response: requests.Response) -> None:
        """Sleep until GitHub rate limit reset or retry-after expires."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            wait_seconds = max(int(retry_after), 1)
        else:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            wait_seconds = max(int(reset_time - time.time()), 1)

        logger.warning(f"Rate limit hit. Waiting {wait_seconds}s before retry...")
        time.sleep(wait_seconds)

    @retry(
        retry=retry_if_exception(lambda exc: GitHubClient._is_retriable_exception(exc)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Make a rate-limit-aware request to GitHub API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params, timeout=30)

        # Handle hard rate limiting first so tenacity can retry cleanly.
        if response.status_code in (403, 429):
            remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
            if remaining == 0 or response.status_code == 429:
                self._handle_rate_limit_wait(response)
                response.raise_for_status()

        # Retry transient server-side errors.
        if response.status_code >= 500:
            logger.warning(f"GitHub transient error {response.status_code} on {endpoint}")
            response.raise_for_status()
        
        # Check rate limit
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        
        if remaining < 10:
            wait_seconds = max(reset_time - time.time(), 0) + 1
            logger.warning(
                f"Rate limit low ({remaining} remaining). "
                f"Waiting {wait_seconds:.0f} seconds..."
            )
            time.sleep(wait_seconds)
        
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _is_retriable_exception(exception: Exception) -> bool:
        if isinstance(exception, requests.HTTPError):
            response = exception.response
            if response is None:
                return True
            return response.status_code in (403, 429) or response.status_code >= 500
        return isinstance(exception, requests.RequestException)
