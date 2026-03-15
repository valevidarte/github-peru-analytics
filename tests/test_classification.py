import os
from src.classification.industry_classifier import IndustryClassifier


class DummyResponseMessage:
    content = '{"industry_code": "J", "industry_name": "Information and communication", "confidence": "high", "reasoning": "General software"}'


class DummyChoice:
    message = DummyResponseMessage()


class DummyResponse:
    choices = [DummyChoice()]


class DummyCompletions:
    @staticmethod
    def create(**kwargs):
        return DummyResponse()


class DummyChat:
    completions = DummyCompletions()


class DummyClient:
    chat = DummyChat()


class InvalidDummyResponseMessage:
    content = '{"industry_code": "Z", "industry_name": "Unknown", "confidence": "sure", "reasoning": "n/a"}'


class InvalidDummyChoice:
    message = InvalidDummyResponseMessage()


class InvalidDummyResponse:
    choices = [InvalidDummyChoice()]


class InvalidDummyCompletions:
    @staticmethod
    def create(**kwargs):
        return InvalidDummyResponse()


class InvalidDummyChat:
    completions = InvalidDummyCompletions()


class InvalidDummyClient:
    chat = InvalidDummyChat()


def test_classify_repository_returns_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    classifier = IndustryClassifier()
    classifier.client = DummyClient()

    result = classifier.classify_repository(
        name="my-repo",
        description="sample",
        readme="readme",
        topics=["api"],
        language="Python",
    )

    assert result["industry_code"] == "J"
    assert result["confidence"] == "high"


def test_classify_repository_normalizes_invalid_model_output(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    classifier = IndustryClassifier()
    classifier.client = InvalidDummyClient()

    result = classifier.classify_repository(
        name="unknown-repo",
        description="",
        readme="",
        topics=[],
        language="",
    )

    assert result["industry_code"] == "J"
    assert result["industry_name"] == "Information and communication"
    assert result["confidence"] == "low"


def test_batch_classify_returns_expected_length(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    classifier = IndustryClassifier()
    classifier.client = DummyClient()

    repositories = [
        {"id": 1, "name": "repo-1", "description": "a", "readme": "x", "topics": ["api"], "language": "Python"},
        {"id": 2, "name": "repo-2", "description": "b", "readme": "y", "topics": ["web"], "language": "JavaScript"},
        {"id": 3, "name": "repo-3", "description": "c", "readme": "z", "topics": [], "language": "Go"},
    ]

    results = classifier.batch_classify(repositories, batch_size=2)
    assert len(results) == 3
    assert {result["repo_id"] for result in results} == {1, 2, 3}
