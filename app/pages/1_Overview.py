"""Overview dashboard page."""

import json
import pandas as pd
import streamlit as st
from app.components import (
    plot_geographic_distribution,
    plot_industry_distribution,
    plot_language_distribution,
    plot_top_developers,
)

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    users_df = pd.read_csv("data/metrics/user_metrics.csv")
    repos_df = pd.read_csv("data/processed/repositories.csv")
    classifications_df = pd.read_csv("data/processed/classifications.csv")
    with open("data/metrics/ecosystem_metrics.json", "r", encoding="utf-8") as f:
        ecosystem_metrics = json.load(f)
    return users_df, repos_df, classifications_df, ecosystem_metrics


users_df, repos_df, classifications_df, eco = load_data()

st.title("Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Developers", f"{eco.get('total_developers', 0):,}")
col2.metric("Total Repositories", f"{eco.get('total_repositories', 0):,}")
col3.metric("Total Stars", f"{eco.get('total_stars', 0):,}")
col4.metric("Active Developers", f"{eco.get('active_developer_pct', 0):.1f}%")

left, right = st.columns(2)
with left:
    st.plotly_chart(plot_top_developers(users_df), use_container_width=True)
with right:
    st.plotly_chart(plot_industry_distribution(classifications_df), use_container_width=True)

st.plotly_chart(plot_language_distribution(repos_df), use_container_width=True)

if "created_at" in repos_df.columns:
    repos_trend = repos_df.copy()
    repos_trend["created_at"] = pd.to_datetime(repos_trend["created_at"], errors="coerce")
    repos_trend = repos_trend.dropna(subset=["created_at"])
    if not repos_trend.empty:
        trend_df = (
            repos_trend.assign(month=repos_trend["created_at"].dt.to_period("M").dt.to_timestamp())
            .groupby("month")
            .size()
            .reset_index(name="repositories")
        )
        st.subheader("Activity Timeline")
        st.line_chart(trend_df.set_index("month")["repositories"])

st.subheader("Top 10 Repositories by Stars")
top_repos = repos_df.nlargest(10, "stargazers_count")[["full_name", "stargazers_count", "forks_count", "language"]]
st.dataframe(top_repos, use_container_width=True, hide_index=True)

geo_fig = plot_geographic_distribution(users_df)
if geo_fig is not None:
    st.plotly_chart(geo_fig, use_container_width=True)
