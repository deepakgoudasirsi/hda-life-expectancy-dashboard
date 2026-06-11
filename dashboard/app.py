"""NXP Global Health Indicators — Streamlit dashboard entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.charts import (  # noqa: E402
    create_death_rate_trend,
    create_fertility_trend,
    create_gender_life_expectancy_trend,
    create_income_group_comparison,
    create_life_expectancy_trend,
    create_region_comparison,
)
from dashboard.components.data_table import render_data_table  # noqa: E402
from dashboard.components.filters import render_sidebar  # noqa: E402
from dashboard.components.kpi import render_kpi_cards  # noqa: E402
from dashboard.services.data_service import (  # noqa: E402
    filter_country_data,
    get_income_aggregate_data,
    get_latest_year_data,
    get_region_aggregate_data,
    load_country_metadata,
    load_master_data,
    prepare_country_data,
)
from dashboard.styles import CUSTOM_CSS, PAGE_CONFIG, PLOTLY_CONFIG  # noqa: E402
from exceptions import DashboardError, DataLoadError, MetadataFetchError  # noqa: E402
from logging_config import configure_logging  # noqa: E402

logger = logging.getLogger(__name__)


def apply_page_style() -> None:
    """Inject global page configuration and custom styling."""
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Render the dashboard title banner."""
    st.markdown(
        """
        <div class="dashboard-header">
            <h1>NXP Global Health Indicators Dashboard</h1>
            <p>World Bank life expectancy, fertility, and mortality analytics (1960–2023)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render attribution and data-source footer."""
    st.markdown(
        """
        <div class="dashboard-footer">
            Data source: World Bank Development Indicators (WDI) ·
            Built for the NXP Life Expectancy Dashboard assignment
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_content(
    master_df,
    country_df,
    filters: dict[str, object],
) -> None:
    """Render all dashboard sections for the active filter state."""
    filtered_df = filter_country_data(country_df, **filters)
    year_range = filters["year_range"]
    end_year = year_range[1]

    st.caption(
        f"Showing {len(filtered_df):,} country-year records · "
        f"{filtered_df['Country'].nunique() if not filtered_df.empty else 0} countries"
    )

    if filtered_df.empty:
        st.warning(
            "No data matches the current filters. "
            "Adjust your selections in the sidebar or click **Reset filters**."
        )
        return

    latest_df = get_latest_year_data(filtered_df, end_year)
    render_kpi_cards(latest_df, end_year)

    overview_tab, trends_tab, comparisons_tab, data_tab = st.tabs(
        ["Overview", "Trends", "Comparisons", "Data"]
    )

    with overview_tab:
        st.markdown(
            '<p class="section-title">Life Expectancy Trend</p>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            create_life_expectancy_trend(filtered_df),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    with trends_tab:
        trend_col1, trend_col2 = st.columns(2)
        with trend_col1:
            st.markdown(
                '<p class="section-title">Fertility Trend</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                create_fertility_trend(filtered_df),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        with trend_col2:
            st.markdown(
                '<p class="section-title">Death Rate Trend</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                create_death_rate_trend(filtered_df),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

        st.markdown(
            '<p class="section-title">Male vs Female Life Expectancy Trend</p>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            create_gender_life_expectancy_trend(filtered_df),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    with comparisons_tab:
        region_df = get_region_aggregate_data(
            master_df,
            year_range,
            filters["regions"],
        )
        income_df = get_income_aggregate_data(
            master_df,
            year_range,
            filters["income_groups"],
        )
        compare_col1, compare_col2 = st.columns(2)
        with compare_col1:
            st.plotly_chart(
                create_region_comparison(region_df, end_year),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        with compare_col2:
            st.plotly_chart(
                create_income_group_comparison(income_df, end_year),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with data_tab:
        render_data_table(filtered_df)


def main() -> None:
    """Application entry point."""
    configure_logging()
    apply_page_style()
    render_header()

    try:
        with st.spinner("Initializing dashboard data…"):
            master_df = load_master_data()
            metadata, aggregate_codes = load_country_metadata()
            country_df = prepare_country_data(master_df, metadata, aggregate_codes)
    except DataLoadError as exc:
        logger.exception("Master dataset load failed")
        st.error(str(exc))
        st.stop()
    except MetadataFetchError as exc:
        logger.exception("Metadata load failed")
        st.error(str(exc))
        st.info(
            "Check your network connection. Cached metadata is used when available "
            f"at `{ROOT_DIR / 'data' / 'cache'}`."
        )
        st.stop()
    except DashboardError as exc:
        logger.exception("Dashboard initialization failed")
        st.error(str(exc))
        st.stop()

    filters = render_sidebar(country_df)

    try:
        render_dashboard_content(master_df, country_df, filters)
    except Exception as exc:
        logger.exception("Dashboard rendering failed")
        st.error("An unexpected error occurred while rendering the dashboard.")
        st.exception(exc)

    render_footer()


if __name__ == "__main__":
    main()
