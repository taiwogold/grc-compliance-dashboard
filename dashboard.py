"""
GRC Compliance Dashboard
===============================================================

Author:
    Taiwo Durodola-Tunde

Version:
    1.2.0

Purpose:
    Interactive Governance, Risk & Compliance (GRC)
    dashboard built using Streamlit and Plotly.

    The dashboard provides visibility of:

    - Compliance posture
    - Risk status
    - Risk owner accountability
    - Control implementation progress
    - ISO 27001 coverage
    - Executive-level KPIs

Data Sources:
    - data/risk_register.csv
    - data/controls.csv

Future Versions:
    v1.3
        - CSV upload capability
        - Compliance trend reporting
        - PDF exports

    v2.0
        - Email automation
        - Executive reporting packs
        - Outlook integration
        - Microsoft Graph integration

===============================================================
"""

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_VERSION = "1.2.0"

st.set_page_config(
    page_title="GRC Compliance Dashboard",
    layout="wide"
)

st.title("🛡️ GRC Compliance Dashboard")

st.caption(f"Version {APP_VERSION}")

st.caption(
    f"Last Refreshed: "
    f"{datetime.now().strftime('%d %b %Y %H:%M')}"
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():
    """
    Load dashboard datasets.

    Returns:
        tuple:
            risk_df (pd.DataFrame)
            controls_df (pd.DataFrame)
    """

    risk_df = pd.read_csv(
        "data/risk_register.csv"
    )

    controls_df = pd.read_csv(
        "data/controls.csv"
    )

    return risk_df, controls_df


risk_df, controls_df = load_data()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Filters")

selected_owners = st.sidebar.multiselect(
    "Risk Owner",
    options=sorted(
        risk_df["Risk_Owner"].unique()
    ),
    default=sorted(
        risk_df["Risk_Owner"].unique()
    )
)

filtered_risk_df = risk_df[
    risk_df["Risk_Owner"].isin(
        selected_owners
    )
]


# ============================================================
# KPI CALCULATIONS
# ============================================================

def calculate_compliance_score(control_df):
    """
    Calculate compliance score.

    Args:
        control_df (DataFrame)

    Returns:
        float
    """

    implemented_controls = len(
        control_df[
            control_df["Status"] == "Implemented"
        ]
    )

    total_controls = len(control_df)

    if total_controls == 0:
        return 0

    return round(
        (implemented_controls / total_controls)
        * 100,
        1
    )


def calculate_risk_metrics(df):
    """
    Calculate risk KPI metrics.

    Args:
        df (DataFrame)

    Returns:
        dict
    """

    return {
        "high_risks": len(
            df[df["Risk_Level"] == "High"]
        ),
        "open_risks": len(
            df[df["Status"] == "Open"]
        ),
        "closed_risks": len(
            df[df["Status"] == "Closed"]
        )
    }


compliance_score = calculate_compliance_score(
    controls_df
)

metrics = calculate_risk_metrics(
    filtered_risk_df
)


# ============================================================
# KPI DASHBOARD
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Compliance Score",
    f"{compliance_score}%"
)

col2.metric(
    "Open Risks",
    metrics["open_risks"]
)

col3.metric(
    "Closed Risks",
    metrics["closed_risks"]
)

col4.metric(
    "High Risks",
    metrics["high_risks"]
)

st.divider()


# ============================================================
# COMPLIANCE STATUS
# ============================================================

if compliance_score >= 80:

    rating = "🟢 Healthy"

    st.success(
        "Overall Compliance Status: Healthy"
    )

elif compliance_score >= 60:

    rating = "🟠 Requires Attention"

    st.warning(
        "Overall Compliance Status: Requires Attention"
    )

else:

    rating = "🔴 Critical"

    st.error(
        "Overall Compliance Status: Critical"
    )


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.subheader("Executive Summary")

st.info(
    f"""
**Compliance Score:** {compliance_score}%

**Current Status:** {rating}

**Open Risks:** {metrics['open_risks']}

**Closed Risks:** {metrics['closed_risks']}

**High Risks:** {metrics['high_risks']}

The dashboard provides an overview of the
organisation's current compliance posture,
risk exposure and control implementation status.
"""
)


# ============================================================
# CONTROL IMPLEMENTATION STATUS
# ============================================================

st.subheader("Control Implementation Status")

control_chart = px.pie(
    controls_df,
    names="Status",
    title="Control Status Distribution"
)

st.plotly_chart(
    control_chart,
    width="stretch"
)


# ============================================================
# RISK DISTRIBUTION & ACTION STATUS
# ============================================================

left_col, right_col = st.columns(2)

with left_col:

    st.subheader("Risk Distribution")

    risk_counts = (
        filtered_risk_df["Risk_Level"]
        .value_counts()
        .reset_index()
    )

    risk_counts.columns = [
        "Risk Level",
        "Count"
    ]

    risk_chart = px.bar(
        risk_counts,
        x="Risk Level",
        y="Count",
        color="Risk Level",
        title="Risk Severity Distribution"
    )

    st.plotly_chart(
        risk_chart,
        width="stretch"
    )

with right_col:

    st.subheader("Open vs Closed Actions")

    status_chart = px.pie(
        filtered_risk_df,
        names="Status",
        title="Risk Status Breakdown"
    )

    st.plotly_chart(
        status_chart,
        width="stretch"
    )


# ============================================================
# ISO 27001 CONTROL COVERAGE
# ============================================================

st.subheader("ISO 27001 Control Coverage")

iso_chart = px.pie(
    controls_df,
    names="Status",
    title="ISO 27001 Control Coverage"
)

st.plotly_chart(
    iso_chart,
    width="stretch"
)


# ============================================================
# RISK HEAT MAP
# ============================================================

st.subheader("Risk Heat Map")

heatmap = px.density_heatmap(
    filtered_risk_df,
    x="Likelihood",
    y="Impact",
    title="Risk Heat Map",
    color_continuous_scale="Reds"
)

st.plotly_chart(
    heatmap,
    width="stretch"
)


# ============================================================
# RISK REGISTER
# ============================================================

st.subheader("Risk Register")

st.dataframe(
    filtered_risk_df,
    width="stretch"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"GRC Compliance Dashboard | Version {APP_VERSION}"
)