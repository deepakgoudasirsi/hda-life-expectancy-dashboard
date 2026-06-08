"""World Bank indicator data loading utilities.

This module downloads and loads World Bank Development Indicators (WDI)
CSV files for life expectancy, fertility, and death-rate datasets used
in the HDA life-expectancy analysis pipeline.
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from typing import Final

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# World Bank API base URL for bulk CSV downloads (returns a ZIP archive).
_WB_API_BASE: Final[str] = "https://api.worldbank.org/v2/en/indicator"

# Indicator metadata: code, human-readable name, and output filename stem.
INDICATORS: Final[dict[str, dict[str, str]]] = {
    "life_expectancy_total": {
        "code": "SP.DYN.LE00.IN",
        "name": "Life expectancy at birth, total (years)",
        "filename": "life_expectancy_total.csv",
    },
    "life_expectancy_male": {
        "code": "SP.DYN.LE00.MA.IN",
        "name": "Life expectancy at birth, male (years)",
        "filename": "life_expectancy_male.csv",
    },
    "life_expectancy_female": {
        "code": "SP.DYN.LE00.FE.IN",
        "name": "Life expectancy at birth, female (years)",
        "filename": "life_expectancy_female.csv",
    },
    "fertility_rate": {
        "code": "SP.DYN.TFRT.IN",
        "name": "Fertility rate, total (births per woman)",
        "filename": "fertility_rate.csv",
    },
    "death_rate": {
        "code": "SP.DYN.CDRT.IN",
        "name": "Death rate, crude (per 1,000 people)",
        "filename": "death_rate.csv",
    },
}

# World Bank WDI exports include four metadata rows before the data header.
_METADATA_SKIP_ROWS: Final[int] = 4

# Expected wide-format column names in raw WDI CSV files.
_ID_COLUMNS: Final[list[str]] = [
    "Country Name",
    "Country Code",
    "Indicator Name",
    "Indicator Code",
]


def _download_indicator_csv(indicator_code: str, timeout: int = 120) -> bytes:
    """Download the ZIP archive for a single World Bank indicator.

    Args:
        indicator_code: WDI indicator code (e.g. ``SP.DYN.LE00.IN``).
        timeout: HTTP request timeout in seconds.

    Returns:
        Raw bytes of the primary data CSV extracted from the ZIP archive.

    Raises:
        requests.HTTPError: If the download request fails.
        ValueError: If the ZIP archive does not contain a data CSV file.
    """
    url = f"{_WB_API_BASE}/{indicator_code}?downloadformat=csv"
    logger.info("Downloading indicator %s from %s", indicator_code, url)

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        data_files = [
            name
            for name in archive.namelist()
            if name.startswith("API_") and name.endswith(".csv")
        ]
        if not data_files:
            raise ValueError(
                f"No data CSV found in ZIP archive for indicator {indicator_code}"
            )

        data_filename = data_files[0]
        logger.debug(
            "Extracted %s from archive for indicator %s",
            data_filename,
            indicator_code,
        )
        return archive.read(data_filename)


def _read_world_bank_csv(csv_bytes: bytes) -> pd.DataFrame:
    """Parse a raw World Bank WDI CSV export into a wide-format DataFrame.

    Args:
        csv_bytes: Raw CSV content from a World Bank ZIP download.

    Returns:
        Wide-format DataFrame with country/indicator metadata and year columns.
    """
    df = pd.read_csv(
        io.BytesIO(csv_bytes),
        skiprows=_METADATA_SKIP_ROWS,
        encoding="utf-8-sig",
    )

    # Normalize column names and strip whitespace from string fields.
    df.columns = df.columns.astype(str).str.strip()
    for column in _ID_COLUMNS:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    # Drop completely empty trailing columns that sometimes appear in exports.
    df = df.dropna(axis=1, how="all")

    logger.info(
        "Loaded wide-format dataset: %d rows, %d columns",
        len(df),
        len(df.columns),
    )
    return df


def load_world_bank_csv(path: Path | str) -> pd.DataFrame:
    """Load a World Bank WDI CSV file from disk.

    Args:
        path: Path to a locally saved World Bank CSV export.

    Returns:
        Wide-format DataFrame with country/indicator metadata and year columns.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    logger.info("Loading World Bank CSV from %s", file_path)
    df = pd.read_csv(
        file_path,
        skiprows=_METADATA_SKIP_ROWS,
        encoding="utf-8-sig",
    )
    df.columns = df.columns.astype(str).str.strip()
    for column in _ID_COLUMNS:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    df = df.dropna(axis=1, how="all")
    logger.info(
        "Loaded wide-format dataset from disk: %d rows, %d columns",
        len(df),
        len(df.columns),
    )
    return df


def download_indicator(
    indicator_key: str,
    raw_dir: Path | str,
    *,
    force: bool = False,
) -> pd.DataFrame:
    """Download (or load from cache) a single indicator dataset.

    Args:
        indicator_key: Key in :data:`INDICATORS` (e.g. ``life_expectancy_total``).
        raw_dir: Directory where raw CSV files are stored.
        force: When ``True``, re-download even if a cached file exists.

    Returns:
        Wide-format DataFrame for the requested indicator.

    Raises:
        KeyError: If ``indicator_key`` is not a known indicator.
    """
    if indicator_key not in INDICATORS:
        raise KeyError(
            f"Unknown indicator key '{indicator_key}'. "
            f"Valid keys: {sorted(INDICATORS)}"
        )

    metadata = INDICATORS[indicator_key]
    raw_path = Path(raw_dir) / metadata["filename"]

    if raw_path.exists() and not force:
        logger.info("Using cached file for %s at %s", indicator_key, raw_path)
        return load_world_bank_csv(raw_path)

    csv_bytes = _download_indicator_csv(metadata["code"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(csv_bytes)
    logger.info("Saved raw CSV for %s to %s", indicator_key, raw_path)

    return _read_world_bank_csv(csv_bytes)


def load_life_expectancy_total(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Load life expectancy at birth (total) data."""
    return download_indicator(
        "life_expectancy_total", raw_dir, force=force_download
    )


def load_life_expectancy_male(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Load life expectancy at birth (male) data."""
    return download_indicator(
        "life_expectancy_male", raw_dir, force=force_download
    )


def load_life_expectancy_female(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Load life expectancy at birth (female) data."""
    return download_indicator(
        "life_expectancy_female", raw_dir, force=force_download
    )


def load_fertility_rate(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Load total fertility rate data."""
    return download_indicator("fertility_rate", raw_dir, force=force_download)


def load_death_rate(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Load crude death rate data."""
    return download_indicator("death_rate", raw_dir, force=force_download)


def load_all_indicators(
    raw_dir: Path | str = "data/raw",
    *,
    force_download: bool = False,
) -> dict[str, pd.DataFrame]:
    """Load all assignment indicators into a dictionary of wide DataFrames.

    Args:
        raw_dir: Directory for cached raw CSV files.
        force_download: When ``True``, re-download all indicators from the API.

    Returns:
        Mapping of indicator keys to wide-format DataFrames.
    """
    logger.info("Loading all World Bank indicators (force_download=%s)", force_download)
    datasets: dict[str, pd.DataFrame] = {}

    for indicator_key in INDICATORS:
        datasets[indicator_key] = download_indicator(
            indicator_key,
            raw_dir,
            force=force_download,
        )

    logger.info("Successfully loaded %d indicator datasets", len(datasets))
    return datasets


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging for the data pipeline."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    configure_logging()
    frames = load_all_indicators()
    for name, frame in frames.items():
        print(f"{name}: {frame.shape}")
