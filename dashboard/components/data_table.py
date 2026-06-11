"""Data table component for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

DISPLAY_COLUMNS = [
    "Country",
    "Country_Code",
    "Region",
    "Income_Group",
    "Year",
    "Life_Expectancy_Total",
    "Life_Expectancy_Male",
    "Life_Expectancy_Female",
    "Fertility_Rate",
    "Death_Rate",
]

COLUMN_LABELS = {
    "Country_Code": "Code",
    "Income_Group": "Income Group",
    "Life_Expectancy_Total": "Life Expectancy",
    "Life_Expectancy_Male": "Male LE",
    "Life_Expectancy_Female": "Female LE",
    "Fertility_Rate": "Fertility Rate",
    "Death_Rate": "Death Rate",
}


def render_data_table(filtered_df: pd.DataFrame) -> None:
    """Render a searchable, sortable data table with CSV export."""
    st.markdown('<p class="section-title">Data Table</p>', unsafe_allow_html=True)

    display_df = filtered_df[DISPLAY_COLUMNS].rename(columns=COLUMN_LABELS)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered data (CSV)",
        data=csv_data,
        file_name="health_indicators_filtered.csv",
        mime="text/csv",
        use_container_width=False,
    )
