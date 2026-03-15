# 🇵🇪 GitHub Peru Analytics: Developer Ecosystem Dashboard

An analytics platform to extract, classify, and visualize the developer ecosystem of Peru on GitHub using the REST API, GPT-4, and Streamlit.

## 1. Project Title and Description

**GitHub Peru Analytics** analyzes public GitHub repositories and developers associated with Peru, classifies each repository into one of 21 ISIC (CIIU) industry categories using GPT-4 function-calling, computes user-level and ecosystem-level metrics, and presents all results through an interactive 5-page Streamlit dashboard.

The project includes two autonomous AI agents:
- A **ClassificationAgent** that decides how deeply to inspect each repository before assigning an industry label.
- A **DataCollectionAgent** (Option A) that autonomously discovers Peruvian developers, evaluates profile quality, and collects their repositories.

Antigravity Easter Egg (required evidence):
- Run with `python antigravity_demo.py`
- Screenshot saved in `demo/antigravity_screenshot.png`

![Antigravity Screenshot](demo/antigravity_screenshot.png)

## 2. Key Findings

Top 5 insights about the Peruvian developer ecosystem on GitHub:

1. **1,000 repositories and 24 developers** were analyzed across the full pipeline.
2. **Information and communication** (ISIC J) is the dominant industry with **614 repositories** — reflecting the strong presence of software and web projects.
3. **62.5% of developers** are considered active (at least one push in the last 90 days).
4. The developer with the highest impact score is **devaige** with an `impact_score` of **9,158** (a composite of stars, forks, followers, and h-index).
5. The most frequent industry–language combination is **Information and communication + JavaScript** with **114 repositories**.

**Most popular programming languages:**
| Language | Repositories |
|---|---|
| JavaScript | 158 |
| Python | 88 |
| TypeScript | 87 |
| HTML | 61 |
| Jupyter Notebook | 49 |

**Top industries by repository count:**
| Industry | Repositories |
|---|---|
| Information and communication (J) | 614 |
| Education (P) | 93 |
| Professional, scientific activities (M) | 64 |
| Public administration and defense (O) | 42 |
| Wholesale and retail trade (G) | 41 |

## 3. Data Collection

**Strategy (combined approach):**
- User search by location keywords: `Peru`, `Lima`, `Arequipa`, `Trujillo`, `Cusco`.
- Repository enrichment per user (sorted by stars, capped at 50 repos/user).
- Final deduplication and ranking by star count, keeping top 1,000 repositories.

**Volume collected:**
- Users: 24
- Repositories: 1,000

**Time period:**
- `created_at` range: 2011-10-20 to 2026-03-15

**Rate limiting approach:**
- Implemented in `src/extraction/github_client.py`.
- Retries via `tenacity` with `wait_exponential(min=4, max=60)`.
- Explicit handling of HTTP `403`/`429`, `Retry-After` headers, and `X-RateLimit-Reset` timestamps.

## 4. Features

**Dashboard pages:**
- **Overview**: global ecosystem metrics, top developers, top repositories, industry distribution, language distribution, activity timeline, and geographic map.
- **Developers**: search and filter by name/language/activity, sortable metric table, per-developer detail view, CSV export.
- **Repositories**: filter by stars/industry/language, full-text search by name and description, classification detail panel.
- **Industries**: bar and pie distribution, top repositories per industry, developer specialization by industry.
- **Languages**: language distribution chart, language trends, top developers per language, industry–language heatmap.

**Screenshots:**

**Overview**
![Overview](demo/screenshots/overview.png)

**Developers**
![Developers](demo/screenshots/developers.png)

**Repositories**
![Repositories](demo/screenshots/repositories.png)

**Industries**
![Industries](demo/screenshots/industries.png)

**Languages**
![Languages](demo/screenshots/languages.png)

## 5. Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file at the project root (do **not** commit this file):
   ```env
   GITHUB_TOKEN=ghp_your_token_here
   OPENAI_API_KEY=sk-your-api-key-here
   OPENAI_CLASSIFICATION_MODEL=gpt-4.1-mini
   TARGET_REPOSITORIES=1000
   ```

**GitHub token setup:**
- Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic).
- Click **Generate new token (classic)**.
- Required scopes: `public_repo`, `read:user`.

**OpenAI key setup:**
- Create an API key at [platform.openai.com](https://platform.openai.com).
- Save it in `.env` as `OPENAI_API_KEY`.

## 6. Usage

Run each pipeline step in order:

```bash
# 1. Extract raw data from GitHub
python scripts/extract_data.py

# 2. Classify repositories with the AI agent
python scripts/classify_repos.py

# 3. Calculate user and ecosystem metrics
python scripts/calculate_metrics.py

# 4. Launch the Streamlit dashboard
streamlit run app/main.py
```

## 7. Metrics Documentation

**User-level metrics** (`data/processed/users.csv`):

| Group | Metrics |
|---|---|
| Activity | `total_repos`, `total_stars_received`, `total_forks_received`, `avg_stars_per_repo`, `account_age_days`, `repos_per_year` |
| Influence | `followers`, `following`, `follower_ratio`, `h_index`, `impact_score` |
| Technical | `primary_languages`, `language_diversity`, `industries_served`, `has_readme_pct`, `has_license_pct` |
| Engagement | `total_open_issues`, `days_since_last_push`, `is_active`, `contribution_consistency` |

**Ecosystem-level metrics** (`data/metrics/ecosystem_metrics.json`):
- `total_developers`, `total_repositories`, `total_stars`
- `avg_repos_per_user`, `active_developer_pct`, `avg_account_age`
- `most_popular_languages`, `industry_distribution`

## 8. AI Agent Documentation

Both agents live in `src/agents/classification_agent.py`.

---

### ClassificationAgent

**Purpose:** Autonomously classifies a single repository into one of 21 ISIC (CIIU) industry categories (A through U) using OpenAI function-calling.

**How it works — agentic loop:**
1. The agent receives basic repository metadata (name, description, primary language, topics, stars, forks).
2. It issues a structured prompt to `gpt-4.1-mini` including the 21 industry codes and a step-by-step instruction.
3. The model decides autonomously whether to call a tool for more context or to classify immediately:
   - `get_readme` — fetches and truncates the repository README (up to 2,000 characters) when the description is empty or ambiguous.
   - `get_languages` — fetches the language breakdown in bytes when the domain is unclear from language alone.
   - `classify_industry` — the final tool call that commits to an `industry_code` (A–U), `confidence` level (`high`/`medium`/`low`), and a human-readable `reasoning`.
4. Tool results are appended to the conversation and the loop continues for up to **5 iterations**.
5. Both tool calls and classification decisions are logged with `loguru`.

**Robustness features:**
- `_create_completion` retries up to 3 times with increasing back-off (1.5 s, 3 s) on transient API failures.
- `_parse_tool_arguments` safely decodes JSON arguments and logs a warning if malformed.
- `_to_message_dict` normalizes the SDK response object into a plain dict for multi-turn history.
- `_fallback_result` centralizes the default response (`J – Information and communication`, confidence `low`) used whenever the agent cannot complete classification.
- Invalid industry codes produced by the model are normalized to `J` automatically.

**Example usage:**
```python
from src.extraction import GitHubClient
from src.agents import ClassificationAgent

client = GitHubClient()
agent = ClassificationAgent(github_client=client)

result = agent.run({
    "name": "fintech-api",
    "full_name": "owner/fintech-api",
    "description": "REST API for payment processing in Peru",
    "language": "Python",
    "topics": ["payments", "fintech"],
    "stargazers_count": 42,
    "forks_count": 7,
})

print(result)
# → {"industry_code": "K", "industry_name": "Financial and insurance activities",
#    "confidence": "high", "reasoning": "The repository is a payment processing API..."}
```

---

### DataCollectionAgent — Option A

**Purpose:** An autonomous agent that discovers Peruvian developers on GitHub, evaluates each profile, and decides whether to collect their repositories — without any hard-coded user list.

**Design philosophy (Option A):**
The agent embodies the *Option A* autonomous collection strategy required by the assignment: instead of passively iterating a predetermined list, it **actively reasons about each user profile** to decide whether investing API quota in that user is worthwhile. This makes the collection adaptive — the agent concentrates effort on high-signal developers and skips low-value accounts, optimizing the quality-to-quota ratio.

**How it works — step by step:**

1. **Seeding phase.** The agent queries the GitHub Search API for users in five Peruvian locations: `Peru`, `Lima`, `Arequipa`, `Cusco`, and `Trujillo`. Up to 250 users per location are retrieved and deduplicated by numeric user ID, producing a unique seed list.

2. **Profile evaluation — `_should_dig_deeper`.** For every seed user, the agent fetches full profile details and applies a three-rule decision policy:
   - **Location rule**: if the profile location field explicitly contains `"peru"` (case-insensitive), the user is always processed — high confidence of relevance.
   - **Followers rule**: if `followers >= min_followers_to_dig` (default 5), the user has community recognition and is likely active.
   - **Repository count rule**: if `public_repos >= min_public_repos_to_dig` (default 3), the user has meaningful contributions.
   - If none of the three rules fire, the agent skips the user entirely and logs the reason (`"low followers and low public repo count"`).
   - Every decision (dig / skip + reason) is logged with `loguru` at INFO level, providing a full audit trail.

3. **Repository collection.** For approved users, the agent fetches all public repositories, sorts them by star count (descending), and retains the top `max_repos_per_user` (default 50). These are then passed to `RepoExtractor.enrich_repositories` to add language, topic, README, and license data.

4. **Deduplication and ranking.** Repositories collected from multiple users may overlap; an `OrderedDict` keyed by repository ID deduplicates them, always keeping the copy with the higher star count. The final list is sorted by stars and trimmed to `target_repositories` (default 1,000).

5. **User alignment.** Only users whose repositories survived the final cut are included in the returned user list, ensuring strict consistency between the users and repositories datasets.

6. **Summary report.** The agent returns a dictionary with three keys:
   - `"users"` — list of enriched user profiles.
   - `"repositories"` — list of enriched, deduplicated repositories.
   - `"summary"` — dictionary with `seed_users`, `collected_users`, and `collected_repositories` counts.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `target_repositories` | `1000` | Maximum repositories to return |
| `locations` | `["Peru", "Lima", "Arequipa", "Cusco", "Trujillo"]` | Search locations |
| `max_users_per_location` | `250` | Users fetched per location query |
| `max_repos_per_user` | `50` | Repositories collected per approved user |
| `min_followers_to_dig` | `5` | Minimum followers to qualify a user |
| `min_public_repos_to_dig` | `3` | Minimum public repos to qualify a user |

**Example usage:**
```python
from src.agents import DataCollectionAgent

collector = DataCollectionAgent()

result = collector.run(
    target_repositories=1000,
    locations=["Peru", "Lima", "Arequipa"],
    min_followers_to_dig=10,
)

print(result["summary"])
# → {"seed_users": 87, "collected_users": 24, "collected_repositories": 1000}

# Access the data directly
users = result["users"]         # list of user profile dicts
repos = result["repositories"]  # list of enriched repository dicts
```

**Logged decision trail (sample output):**
```
INFO  [Agent] Starting autonomous data collection
INFO  [Agent] Strategy: locations=['Peru', 'Lima', ...], target_repositories=1000
INFO  [Agent] Found 45 seed users for 'Lima'
INFO  [Agent] Decision for 'devaige': dig_deeper=True (followers >= 5)
INFO  [Agent] Digging deeper for 'devaige': enriching 50 repositories
INFO  [Agent] Decision for 'anon123': dig_deeper=False (low followers and low public repo count)
INFO  [Agent] Collection finished: users=24, repos=1000
```

## 9. Limitations

1. **Geolocation bias:** Many GitHub users do not set a location in their profile, which means the collection likely under-represents Peruvian developers who omit this field.
2. **Classification ambiguity:** Generic or multipurpose repositories (e.g., personal portfolios, dotfiles) may be assigned to industry `J` with low confidence due to insufficient context.
3. **Public data only:** Only public repositories and public profile information are accessible via the GitHub REST API; private or organization-internal activity is excluded.
4. **API cost:** Classification of 1,000 repositories with GPT-4.1-mini involves roughly 1,000 API calls; actual token usage and cost depend on how many `get_readme` / `get_languages` tool calls the agent triggers per repository.
5. **Rate limits:** Sustained extraction at scale may hit GitHub's secondary rate limits; the exponential back-off in `GitHubClient` mitigates but does not eliminate this risk.

## 10. Author Information

- **Name:** Valeria Vidarte Echeverri
- **Course:** Prompt Engineering Training Course using GPT-4
- **Date:** March 15, 2026
