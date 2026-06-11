"""Production Streamlit dashboard for World Bank health indicators."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from analysis import load_master_dataset  # noqa: E402

DATA_PATH = ROOT_DIR / "master_dataset.csv"

PAGE_CONFIG = {
    "page_title": "Global Health Indicators Dashboard",
    "page_icon": "🌍",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .dashboard-header {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 45%, #134e4a 100%);
        padding: 1.75rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(15, 118, 110, 0.25);
    }
    .dashboard-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .dashboard-header p {
        color: #ccfbf1;
        margin: 0.35rem 0 0 0;
        font-size: 1rem;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        height: 100%;
    }
    .kpi-label {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .kpi-subtext {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 0.35rem;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin: 1.5rem 0 0.75rem 0;
        padding-bottom: 0.35rem;
        border-bottom: 2px solid #14b8a6;
        display: inline-block;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    @media (max-width: 768px) {
        .dashboard-header h1 { font-size: 1.5rem; }
        .kpi-value { font-size: 1.5rem; }
    }
</style>
"""


@st.cache_data(show_spinner="Loading master dataset…")
def load_data(path: str) -> pd.DataFrame:
    """Load and cache the master dataset."""
    return load_master_dataset(path)


def apply_page_style() -> None:
    """Inject global page configuration and custom styling."""
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Render the dashboard title banner."""
    st.markdown(
        """
        <div class="dashboard-header">
            <h1>Global Health Indicators Dashboard</h1>
            <p>World Bank life expectancy, fertility, and mortality analytics (1960–2023)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""
    apply_page_style()
    render_header()

    df = load_data(str(DATA_PATH))
    st.caption(f"Dataset loaded: {len(df):,} rows · {df['Country_Code'].nunique()} entities")

    st.info("Use the sidebar filters to explore country-level and aggregate trends.")


if __name__ == "__main__":
    main()
