"""Cached data access layer for the Streamlit dashboard."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from analysis import get_aggregate_income_group_data, load_master_dataset
from config import MASTER_DATASET_PATH
from exceptions import DataLoadError, MetadataFetchError
from wb_metadata import fetch_country_metadata

logger = logging.getLogger(__name__)


@st.cache_data(show_spinner="Loading master dataset…", ttl=3600)
def load_master_data(path: str = str(MASTER_DATASET_PATH)) -> pd.DataFrame:
    """Load and cache the master dataset from disk."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise DataLoadError(
            f"Master dataset not found at {dataset_path}. "
            "Run `python preprocessing.py` first."
        )

    try:
        dataset = load_master_dataset(dataset_path)
        logger.info("Dashboard loaded %d master rows", len(dataset))
        return dataset
    except (OSError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Failed to read master dataset: {dataset_path}") from exc


@st.cache_data(show_spinner="Loading country metadata…", ttl=86400)
def load_country_metadata() -> tuple[pd.DataFrame, frozenset[str]]:
    """Load and cache World Bank country metadata."""
    try:
        return fetch_country_metadata()
    except MetadataFetchError:
        raise
    except Exception as exc:
        raise MetadataFetchError("Country metadata could not be prepared.") from exc


def _prepare_country_dataframe(
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


@st.cache_data(show_spinner="Preparing country-level data…", ttl=3600)
def prepare_country_data(
    master_df: pd.DataFrame,
    metadata: pd.DataFrame,
    aggregate_codes: frozenset[str],
) -> pd.DataFrame:
    """Cached wrapper for country-level dataset preparation."""
    return _prepare_country_dataframe(master_df, metadata, aggregate_codes)


def filter_country_data(
    country_df: pd.DataFrame,
    countries: list[str],
    income_groups: list[str],
    regions: list[str],
    year_range: tuple[int, int],
) -> pd.DataFrame:
    """Apply sidebar filters to country-level data."""
    start_year, end_year = year_range
    mask = (
        country_df["Year"].between(start_year, end_year)
        & country_df["Income_Group"].isin(income_groups)
        & country_df["Region"].isin(regions)
    )
    if countries:
        mask &= country_df["Country"].isin(countries)
    return country_df.loc[mask].reset_index(drop=True)


def get_latest_year_data(
    filtered_df: pd.DataFrame,
    end_year: int,
) -> pd.DataFrame:
    """Return the most recent available row per country within the year range."""
    if filtered_df.empty:
        return filtered_df

    in_range = filtered_df[filtered_df["Year"] <= end_year]
    return (
        in_range.sort_values("Year")
        .groupby("Country", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )


def get_region_aggregate_data(
    master_df: pd.DataFrame,
    year_range: tuple[int, int],
    regions: list[str],
) -> pd.DataFrame:
    """Extract regional aggregate series for comparison charts."""
    from config import REGIONS

    start_year, end_year = year_range
    selected_regions = regions if regions else REGIONS
    region_df = master_df.loc[
        master_df["Country"].isin(selected_regions)
        & master_df["Year"].between(start_year, end_year)
    ].copy()
    return region_df.rename(columns={"Country": "Region"})


def get_income_aggregate_data(
    master_df: pd.DataFrame,
    year_range: tuple[int, int],
    income_groups: list[str],
) -> pd.DataFrame:
    """Extract income-group aggregate series for comparison charts."""
    from config import INCOME_GROUPS

    start_year, end_year = year_range
    selected_groups = income_groups if income_groups else INCOME_GROUPS
    income_data = get_aggregate_income_group_data(master_df)
    income_data = income_data.loc[
        income_data["Country"].isin(selected_groups)
        & income_data["Year"].between(start_year, end_year)
    ].copy()
    return income_data.rename(columns={"Country": "Income Group"})
