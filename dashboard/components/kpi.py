"""KPI card components for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _format_metric(value: float | None, pattern: str, fallback: str = "N/A") -> str:
    """Safely format a KPI value."""
    if value is None or pd.isna(value):
        return fallback
    return pattern.format(value)


def render_kpi_cards(latest_df: pd.DataFrame, end_year: int) -> None:
    """Render headline KPI metrics for the selected countries."""
    st.markdown(
        '<p class="section-title">Key Performance Indicators</p>',
        unsafe_allow_html=True,
    )

    life_expectancy = latest_df["Life_Expectancy_Total"].mean()
    fertility = latest_df["Fertility_Rate"].mean()
    death_rate = latest_df["Death_Rate"].mean()
    gender_gap = (
        latest_df["Life_Expectancy_Female"] - latest_df["Life_Expectancy_Male"]
    ).mean()

    cards = [
        ("Current Life Expectancy", _format_metric(life_expectancy, "{:.1f}"), f"years · as of {end_year}"),
        ("Current Fertility Rate", _format_metric(fertility, "{:.2f}"), f"births per woman · {end_year}"),
        ("Current Death Rate", _format_metric(death_rate, "{:.1f}"), f"per 1,000 people · {end_year}"),
        ("Male-Female Gap", _format_metric(gender_gap, "{:.1f}"), f"years (female − male) · {end_year}"),
    ]

    columns = st.columns(4)
    for column, (label, value, subtext) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-subtext">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
