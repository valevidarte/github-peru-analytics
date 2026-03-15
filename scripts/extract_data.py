"""
Data extraction script - Extract data from GitHub API.
"""

import os
import sys
import json
from pathlib import Path
from collections import OrderedDict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import init_db
from src.database.crud import DataStore
from src.extraction import GitHubClient, RepoExtractor, UserExtractor
from loguru import logger
from tqdm import tqdm


TARGET_REPOSITORIES = int(os.getenv("TARGET_REPOSITORIES", "1000"))
MAX_USERS_PER_LOCATION = int(os.getenv("MAX_USERS_PER_LOCATION", "250"))
MAX_REPOS_PER_USER = int(os.getenv("MAX_REPOS_PER_USER", "50"))
MAX_REPOS_PER_TOPIC_QUERY = int(os.getenv("MAX_REPOS_PER_TOPIC_QUERY", "350"))


def main():
    """Main extraction pipeline."""
    logger.info("Starting GitHub data extraction for Peru...")

    engine = init_db()
    store = DataStore(engine)
    
    # Initialize API client
    client = GitHubClient()
    user_extractor = UserExtractor(client)
    repo_extractor = RepoExtractor(client)
    
    # Check rate limit
    rate_limit = client.check_rate_limit()
    logger.info(f"Rate limit: {rate_limit['remaining']}/{rate_limit['limit']}")
    
    # Strategy 1: Search users by Peru-related locations
    locations = ["Peru", "Lima", "Arequipa", "Cusco", "Trujillo"]
    all_users = []
    all_repos: list[dict] = []
    
    # Extract users from each location
    for location in locations:
        logger.info(f"Searching users in {location}...")
        users = user_extractor.search_users_by_location(
            location,
            max_users=MAX_USERS_PER_LOCATION,
        )
        all_users.extend(users)
    
    # Remove duplicates
    unique_users = {user["id"]: user for user in all_users}
    all_users = list(unique_users.values())
    logger.info(f"Found {len(all_users)} unique users")
    
    # Strategy 3: Search users, then get their repositories
    logger.info("Fetching user details and repositories...")
    users_detailed: list[dict] = []
    for user in tqdm(all_users, desc="Processing users"):
        if len(all_repos) >= TARGET_REPOSITORIES:
            logger.info(f"Reached target repositories: {TARGET_REPOSITORIES}")
            break

        try:
            # Get user details
            user_details = user_extractor.get_user_details(user["login"])
            users_detailed.append(user_details)
            
            # Get user's repositories
            repos = user_extractor.get_user_repos(user["login"])
            
            if repos:
                all_repos.extend(repos[:MAX_REPOS_PER_USER])
            
        except Exception as e:
            logger.error(f"Error processing user {user['login']}: {e}")
            continue
    
    # Strategy 2: Search repositories by Peru-related topics
    topic_queries = ["topic:peru", "topic:lima", "topic:peruvian"]
    query_modes = [("stars", "desc"), ("updated", "desc")]

    for topic_query in topic_queries:
        for sort, order in query_modes:
            logger.info(
                f"Searching repositories by topic strategy: query={topic_query}, sort={sort}"
            )
            topic_repos = repo_extractor.search_repositories(
                query=topic_query,
                sort=sort,
                order=order,
                max_repositories=MAX_REPOS_PER_TOPIC_QUERY,
            )

            if topic_repos:
                all_repos.extend(topic_repos)

    # Deduplicate repositories and keep highest-star copy if duplicates appear.
    deduped: "OrderedDict[int, dict]" = OrderedDict()
    for repo in all_repos:
        repo_id = repo.get("id")
        if repo_id is None:
            continue
        existing = deduped.get(repo_id)
        if not existing or repo.get("stargazers_count", 0) >= existing.get("stargazers_count", 0):
            deduped[repo_id] = repo

    all_repos = list(deduped.values())

    # Keep repository quality: exclude forks when selecting final top set.
    all_repos = [repo for repo in all_repos if not repo.get("fork", False)]

    # Required strategy outcome: top repositories by star count.
    all_repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    all_repos = all_repos[:TARGET_REPOSITORIES]

    logger.info("Enriching final repository set ({}) with README and languages...", len(all_repos))
    all_repos = repo_extractor.enrich_repositories(all_repos, fetch_details=False)

    # Keep only owners that appear in final repository set for a coherent dataset.
    final_owners = {repo.get("owner", {}).get("login") for repo in all_repos}
    final_owners.discard(None)
    users_detailed = [u for u in users_detailed if u.get("login") in final_owners]

    logger.info(
        "Collected {} users and {} repositories (combined strategy: location + topics + user repos)",
        len(users_detailed),
        len(all_repos),
    )
    
    try:
        # Save raw data
        os.makedirs("data/raw/users", exist_ok=True)
        os.makedirs("data/raw/repos", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)

        with open("data/raw/users/users.json", "w", encoding="utf-8") as f:
            json.dump(users_detailed, f, indent=2, ensure_ascii=False)

        with open("data/raw/repos/repositories.json", "w", encoding="utf-8") as f:
            json.dump(all_repos, f, indent=2, ensure_ascii=False)

        # Convenience processed snapshot for dashboard/scripts.
        with open("data/processed/repositories.json", "w", encoding="utf-8") as f:
            json.dump(all_repos, f, indent=2, ensure_ascii=False)

        store.save_users(users_detailed)
        store.save_repositories(all_repos)
        logger.info("Persisted extracted users and repositories to SQLite")
    finally:
        store.close()
    
    logger.info("Data extraction complete!")
    logger.info(f"Users: data/raw/users/users.json ({len(users_detailed)} users)")
    logger.info(f"Repos: data/raw/repos/repositories.json ({len(all_repos)} repos)")
    
    print("\n✅ Data extraction successful!")
    print(f"📊 Collected {len(users_detailed)} users and {len(all_repos)} repositories")
    print("\nNext step: Run classification")
    print("python scripts/classify_repos.py")


if __name__ == "__main__":
    main()
