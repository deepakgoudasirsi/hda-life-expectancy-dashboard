"""Statistical analysis for World Bank life expectancy data.

Answers assignment questions on income-group gender gaps,
life-expectancy variability, and fertility-life-expectancy correlations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
from scipy.stats import pearsonr

from config import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    INCOME_GROUPS,
    MASTER_DATASET_PATH,
)
from data_loader import configure_logging
from exceptions import DataLoadError, MetadataFetchError, PipelineError
from wb_metadata import fetch_country_income_groups, get_aggregate_country_codes

logger = logging.getLogger(__name__)

_DEFAULT_START_YEAR: Final[int] = DEFAULT_START_YEAR
_DEFAULT_END_YEAR: Final[int] = DEFAULT_END_YEAR
_MIN_CORRELATION_YEARS: Final[int] = 3
_TOP_N_COUNTRIES: Final[int] = 10


def load_master_dataset(
    path: Path | str = MASTER_DATASET_PATH,
) -> pd.DataFrame:
    """Load the merged master dataset from CSV.

    Args:
        path: Path to ``master_dataset.csv``.

    Returns:
        Master DataFrame with country-year indicator values.

    Raises:
        DataLoadError: If the dataset file is missing or cannot be parsed.
    """
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise DataLoadError(f"Master dataset not found: {dataset_path}")

    try:
        dataset = pd.read_csv(dataset_path)
    except (OSError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Failed to read master dataset: {dataset_path}") from exc

    logger.info("Loaded master dataset: %d rows from %s", len(dataset), dataset_path)
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
    aggregate_entities = get_aggregate_country_codes()
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


def compute_country_correlations(
    df: pd.DataFrame,
    x_column: str = "Fertility_Rate",
    y_column: str = "Life_Expectancy_Total",
    min_years: int = _MIN_CORRELATION_YEARS,
) -> pd.DataFrame:
    """Compute Pearson correlation between two indicators for each country.

    Args:
        df: Master dataset.
        x_column: Independent variable column.
        y_column: Dependent variable column.
        min_years: Minimum paired observations required per country.

    Returns:
        DataFrame with correlation, p-value, and observation count per country.
    """
    aggregate_codes = get_aggregate_country_codes()
    country_df = df[~df["Country_Code"].isin(aggregate_codes)].copy()

    records: list[dict[str, object]] = []
    for country_code, group in country_df.groupby("Country_Code"):
        paired = group.dropna(subset=[x_column, y_column])
        if len(paired) < min_years:
            continue

        correlation, p_value = pearsonr(paired[x_column], paired[y_column])
        records.append(
            {
                "Country": group["Country"].iloc[0],
                "Country_Code": country_code,
                "Correlation": correlation,
                "P_Value": p_value,
                "N_Years": len(paired),
            }
        )

    correlations = pd.DataFrame(records).sort_values(
        "Correlation", ascending=False
    ).reset_index(drop=True)
    logger.info("Q3: Computed correlations for %d countries", len(correlations))
    return correlations


def summarize_correlation_extremes(
    correlations: pd.DataFrame,
    top_n: int = _TOP_N_COUNTRIES,
) -> dict[str, pd.DataFrame]:
    """Summarize highest, lowest, and weakest absolute correlations.

    Args:
        correlations: Per-country correlation DataFrame.
        top_n: Number of countries to return in each summary list.

    Returns:
        Dictionary with ``highest_positive``, ``highest_negative``, and
        ``lowest_absolute`` DataFrames.
    """
    ranked = correlations.copy()
    ranked["Abs_Correlation"] = ranked["Correlation"].abs()

    return {
        "highest_positive": ranked.nlargest(top_n, "Correlation").copy(),
        "highest_negative": ranked.nsmallest(top_n, "Correlation").copy(),
        "lowest_absolute": ranked.nsmallest(top_n, "Abs_Correlation").copy(),
    }


def export_analysis_results(
    gap_results: pd.DataFrame,
    variability_results: pd.DataFrame,
    correlations: pd.DataFrame,
    correlation_summaries: dict[str, pd.DataFrame],
    output_path: Path | str = "analysis_results.csv",
) -> Path:
    """Export all analysis outputs to a single tidy CSV file.

    Args:
        gap_results: Output of :func:`analyze_income_group_gender_gap_change`.
        variability_results: Output of :func:`analyze_income_group_variability_change`.
        correlations: Full per-country correlation table.
        correlation_summaries: Extreme correlation summaries.
        output_path: Destination CSV path.

    Returns:
        Resolved path to the written CSV file.
    """
    export_frames: list[pd.DataFrame] = []

    gap_export = gap_results.copy()
    gap_export.insert(0, "Section", "Q1_Gender_Gap_Change")
    export_frames.append(gap_export)

    variability_export = variability_results.copy()
    variability_export.insert(0, "Section", "Q2_Variability_Change")
    export_frames.append(variability_export)

    correlation_export = correlations.copy()
    correlation_export.insert(0, "Section", "Q3_Country_Correlations")
    export_frames.append(correlation_export)

    for summary_name, summary_df in correlation_summaries.items():
        summary_export = summary_df.copy()
        summary_export.insert(0, "Section", f"Q3_{summary_name}")
        export_frames.append(summary_export)

    combined = pd.concat(export_frames, ignore_index=True, sort=False)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(path, index=False)
    logger.info("Exported analysis results to %s (%d rows)", path, len(combined))
    return path


def run_analysis(
    master_path: Path | str = "master_dataset.csv",
    output_path: Path | str = "analysis_results.csv",
    start_year: int = _DEFAULT_START_YEAR,
    end_year: int = _DEFAULT_END_YEAR,
) -> dict[str, pd.DataFrame]:
    """Execute the full statistical analysis pipeline.

    Args:
        master_path: Path to the master dataset CSV.
        output_path: Path for exported results.
        start_year: Baseline year for income-group comparisons.
        end_year: Comparison year for income-group comparisons.

    Returns:
        Dictionary of result DataFrames keyed by analysis name.
    """
    try:
        master_df = load_master_dataset(master_path)
        income_mapping = fetch_country_income_groups()
    except (DataLoadError, MetadataFetchError) as exc:
        raise PipelineError("Analysis pipeline failed during data loading.") from exc

    gap_results = analyze_income_group_gender_gap_change(
        master_df, start_year=start_year, end_year=end_year
    )
    variability_results = analyze_income_group_variability_change(
        master_df, income_mapping, start_year=start_year, end_year=end_year
    )
    correlations = compute_country_correlations(master_df)
    correlation_summaries = summarize_correlation_extremes(correlations)

    export_analysis_results(
        gap_results,
        variability_results,
        correlations,
        correlation_summaries,
        output_path=output_path,
    )

    return {
        "gender_gap_change": gap_results,
        "variability_change": variability_results,
        "correlations": correlations,
        **correlation_summaries,
    }


if __name__ == "__main__":
    configure_logging()
    results = run_analysis()

    gap_winner = results["gender_gap_change"].loc[
        results["gender_gap_change"]["Largest_Change"], "Income_Group"
    ].iloc[0]
    variability_winner = results["variability_change"].loc[
        results["variability_change"]["Largest_Change"], "Income_Group"
    ].iloc[0]

    print("=== Question 1: Gender gap change by income group ===")
    print(results["gender_gap_change"].to_string(index=False))
    print(f"\nAnswer: {gap_winner}")

    print("\n=== Question 2: Life expectancy variability change ===")
    print(results["variability_change"].to_string(index=False))
    print(f"\nAnswer: {variability_winner}")

    print("\n=== Question 3: Fertility vs life expectancy correlations ===")
    print("\nHighest positive:")
    print(results["highest_positive"][["Country", "Correlation"]].to_string(index=False))
    print("\nHighest negative:")
    print(results["highest_negative"][["Country", "Correlation"]].to_string(index=False))
    print("\nLowest absolute:")
    print(results["lowest_absolute"][["Country", "Correlation"]].to_string(index=False))
