"""Database CRUD operations."""

import json
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import sessionmaker

from .models import Classification, Repository, User


class DataStore:
    """Handle data storage and retrieval operations."""
    
    def __init__(self, engine):
        self.engine = engine
        Session = sessionmaker(bind=engine)
        self.session = Session()
    
    def save_users(self, users: list[dict]):
        """Save users to database."""
        for user_data in users:
            user = User(**self._normalize_user(user_data))
            self.session.merge(user)
        self.session.commit()
    
    def save_repositories(self, repos: list[dict]):
        """Save repositories to database."""
        for repo_data in repos:
            repo = Repository(**self._normalize_repository(repo_data))
            self.session.merge(repo)
        self.session.commit()
    
    def save_classifications(self, classifications: list[dict]):
        """Save classifications to database."""
        for class_data in classifications:
            normalized = self._normalize_classification(class_data)
            existing = (
                self.session.query(Classification)
                .filter_by(repo_id=normalized["repo_id"])
                .one_or_none()
            )
            if existing:
                for key, value in normalized.items():
                    setattr(existing, key, value)
            else:
                self.session.add(Classification(**normalized))
        self.session.commit()
    
    def get_users_df(self) -> pd.DataFrame:
        """Get all users as DataFrame."""
        return pd.read_sql_table("users", self.engine)
    
    def get_repositories_df(self) -> pd.DataFrame:
        """Get all repositories as DataFrame."""
        return pd.read_sql_table("repositories", self.engine)
    
    def get_classifications_df(self) -> pd.DataFrame:
        """Get all classifications as DataFrame."""
        return pd.read_sql_table("classifications", self.engine)
    
    def close(self):
        """Close the session."""
        self.session.close()

    def _normalize_user(self, user_data: dict) -> dict:
        allowed_fields = {
            "id",
            "login",
            "name",
            "location",
            "bio",
            "company",
            "blog",
            "email",
            "followers",
            "following",
            "public_repos",
            "created_at",
            "updated_at",
        }
        normalized = {key: user_data.get(key) for key in allowed_fields}
        normalized["created_at"] = self._parse_datetime(normalized.get("created_at"))
        normalized["updated_at"] = self._parse_datetime(normalized.get("updated_at"))
        return normalized

    def _normalize_repository(self, repo_data: dict) -> dict:
        license_data = repo_data.get("license")
        if isinstance(license_data, dict):
            license_value = license_data.get("spdx_id") or license_data.get("key") or license_data.get("name")
        else:
            license_value = license_data

        topics = repo_data.get("topics") or []
        languages = repo_data.get("languages") or {}

        allowed = {
            "id": repo_data.get("id"),
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "owner_login": (repo_data.get("owner") or {}).get("login"),
            "description": repo_data.get("description"),
            "language": repo_data.get("language"),
            "stargazers_count": repo_data.get("stargazers_count", 0),
            "forks_count": repo_data.get("forks_count", 0),
            "watchers_count": repo_data.get("watchers_count", 0),
            "open_issues_count": repo_data.get("open_issues_count", 0),
            "created_at": self._parse_datetime(repo_data.get("created_at")),
            "updated_at": self._parse_datetime(repo_data.get("updated_at")),
            "pushed_at": self._parse_datetime(repo_data.get("pushed_at")),
            "license": license_value,
            "topics": json.dumps(topics, ensure_ascii=False),
            "languages": json.dumps(languages, ensure_ascii=False),
            "readme": repo_data.get("readme"),
            "has_readme": repo_data.get("has_readme", False),
        }
        return allowed

    def _normalize_classification(self, class_data: dict) -> dict:
        allowed_fields = {
            "repo_id",
            "repo_name",
            "repo_full_name",
            "industry_code",
            "industry_name",
            "confidence",
            "reasoning",
        }
        return {key: class_data.get(key) for key in allowed_fields}

    def _parse_datetime(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        return value
