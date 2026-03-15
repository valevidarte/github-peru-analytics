"""Language analytics page."""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Languages", page_icon="💻", layout="wide")


@st.cache_data
def load_data():
    users = pd.read_csv("data/metrics/user_metrics.csv")
    repos = pd.read_csv("data/processed/repositories.csv")
    classifications = pd.read_csv("data/processed/classifications.csv")
    merged = repos.merge(classifications[["repo_id", "industry_name"]], left_on="id", right_on="repo_id", how="left")
    return users, repos, merged


users_df, repos_df, merged_df = load_data()
st.title("Languages")

lang_counts = repos_df["language"].dropna().value_counts().head(20)
st.plotly_chart(
    px.bar(
        x=lang_counts.values,
        y=lang_counts.index,
        orientation="h",
        title="Top 20 languages",
        labels={"x": "Repositories", "y": "Language"},
    ),
    use_container_width=True,
)

st.subheader("Top developers by language")
selected_lang = st.selectbox("Language", sorted(lang_counts.index))
lang_users = users_df[users_df["primary_language_1"] == selected_lang]
st.dataframe(
    lang_users.sort_values("impact_score", ascending=False)[["login", "impact_score", "total_stars_received", "followers"]].head(20),
    use_container_width=True,
)

if "created_at" in repos_df.columns:
    trend_df = repos_df.copy()
    trend_df["created_at"] = pd.to_datetime(trend_df["created_at"], errors="coerce")
    trend_df = trend_df.dropna(subset=["created_at", "language"])
    if not trend_df.empty:
        trend_df["month"] = trend_df["created_at"].dt.to_period("M").dt.to_timestamp()
        top_languages = lang_counts.head(5).index.tolist()
        trend_df = trend_df[trend_df["language"].isin(top_languages)]
        grouped = trend_df.groupby(["month", "language"]).size().reset_index(name="repos")
        st.subheader("Language Trends")
        st.plotly_chart(
            px.line(grouped, x="month", y="repos", color="language", markers=True),
            use_container_width=True,
        )

st.subheader("Language vs industry correlation")
heat_df = (
    merged_df.dropna(subset=["language", "industry_name"])
    .groupby(["industry_name", "language"]).size().reset_index(name="count")
)
heat_df = heat_df[heat_df["language"].isin(lang_counts.index)]
fig = px.density_heatmap(
    heat_df,
    x="language",
    y="industry_name",
    z="count",
    title="Industry by language heatmap",
)
st.plotly_chart(fig, use_container_width=True)
