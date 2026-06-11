"""Data preprocessing and merging for World Bank life-expectancy datasets.

Transforms wide-format World Bank exports into a single long-format master
dataset suitable for downstream analysis and dashboard development.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd

from config import MASTER_COLUMNS
from data_loader import INDICATORS, configure_logging, load_all_indicators
from exceptions import PipelineError

logger = logging.getLogger(__name__)

# Standard long-format column names required by the assignment.
LONG_FORMAT_COLUMNS: Final[list[str]] = [
    "Country Name",
    "Country Code",
    "Indicator Name",
    "Indicator Code",
    "Year",
    "Value",
]

# Mapping from loader keys to master-dataset value column names.
_VALUE_COLUMN_MAP: Final[dict[str, str]] = {
    "life_expectancy_total": "Life_Expectancy_Total",
    "life_expectancy_male": "Life_Expectancy_Male",
    "life_expectancy_female": "Life_Expectancy_Female",
    "fertility_rate": "Fertility_Rate",
    "death_rate": "Death_Rate",
}

_ID_VARS: Final[list[str]] = [
    "Country Name",
    "Country Code",
    "Indicator Name",
    "Indicator Code",
]


def wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a wide-format World Bank DataFrame to long format.

    Args:
        df: Wide-format DataFrame with year columns (e.g. ``1960``, ``2023``).

    Returns:
        Long-format DataFrame with columns:
        Country Name, Country Code, Indicator Name, Indicator Code, Year, Value.
    """
    year_columns = [
        column
        for column in df.columns
        if column not in _ID_VARS and str(column).strip().isdigit()
    ]

    if not year_columns:
        raise ValueError("No year columns found in wide-format DataFrame")

    long_df = df.melt(
        id_vars=_ID_VARS,
        value_vars=year_columns,
        var_name="Year",
        value_name="Value",
    )

    long_df["Year"] = pd.to_numeric(long_df["Year"], errors="coerce").astype("Int64")
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")

    # Drop rows with missing year or value after coercion.
    before_rows = len(long_df)
    long_df = long_df.dropna(subset=["Year", "Value"]).copy()
    long_df["Year"] = long_df["Year"].astype(int)

    logger.info(
        "Converted wide to long: %d -> %d rows (%d rows dropped for missing values)",
        before_rows,
        len(long_df),
        before_rows - len(long_df),
    )

    return long_df[LONG_FORMAT_COLUMNS]


def _prepare_indicator_frame(
    wide_df: pd.DataFrame,
    indicator_key: str,
) -> pd.DataFrame:
    """Transform one indicator from wide to a slim long-format frame.

    Args:
        wide_df: Wide-format source DataFrame.
        indicator_key: Key in :data:`INDICATORS` and :data:`_VALUE_COLUMN_MAP`.

    Returns:
        DataFrame with Country, Country_Code, Year, and one value column.
    """
    value_column = _VALUE_COLUMN_MAP[indicator_key]
    long_df = wide_to_long(wide_df)

    slim_df = long_df.rename(
        columns={
            "Country Name": "Country",
            "Country Code": "Country_Code",
            "Value": value_column,
        }
    )[["Country", "Country_Code", "Year", value_column]]

    logger.info(
        "Prepared %s (%s): %d rows",
        indicator_key,
        INDICATORS[indicator_key]["code"],
        len(slim_df),
    )
    return slim_df


def merge_datasets(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all indicator datasets into a single master DataFrame.

    Args:
        datasets: Mapping of indicator keys to wide-format DataFrames.

    Returns:
        Master DataFrame with one row per country-year and all indicator values.

    Raises:
        KeyError: If a required indicator key is missing from ``datasets``.
    """
    missing_keys = set(_VALUE_COLUMN_MAP) - set(datasets)
    if missing_keys:
        raise KeyError(f"Missing required datasets: {sorted(missing_keys)}")

    prepared_frames = [
        _prepare_indicator_frame(datasets[key], key) for key in _VALUE_COLUMN_MAP
    ]

    master_df = prepared_frames[0]
    for frame in prepared_frames[1:]:
        master_df = master_df.merge(
            frame,
            on=["Country", "Country_Code", "Year"],
            how="outer",
        )

    master_df = master_df[MASTER_COLUMNS].sort_values(
        ["Country", "Year"]
    ).reset_index(drop=True)

    logger.info(
        "Built master dataset: %d rows, %d countries, years %d-%d",
        len(master_df),
        master_df["Country_Code"].nunique(),
        master_df["Year"].min(),
        master_df["Year"].max(),
    )
    return master_df


def build_master_dataset(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Run the full preprocessing pipeline and return the master DataFrame.

    Args:
        raw_dir: Directory containing (or receiving) raw CSV files.
        force_download: When ``True``, re-download all indicators from the API.

    Returns:
        Clean, merged master DataFrame.
    """
    logger.info("Starting master dataset build")
    try:
        datasets = load_all_indicators(raw_dir, force_download=force_download)
        master_df = merge_datasets(datasets)
    except (KeyError, ValueError, OSError) as exc:
        raise PipelineError("Master dataset build failed.") from exc
    return master_df


def save_master_dataset(
    master_df: pd.DataFrame,
    output_path: Path | str = "master_dataset.csv",
) -> Path:
    """Persist the master dataset to CSV.

    Args:
        master_df: Master DataFrame to save.
        output_path: Destination CSV path.

    Returns:
        Resolved path to the written file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(path, index=False)
    logger.info("Saved master dataset to %s (%d rows)", path, len(master_df))
    return path


def run_pipeline(
    raw_dir: Path | str = "data/raw",
    output_path: Path | str = "master_dataset.csv",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Execute the complete data pipeline.

    Args:
        raw_dir: Directory for raw CSV files.
        output_path: Path for the output master CSV.
        force_download: When ``True``, re-download all indicators.

    Returns:
        The generated master DataFrame.
    """
    master_df = build_master_dataset(raw_dir, force_download=force_download)
    save_master_dataset(master_df, output_path)
    return master_df


if __name__ == "__main__":
    configure_logging()
    result = run_pipeline()
    print(result.head())
    print(f"\nMaster dataset shape: {result.shape}")
