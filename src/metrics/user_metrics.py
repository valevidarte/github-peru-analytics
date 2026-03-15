"""
User-level metrics calculation.
"""

from datetime import datetime
from collections import Counter
from loguru import logger


class UserMetricsCalculator:
    """Calculate user-level metrics for developers."""
    
    def __init__(self):
        self.today = datetime.now()
    
    def calculate_all_metrics(
        self,
        user: dict,
        repos: list[dict],
        classifications: list[dict] = None
    ) -> dict:
        """
        Calculate all user-level metrics.
        
        Args:
            user: User data from GitHub API
            repos: List of user's repositories
            classifications: Industry classifications for repos
            
        Returns:
            Dictionary with all calculated metrics
        """
        metrics = {}
        
        # Basic info
        metrics["user_id"] = user["id"]
        metrics["login"] = user["login"]
        metrics["name"] = user.get("name", "")
        metrics["location"] = user.get("location", "")
        
        # Activity Metrics
        metrics["total_repos"] = len(repos)
        metrics["total_stars_received"] = sum(r.get("stargazers_count", 0) for r in repos)
        metrics["total_forks_received"] = sum(r.get("forks_count", 0) for r in repos)
        metrics["avg_stars_per_repo"] = (
            metrics["total_stars_received"] / metrics["total_repos"]
            if metrics["total_repos"] > 0 else 0
        )
        
        # Account age
        created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
        metrics["account_age_days"] = (self.today - created_at.replace(tzinfo=None)).days
        metrics["repos_per_year"] = (
            metrics["total_repos"] / (metrics["account_age_days"] / 365)
            if metrics["account_age_days"] > 0 else 0
        )
        
        # Influence Metrics
        metrics["followers"] = user.get("followers", 0)
        metrics["following"] = user.get("following", 0)
        metrics["follower_ratio"] = (
            metrics["followers"] / metrics["following"]
            if metrics["following"] > 0 else metrics["followers"]
        )
        metrics["h_index"] = self._calculate_h_index(repos)
        metrics["impact_score"] = (
            metrics["total_stars_received"] +
            (metrics["total_forks_received"] * 2) +
            metrics["followers"]
        )
        
        # Technical Metrics
        languages = [r.get("language") for r in repos if r.get("language")]
        if languages:
            lang_counts = Counter(languages)
            top_langs = lang_counts.most_common(3)
            metrics["primary_languages"] = [lang for lang, _ in top_langs]
            metrics["primary_language_1"] = top_langs[0][0] if len(top_langs) > 0 else None
            metrics["primary_language_2"] = top_langs[1][0] if len(top_langs) > 1 else None
            metrics["primary_language_3"] = top_langs[2][0] if len(top_langs) > 2 else None
            metrics["language_diversity"] = len(set(languages))
        else:
            metrics["primary_languages"] = []
            metrics["primary_language_1"] = None
            metrics["primary_language_2"] = None
            metrics["primary_language_3"] = None
            metrics["language_diversity"] = 0
        
        # Industry metrics (if classifications provided)
        if classifications:
            industry_codes = [c.get("industry_code") for c in classifications]
            metrics["industries_served"] = len(set(industry_codes))
            metrics["primary_industry"] = (
                Counter(industry_codes).most_common(1)[0][0]
                if industry_codes else None
            )
        else:
            metrics["industries_served"] = 0
            metrics["primary_industry"] = None
        
        # Documentation quality
        repos_with_readme = sum(1 for r in repos if r.get("has_readme", False))
        repos_with_license = sum(1 for r in repos if r.get("license"))
        metrics["has_readme_pct"] = repos_with_readme / len(repos) if repos else 0
        metrics["has_license_pct"] = repos_with_license / len(repos) if repos else 0
        
        # Engagement Metrics
        metrics["total_open_issues"] = sum(r.get("open_issues_count", 0) for r in repos)
        
        if repos:
            pushed_dates = [
                datetime.fromisoformat(r.get("pushed_at", r.get("updated_at", user["created_at"])).replace("Z", "+00:00"))
                for r in repos
            ]
            last_push = max(pushed_dates)
            metrics["days_since_last_push"] = (self.today - last_push.replace(tzinfo=None)).days
            metrics["is_active"] = metrics["days_since_last_push"] < 90
            metrics["contribution_consistency"] = self._calculate_contribution_consistency(pushed_dates)
        else:
            metrics["days_since_last_push"] = None
            metrics["is_active"] = False
            metrics["contribution_consistency"] = 0.0
        
        return metrics
    
    def _calculate_h_index(self, repos: list[dict]) -> int:
        """
        Calculate h-index based on repository stars.
        h-index = h if h repos have at least h stars each.
        """
        stars = sorted([r.get("stargazers_count", 0) for r in repos], reverse=True)
        h = 0
        for i, s in enumerate(stars):
            if s >= i + 1:
                h = i + 1
            else:
                break
        return h

    def _calculate_contribution_consistency(self, pushed_dates: list[datetime]) -> float:
        """
        Score consistency from 0-1 based on activity spread across recent months.
        """
        if not pushed_dates:
            return 0.0

        monthly_buckets = Counter((d.year, d.month) for d in pushed_dates)
        active_months = len(monthly_buckets)

        # Normalize by the last 12 months to make users comparable.
        return min(active_months / 12.0, 1.0)
