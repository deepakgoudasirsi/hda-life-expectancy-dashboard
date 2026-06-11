"""Sidebar filter controls for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st

from config import INCOME_GROUPS, REGIONS


def render_sidebar(country_df) -> dict[str, object]:
    """Render sidebar filters and return the active selection."""
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown(
        '<div class="filter-panel">Refine geography and time period.</div>',
        unsafe_allow_html=True,
    )

    min_year = int(country_df["Year"].min())
    max_year = int(country_df["Year"].max())

    income_groups = st.sidebar.multiselect(
        "Income Group",
        options=INCOME_GROUPS,
        default=INCOME_GROUPS,
        help="Filter countries by World Bank income classification.",
    )
    regions = st.sidebar.multiselect(
        "Region",
        options=REGIONS,
        default=REGIONS,
        help="Filter countries by World Bank region.",
    )

    eligible = country_df
    if income_groups:
        eligible = eligible[eligible["Income_Group"].isin(income_groups)]
    if regions:
        eligible = eligible[eligible["Region"].isin(regions)]

    country_options = sorted(eligible["Country"].unique())
    countries = st.sidebar.multiselect(
        "Country",
        options=country_options,
        default=country_options[:1] if country_options else [],
        help="Select one or more countries for trend analysis.",
    )

    year_range = st.sidebar.slider(
        "Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
        help="Set the analysis window for charts and KPIs.",
    )

    if st.sidebar.button("Reset filters", use_container_width=True):
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"{len(countries)} of {len(country_options)} countries · "
        f"{year_range[0]}–{year_range[1]}"
    )

    return {
        "countries": countries,
        "income_groups": income_groups,
        "regions": regions,
        "year_range": year_range,
    }
