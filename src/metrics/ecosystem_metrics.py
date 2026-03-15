"""
Ecosystem-level metrics calculation.
"""

from collections import Counter
import pandas as pd
from loguru import logger


class EcosystemMetricsCalculator:
    """Calculate ecosystem-level metrics."""
    
    def calculate_ecosystem_metrics(
        self,
        users_df: pd.DataFrame,
        repos_df: pd.DataFrame,
        classifications_df: pd.DataFrame = None
    ) -> dict:
        """
        Calculate ecosystem-level metrics for Peru's developer community.
        
        Args:
            users_df: DataFrame of user metrics
            repos_df: DataFrame of repositories
            classifications_df: DataFrame of industry classifications
            
        Returns:
            Dictionary of ecosystem metrics
        """
        metrics = {}
        
        # Basic counts
        metrics["total_developers"] = len(users_df)
        metrics["total_repositories"] = len(repos_df)
        metrics["total_stars"] = repos_df["stargazers_count"].sum()
        metrics["total_forks"] = repos_df["forks_count"].sum()
        
        # Averages
        metrics["avg_repos_per_user"] = len(repos_df) / len(users_df) if len(users_df) > 0 else 0
        metrics["avg_stars_per_repo"] = repos_df["stargazers_count"].mean()
        metrics["avg_forks_per_repo"] = repos_df["forks_count"].mean()
        
        # Activity metrics
        if "is_active" in users_df.columns:
            metrics["active_developer_pct"] = (users_df["is_active"].sum() / len(users_df)) * 100
        else:
            metrics["active_developer_pct"] = 0
        
        if "account_age_days" in users_df.columns:
            metrics["avg_account_age_days"] = users_df["account_age_days"].mean()
            metrics["avg_account_age"] = metrics["avg_account_age_days"]
        
        # Language analysis
        if "language" in repos_df.columns:
            languages = repos_df["language"].dropna()
            lang_counts = languages.value_counts()
            metrics["most_popular_languages"] = lang_counts.head(10).to_dict()
            metrics["total_languages"] = len(lang_counts)
        
        # Industry distribution
        if classifications_df is not None and "industry_code" in classifications_df.columns:
            industry_counts = classifications_df["industry_code"].value_counts()
            metrics["industry_distribution"] = industry_counts.to_dict()
            
            if "industry_name" in classifications_df.columns:
                industry_names = classifications_df.groupby("industry_code")["industry_name"].first()
                metrics["industry_names"] = industry_names.to_dict()
        
        # Top contributors
        if "impact_score" in users_df.columns:
            top_contributors = users_df.nlargest(10, "impact_score")[["login", "impact_score"]]
            metrics["top_contributors"] = top_contributors.to_dict("records")
        
        # Top repositories
        if "stargazers_count" in repos_df.columns:
            top_repos = repos_df.nlargest(10, "stargazers_count")[["name", "full_name", "stargazers_count"]]
            metrics["top_repositories"] = top_repos.to_dict("records")
        
        logger.info(f"Calculated ecosystem metrics: {metrics['total_developers']} developers, {metrics['total_repositories']} repos")

        return self._to_native_types(metrics)

    def _to_native_types(self, value):
        """Recursively convert pandas/numpy scalars to JSON-serializable Python types."""
        if isinstance(value, dict):
            return {str(key): self._to_native_types(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._to_native_types(item) for item in value]
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                return value
        return value
