#!/usr/bin/env python3
"""Export static visualization and dashboard screenshot assets."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from analysis import load_master_dataset  # noqa: E402
from config import FIGURES_DIR, MASTER_DATASET_PATH, SCREENSHOTS_DIR  # noqa: E402
from dashboard.components.charts import (  # noqa: E402
    create_death_rate_trend,
    create_fertility_trend,
    create_gender_life_expectancy_trend,
    create_income_group_comparison,
    create_life_expectancy_trend,
    create_region_comparison,
)
from dashboard.services.data_service import (  # noqa: E402
    _prepare_country_dataframe,
    filter_country_data,
    get_income_aggregate_data,
    get_region_aggregate_data,
)
from logging_config import configure_logging, get_logger  # noqa: E402
from visualizations import run_visualizations  # noqa: E402
from wb_metadata import fetch_country_metadata  # noqa: E402

logger = get_logger(__name__)

ROOT_ASSETS = (
    "life_expectancy_trend.html",
    "life_expectancy_trend.png",
    "world_map.html",
    "world_map.png",
    "sankey.html",
    "sankey.png",
)


def migrate_root_assets() -> None:
    """Move legacy root-level visualization exports into outputs/figures."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for asset_name in ROOT_ASSETS:
        source = ROOT_DIR / asset_name
        if source.exists():
            destination = FIGURES_DIR / asset_name
            shutil.move(str(source), str(destination))
            logger.info("Moved %s -> %s", source.name, destination)


def export_dashboard_screenshots() -> None:
    """Render representative dashboard charts and save PNG screenshots."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    master_df = load_master_dataset(MASTER_DATASET_PATH)
    metadata, aggregate_codes = fetch_country_metadata()
    country_df = _prepare_country_dataframe(master_df, metadata, aggregate_codes)

    filters = {
        "countries": ["India", "China", "United States"],
        "income_groups": metadata["Income_Group"].unique().tolist(),
        "regions": metadata["Region"].unique().tolist(),
        "year_range": (2000, 2023),
    }
    filtered_df = filter_country_data(country_df, **filters)
    year_range = filters["year_range"]
    end_year = year_range[1]

    exports = {
        "dashboard_life_expectancy_trend.png": create_life_expectancy_trend(filtered_df),
        "dashboard_fertility_trend.png": create_fertility_trend(filtered_df),
        "dashboard_death_rate_trend.png": create_death_rate_trend(filtered_df),
        "dashboard_gender_comparison.png": create_gender_life_expectancy_trend(
            filtered_df
        ),
        "dashboard_region_comparison.png": create_region_comparison(
            get_region_aggregate_data(master_df, year_range, filters["regions"]),
            end_year,
        ),
        "dashboard_income_comparison.png": create_income_group_comparison(
            get_income_aggregate_data(master_df, year_range, filters["income_groups"]),
            end_year,
        ),
    }

    for filename, figure in exports.items():
        output_path = SCREENSHOTS_DIR / filename
        figure.write_image(str(output_path), width=1280, height=720, scale=2)
        logger.info("Exported dashboard screenshot: %s", output_path)


def main() -> None:
    """Generate all output assets for submission."""
    configure_logging()
    migrate_root_assets()
    run_visualizations(output_dir=FIGURES_DIR)
    export_dashboard_screenshots()
    logger.info("Asset export complete")


if __name__ == "__main__":
    main()
