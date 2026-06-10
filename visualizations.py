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

LIFE_EXPECTANCY_CATEGORIES: Final[list[str]] = [
    "Very low life expectancy",
    "Low life expectancy",
    "Medium life expectancy",
    "High life expectancy",
    "Very high life expectancy",
]


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


def categorize_life_expectancy(
    df: pd.DataFrame,
    year: int,
    value_column: str = "Life_Expectancy_Total",
) -> pd.DataFrame:
    """Assign countries to quintile life-expectancy buckets for a given year.

    Countries are ranked by life expectancy and split into five groups of
    roughly equal size.

    Args:
        df: Master dataset.
        year: Year to categorize.
        value_column: Life expectancy column to rank on.

    Returns:
        DataFrame with country metadata and assigned category labels.
    """
    country_data = get_country_level_data(df)
    year_data = country_data[country_data["Year"] == year].dropna(subset=[value_column])

    ranked = year_data.sort_values(value_column).reset_index(drop=True)
    ranked["Category"] = pd.qcut(
        ranked[value_column].rank(method="first"),
        q=len(LIFE_EXPECTANCY_CATEGORIES),
        labels=LIFE_EXPECTANCY_CATEGORIES,
    )

    logger.info(
        "Categorized %d countries into life-expectancy buckets for %d",
        len(ranked),
        year,
    )
    return ranked[["Country", "Country_Code", value_column, "Category"]]


def _build_sankey_flows(
    start_categories: pd.DataFrame,
    end_categories: pd.DataFrame,
) -> tuple[list[str], list[int], list[int], list[int], list[str]]:
    """Build Sankey node labels and link indices from category assignments.

    Args:
        start_categories: Categorized countries for the start year.
        end_categories: Categorized countries for the end year.

    Returns:
        Tuple of node labels, source indices, target indices, values, and link colors.
    """
    merged = start_categories.merge(
        end_categories,
        on="Country_Code",
        suffixes=("_start", "_end"),
    )

    start_nodes = [f"{_SANKEY_START_YEAR}: {label}" for label in LIFE_EXPECTANCY_CATEGORIES]
    end_nodes = [f"{_SANKEY_END_YEAR}: {label}" for label in LIFE_EXPECTANCY_CATEGORIES]
    all_nodes = start_nodes + end_nodes
    node_index = {label: index for index, label in enumerate(all_nodes)}

    flows = (
        merged.groupby(["Category_start", "Category_end"])
        .size()
        .reset_index(name="Count")
    )

    category_colors = {
        "Very low life expectancy": "rgba(215, 48, 39, 0.45)",
        "Low life expectancy": "rgba(244, 109, 67, 0.45)",
        "Medium life expectancy": "rgba(254, 224, 139, 0.55)",
        "High life expectancy": "rgba(171, 221, 164, 0.55)",
        "Very high life expectancy": "rgba(102, 194, 165, 0.55)",
    }

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    link_colors: list[str] = []

    for _, row in flows.iterrows():
        source_label = f"{_SANKEY_START_YEAR}: {row['Category_start']}"
        target_label = f"{_SANKEY_END_YEAR}: {row['Category_end']}"
        sources.append(node_index[source_label])
        targets.append(node_index[target_label])
        values.append(int(row["Count"]))
        link_colors.append(category_colors[str(row["Category_start"])])

    return all_nodes, sources, targets, values, link_colors


def create_sankey_diagram(
    df: pd.DataFrame,
    start_year: int = _SANKEY_START_YEAR,
    end_year: int = _SANKEY_END_YEAR,
) -> go.Figure:
    """Create a Sankey diagram of life-expectancy category transitions.

    Args:
        df: Master dataset.
        start_year: Baseline year for categorization.
        end_year: Comparison year for categorization.

    Returns:
        Plotly Sankey figure showing country movement between quintiles.
    """
    start_categories = categorize_life_expectancy(df, start_year)
    end_categories = categorize_life_expectancy(df, end_year)

    labels, sources, targets, values, link_colors = _build_sankey_flows(
        start_categories,
        end_categories,
    )

    node_colors = [
        "#d73027",
        "#fc8d59",
        "#fee08b",
        "#91cf60",
        "#1a9850",
        "#d73027",
        "#fc8d59",
        "#fee08b",
        "#91cf60",
        "#1a9850",
    ]

    sankey = go.Sankey(
        arrangement="snap",
        node={
            "label": labels,
            "pad": 18,
            "thickness": 18,
            "color": node_colors,
            "hovertemplate": "<b>%{label}</b><extra></extra>",
        },
        link={
            "source": sources,
            "target": targets,
            "value": values,
            "color": link_colors,
            "hovertemplate": (
                "%{source.label} → %{target.label}<br>"
                "Countries: %{value}<extra></extra>"
            ),
        },
    )

    figure = go.Figure(sankey)
    figure.update_layout(
        title=(
            f"Life Expectancy Category Transitions "
            f"({start_year} → {end_year})"
        ),
    )
    logger.info(
        "Created Sankey diagram for %d → %d with %d flows",
        start_year,
        end_year,
        len(values),
    )
    return figure
