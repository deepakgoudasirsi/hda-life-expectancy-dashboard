"""Production Streamlit dashboard for World Bank health indicators."""

from __future__ import annotations

import sys
from pathlib import Path

from typing import Final

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from analysis import (  # noqa: E402
    INCOME_GROUPS,
    fetch_country_income_groups,
    get_aggregate_income_group_data,
    load_master_dataset,
)
from visualizations import _INCOME_GROUP_COLORS, apply_chart_theme  # noqa: E402

DATA_PATH = ROOT_DIR / "master_dataset.csv"
_WB_COUNTRY_API: Final[str] = "https://api.worldbank.org/v2/country"

REGIONS: Final[list[str]] = [
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East, North Africa, Afghanistan & Pakistan",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
]

_REGION_COLORS: Final[dict[str, str]] = {
    "East Asia & Pacific": "#0284c7",
    "Europe & Central Asia": "#7c3aed",
    "Latin America & Caribbean": "#db2777",
    "Middle East, North Africa, Afghanistan & Pakistan": "#ea580c",
    "North America": "#059669",
    "South Asia": "#ca8a04",
    "Sub-Saharan Africa": "#dc2626",
}

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


@st.cache_data(show_spinner="Fetching country metadata…")
def load_country_metadata() -> tuple[pd.DataFrame, frozenset[str]]:
    """Fetch and cache World Bank country income and region classifications."""
    income_mapping = fetch_country_income_groups()
    response = requests.get(
        _WB_COUNTRY_API,
        params={"format": "json", "per_page": 400},
        timeout=60,
    )
    response.raise_for_status()
    countries = response.json()[1]

    region_records: list[dict[str, str]] = []
    aggregate_codes: set[str] = set()
    for country in countries:
        income_level = country.get("incomeLevel", {}).get("value")
        if income_level == "Aggregates":
            aggregate_codes.add(country["id"])
            continue
        region_value = country.get("region", {}).get("value", "").strip()
        if region_value in ("", "Aggregates", "Not classified"):
            continue
        region_records.append(
            {
                "Country_Code": country["id"],
                "Region": region_value,
            }
        )

    region_mapping = pd.DataFrame(region_records)
    metadata = income_mapping.merge(region_mapping, on="Country_Code", how="left")
    metadata = metadata[
        metadata["Income_Group"].isin(INCOME_GROUPS)
        & metadata["Region"].isin(REGIONS)
    ].copy()
    return metadata, frozenset(aggregate_codes)


@st.cache_data(show_spinner="Preparing country-level data…")
def prepare_country_data(
    master_df: pd.DataFrame,
    metadata: pd.DataFrame,
    aggregate_codes: frozenset[str],
) -> pd.DataFrame:
    """Return enriched country-level rows excluding World Bank aggregates."""
    country_df = master_df[~master_df["Country_Code"].isin(aggregate_codes)].copy()
    enriched = country_df.merge(
        metadata[["Country_Code", "Income_Group", "Region"]],
        on="Country_Code",
        how="inner",
    )
    return enriched.sort_values(["Country", "Year"]).reset_index(drop=True)


def filter_country_data(
    country_df: pd.DataFrame,
    countries: list[str],
    income_groups: list[str],
    regions: list[str],
    year_range: tuple[int, int],
) -> pd.DataFrame:
    """Apply sidebar filters to country-level data."""
    filtered = country_df.copy()
    if income_groups:
        filtered = filtered[filtered["Income_Group"].isin(income_groups)]
    if regions:
        filtered = filtered[filtered["Region"].isin(regions)]
    if countries:
        filtered = filtered[filtered["Country"].isin(countries)]
    start_year, end_year = year_range
    filtered = filtered[
        (filtered["Year"] >= start_year) & (filtered["Year"] <= end_year)
    ]
    return filtered.reset_index(drop=True)


def render_sidebar(country_df: pd.DataFrame) -> dict[str, object]:
    """Render sidebar filters and return the active selection."""
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("Refine the dashboard by geography and time period.")

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

    eligible = country_df.copy()
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


def get_latest_year_data(filtered_df: pd.DataFrame, year_range: tuple[int, int]) -> pd.DataFrame:
    """Return the most recent available row per country within the year range."""
    if filtered_df.empty:
        return filtered_df
    _, end_year = year_range
    in_range = filtered_df[filtered_df["Year"] <= end_year].copy()
    return (
        in_range.sort_values("Year")
        .groupby("Country", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )


def render_kpi_cards(latest_df: pd.DataFrame, end_year: int) -> None:
    """Render headline KPI metrics for the selected countries."""
    st.markdown('<p class="section-title">Key Performance Indicators</p>', unsafe_allow_html=True)

    life_expectancy = latest_df["Life_Expectancy_Total"].mean()
    fertility = latest_df["Fertility_Rate"].mean()
    death_rate = latest_df["Death_Rate"].mean()
    gender_gap = (
        latest_df["Life_Expectancy_Female"] - latest_df["Life_Expectancy_Male"]
    ).mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Current Life Expectancy</div>
                <div class="kpi-value">{life_expectancy:.1f}</div>
                <div class="kpi-subtext">years · as of {end_year}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Current Fertility Rate</div>
                <div class="kpi-value">{fertility:.2f}</div>
                <div class="kpi-subtext">births per woman · {end_year}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Current Death Rate</div>
                <div class="kpi-value">{death_rate:.1f}</div>
                <div class="kpi-subtext">per 1,000 people · {end_year}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Male-Female Gap</div>
                <div class="kpi-value">{gender_gap:.1f}</div>
                <div class="kpi-subtext">years (female − male) · {end_year}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def create_life_expectancy_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a life expectancy trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Life_Expectancy_Total"]).copy()
    figure = px.line(
        trend_data,
        x="Year",
        y="Life_Expectancy_Total",
        color="Country",
        markers=True,
        title="Life Expectancy Trend",
        labels={
            "Year": "Year",
            "Life_Expectancy_Total": "Life Expectancy (years)",
            "Country": "Country",
        },
    )
    figure.update_traces(
        mode="lines+markers",
        line={"width": 2.5},
        marker={"size": 5},
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Life Expectancy: %{y:.1f} years<extra></extra>"
        ),
    )
    figure.update_layout(hovermode="x unified", legend_title="Country")
    return apply_chart_theme(figure)


def create_fertility_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a fertility rate trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Fertility_Rate"]).copy()
    figure = px.line(
        trend_data,
        x="Year",
        y="Fertility_Rate",
        color="Country",
        markers=True,
        title="Fertility Rate Trend",
        labels={
            "Year": "Year",
            "Fertility_Rate": "Fertility Rate (births per woman)",
            "Country": "Country",
        },
    )
    figure.update_traces(
        mode="lines+markers",
        line={"width": 2.5},
        marker={"size": 5},
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Fertility Rate: %{y:.2f}<extra></extra>"
        ),
    )
    figure.update_layout(hovermode="x unified", legend_title="Country")
    return apply_chart_theme(figure)


def create_death_rate_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a crude death rate trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Death_Rate"]).copy()
    figure = px.line(
        trend_data,
        x="Year",
        y="Death_Rate",
        color="Country",
        markers=True,
        title="Death Rate Trend",
        labels={
            "Year": "Year",
            "Death_Rate": "Death Rate (per 1,000 people)",
            "Country": "Country",
        },
    )
    figure.update_traces(
        mode="lines+markers",
        line={"width": 2.5},
        marker={"size": 5},
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Death Rate: %{y:.1f}<extra></extra>"
        ),
    )
    figure.update_layout(hovermode="x unified", legend_title="Country")
    return apply_chart_theme(figure)


def get_region_aggregate_data(
    master_df: pd.DataFrame,
    year_range: tuple[int, int],
    regions: list[str],
) -> pd.DataFrame:
    """Extract regional aggregate series for comparison charts."""
    start_year, end_year = year_range
    region_df = master_df[
        master_df["Country"].isin(regions if regions else REGIONS)
        & (master_df["Year"] >= start_year)
        & (master_df["Year"] <= end_year)
    ].copy()
    region_df = region_df.rename(columns={"Country": "Region"})
    return region_df


def get_income_aggregate_data(
    master_df: pd.DataFrame,
    year_range: tuple[int, int],
    income_groups: list[str],
) -> pd.DataFrame:
    """Extract income-group aggregate series for comparison charts."""
    income_data = get_aggregate_income_group_data(master_df)
    start_year, end_year = year_range
    selected_groups = income_groups if income_groups else INCOME_GROUPS
    income_data = income_data[
        income_data["Country"].isin(selected_groups)
        & (income_data["Year"] >= start_year)
        & (income_data["Year"] <= end_year)
    ].copy()
    return income_data.rename(columns={"Country": "Income Group"})


def create_region_comparison(
    region_df: pd.DataFrame,
    end_year: int,
) -> go.Figure:
    """Build a grouped bar chart comparing life expectancy across regions."""
    latest = (
        region_df.dropna(subset=["Life_Expectancy_Total"])
        .sort_values("Year")
        .groupby("Region", as_index=False)
        .tail(1)
    )
    figure = px.bar(
        latest,
        x="Region",
        y="Life_Expectancy_Total",
        color="Region",
        category_orders={"Region": REGIONS},
        color_discrete_map=_REGION_COLORS,
        title=f"Region Comparison · Life Expectancy ({end_year})",
        labels={
            "Region": "Region",
            "Life_Expectancy_Total": "Life Expectancy (years)",
        },
        text=latest["Life_Expectancy_Total"].round(1),
    )
    figure.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>Life Expectancy: %{y:.1f} years<extra></extra>"
        ),
    )
    figure.update_layout(showlegend=False, xaxis_tickangle=-25)
    return apply_chart_theme(figure)


def create_income_group_comparison(
    income_df: pd.DataFrame,
    end_year: int,
) -> go.Figure:
    """Build a grouped bar chart comparing life expectancy across income groups."""
    latest = (
        income_df.dropna(subset=["Life_Expectancy_Total"])
        .sort_values("Year")
        .groupby("Income Group", as_index=False)
        .tail(1)
    )
    figure = px.bar(
        latest,
        x="Income Group",
        y="Life_Expectancy_Total",
        color="Income Group",
        category_orders={"Income Group": INCOME_GROUPS},
        color_discrete_map=_INCOME_GROUP_COLORS,
        title=f"Income Group Comparison · Life Expectancy ({end_year})",
        labels={
            "Income Group": "Income Group",
            "Life_Expectancy_Total": "Life Expectancy (years)",
        },
        text=latest["Life_Expectancy_Total"].round(1),
    )
    figure.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>Life Expectancy: %{y:.1f} years<extra></extra>"
        ),
    )
    figure.update_layout(showlegend=False, xaxis_tickangle=-15)
    return apply_chart_theme(figure)


def render_data_table(filtered_df: pd.DataFrame) -> None:
    """Render a searchable, sortable data table."""
    st.markdown('<p class="section-title">Data Table</p>', unsafe_allow_html=True)

    display_df = filtered_df[
        [
            "Country",
            "Country_Code",
            "Region",
            "Income_Group",
            "Year",
            "Life_Expectancy_Total",
            "Life_Expectancy_Male",
            "Life_Expectancy_Female",
            "Fertility_Rate",
            "Death_Rate",
        ]
    ].rename(
        columns={
            "Country_Code": "Code",
            "Income_Group": "Income Group",
            "Life_Expectancy_Total": "Life Expectancy",
            "Life_Expectancy_Male": "Male LE",
            "Life_Expectancy_Female": "Female LE",
            "Fertility_Rate": "Fertility Rate",
            "Death_Rate": "Death Rate",
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered data (CSV)",
        data=csv_data,
        file_name="health_indicators_filtered.csv",
        mime="text/csv",
    )


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

    master_df = load_data(str(DATA_PATH))
    metadata, aggregate_codes = load_country_metadata()
    country_df = prepare_country_data(master_df, metadata, aggregate_codes)

    filters = render_sidebar(country_df)
    filtered_df = filter_country_data(country_df, **filters)

    st.caption(
        f"Showing {len(filtered_df):,} country-year records · "
        f"{filtered_df['Country'].nunique() if not filtered_df.empty else 0} countries"
    )

    if filtered_df.empty:
        st.warning("No data matches the current filters. Adjust your selections in the sidebar.")
        return

    year_range = filters["year_range"]
    end_year = year_range[1]
    latest_df = get_latest_year_data(filtered_df, year_range)

    render_kpi_cards(latest_df, end_year)

    st.markdown('<p class="section-title">Life Expectancy Trend</p>', unsafe_allow_html=True)
    st.plotly_chart(
        create_life_expectancy_trend(filtered_df),
        use_container_width=True,
    )

    trend_col1, trend_col2 = st.columns(2)
    with trend_col1:
        st.markdown('<p class="section-title">Fertility Trend</p>', unsafe_allow_html=True)
        st.plotly_chart(
            create_fertility_trend(filtered_df),
            use_container_width=True,
        )
    with trend_col2:
        st.markdown('<p class="section-title">Death Rate Trend</p>', unsafe_allow_html=True)
        st.plotly_chart(
            create_death_rate_trend(filtered_df),
            use_container_width=True,
        )

    region_df = get_region_aggregate_data(master_df, year_range, filters["regions"])
    income_df = get_income_aggregate_data(master_df, year_range, filters["income_groups"])

    compare_col1, compare_col2 = st.columns(2)
    with compare_col1:
        st.plotly_chart(
            create_region_comparison(region_df, end_year),
            use_container_width=True,
        )
    with compare_col2:
        st.plotly_chart(
            create_income_group_comparison(income_df, end_year),
            use_container_width=True,
        )

    render_data_table(filtered_df)


if __name__ == "__main__":
    main()
