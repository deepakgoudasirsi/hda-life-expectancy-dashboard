"""Dashboard styling and layout configuration."""

from __future__ import annotations

from typing import Final

PAGE_CONFIG: Final[dict[str, object]] = {
    "page_title": "NXP Global Health Indicators",
    "page_icon": "🌍",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

PLOTLY_CONFIG: Final[dict[str, object]] = {
    "displayModeBar": True,
    "responsive": True,
    "scrollZoom": False,
}

CUSTOM_CSS: Final[str] = """
<style>
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    [data-testid="stSidebar"] span[data-baseweb="tag"] {
        background-color: #14b8a6 !important;
        border: 1px solid #0d9488 !important;
    }
    [data-testid="stSidebar"] span[data-baseweb="tag"] span {
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] span[data-baseweb="tag"] svg {
        fill: #0f172a !important;
    }
    [data-testid="stSidebar"] .filter-panel {
        color: #cbd5e1 !important;
    }
    .dashboard-header {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 45%, #134e4a 100%);
        padding: 1.75rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.25rem;
        box-shadow: 0 12px 32px rgba(15, 118, 110, 0.22);
    }
    .dashboard-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .dashboard-header p {
        color: #ccfbf1;
        margin: 0.35rem 0 0 0;
        font-size: 1rem;
    }
    .filter-panel {
        background: rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 4px solid #14b8a6 !important;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        height: 100%;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.1);
    }
    .kpi-label {
        color: #64748b !important;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        color: #0f172a !important;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .kpi-subtext {
        color: #94a3b8 !important;
        font-size: 0.85rem;
        margin-top: 0.35rem;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0f172a !important;
        margin: 1.25rem 0 0.75rem 0;
        padding-bottom: 0.35rem;
        border-bottom: 2px solid #14b8a6;
        display: inline-block;
    }
    .dashboard-footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
        color: #64748b !important;
        font-size: 0.85rem;
    }
    @media (max-width: 768px) {
        .dashboard-header h1 { font-size: 1.5rem; }
        .kpi-value { font-size: 1.5rem; }
    }
</style>
"""
