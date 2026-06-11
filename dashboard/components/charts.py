"""Plotly chart builders for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import INCOME_GROUP_COLORS, INCOME_GROUPS, REGION_COLORS, REGIONS
from visualizations import apply_chart_theme


def _apply_line_chart_defaults(figure: go.Figure, legend_title: str) -> go.Figure:
    """Apply shared styling to multi-series line charts."""
    figure.update_traces(
        mode="lines+markers",
        line={"width": 2.5},
        marker={"size": 5},
    )
    figure.update_layout(hovermode="x unified", legend_title=legend_title)
    return apply_chart_theme(figure)


def create_life_expectancy_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a life expectancy trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Life_Expectancy_Total"])
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
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Life Expectancy: %{y:.1f} years<extra></extra>"
        )
    )
    return _apply_line_chart_defaults(figure, "Country")


def create_fertility_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a fertility rate trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Fertility_Rate"])
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
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Fertility Rate: %{y:.2f}<extra></extra>"
        )
    )
    return _apply_line_chart_defaults(figure, "Country")


def create_death_rate_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build a crude death rate trend chart for selected countries."""
    trend_data = filtered_df.dropna(subset=["Death_Rate"])
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
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Death Rate: %{y:.1f}<extra></extra>"
        )
    )
    return _apply_line_chart_defaults(figure, "Country")


def create_gender_life_expectancy_trend(filtered_df: pd.DataFrame) -> go.Figure:
    """Build male versus female life expectancy trends for selected countries."""
    gender_long = filtered_df[
        ["Country", "Year", "Life_Expectancy_Male", "Life_Expectancy_Female"]
    ].melt(
        id_vars=["Country", "Year"],
        value_vars=["Life_Expectancy_Male", "Life_Expectancy_Female"],
        var_name="Sex",
        value_name="Life Expectancy",
    )
    gender_long["Sex"] = gender_long["Sex"].map(
        {
            "Life_Expectancy_Male": "Male",
            "Life_Expectancy_Female": "Female",
        }
    )
    gender_long = gender_long.dropna(subset=["Life Expectancy"])

    figure = px.line(
        gender_long,
        x="Year",
        y="Life Expectancy",
        color="Sex",
        line_dash="Country",
        markers=True,
        category_orders={"Sex": ["Male", "Female"]},
        color_discrete_map={"Male": "#2563eb", "Female": "#db2777"},
        title="Male vs Female Life Expectancy Trend",
        labels={"Year": "Year", "Life Expectancy": "Life Expectancy (years)"},
    )
    figure.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>Year: %{x}<br>"
            "Life Expectancy: %{y:.1f} years<extra></extra>"
        )
    )
    return _apply_line_chart_defaults(figure, "Sex")


def create_region_comparison(region_df: pd.DataFrame, end_year: int) -> go.Figure:
    """Build a bar chart comparing life expectancy across regions."""
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
        color_discrete_map=REGION_COLORS,
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
    figure.update_layout(showlegend=False, xaxis_tickangle=-25, height=460)
    return apply_chart_theme(figure)


def create_income_group_comparison(
    income_df: pd.DataFrame,
    end_year: int,
) -> go.Figure:
    """Build a bar chart comparing life expectancy across income groups."""
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
        color_discrete_map=INCOME_GROUP_COLORS,
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
    figure.update_layout(showlegend=False, xaxis_tickangle=-15, height=460)
    return apply_chart_theme(figure)
