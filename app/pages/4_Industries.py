"""Industry analytics page."""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Industries", page_icon="🏭", layout="wide")


@st.cache_data
def load_data():
    repos = pd.read_csv("data/processed/repositories.csv")
    classifications = pd.read_csv("data/processed/classifications.csv")
    users = pd.read_csv("data/metrics/user_metrics.csv")
    merged = repos.merge(classifications, left_on="id", right_on="repo_id", how="left")
    return users, merged


users_df, merged_df = load_data()
st.title("Industries")

industry_counts = merged_df["industry_name"].value_counts()
left, right = st.columns(2)

with left:
    st.plotly_chart(
        px.bar(
            x=industry_counts.values,
            y=industry_counts.index,
            orientation="h",
            title="Repository distribution by industry",
        ),
        use_container_width=True,
    )

with right:
    st.plotly_chart(
        px.pie(values=industry_counts.values, names=industry_counts.index, title="Industry share"),
        use_container_width=True,
    )

selected = st.selectbox("Select industry", sorted(industry_counts.index))
subset = merged_df[merged_df["industry_name"] == selected]
st.subheader("Top repositories in selected industry")
st.dataframe(
    subset.sort_values("stargazers_count", ascending=False)[["full_name", "stargazers_count", "forks_count", "language", "confidence"]].head(20),
    use_container_width=True,
)

if "created_at" in merged_df.columns:
    trend_df = merged_df.copy()
    trend_df["created_at"] = pd.to_datetime(trend_df["created_at"], errors="coerce")
    trend_df = trend_df.dropna(subset=["created_at", "industry_name"])
    if not trend_df.empty:
        trend_df["month"] = trend_df["created_at"].dt.to_period("M").dt.to_timestamp()
        top_industries = industry_counts.head(5).index.tolist()
        trend_df = trend_df[trend_df["industry_name"].isin(top_industries)]
        grouped = trend_df.groupby(["month", "industry_name"]).size().reset_index(name="repos")
        st.subheader("Industry Trends")
        st.plotly_chart(
            px.line(grouped, x="month", y="repos", color="industry_name", markers=True),
            use_container_width=True,
        )

if "primary_industry" in users_df.columns:
    spec = users_df["primary_industry"].value_counts().reset_index()
    spec.columns = ["industry_code", "developers"]
    st.subheader("Developer specialization by industry")
    st.plotly_chart(px.bar(spec, x="industry_code", y="developers"), use_container_width=True)
