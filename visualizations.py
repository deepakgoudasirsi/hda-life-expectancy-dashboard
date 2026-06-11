"""Interactive Plotly visualizations for World Bank life expectancy data."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Final

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from analysis import get_aggregate_income_group_data, load_master_dataset
from config import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    FIGURES_DIR,
    INCOME_GROUP_COLORS,
    INCOME_GROUPS,
)
from data_loader import configure_logging
from wb_metadata import get_aggregate_country_codes

logger = logging.getLogger(__name__)

_WB_COUNTRY_API: Final[str] = "https://api.worldbank.org/v2/country"
_WORLD_GEOJSON_PATH: Final[Path] = Path("data/world_110m.json")
_WORLD_GEOJSON_URL: Final[str] = (
    "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
)
_MAP_YEAR: Final[int] = DEFAULT_END_YEAR
_SANKEY_START_YEAR: Final[int] = DEFAULT_START_YEAR
_SANKEY_END_YEAR: Final[int] = DEFAULT_END_YEAR

LIFE_EXPECTANCY_CATEGORIES: Final[list[str]] = [
    "Very low life expectancy",
    "Low life expectancy",
    "Medium life expectancy",
    "High life expectancy",
    "Very high life expectancy",
]

_INCOME_GROUP_COLORS: Final[dict[str, str]] = INCOME_GROUP_COLORS

_CHART_TEMPLATE: Final[dict[str, object]] = {
    "layout": {
        "template": "plotly_white",
        "font": {"family": "Arial, Helvetica, sans-serif", "size": 13, "color": "#1f2937"},
        "title": {"font": {"size": 22, "color": "#111827"}, "x": 0.02, "xanchor": "left"},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#fafafa",
        "hoverlabel": {
            "bgcolor": "#111827",
            "font_size": 12,
            "font_family": "Arial, Helvetica, sans-serif",
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": "#e5e7eb",
            "borderwidth": 1,
        },
        "margin": {"l": 60, "r": 30, "t": 90, "b": 60},
    }
}


def get_country_level_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return country-level rows excluding World Bank aggregate entities."""
    aggregate_codes = get_aggregate_country_codes()
    country_df = df[~df["Country_Code"].isin(aggregate_codes)].copy()
    logger.info("Prepared %d country-level rows for visualization", len(country_df))
    return country_df


def get_world_geojson(
    cache_path: Path = _WORLD_GEOJSON_PATH,
    geojson_url: str = _WORLD_GEOJSON_URL,
) -> dict:
    """Load Plotly world GeoJSON, downloading and caching it when missing."""
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    logger.info("Downloading world GeoJSON from %s", geojson_url)
    response = requests.get(geojson_url, timeout=60)
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response.text, encoding="utf-8")
    return json.loads(response.text)


def apply_chart_theme(figure: go.Figure) -> go.Figure:
    """Apply shared styling for professional, consistent chart presentation."""
    layout_kwargs = _CHART_TEMPLATE["layout"]
    figure.update_layout(**layout_kwargs)
    figure.update_xaxes(
        showgrid=True,
        gridcolor="#e5e7eb",
        linecolor="#9ca3af",
        zeroline=False,
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor="#e5e7eb",
        linecolor="#9ca3af",
        zeroline=False,
    )
    return figure


def export_figure_html(figure: go.Figure, output_path: Path | str) -> Path:
    """Export a Plotly figure to a standalone HTML file.

    Args:
        figure: Plotly figure to export.
        output_path: Destination HTML path.

    Returns:
        Resolved path to the written HTML file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(
        str(path),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "responsive": True},
    )
    logger.info("Exported HTML visualization to %s", path)
    return path


def export_figure_png(
    figure: go.Figure,
    output_path: Path | str,
    *,
    width: int = 1280,
    height: int = 720,
    scale: int = 2,
) -> Path:
    """Export a Plotly figure to PNG using Kaleido.

    Args:
        figure: Plotly figure to export.
        output_path: Destination PNG path.
        width: Image width in pixels.
        height: Image height in pixels.
        scale: Resolution scale factor.

    Returns:
        Resolved path to the written PNG file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_image(str(path), width=width, height=height, scale=scale)
    logger.info("Exported PNG visualization to %s", path)
    return path


def export_figure(
    figure: go.Figure,
    html_path: Path | str,
    png_path: Path | str | None = None,
) -> tuple[Path, Path | None]:
    """Export a figure to HTML and optionally PNG.

    Args:
        figure: Plotly figure to export.
        html_path: Destination HTML path.
        png_path: Optional destination PNG path.

    Returns:
        Tuple of HTML path and optional PNG path.
    """
    html_output = export_figure_html(figure, html_path)
    png_output = None
    if png_path is not None:
        png_output = export_figure_png(figure, png_path)
    return html_output, png_output


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
        color_discrete_map=_INCOME_GROUP_COLORS,
        title="Life Expectancy at Birth by Income Group",
        labels={"Year": "Year", "Life Expectancy": "Life Expectancy (years)"},
    )

    figure.update_traces(
        mode="lines+markers",
        line={"width": 2.5},
        marker={"size": 6},
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Year: %{x}<br>"
            "Life Expectancy: %{y:.1f} years<extra></extra>"
        ),
    )
    figure.update_layout(
        xaxis_title="Year",
        yaxis_title="Life Expectancy (years)",
        legend_title="Income Group",
        hovermode="x unified",
    )
    apply_chart_theme(figure)
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
    geojson = get_world_geojson()

    figure = go.Figure(
        data=go.Choroplethmap(
            geojson=geojson,
            featureidkey="id",
            locations=map_data["Country_Code"],
            z=map_data["Life_Expectancy_Total"],
            text=map_data["Country"],
            colorscale="Viridis",
            zmin=map_data["Life_Expectancy_Total"].min(),
            zmax=map_data["Life_Expectancy_Total"].max(),
            colorbar={"title": "Years"},
            hovertemplate=(
                "<b>%{text}</b><br>"
                "ISO Code: %{location}<br>"
                "Life Expectancy: %{z:.1f} years<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title=f"Life Expectancy at Birth by Country ({year})",
        map=dict(style="white-bg", center={"lat": 20, "lon": 0}, zoom=0.8),
        margin={"r": 0, "t": 80, "l": 0, "b": 0},
    )
    apply_chart_theme(figure)
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
        height=720,
        margin={"l": 20, "r": 20, "t": 80, "b": 20},
    )
    apply_chart_theme(figure)
    figure.update_layout(showlegend=False, plot_bgcolor="#ffffff")
    logger.info(
        "Created Sankey diagram for %d → %d with %d flows",
        start_year,
        end_year,
        len(values),
    )
    return figure


def run_visualizations(
    master_path: Path | str = "master_dataset.csv",
    output_dir: Path | str = FIGURES_DIR,
) -> dict[str, go.Figure]:
    """Build and export all required visualizations.

    Args:
        master_path: Path to the master dataset CSV.
        output_dir: Directory for HTML and PNG exports.

    Returns:
        Dictionary mapping visualization names to Plotly figures.
    """
    output_directory = Path(output_dir)
    master_df = load_master_dataset(master_path)

    figures = {
        "life_expectancy_trend": create_life_expectancy_timeseries(master_df),
        "world_map": create_world_map_choropleth(master_df),
        "sankey": create_sankey_diagram(master_df),
    }

    export_specs = {
        "life_expectancy_trend": "life_expectancy_trend",
        "world_map": "world_map",
        "sankey": "sankey",
    }

    for key, stem in export_specs.items():
        export_figure(
            figures[key],
            output_directory / f"{stem}.html",
            output_directory / f"{stem}.png",
        )

    logger.info("Exported %d visualizations to %s", len(figures), output_directory)
    return figures


if __name__ == "__main__":
    configure_logging()
    charts = run_visualizations()
    print("Generated visualizations:")
    for name in charts:
        print(f"  - {name}.html")
        print(f"  - {name}.png")
