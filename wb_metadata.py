"""World Bank country metadata client with caching and error handling."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import pandas as pd
import requests

from config import (
    CACHE_DIR,
    INCOME_GROUPS,
    REGIONS,
    WB_API_TIMEOUT,
    WB_COUNTRY_API,
    WB_COUNTRY_CACHE_PATH,
)
from exceptions import MetadataFetchError

logger = logging.getLogger(__name__)


def _parse_country_payload(payload: Any) -> list[dict[str, Any]]:
    """Extract the country list from a World Bank API JSON payload."""
    if not isinstance(payload, list) or len(payload) < 2:
        raise MetadataFetchError("Unexpected World Bank API response format.")
    countries = payload[1]
    if not isinstance(countries, list):
        raise MetadataFetchError("World Bank API did not return a country list.")
    return countries


def _fetch_countries_from_api() -> list[dict[str, Any]]:
    """Download country metadata from the World Bank API."""
    logger.info("Fetching country metadata from World Bank API")
    try:
        response = requests.get(
            WB_COUNTRY_API,
            params={"format": "json", "per_page": 400},
            timeout=WB_API_TIMEOUT,
        )
        response.raise_for_status()
        return _parse_country_payload(response.json())
    except requests.RequestException as exc:
        raise MetadataFetchError(
            "Unable to retrieve World Bank country metadata."
        ) from exc


def _load_cached_countries() -> list[dict[str, Any]] | None:
    """Load cached country metadata from disk when available."""
    if not WB_COUNTRY_CACHE_PATH.exists():
        return None
    try:
        return json.loads(WB_COUNTRY_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring invalid metadata cache: %s", exc)
        return None


def _save_country_cache(countries: list[dict[str, Any]]) -> None:
    """Persist country metadata to the local cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    WB_COUNTRY_CACHE_PATH.write_text(
        json.dumps(countries, ensure_ascii=True),
        encoding="utf-8",
    )
    logger.info("Cached World Bank metadata at %s", WB_COUNTRY_CACHE_PATH)


@lru_cache(maxsize=1)
def get_world_bank_countries(*, refresh: bool = False) -> tuple[dict[str, Any], ...]:
    """Return cached World Bank country metadata records."""
    if refresh:
        countries = _fetch_countries_from_api()
        _save_country_cache(countries)
        return tuple(countries)

    cached = _load_cached_countries()
    if cached is not None:
        logger.debug("Loaded World Bank metadata from cache")
        return tuple(cached)

    countries = _fetch_countries_from_api()
    _save_country_cache(countries)
    return tuple(countries)


def get_aggregate_country_codes() -> frozenset[str]:
    """Return ISO codes for World Bank aggregate entities."""
    countries = get_world_bank_countries()
    return frozenset(
        country["id"]
        for country in countries
        if country.get("incomeLevel", {}).get("value") == "Aggregates"
    )


def fetch_country_income_groups() -> pd.DataFrame:
    """Fetch country-to-income-group mappings."""
    records: list[dict[str, str]] = []
    for country in get_world_bank_countries():
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
    logger.info("Prepared income groups for %d countries", len(mapping))
    return mapping


def fetch_country_metadata() -> tuple[pd.DataFrame, frozenset[str]]:
    """Return enriched country metadata and aggregate ISO codes."""
    income_mapping = fetch_country_income_groups()
    region_records: list[dict[str, str]] = []

    for country in get_world_bank_countries():
        region_value = country.get("region", {}).get("value", "").strip()
        if region_value in ("", "Aggregates", "Not classified"):
            continue
        region_records.append(
            {
                "Country_Code": country["id"],
                "Region": region_value,
            }
        )

    region_mapping = pd.DataFrame(region_records)
    metadata = income_mapping.merge(region_mapping, on="Country_Code", how="left")
    metadata = metadata[
        metadata["Income_Group"].isin(INCOME_GROUPS)
        & metadata["Region"].isin(REGIONS)
    ].copy()

    logger.info("Prepared dashboard metadata for %d countries", len(metadata))
    return metadata, get_aggregate_country_codes()
