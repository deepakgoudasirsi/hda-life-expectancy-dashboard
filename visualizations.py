"""Interactive Plotly visualizations for World Bank life expectancy data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from analysis import INCOME_GROUPS, get_aggregate_income_group_data, load_master_dataset
from data_loader import configure_logging

logger = logging.getLogger(__name__)

_WB_COUNTRY_API: Final[str] = "https://api.worldbank.org/v2/country"
_MAP_YEAR: Final[int] = 2023
_SANKEY_START_YEAR: Final[int] = 1960
_SANKEY_END_YEAR: Final[int] = 2023


def _get_aggregate_country_codes() -> set[str]:
    """Return World Bank entity codes classified as regional or income aggregates."""
    response = requests.get(
        _WB_COUNTRY_API,
        params={"format": "json", "per_page": 400},
        timeout=60,
    )
    response.raise_for_status()
    countries = response.json()[1]
    return {
        country["id"]
        for country in countries
        if country.get("incomeLevel", {}).get("value") == "Aggregates"
    }


def get_country_level_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return country-level rows excluding World Bank aggregate entities.

    Args:
        df: Master dataset.

    Returns:
        Filtered DataFrame with one row per country-year.
    """
    aggregate_codes = _get_aggregate_country_codes()
    country_df = df[~df["Country_Code"].isin(aggregate_codes)].copy()
    logger.info("Prepared %d country-level rows for visualization", len(country_df))
    return country_df


def create_life_expectancy_timeseries(df: pd.DataFrame) -> go.Figure:
    """Create a line chart of life expectancy trends by income group.

    Args:
        df: Master dataset containing World Bank income-group aggregates.

    Returns:
        Plotly figure with year on the x-axis and life expectancy on the y-axis.
    """
    income_data = get_aggregate_income_group_data(df)
    trend_data = (
        income_data.dropna(subset=["Life_Expectancy_Total"])
        .rename(columns={"Country": "Income Group", "Life_Expectancy_Total": "Life Expectancy"})
    )

    figure = px.line(
        trend_data,
        x="Year",
        y="Life Expectancy",
        color="Income Group",
        markers=True,
        category_orders={"Income Group": INCOME_GROUPS},
        title="Life Expectancy at Birth by Income Group",
        labels={"Year": "Year", "Life Expectancy": "Life Expectancy (years)"},
    )

    figure.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Year: %{x}<br>"
            "Life Expectancy: %{y:.1f} years<extra></extra>"
        )
    )
    figure.update_layout(
        xaxis_title="Year",
        yaxis_title="Life Expectancy (years)",
        legend_title="Income Group",
    )
    logger.info("Created life expectancy time-series chart")
    return figure


def create_world_map_choropleth(
    df: pd.DataFrame,
    year: int = _MAP_YEAR,
) -> go.Figure:
    """Create a choropleth world map colored by life expectancy.

    Args:
        df: Master dataset.
        year: Map year (default 2023).

    Returns:
        Plotly choropleth figure.
    """
    country_data = get_country_level_data(df)
    map_data = country_data[country_data["Year"] == year].dropna(
        subset=["Life_Expectancy_Total"]
    )

    figure = px.choropleth(
        map_data,
        locations="Country_Code",
        color="Life_Expectancy_Total",
        hover_name="Country",
        color_continuous_scale="Viridis",
        range_color=(map_data["Life_Expectancy_Total"].min(), map_data["Life_Expectancy_Total"].max()),
        title=f"Life Expectancy at Birth by Country ({year})",
        labels={"Life_Expectancy_Total": "Life Expectancy (years)"},
    )

    figure.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "ISO Code: %{location}<br>"
            "Life Expectancy: %{z:.1f} years<extra></extra>"
        )
    )
    figure.update_geos(
        showcountries=True,
        showcoastlines=True,
        showland=True,
        landcolor="#f5f5f5",
        countrycolor="#cccccc",
        projection_type="natural earth",
    )
    figure.update_layout(
        coloraxis_colorbar_title="Years",
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
    )
    logger.info("Created choropleth map for %d with %d countries", year, len(map_data))
    return figure
