"""Developers explorer page."""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Developers", page_icon="👥", layout="wide")


@st.cache_data
def load_data():
    return pd.read_csv("data/metrics/user_metrics.csv")


users_df = load_data()
st.title("Developers")

search_query = st.sidebar.text_input("Search login/name")
min_stars = st.sidebar.slider(
    "Minimum total stars",
    min_value=0,
    max_value=int(users_df["total_stars_received"].max() if not users_df.empty else 0),
    value=0,
)
active_only = st.sidebar.checkbox("Active only")
languages = sorted(users_df["primary_language_1"].dropna().unique())
selected_languages = st.sidebar.multiselect("Primary language", languages)

sort_candidates = [
    column
    for column in users_df.columns
    if pd.api.types.is_numeric_dtype(users_df[column])
]
default_sort = "impact_score" if "impact_score" in sort_candidates else sort_candidates[0]
sort_by = st.sidebar.selectbox("Sort by metric", options=sort_candidates, index=sort_candidates.index(default_sort))
sort_desc = st.sidebar.checkbox("Sort descending", value=True)

filtered = users_df[users_df["total_stars_received"] >= min_stars]
if active_only:
    filtered = filtered[filtered["is_active"] == True]
if selected_languages:
    filtered = filtered[filtered["primary_language_1"].isin(selected_languages)]
if search_query:
    mask = filtered["login"].str.contains(search_query, case=False, na=False) | filtered["name"].fillna("").str.contains(search_query, case=False, na=False)
    filtered = filtered[mask]

filtered = filtered.sort_values(sort_by, ascending=not sort_desc)

st.write(f"Showing {len(filtered)} developers")

fig = px.bar(
    filtered.nlargest(15, "impact_score").sort_values("impact_score"),
    x="impact_score",
    y="login",
    orientation="h",
    title="Top 15 Developers by Impact",
)
st.plotly_chart(fig, use_container_width=True)

show_cols = [
    "login",
    "name",
    "total_repos",
    "total_stars_received",
    "followers",
    "impact_score",
    "h_index",
    "primary_language_1",
    "industries_served",
    "contribution_consistency",
    "is_active",
]
show_cols = [c for c in show_cols if c in filtered.columns]
st.dataframe(filtered.sort_values("impact_score", ascending=False)[show_cols], use_container_width=True)

st.subheader("Developer Detail")
if filtered.empty:
    st.info("No developers available with current filters.")
else:
    selected_login = st.selectbox("Select developer", options=filtered["login"].tolist())
    detail = filtered[filtered["login"] == selected_login].iloc[0]
    metric_cols = st.columns(4)
    metric_cols[0].metric("Impact Score", f"{detail.get('impact_score', 0):,.2f}")
    metric_cols[1].metric("Followers", f"{int(detail.get('followers', 0)):,}")
    metric_cols[2].metric("Total Stars", f"{int(detail.get('total_stars_received', 0)):,}")
    metric_cols[3].metric("Repos", f"{int(detail.get('total_repos', 0)):,}")
    st.dataframe(detail.to_frame(name="value"), use_container_width=True)

st.download_button(
    label="Export CSV",
    data=filtered.to_csv(index=False),
    file_name="developers_filtered.csv",
    mime="text/csv",
)
