from src.extraction.user_extractor import UserExtractor
from src.extraction.repo_extractor import RepoExtractor


class DummyClient:
    def __init__(self):
        self.calls = 0

    def make_request(self, endpoint, params=None):
        self.calls += 1
        if endpoint == "search/users":
            if self.calls == 1:
                return {"items": [{"id": 1, "login": "dev1"}, {"id": 2, "login": "dev2"}]}
            return {"items": []}
        if endpoint == "users/dev1/repos":
            return []
        return {}


def test_search_users_by_location_stops_on_empty_items():
    extractor = UserExtractor(DummyClient())
    users = extractor.search_users_by_location("Peru", max_users=10)
    assert len(users) == 2
    assert users[0]["login"] == "dev1"


class RepoDummyClient:
    def make_request(self, endpoint, params=None):
        if endpoint == "users/dev1/repos":
            return [
                {"id": 1, "name": "a", "stargazers_count": 1},
                {"id": 2, "name": "b", "stargazers_count": 10},
            ]
        if endpoint == "users/dev2/repos":
            return [
                {"id": 3, "name": "c", "stargazers_count": 5},
                {"id": 4, "name": "d", "stargazers_count": 0},
            ]
        return []


def test_search_repos_by_stars_sorts_and_filters():
    extractor = RepoExtractor(RepoDummyClient())
    repos = extractor.search_repos_by_stars(["dev1", "dev2"], min_stars=1)

    assert [repo["id"] for repo in repos] == [2, 3, 1]
