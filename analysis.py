"""Statistical analysis for World Bank life expectancy data.

Answers assignment questions on income-group gender gaps,
life-expectancy variability, and fertility-life-expectancy correlations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
import requests

from data_loader import configure_logging

logger = logging.getLogger(__name__)

INCOME_GROUPS: Final[list[str]] = [
    "High income",
    "Upper middle income",
    "Lower middle income",
    "Low income",
]

_WB_COUNTRY_API: Final[str] = "https://api.worldbank.org/v2/country"
_DEFAULT_START_YEAR: Final[int] = 1960
_DEFAULT_END_YEAR: Final[int] = 2023


def load_master_dataset(path: Path | str = "master_dataset.csv") -> pd.DataFrame:
    """Load the merged master dataset from CSV.

    Args:
        path: Path to ``master_dataset.csv``.

    Returns:
        Master DataFrame with country-year indicator values.
    """
    dataset = pd.read_csv(path)
    logger.info("Loaded master dataset: %d rows from %s", len(dataset), path)
    return dataset


def get_aggregate_income_group_data(df: pd.DataFrame) -> pd.DataFrame:
    """Extract World Bank income-group aggregate rows from the master dataset.

    Args:
        df: Master dataset containing aggregate income-group entities.

    Returns:
        Subset with only the four standard World Bank income groups.
    """
    return df[df["Country"].isin(INCOME_GROUPS)].copy()


def compute_gender_life_expectancy_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Compute female-minus-male life expectancy gap for each row.

    Args:
        df: DataFrame with ``Life_Expectancy_Male`` and ``Life_Expectancy_Female``.

    Returns:
        Copy of ``df`` with an added ``Gender_Gap`` column.
    """
    result = df.copy()
    result["Gender_Gap"] = (
        result["Life_Expectancy_Female"] - result["Life_Expectancy_Male"]
    )
    return result


def analyze_income_group_gender_gap_change(
    df: pd.DataFrame,
    start_year: int = _DEFAULT_START_YEAR,
    end_year: int = _DEFAULT_END_YEAR,
) -> pd.DataFrame:
    """Determine how the male-female life expectancy gap changed by income group.

    Uses World Bank income-group aggregate series for male and female life
    expectancy. The group with the largest absolute change in average gap
    between ``start_year`` and ``end_year`` is flagged as the answer.

    Args:
        df: Master dataset.
        start_year: Baseline year for comparison.
        end_year: Comparison year.

    Returns:
        DataFrame with gap values, change, and ranking per income group.
    """
    income_data = get_aggregate_income_group_data(df)
    income_data = compute_gender_life_expectancy_gap(income_data)

    gap_by_year = (
        income_data[income_data["Year"].isin([start_year, end_year])]
        .pivot_table(index="Country", columns="Year", values="Gender_Gap")
        .reindex(INCOME_GROUPS)
    )

    start_col = int(start_year)
    end_col = int(end_year)
    gap_by_year["Gap_Start"] = gap_by_year[start_col]
    gap_by_year["Gap_End"] = gap_by_year[end_col]
    gap_by_year["Gap_Change"] = gap_by_year["Gap_End"] - gap_by_year["Gap_Start"]
    gap_by_year["Abs_Gap_Change"] = gap_by_year["Gap_Change"].abs()

    max_change_group = gap_by_year["Abs_Gap_Change"].idxmax()
    gap_by_year["Largest_Change"] = gap_by_year.index == max_change_group

    gap_by_year = gap_by_year.reset_index().rename(columns={"Country": "Income_Group"})
    logger.info(
        "Q1: Largest gender-gap change (%d-%d): %s (%.3f years)",
        start_year,
        end_year,
        max_change_group,
        gap_by_year.loc[gap_by_year["Largest_Change"], "Gap_Change"].iloc[0],
    )
    return gap_by_year


def fetch_country_income_groups(
    api_url: str = _WB_COUNTRY_API,
    timeout: int = 60,
) -> pd.DataFrame:
    """Fetch World Bank country-to-income-group mappings from the API.

    Args:
        api_url: World Bank country metadata API base URL.
        timeout: HTTP request timeout in seconds.

    Returns:
        DataFrame with columns ``Country_Code``, ``Country``, ``Income_Group``.
    """
    logger.info("Fetching country income classifications from World Bank API")
    response = requests.get(
        api_url,
        params={"format": "json", "per_page": 400},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    countries = payload[1] if isinstance(payload, list) and len(payload) > 1 else []

    records: list[dict[str, str]] = []
    for country in countries:
        income_group = country.get("incomeLevel", {}).get("value")
        if income_group in (None, "Aggregates", "Not classified"):
            continue
        records.append(
            {
                "Country_Code": country["id"],
                "Country": country["name"],
                "Income_Group": income_group,
            }
        )

    mapping = pd.DataFrame(records)
    logger.info("Fetched income groups for %d countries", len(mapping))
    return mapping


def filter_country_level_data(
    df: pd.DataFrame,
    income_mapping: pd.DataFrame,
) -> pd.DataFrame:
    """Return country-level rows enriched with income-group membership.

    Args:
        df: Master dataset.
        income_mapping: Country-to-income-group mapping.

    Returns:
        Country-level DataFrame excluding regional and income aggregates.
    """
    wb_response = requests.get(
        _WB_COUNTRY_API,
        params={"format": "json", "per_page": 400},
        timeout=60,
    )
    wb_response.raise_for_status()
    wb_countries = wb_response.json()[1]
    aggregate_entities = {
        country["id"]
        for country in wb_countries
        if country.get("incomeLevel", {}).get("value") == "Aggregates"
    }

    country_df = df[~df["Country_Code"].isin(aggregate_entities)].copy()
    country_df = country_df.merge(
        income_mapping[["Country_Code", "Income_Group"]],
        on="Country_Code",
        how="left",
    )
    country_df = country_df[country_df["Income_Group"].isin(INCOME_GROUPS)]
    logger.info("Filtered to %d country-level rows", len(country_df))
    return country_df


def compute_life_expectancy_variability(
    df: pd.DataFrame,
    year: int,
    value_column: str = "Life_Expectancy_Total",
) -> pd.Series:
    """Compute cross-country standard deviation of life expectancy by income group.

    Args:
        df: Country-level DataFrame with ``Income_Group`` column.
        year: Year to evaluate.
        value_column: Life expectancy column to measure.

    Returns:
        Standard deviation indexed by income group.
    """
    year_data = df[df["Year"] == year].dropna(subset=[value_column, "Income_Group"])
    return year_data.groupby("Income_Group")[value_column].std().reindex(INCOME_GROUPS)


def analyze_income_group_variability_change(
    df: pd.DataFrame,
    income_mapping: pd.DataFrame,
    start_year: int = _DEFAULT_START_YEAR,
    end_year: int = _DEFAULT_END_YEAR,
) -> pd.DataFrame:
    """Determine which income group had the largest variability change.

    Variability is measured as the standard deviation of total life expectancy
    across member countries within each income group.

    Args:
        df: Master dataset.
        income_mapping: Country-to-income-group mapping.
        start_year: Baseline year.
        end_year: Comparison year.

    Returns:
        DataFrame with variability metrics and change per income group.
    """
    country_df = filter_country_level_data(df, income_mapping)

    std_start = compute_life_expectancy_variability(country_df, start_year)
    std_end = compute_life_expectancy_variability(country_df, end_year)

    results = pd.DataFrame(
        {
            "Income_Group": INCOME_GROUPS,
            "Variability_Start": std_start.values,
            "Variability_End": std_end.values,
        }
    )
    results["Variability_Change"] = (
        results["Variability_End"] - results["Variability_Start"]
    )
    results["Abs_Variability_Change"] = results["Variability_Change"].abs()

    max_change_group = results.loc[
        results["Abs_Variability_Change"].idxmax(), "Income_Group"
    ]
    results["Largest_Change"] = results["Income_Group"] == max_change_group

    logger.info(
        "Q2: Largest variability change (%d-%d): %s (%.3f years)",
        start_year,
        end_year,
        max_change_group,
        results.loc[results["Largest_Change"], "Variability_Change"].iloc[0],
    )
    return results
