"""
Metrics calculation script - Calculate user and ecosystem metrics.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics import UserMetricsCalculator, EcosystemMetricsCalculator
from loguru import logger


def _atomic_write_json(path: str, payload: dict) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, path)


def main():
    """Main metrics calculation pipeline."""
    logger.info("Starting metrics calculation...")
    
    # Load data
    with open("data/raw/users/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)
    
    with open("data/raw/repos/repositories.json", "r", encoding="utf-8") as f:
        repos = json.load(f)
    
    with open("data/processed/classifications.json", "r", encoding="utf-8") as f:
        classifications = json.load(f)
    
    logger.info(f"Loaded {len(users)} users, {len(repos)} repos, {len(classifications)} classifications")
    
    # Group repos by owner
    repos_by_owner = defaultdict(list)
    for repo in repos:
        owner = repo.get("owner", {}).get("login")
        if owner:
            repos_by_owner[owner].append(repo)
    
    # Group classifications by repo
    classifications_by_repo = {c["repo_id"]: c for c in classifications}
    
    # Calculate user metrics
    metrics_calculator = UserMetricsCalculator()
    user_metrics = []
    
    logger.info("Calculating user metrics...")
    for user in users:
        username = user["login"]
        user_repos = repos_by_owner.get(username, [])
        
        # Get classifications for this user's repos
        user_classifications = [
            classifications_by_repo.get(repo["id"])
            for repo in user_repos
            if repo["id"] in classifications_by_repo
        ]
        user_classifications = [c for c in user_classifications if c]
        
        # Calculate metrics
        metrics = metrics_calculator.calculate_all_metrics(
            user=user,
            repos=user_repos,
            classifications=user_classifications
        )
        user_metrics.append(metrics)
    
    # Save user metrics
    user_metrics_df = pd.DataFrame(user_metrics)
    repos_df = pd.DataFrame(repos)
    classifications_df = pd.DataFrame(classifications)
    
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/metrics", exist_ok=True)
    
    user_metrics_df.to_csv("data/metrics/user_metrics.csv", index=False)
    user_metrics_df.to_csv("data/processed/users.csv", index=False)
    repos_df.to_csv("data/processed/repositories.csv", index=False)
    classifications_df.to_csv("data/processed/classifications.csv", index=False)
    
    logger.info("Saved user metrics, repositories, and classifications")
    
    # Calculate ecosystem metrics
    ecosystem_calculator = EcosystemMetricsCalculator()
    ecosystem_metrics = ecosystem_calculator.calculate_ecosystem_metrics(
        users_df=user_metrics_df,
        repos_df=repos_df,
        classifications_df=classifications_df
    )
    
    # Save ecosystem metrics
    _atomic_write_json("data/metrics/ecosystem_metrics.json", ecosystem_metrics)
    _atomic_write_json("data/processed/ecosystem_metrics.json", ecosystem_metrics)
    
    logger.info("Metrics calculation complete!")
    
    print("\n✅ Metrics calculation complete!")
    print(f"📊 User metrics: data/metrics/user_metrics.csv ({len(user_metrics)} users)")
    print(f"📊 Ecosystem metrics: data/metrics/ecosystem_metrics.json")
    print("\nNext step: Launch dashboard")
    print("streamlit run app/main.py")


if __name__ == "__main__":
    main()
