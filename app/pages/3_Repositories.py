"""Repository browser page."""

import sys
import os
import pandas as pd
import streamlit as st

# Ensure repo root is on the path (needed on Streamlit Cloud)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.components import plot_stars_vs_forks

st.set_page_config(page_title="Repositories", page_icon="📦", layout="wide")


@st.cache_data
def load_data():
    repos = pd.read_csv("data/processed/repositories.csv")
    classifications = pd.read_csv("data/processed/classifications.csv")
    merged = repos.merge(
        classifications[["repo_id", "industry_code", "industry_name", "confidence"]],
        left_on="id",
        right_on="repo_id",
        how="left",
    )
    return merged


repos_df = load_data()
st.title("Repositories")

min_stars = st.sidebar.slider(
    "Minimum stars",
    min_value=0,
    max_value=int(repos_df["stargazers_count"].max() if not repos_df.empty else 0),
    value=0,
)
query = st.sidebar.text_input("Search")
languages = sorted(repos_df["language"].dropna().unique())
industries = sorted(repos_df["industry_name"].dropna().unique())
selected_languages = st.sidebar.multiselect("Language", languages)
selected_industries = st.sidebar.multiselect("Industry", industries)

filtered = repos_df[repos_df["stargazers_count"] >= min_stars]
if selected_languages:
    filtered = filtered[filtered["language"].isin(selected_languages)]
if selected_industries:
    filtered = filtered[filtered["industry_name"].isin(selected_industries)]
if query:
    mask = filtered["name"].str.contains(query, case=False, na=False) | filtered["description"].str.contains(query, case=False, na=False)
    filtered = filtered[mask]

st.write(f"Showing {len(filtered)} repositories")

st.plotly_chart(plot_stars_vs_forks(filtered), use_container_width=True)

show_cols = [
    "full_name",
    "description",
    "language",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "industry_name",
    "confidence",
]
st.dataframe(filtered.sort_values("stargazers_count", ascending=False)[show_cols], use_container_width=True, height=500)
