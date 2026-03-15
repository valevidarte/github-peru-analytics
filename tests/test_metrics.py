from src.metrics.user_metrics import UserMetricsCalculator


def test_user_metrics_contains_required_fields():
    calc = UserMetricsCalculator()
    user = {
        "id": 1,
        "login": "dev1",
        "name": "Dev One",
        "created_at": "2020-01-01T00:00:00Z",
        "followers": 10,
        "following": 5,
    }
    repos = [
        {
            "id": 11,
            "name": "repo-a",
            "stargazers_count": 5,
            "forks_count": 2,
            "language": "Python",
            "has_readme": True,
            "license": {"key": "mit"},
            "open_issues_count": 1,
            "pushed_at": "2025-12-15T00:00:00Z",
        },
        {
            "id": 12,
            "name": "repo-b",
            "stargazers_count": 1,
            "forks_count": 0,
            "language": "JavaScript",
            "has_readme": False,
            "license": None,
            "open_issues_count": 0,
            "pushed_at": "2025-11-01T00:00:00Z",
        },
    ]
    classifications = [
        {"industry_code": "J"},
        {"industry_code": "P"},
    ]

    metrics = calc.calculate_all_metrics(user, repos, classifications)

    assert metrics["total_repos"] == 2
    assert metrics["h_index"] == 1
    assert "contribution_consistency" in metrics
    assert 0.0 <= metrics["contribution_consistency"] <= 1.0
    assert metrics["industries_served"] == 2
