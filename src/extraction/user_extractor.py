"""
User extraction from GitHub API.
"""

from loguru import logger
from tqdm import tqdm
from .github_client import GitHubClient


class UserExtractor:
    """Extract user data from GitHub API."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    def search_users_by_location(
        self,
        location: str,
        max_users: int = 1000
    ) -> list[dict]:
        """
        Search for users by location.
        
        Args:
            location: Location string (e.g., "Peru", "Lima")
            max_users: Maximum number of users to retrieve
            
        Returns:
            List of user dictionaries
        """
        users = []
        page = 1
        per_page = 100  # Max allowed by GitHub
        
        logger.info(f"Searching for users in {location}...")
        
        with tqdm(total=max_users, desc=f"Fetching users from {location}") as pbar:
            while len(users) < max_users:
                try:
                    result = self.client.make_request(
                        "search/users",
                        params={
                            "q": f"location:{location}",
                            "per_page": per_page,
                            "page": page,
                            "sort": "followers",
                            "order": "desc"
                        }
                    )
                    
                    if not result.get("items"):
                        logger.info(f"No more users found for {location}")
                        break
                    
                    users.extend(result["items"])
                    pbar.update(len(result["items"]))
                    page += 1
                    
                    # GitHub search API limits to 1000 results
                    if page * per_page >= 1000:
                        logger.warning("Reached GitHub search API limit (1000 results)")
                        break
                        
                except Exception as e:
                    logger.error(f"Error fetching users: {e}")
                    break
        
        logger.info(f"Found {len(users)} users")
        return users[:max_users]
    
    def get_user_details(self, username: str) -> dict:
        """Get detailed information for a specific user."""
        logger.debug(f"Fetching details for user: {username}")
        return self.client.make_request(f"users/{username}")
    
    def get_user_repos(self, username: str) -> list[dict]:
        """Get all repositories for a user."""
        repos = []
        page = 1
        
        logger.debug(f"Fetching repos for user: {username}")
        
        while True:
            try:
                result = self.client.make_request(
                    f"users/{username}/repos",
                    params={
                        "per_page": 100,
                        "page": page,
                        "type": "owner",  # Only owned repos
                        "sort": "updated"
                    }
                )
                
                if not result:
                    break
                
                repos.extend(result)
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching repos for {username}: {e}")
                break
        
        return repos
