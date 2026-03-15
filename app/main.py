"""Main entry page for GitHub Peru Analytics dashboard."""

import os
import json
import streamlit as st

st.set_page_config(
    page_title="🇵🇪 GitHub Peru Analytics",
    page_icon="🇵🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)


def data_ready() -> tuple[bool, str]:
    required = [
        "data/processed/repositories.csv",
        "data/processed/classifications.csv",
        "data/metrics/user_metrics.csv",
        "data/metrics/ecosystem_metrics.json",
    ]
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        return False, "\n".join(missing)
    return True, ""


st.title("🇵🇪 GitHub Peru Analytics")
st.caption("Analisis del ecosistema de desarrolladores en Peru con GitHub API, GPT-4 y Streamlit.")

ready, missing_paths = data_ready()
if not ready:
    st.error("No se encontraron todos los archivos de datos requeridos.")
    st.code(missing_paths)
    st.markdown("Ejecuta el pipeline completo:")
    st.code(
        "python scripts/extract_data.py\n"
        "python scripts/classify_repos.py\n"
        "python scripts/calculate_metrics.py"
    )
    st.stop()

with open("data/metrics/ecosystem_metrics.json", "r", encoding="utf-8") as f:
    ecosystem_metrics = json.load(f)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Developers", f"{ecosystem_metrics.get('total_developers', 0):,}")
col2.metric("Total Repositories", f"{ecosystem_metrics.get('total_repositories', 0):,}")
col3.metric("Total Stars", f"{ecosystem_metrics.get('total_stars', 0):,}")
col4.metric("Active Developers", f"{ecosystem_metrics.get('active_developer_pct', 0):.1f}%")

st.markdown("### Navegacion")
st.markdown("Usa la barra lateral para abrir las 5 paginas requeridas:")
st.markdown("1. Overview")
st.markdown("2. Developers")
st.markdown("3. Repositories")
st.markdown("4. Industries")
st.markdown("5. Languages")
