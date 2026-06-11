"""Shared configuration and constants for the NXP health dashboard project."""

from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
CACHE_DIR: Final[Path] = DATA_DIR / "cache"
OUTPUTS_DIR: Final[Path] = PROJECT_ROOT / "outputs"
FIGURES_DIR: Final[Path] = OUTPUTS_DIR / "figures"
SCREENSHOTS_DIR: Final[Path] = OUTPUTS_DIR / "screenshots"

MASTER_DATASET_PATH: Final[Path] = PROJECT_ROOT / "master_dataset.csv"
ANALYSIS_RESULTS_PATH: Final[Path] = PROJECT_ROOT / "analysis_results.csv"
WB_COUNTRY_CACHE_PATH: Final[Path] = CACHE_DIR / "wb_countries.json"

WB_COUNTRY_API: Final[str] = "https://api.worldbank.org/v2/country"
WB_API_TIMEOUT: Final[int] = 60

DEFAULT_START_YEAR: Final[int] = 1960
DEFAULT_END_YEAR: Final[int] = 2023

INCOME_GROUPS: Final[list[str]] = [
    "High income",
    "Upper middle income",
    "Lower middle income",
    "Low income",
]

REGIONS: Final[list[str]] = [
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East, North Africa, Afghanistan & Pakistan",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
]

INCOME_GROUP_COLORS: Final[dict[str, str]] = {
    "High income": "#1a9850",
    "Upper middle income": "#91cf60",
    "Lower middle income": "#fc8d59",
    "Low income": "#d73027",
}

REGION_COLORS: Final[dict[str, str]] = {
    "East Asia & Pacific": "#0284c7",
    "Europe & Central Asia": "#7c3aed",
    "Latin America & Caribbean": "#db2777",
    "Middle East, North Africa, Afghanistan & Pakistan": "#ea580c",
    "North America": "#059669",
    "South Asia": "#ca8a04",
    "Sub-Saharan Africa": "#dc2626",
}

MASTER_COLUMNS: Final[list[str]] = [
    "Country",
    "Country_Code",
    "Year",
    "Life_Expectancy_Total",
    "Life_Expectancy_Male",
    "Life_Expectancy_Female",
    "Fertility_Rate",
    "Death_Rate",
]
