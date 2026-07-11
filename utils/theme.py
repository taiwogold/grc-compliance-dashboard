"""
Theme Module - Full Dark/Light Mode Toggle
Version: 3.3.1
Author: Taiwo Durodola-Tunde

Provides a fully working dark/light mode toggle that controls
EVERY visual element in the dashboard — backgrounds, text,
cards, charts, tables, sidebar, tabs, buttons, borders.

How it works:
    Streamlit's config.toml sets the base theme, but we override
    it completely via comprehensive CSS injection that covers all
    Streamlit internal class names. Charts use transparent
    backgrounds so they inherit the page colour automatically.

Usage:
    from utils.theme import get_theme, get_custom_css, apply_chart_theme
"""

import streamlit as st


# ==========================================================
# COLOUR PALETTES — Saturated for both backgrounds
# ==========================================================

RISK_LEVEL_COLOURS = {
    "High": "#ef5350",
    "Medium": "#ffca28",
    "Low": "#66bb6a",
}

ESCALATION_COLOURS = {
    "Level 1 - Owner Reminder": "#ffca28",
    "Level 2 - Manager Escalation": "#ff9800",
    "Level 3 - Director Escalation": "#ef5350",
    "Level 4 - Executive Escalation": "#ab47bc",
}

SCORE_BAND_COLOURS = {
    "Critical": "#ab47bc",
    "High": "#ef5350",
    "Medium": "#ffca28",
    "Low": "#66bb6a",
}


# ==========================================================
# THEME DEFINITIONS
# ==========================================================

THEMES = {
    "light": {
        "name": "Light",
        # Page
        "bg_primary": "#ffffff",
        "bg_secondary": "#f0f2f6",
        "bg_card": "#ffffff",
        "bg_sidebar": "#f8f9fc",
        # Text
        "text_primary": "#1e1e1e",
        "text_secondary": "#555555",
        "text_muted": "#888888",
        # Accents
        "accent": "#1a237e",
        "accent_light": "#e8eaf6",
        "border": "rgba(0, 0, 0, 0.08)",
        "shadow": "rgba(0, 0, 0, 0.04)",
        # Charts
        "plotly_template": "plotly_white",
        "chart_bg": "rgba(0,0,0,0)",
        "chart_text": "#1e1e1e",
        "chart_grid": "#e8e8e8",
        "trend_line": "#1a237e",
        # Components
        "tab_active_bg": "#ffffff",
        "tab_hover_bg": "#f0f2f6",
        "input_bg": "#ffffff",
        "input_border": "#d1d5db",
        "button_bg": "#1a237e",
        "button_text": "#ffffff",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
    },
    "dark": {
        "name": "Dark",
        # Page
        "bg_primary": "#0e1117",
        "bg_secondary": "#161b22",
        "bg_card": "#1c2128",
        "bg_sidebar": "#161b22",
        # Text
        "text_primary": "#e6edf3",
        "text_secondary": "#b1bac4",
        "text_muted": "#768390",
        # Accents
        "accent": "#58a6ff",
        "accent_light": "#1c3a5c",
        "border": "rgba(255, 255, 255, 0.08)",
        "shadow": "rgba(0, 0, 0, 0.3)",
        # Charts
        "plotly_template": "plotly_dark",
        "chart_bg": "rgba(0,0,0,0)",
        "chart_text": "#e6edf3",
        "chart_grid": "#2d333b",
        "trend_line": "#58a6ff",
        # Components
        "tab_active_bg": "#1c2128",
        "tab_hover_bg": "#21262d",
        "input_bg": "#1c2128",
        "input_border": "#363b42",
        "button_bg": "#58a6ff",
        "button_text": "#0e1117",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
    },
}


def get_theme(theme_name: str = "light") -> dict:
    """Return theme config dictionary."""
    return THEMES.get(theme_name, THEMES["light"])


def get_available_themes() -> list:
    """List available theme names."""
    return list(THEMES.keys())


def apply_chart_theme(fig, theme: dict):
    """
    Apply theme to a Plotly figure with transparent background.

    Charts use transparent bg so they inherit page colour.
    """
    fig.update_layout(
        template=theme["plotly_template"],
        paper_bgcolor=theme["chart_bg"],
        plot_bgcolor=theme["chart_bg"],
        font=dict(color=theme["chart_text"]),
        title_font=dict(color=theme["accent"]),
        xaxis=dict(gridcolor=theme["chart_grid"]),
        yaxis=dict(gridcolor=theme["chart_grid"]),
    )
    return fig


def get_custom_css(theme: dict) -> str:
    """
    Generate COMPREHENSIVE CSS that overrides every Streamlit element.

    This is a full theme override — not partial. Covers:
    backgrounds, text, sidebar, tabs, inputs, buttons, metrics,
    dataframes, alerts, expanders, and all component states.
    """

    t = theme  # shorthand

    return f"""
    <style>
        /* ===== ROOT OVERRIDES ===== */
        .stApp {{
            background-color: {t['bg_primary']} !important;
            color: {t['text_primary']} !important;
        }}

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {{
            background-color: {t['bg_sidebar']} !important;
        }}
        section[data-testid="stSidebar"] * {{
            color: {t['text_primary']} !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown p {{
            color: {t['text_primary']} !important;
        }}

        /* ===== HEADERS ===== */
        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
            color: {t['text_primary']} !important;
        }}

        /* ===== TEXT ===== */
        p, span, label, .stMarkdown, .stCaption,
        [data-testid="stMarkdownContainer"] p {{
            color: {t['text_primary']} !important;
        }}
        .stCaption, small {{
            color: {t['text_muted']} !important;
        }}

        /* ===== METRIC CARDS ===== */
        [data-testid="stMetric"] {{
            background-color: {t['bg_card']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            box-shadow: 0 2px 8px {t['shadow']} !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {t['text_primary']} !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {t['text_secondary']} !important;
        }}
        [data-testid="stMetricDelta"] {{
            font-weight: 600 !important;
        }}

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {t['bg_secondary']} !important;
            border-radius: 12px !important;
            padding: 4px !important;
            gap: 4px !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent !important;
            color: {t['text_secondary']} !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            font-weight: 500 !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {t['tab_active_bg']} !important;
            color: {t['accent']} !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 4px {t['shadow']} !important;
        }}
        .stTabs [data-baseweb="tab-highlight"] {{
            background-color: {t['accent']} !important;
        }}
        .stTabs [data-baseweb="tab-panel"] {{
            padding-top: 1.5rem !important;
        }}

        /* ===== DATAFRAMES ===== */
        [data-testid="stDataFrame"],
        .stDataFrame {{
            border: 1px solid {t['border']} !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }}

        /* ===== INPUTS ===== */
        .stTextInput input, .stSelectbox select,
        .stTextArea textarea, .stNumberInput input {{
            background-color: {t['input_bg']} !important;
            border-color: {t['input_border']} !important;
            color: {t['text_primary']} !important;
            border-radius: 8px !important;
        }}
        .stMultiSelect [data-baseweb="tag"] {{
            background-color: {t['accent_light']} !important;
        }}

        /* ===== BUTTONS ===== */
        .stButton > button {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            border: 1px solid {t['border']} !important;
            transition: all 0.2s ease !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px {t['shadow']} !important;
        }}
        .stDownloadButton > button {{
            border-radius: 8px !important;
            font-weight: 500 !important;
        }}

        /* ===== ALERTS ===== */
        .stAlert {{
            border-radius: 10px !important;
            border-left-width: 4px !important;
        }}

        /* ===== EXPANDERS ===== */
        .streamlit-expanderHeader {{
            color: {t['text_primary']} !important;
            font-weight: 600 !important;
            background-color: {t['bg_secondary']} !important;
            border-radius: 8px !important;
        }}

        /* ===== DIVIDERS ===== */
        hr {{
            border-color: {t['border']} !important;
            opacity: 0.5 !important;
        }}

        /* ===== CHECKBOX & TOGGLE ===== */
        .stCheckbox label span {{
            color: {t['text_primary']} !important;
        }}

        /* ===== FILE UPLOADER ===== */
        [data-testid="stFileUploader"] {{
            border: 2px dashed {t['border']} !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }}

        /* ===== PLOTLY CHARTS ===== */
        .js-plotly-plot .plotly .main-svg {{
            background: transparent !important;
        }}

        /* ===== SELECTBOX DROPDOWN ===== */
        [data-baseweb="select"] {{
            background-color: {t['input_bg']} !important;
        }}
        [data-baseweb="menu"] {{
            background-color: {t['bg_card']} !important;
        }}
        [data-baseweb="menu"] li {{
            color: {t['text_primary']} !important;
        }}
    </style>
    """
