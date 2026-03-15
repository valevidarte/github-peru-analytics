"""Database models using SQLAlchemy."""

import os

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    name = Column(String)
    location = Column(String)
    bio = Column(Text)
    company = Column(String)
    blog = Column(String)
    email = Column(String)
    followers = Column(Integer)
    following = Column(Integer)
    public_repos = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Repository(Base):
    """Repository model."""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    full_name = Column(String, unique=True, nullable=False)
    owner_login = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String)
    stargazers_count = Column(Integer)
    forks_count = Column(Integer)
    watchers_count = Column(Integer)
    open_issues_count = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pushed_at = Column(DateTime)
    license = Column(String)
    topics = Column(Text)  # Stored as JSON string
    languages = Column(Text)  # Stored as JSON string
    readme = Column(Text)
    has_readme = Column(Boolean)


class Classification(Base):
    """Industry classification model."""
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False, unique=True)
    repo_name = Column(String, nullable=False)
    repo_full_name = Column(String)
    industry_code = Column(String, nullable=False)
    industry_name = Column(String, nullable=False)
    confidence = Column(String)
    reasoning = Column(Text)


def init_db(db_path: str = "data/github_peru.db"):
    """Initialize the database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine
