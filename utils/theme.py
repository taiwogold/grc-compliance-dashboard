"""
Theme Module - Dashboard Theming & Dark Mode
Version: 2.2.0
Author: Taiwo Durodola-Tunde

Provides light and dark theme configurations for the GRC
dashboard. Controls Plotly chart backgrounds, text colours,
grid colours, and font styling to ensure consistent appearance
across both modes.

Usage:
    from utils.theme import get_theme, apply_chart_theme

    theme = get_theme("dark")
    fig = apply_chart_theme(fig, theme)

Functions:
    get_theme: Return a theme configuration dictionary.
    apply_chart_theme: Apply theme to a Plotly figure.
    get_available_themes: List available theme names.
"""


# ==========================================================
# THEME DEFINITIONS
# ==========================================================

THEMES = {
    "light": {
        "name": "Light",
        "background": "#ffffff",
        "paper_bg": "#ffffff",
        "plot_bg": "#f8f9fa",
        "text_color": "#212529",
        "grid_color": "#dee2e6",
        "font_family": "Inter, sans-serif",
        "title_color": "#1a237e",
        "accent_primary": "#1a237e",
        "accent_secondary": "#283593",
        "card_bg": "#f8f9fa",
        "border_color": "#dee2e6",
        # Plotly template
        "plotly_template": "plotly_white",
        # Trend line colour
        "trend_line_color": "#1a237e",
    },
    "dark": {
        "name": "Dark",
        "background": "#0e1117",
        "paper_bg": "#1e1e2e",
        "plot_bg": "#1e1e2e",
        "text_color": "#e0e0e0",
        "grid_color": "#333344",
        "font_family": "Inter, sans-serif",
        "title_color": "#90caf9",
        "accent_primary": "#90caf9",
        "accent_secondary": "#64b5f6",
        "card_bg": "#1e1e2e",
        "border_color": "#333344",
        # Plotly template
        "plotly_template": "plotly_dark",
        # Trend line colour
        "trend_line_color": "#90caf9",
    },
}

# Risk level colours — consistent across both themes
# These are saturated enough to work on both backgrounds
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
# THEME FUNCTIONS
# ==========================================================

def get_theme(theme_name: str = "light") -> dict:
    """
    Return a theme configuration dictionary.

    Args:
        theme_name: Either 'light' or 'dark'.
            Defaults to 'light'.

    Returns:
        dict: Full theme configuration with all colour values.
    """

    if theme_name not in THEMES:
        theme_name = "light"

    return THEMES[theme_name]


def get_available_themes() -> list:
    """
    List available theme names.

    Returns:
        list: Theme name strings.
    """

    return list(THEMES.keys())


def apply_chart_theme(fig, theme: dict):
    """
    Apply theme styling to a Plotly figure.

    Updates the figure's layout with theme-appropriate
    backgrounds, text colours, grid colours, and fonts.

    Args:
        fig: Plotly figure object to style.
        theme: Theme configuration dictionary from get_theme().

    Returns:
        The same figure object with updated styling.
    """

    fig.update_layout(
        template=theme["plotly_template"],
        paper_bgcolor=theme["paper_bg"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(
            family=theme["font_family"],
            color=theme["text_color"]
        ),
        title_font=dict(
            color=theme["title_color"]
        ),
        xaxis=dict(
            gridcolor=theme["grid_color"],
            linecolor=theme["grid_color"]
        ),
        yaxis=dict(
            gridcolor=theme["grid_color"],
            linecolor=theme["grid_color"]
        ),
    )

    return fig


def get_custom_css(theme: dict) -> str:
    """
    Generate custom CSS for Streamlit based on the active theme.

    Applies background colours, text colours, and card styling
    to Streamlit's UI elements via markdown injection.

    Args:
        theme: Theme configuration dictionary.

    Returns:
        str: CSS string to inject via st.markdown.
    """

    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {theme['background']};
        }}

        /* Metric cards */
        [data-testid="stMetric"] {{
            background-color: {theme['card_bg']};
            border: 1px solid {theme['border_color']};
            border-radius: 8px;
            padding: 12px 16px;
        }}

        [data-testid="stMetricLabel"] {{
            color: {theme['text_color']};
        }}

        /* Dataframe styling */
        [data-testid="stDataFrame"] {{
            border: 1px solid {theme['border_color']};
            border-radius: 4px;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {theme['paper_bg']};
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['title_color']} !important;
        }}

        /* Info boxes */
        .stAlert {{
            border-radius: 8px;
        }}
    </style>
    """
