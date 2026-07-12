"""
Theme Module - GovernIQ Brand System
Version: 3.4.0
Author: Taiwo Durodola-Tunde

GovernIQ brand identity with full dark/light mode support.
Professional warm amber/charcoal palette that looks like
a premium SaaS product.

Brand:
    Name: GovernIQ
    Tagline: Intelligent Governance. Clear Risk.
    Primary: Amber #F59E0B
    Dark: Charcoal #1C1917
    Light: Warm Stone #F5F5F4
"""

import streamlit as st


# ==========================================================
# GOVERNIQ COLOUR PALETTES
# ==========================================================

RISK_LEVEL_COLOURS = {
    "High": "#ef4444",
    "Medium": "#F59E0B",
    "Low": "#10b981",
}

ESCALATION_COLOURS = {
    "Level 1 - Owner Reminder": "#FCD34D",
    "Level 2 - Manager Escalation": "#F59E0B",
    "Level 3 - Director Escalation": "#ef4444",
    "Level 4 - Executive Escalation": "#92400E",
}

SCORE_BAND_COLOURS = {
    "Critical": "#92400E",
    "High": "#ef4444",
    "Medium": "#F59E0B",
    "Low": "#10b981",
}


# ==========================================================
# GOVERNIQ THEME DEFINITIONS
# ==========================================================

THEMES = {
    "light": {
        "name": "GovernIQ Light",
        # Page
        "bg_primary": "#F5F5F4",
        "bg_secondary": "#FFFBEB",
        "bg_card": "#ffffff",
        "bg_sidebar": "#ffffff",
        # Text
        "text_primary": "#1C1917",
        "text_secondary": "#57534E",
        "text_muted": "#78716C",
        # Brand
        "accent": "#F59E0B",
        "accent_hover": "#D97706",
        "accent_light": "#FEF3C7",
        "accent_dark": "#92400E",
        "border": "rgba(28, 25, 23, 0.08)",
        "shadow": "rgba(28, 25, 23, 0.06)",
        # Charts
        "plotly_template": "plotly_white",
        "chart_bg": "rgba(0,0,0,0)",
        "chart_text": "#1C1917",
        "chart_grid": "#E7E5E4",
        "trend_line": "#D97706",
        # Components
        "tab_active_bg": "#ffffff",
        "tab_hover_bg": "#FEF3C7",
        "input_bg": "#ffffff",
        "input_border": "#D6D3D1",
        "metric_bg": "#ffffff",
        "metric_border": "rgba(245, 158, 11, 0.15)",
    },
    "dark": {
        "name": "GovernIQ Dark",
        # Page
        "bg_primary": "#1C1917",
        "bg_secondary": "#292524",
        "bg_card": "#292524",
        "bg_sidebar": "#1C1917",
        # Text
        "text_primary": "#FAFAF9",
        "text_secondary": "#D6D3D1",
        "text_muted": "#A8A29E",
        # Brand
        "accent": "#F59E0B",
        "accent_hover": "#FCD34D",
        "accent_light": "#451A03",
        "accent_dark": "#FCD34D",
        "border": "rgba(255, 255, 255, 0.08)",
        "shadow": "rgba(0, 0, 0, 0.4)",
        # Charts
        "plotly_template": "plotly_dark",
        "chart_bg": "rgba(0,0,0,0)",
        "chart_text": "#FAFAF9",
        "chart_grid": "#44403C",
        "trend_line": "#FCD34D",
        # Components
        "tab_active_bg": "#292524",
        "tab_hover_bg": "#44403C",
        "input_bg": "#292524",
        "input_border": "#44403C",
        "metric_bg": "#292524",
        "metric_border": "rgba(245, 158, 11, 0.2)",
    },
}


def get_theme(theme_name: str = "light") -> dict:
    """Return GovernIQ theme configuration."""
    return THEMES.get(theme_name, THEMES["light"])


def get_available_themes() -> list:
    """List available themes."""
    return list(THEMES.keys())


def apply_chart_theme(fig, theme: dict):
    """Apply GovernIQ theme to Plotly charts."""
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
    Generate GovernIQ branded CSS for the entire dashboard.
    Comprehensive override of all Streamlit elements.
    """
    t = theme
    return f"""
    <style>
        /* ===== GOVERNIQ ROOT ===== */
        .stApp {{
            background-color: {t['bg_primary']} !important;
            color: {t['text_primary']} !important;
        }}

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {{
            background-color: {t['bg_sidebar']} !important;
            border-right: 1px solid {t['border']} !important;
        }}
        section[data-testid="stSidebar"] * {{
            color: {t['text_primary']} !important;
        }}

        /* ===== HEADERS ===== */
        h1, h2, h3, h4, h5, h6 {{
            color: {t['text_primary']} !important;
        }}
        h1 {{
            font-weight: 800 !important;
            letter-spacing: -0.5px !important;
        }}

        /* ===== BODY TEXT ===== */
        p, span, label, .stMarkdown,
        [data-testid="stMarkdownContainer"] p {{
            color: {t['text_primary']} !important;
        }}
        .stCaption, small {{
            color: {t['text_muted']} !important;
        }}

        /* ===== METRIC CARDS (GovernIQ branded) ===== */
        [data-testid="stMetric"] {{
            background-color: {t['metric_bg']} !important;
            border: 1px solid {t['metric_border']} !important;
            border-radius: 14px !important;
            padding: 18px 22px !important;
            box-shadow: 0 2px 12px {t['shadow']} !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px {t['shadow']} !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {t['text_primary']} !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {t['text_secondary']} !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            font-size: 0.7rem !important;
            letter-spacing: 0.5px !important;
        }}

        /* ===== TABS (GovernIQ amber accent) ===== */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {t['bg_secondary']} !important;
            border-radius: 14px !important;
            padding: 5px !important;
            gap: 4px !important;
            border: 1px solid {t['border']} !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent !important;
            color: {t['text_muted']} !important;
            border-radius: 10px !important;
            padding: 10px 18px !important;
            font-weight: 500 !important;
            transition: all 0.15s ease !important;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {t['tab_hover_bg']} !important;
            color: {t['text_primary']} !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {t['tab_active_bg']} !important;
            color: {t['accent']} !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 8px {t['shadow']} !important;
        }}
        .stTabs [data-baseweb="tab-highlight"] {{
            background-color: {t['accent']} !important;
        }}

        /* ===== DATAFRAMES ===== */
        [data-testid="stDataFrame"] {{
            border: 1px solid {t['border']} !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 1px 4px {t['shadow']} !important;
        }}

        /* ===== INPUTS ===== */
        .stTextInput input, .stSelectbox [data-baseweb="select"],
        .stTextArea textarea, .stNumberInput input {{
            background-color: {t['input_bg']} !important;
            border: 1px solid {t['input_border']} !important;
            color: {t['text_primary']} !important;
            border-radius: 10px !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: {t['accent']} !important;
            box-shadow: 0 0 0 2px {t['accent_light']} !important;
        }}

        /* ===== BUTTONS (GovernIQ amber) ===== */
        .stButton > button {{
            border-radius: 10px !important;
            font-weight: 600 !important;
            border: 1px solid {t['border']} !important;
            transition: all 0.2s ease !important;
        }}
        .stButton > button:hover {{
            border-color: {t['accent']} !important;
            color: {t['accent']} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px {t['shadow']} !important;
        }}
        .stDownloadButton > button {{
            background-color: {t['accent']} !important;
            color: #1C1917 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }}
        .stDownloadButton > button:hover {{
            background-color: {t['accent_hover']} !important;
            transform: translateY(-1px) !important;
        }}

        /* ===== ALERTS ===== */
        .stAlert {{
            border-radius: 12px !important;
            border-left-width: 4px !important;
        }}

        /* ===== EXPANDERS ===== */
        .streamlit-expanderHeader {{
            color: {t['text_primary']} !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
        }}

        /* ===== DIVIDERS ===== */
        hr {{
            border-color: {t['border']} !important;
        }}

        /* ===== TOGGLE ===== */
        .stCheckbox label span {{
            color: {t['text_primary']} !important;
        }}

        /* ===== FILE UPLOADER ===== */
        [data-testid="stFileUploader"] {{
            border: 2px dashed {t['accent']} !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            background-color: {t['accent_light']} !important;
        }}

        /* ===== PLOTLY TRANSPARENT ===== */
        .js-plotly-plot .plotly .main-svg {{
            background: transparent !important;
        }}

        /* ===== SELECTBOX DROPDOWN ===== */
        [data-baseweb="menu"] {{
            background-color: {t['bg_card']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 10px !important;
        }}
        [data-baseweb="menu"] li {{
            color: {t['text_primary']} !important;
        }}
        [data-baseweb="menu"] li:hover {{
            background-color: {t['accent_light']} !important;
        }}

        /* ===== MULTISELECT TAGS ===== */
        .stMultiSelect [data-baseweb="tag"] {{
            background-color: {t['accent']} !important;
            color: #1C1917 !important;
            border-radius: 6px !important;
        }}

        /* ===== SUCCESS/WARNING/ERROR BADGES ===== */
        .stSuccess {{
            border-left-color: #10b981 !important;
        }}
        .stWarning {{
            border-left-color: {t['accent']} !important;
        }}
        .stError {{
            border-left-color: #ef4444 !important;
        }}
    </style>
    """
