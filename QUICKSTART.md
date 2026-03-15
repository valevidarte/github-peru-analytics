# Quickstart - GitHub Peru Analytics

## 1) Install
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Environment
Create `.env` with:
```env
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_CLASSIFICATION_MODEL=gpt-4.1-mini
TARGET_REPOSITORIES=1000
```

## 2.1) GitHub PAT (classic) setup - REQUIRED
1. GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Click `Generate new token (classic)`
3. Configure:
	- Note: `GitHub Peru Analytics - [Your Name]`
	- Expiration: `No expiration`
	- Scopes: `public_repo`, `read:user`
4. Save token in `.env` as `GITHUB_TOKEN`

Security:
- Never commit `.env`
- Never share the token
- This repository already ignores `.env` in `.gitignore`

## 2.2) Rate limit expected
- No token: ~60 req/hour
- With PAT: ~5000 req/hour
- GitHub App: ~15000 req/hour (not required)

Rate-limit handling is implemented with exponential backoff in `src/extraction/github_client.py`.

## 2.3) Required stack
- Python 3.10+
- GitHub REST API v3
- OpenAI GPT-4 API
- SQLite (via SQLAlchemy)
- Streamlit + Plotly

## 3) Required easter egg
```bash
python antigravity_demo.py
```
Save screenshot as `demo/antigravity_screenshot.png`.

## 4) Run pipeline
```bash
python scripts/extract_data.py
python scripts/classify_repos.py
python scripts/calculate_metrics.py
```

Expected outputs:
- `data/raw/users/users.json`
- `data/raw/repos/repositories.json`
- `data/processed/users.csv`
- `data/processed/repositories.csv`
- `data/processed/classifications.csv`
- `data/metrics/user_metrics.csv`
- `data/metrics/ecosystem_metrics.json`

## 5) Run dashboard
```bash
streamlit run app/main.py
```

## 6) Tests
```bash
pytest -q
```
