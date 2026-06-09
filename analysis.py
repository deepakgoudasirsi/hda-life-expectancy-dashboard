"""Statistical analysis for World Bank life expectancy data.

Answers assignment questions on income-group gender gaps,
life-expectancy variability, and fertility-life-expectancy correlations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd

from data_loader import configure_logging

logger = logging.getLogger(__name__)

INCOME_GROUPS: Final[list[str]] = [
    "High income",
    "Upper middle income",
    "Lower middle income",
    "Low income",
]

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
