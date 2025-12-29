"""
Streamlit dashboard for the AI Model Monitoring system.

Features:
- Key metrics: total predictions, fraud rate, avg latency
- Recent predictions table
- Charts: probability over time, latency distribution
- Drift report links (HTML/JSON) if generated
"""
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# Ensure project root is on path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.config import get_settings  # noqa: E402
from src.repositories import PredictionRepository  # noqa: E402


@st.cache_resource
def get_repo() -> PredictionRepository:
    return PredictionRepository()


def load_predictions(limit: int = 500) -> pd.DataFrame:
    repo = get_repo()
    records = repo.get_predictions(limit=limit)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    # Parse timestamp to datetime for plotting
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_drift_summary(summary_path: Path) -> Optional[dict]:
    if not summary_path.exists():
        return None
    try:
        with open(summary_path) as f:
            return json.load(f)
    except Exception:
        return None


def render_metrics(df: pd.DataFrame):
    total = len(df)
    fraud_rate = df["prediction"].mean() if total else 0
    avg_latency = df["latency_ms"].mean() if total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total predictions", f"{total:,}")
    col2.metric("Fraud rate", f"{fraud_rate*100:.2f}%")
    col3.metric("Avg latency (ms)", f"{avg_latency:.2f}")


def render_charts(df: pd.DataFrame):
    if df.empty:
        st.info("No data to chart yet. Make some predictions first.")
        return

    st.subheader("Probability over time")
    st.line_chart(df.set_index("timestamp")[["probability"]])

    st.subheader("Latency distribution (ms)")
    st.bar_chart(df["latency_ms"])

    st.subheader("Fraud vs Legitimate")
    counts = df["prediction"].value_counts().rename(index={0: "Legit", 1: "Fraud"})
    st.bar_chart(counts)


def render_recent_table(df: pd.DataFrame):
    st.subheader("Recent predictions")
    if df.empty:
        st.info("No predictions yet.")
        return
    display_cols = ["timestamp", "prediction", "probability", "latency_ms"]
    st.dataframe(df[display_cols].sort_values("timestamp", ascending=False).head(50))


def render_drift_section(settings):
    st.subheader("Drift reports")
    html_path = settings.artifacts_dir / "monitoring_report.html"
    json_path = settings.artifacts_dir / "monitoring_summary.json"

    if html_path.exists():
    st.success("Drift HTML report found")g
    with open(html_path, "r", encoding="utf-8") as f:
        st.components.v1.html(
            f.read(),
            height=800,
            scrolling=True,
        )
    else:
        st.warning("No drift HTML report found yet.")


    summary = load_drift_summary(json_path)
    if summary:
        st.write("Drift summary (JSON):")
        st.json(summary)
    else:
        st.info("No drift summary JSON found yet.")


def main():
    st.set_page_config(page_title="AI Model Monitoring Dashboard", layout="wide")
    st.title("AI Model Monitoring Dashboard")

    settings = get_settings()
    st.caption(
        f"Model: {settings.model_path.name} | Features: {settings.features_path.name} | DB: {settings.db_path.name}"
    )

    # Sidebar controls
    st.sidebar.header("Controls")
    limit = st.sidebar.slider("Records to load", min_value=100, max_value=5000, value=500, step=100)

    # Load data
    df = load_predictions(limit=limit)

    # Metrics
    render_metrics(df)

    # Charts
    render_charts(df)

    # Table
    render_recent_table(df)

    # Drift
    render_drift_section(settings)


if __name__ == "__main__":
    main()

