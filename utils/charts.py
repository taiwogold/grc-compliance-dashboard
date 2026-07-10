"""
Charts Module
Version: 2.1.0
Author: Taiwo Durodola-Tunde

Generates all Plotly charts and visualisations used in the
GRC Compliance Dashboard. Centralises chart configuration
for consistent styling across the application.

Functions:
    create_compliance_trend_chart: Line chart with target line.
    create_control_pie_chart: ISO 27001 control coverage pie.
    create_risk_bar_chart: Risk level distribution bar chart.
    create_risk_status_pie: Open vs Closed pie chart.
    create_heatmap: Risk likelihood x impact heatmap.
    create_escalation_bar_chart: Escalation level distribution.
    create_overdue_timeline: Horizontal bar of days overdue.
    create_management_trend_chart: Trend with target overlay.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import (
    RISK_LEVEL_COLOURS,
    ESCALATION_COLOURS,
    SCORE_BAND_COLOURS,
    get_theme,
    apply_chart_theme,
)


# ==========================================================
# COLOUR PALETTES (imported from theme module)
# ==========================================================


# ==========================================================
# COMPLIANCE CHARTS
# ==========================================================

def create_compliance_trend_chart(trend_df):
    """
    Create a line chart showing compliance score over time.

    Args:
        trend_df: DataFrame with 'Month' and 'Score' columns.

    Returns:
        plotly.graph_objects.Figure: Configured line chart.
    """

    fig = px.line(
        trend_df,
        x="Month",
        y="Score",
        markers=True,
        title="Compliance Trend"
    )

    return fig


def create_control_pie_chart(controls_df, title="ISO 27001 Coverage"):
    """
    Create a pie chart of control implementation status.

    Args:
        controls_df: DataFrame with 'Status' column.
        title: Chart title string.

    Returns:
        plotly.graph_objects.Figure: Pie chart figure.
    """

    return px.pie(
        controls_df,
        names="Status",
        title=title
    )


# ==========================================================
# RISK CHARTS
# ==========================================================

def create_risk_bar_chart(risk_df):
    """
    Create a bar chart showing risk level distribution.

    Colour-coded by severity: High=red, Medium=amber, Low=green.

    Args:
        risk_df: DataFrame with 'Risk_Level' column.

    Returns:
        plotly.graph_objects.Figure: Bar chart figure.
    """

    risk_counts = (
        risk_df["Risk_Level"]
        .value_counts()
        .reset_index()
    )
    risk_counts.columns = ["Risk Level", "Count"]

    return px.bar(
        risk_counts,
        x="Risk Level",
        y="Count",
        color="Risk Level",
        color_discrete_map=RISK_LEVEL_COLOURS
    )


def create_risk_status_pie(risk_df):
    """
    Create a pie chart showing Open vs Closed risk split.

    Args:
        risk_df: DataFrame with 'Status' column.

    Returns:
        plotly.graph_objects.Figure: Pie chart figure.
    """

    return px.pie(
        risk_df,
        names="Status",
        title="Open vs Closed Actions"
    )


def create_heatmap(risk_df):
    """
    Create a density heatmap of Likelihood vs Impact.

    Uses a red colour scale to highlight high-risk concentrations.

    Args:
        risk_df: DataFrame with 'Likelihood' and 'Impact' columns.

    Returns:
        plotly.graph_objects.Figure: Heatmap figure.
    """

    return px.density_heatmap(
        risk_df,
        x="Likelihood",
        y="Impact",
        color_continuous_scale="Reds"
    )


# ==========================================================
# ESCALATION CHARTS
# ==========================================================

def create_escalation_bar_chart(overdue_df):
    """
    Create a bar chart of escalation level distribution.

    Colour-coded by severity from amber (Level 1) to
    purple (Level 4).

    Args:
        overdue_df: DataFrame with 'Escalation_Level' column.

    Returns:
        plotly.graph_objects.Figure: Bar chart figure.
    """

    esc_counts = (
        overdue_df["Escalation_Level"]
        .value_counts()
        .reset_index()
    )
    esc_counts.columns = ["Escalation Level", "Count"]

    return px.bar(
        esc_counts,
        x="Escalation Level",
        y="Count",
        color="Escalation Level",
        color_discrete_map=ESCALATION_COLOURS
    )


def create_overdue_timeline(overdue_df):
    """
    Create a horizontal bar chart of days overdue by risk.

    Coloured by risk owner for easy identification.

    Args:
        overdue_df: DataFrame with Risk_ID, Risk_Name,
            Due_Date, Days_Overdue, Risk_Owner columns.

    Returns:
        plotly.graph_objects.Figure: Horizontal bar chart.
    """

    timeline_df = overdue_df[
        ["Risk_ID", "Risk_Name", "Due_Date",
         "Days_Overdue", "Risk_Owner"]
    ].copy()

    fig = px.bar(
        timeline_df,
        x="Days_Overdue",
        y="Risk_ID",
        color="Risk_Owner",
        orientation="h",
        hover_data=["Risk_Name", "Due_Date"],
        title="Days Overdue by Risk"
    )

    fig.update_layout(
        yaxis_title="Risk ID",
        xaxis_title="Days Overdue"
    )

    return fig


# ==========================================================
# MANAGEMENT REPORT CHARTS
# ==========================================================

def create_management_trend_chart(trend_df, target=80, theme_name="light"):
    """
    Create a compliance trend chart with target threshold line.

    Used in the Monthly Management Report section. Includes
    a dashed red target line for visual comparison.

    Args:
        trend_df: DataFrame with 'Month' and 'Score' columns.
        target: Target compliance percentage. Defaults to 80.
        theme_name: Active theme name for colour styling.

    Returns:
        plotly.graph_objects.Figure: Trend chart with target line.
    """

    theme = get_theme(theme_name)

    fig = go.Figure()

    # Actual compliance scores
    fig.add_trace(
        go.Scatter(
            x=trend_df["Month"],
            y=trend_df["Score"],
            mode="lines+markers",
            name="Compliance Score",
            line=dict(color=theme["trend_line_color"], width=3),
            marker=dict(size=8)
        )
    )

    # Target threshold line
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Target: {target}%"
    )

    fig.update_layout(
        title="Compliance Score Trend vs Target",
        yaxis_title="Score (%)",
        xaxis_title="Month",
        yaxis_range=[0, 100]
    )

    # Apply theme
    apply_chart_theme(fig, theme)

    return fig



# ==========================================================
# RISK SCORING CHARTS
# ==========================================================


def create_score_distribution_chart(scored_df):
    """
    Create a bar chart of risk score band distribution.

    Colour-coded by severity: Critical=purple, High=red,
    Medium=amber, Low=green.

    Args:
        scored_df: DataFrame with 'Score_Band' column.

    Returns:
        plotly.graph_objects.Figure: Bar chart figure.
    """

    score_counts = (
        scored_df["Score_Band"]
        .value_counts()
        .reset_index()
    )
    score_counts.columns = ["Score Band", "Count"]

    # Enforce display order
    band_order = ["Critical", "High", "Medium", "Low"]
    score_counts["Score Band"] = pd.Categorical(
        score_counts["Score Band"],
        categories=band_order,
        ordered=True
    )
    score_counts = score_counts.sort_values("Score Band")

    return px.bar(
        score_counts,
        x="Score Band",
        y="Count",
        color="Score Band",
        color_discrete_map=SCORE_BAND_COLOURS,
        title="Risk Score Distribution"
    )


def create_score_waterfall_chart(top_risks_df):
    """
    Create a horizontal bar chart of top risks by score.

    Useful for executive reporting to show the most critical
    risks requiring attention.

    Args:
        top_risks_df: DataFrame with Risk_ID and
            Residual_Risk_Score columns.

    Returns:
        plotly.graph_objects.Figure: Horizontal bar chart.
    """

    fig = px.bar(
        top_risks_df,
        x="Residual_Risk_Score",
        y="Risk_ID",
        color="Score_Band",
        orientation="h",
        hover_data=["Risk_Name", "Risk_Owner"],
        color_discrete_map=SCORE_BAND_COLOURS,
        title="Top Risks by Residual Score"
    )

    fig.update_layout(
        yaxis_title="Risk ID",
        xaxis_title="Residual Risk Score"
    )

    return fig
