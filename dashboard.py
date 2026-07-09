"""
GRC Compliance Dashboard
-----------------------
Author: Taiwo Durodola-Tunde

Purpose:
Display risk and compliance metrics from
the risk register and ISO 27001 control inventory.

Version:
1.1.0

Data Sources:
- data/risk_register.csv
- data/controls.csv
"""

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

APP_VERSION = "1.1.0"

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
            risk_df (DataFrame)
            controls_df (DataFrame)
    """

    risk_df = pd.read_csv(
        "data/risk_register.csv"
    )

    controls_df = pd.read_csv(
        "data/controls.csv"
    )

    return risk_df, controls_df


risk_df, controls = load_data()


# ============================================================
# KPI CALCULATIONS
# ============================================================

def calculate_compliance_score(control_df):
    """
    Calculate compliance percentage.
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
        (implemented_controls / total_controls) * 100,
        1
    )


def calculate_risk_metrics(df):
    """
    Calculate summary risk metrics.
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
    controls
)

metrics = calculate_risk_metrics(
    risk_df
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
# COMPLIANCE HEALTH STATUS
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

The dashboard indicates the current risk and
compliance posture based on control implementation
status and registered risks.
"""
)

# ============================================================
# CONTROL STATUS CHART
# ============================================================

st.subheader("Control Implementation Status")

control_chart = px.pie(
    controls,
    names="Status",
    title="Control Status Distribution"
)

st.plotly_chart(
    control_chart,
    width="stretch"
)


# ============================================================
# RISK DISTRIBUTION
# ============================================================

st.subheader("Risk Distribution")

risk_counts = (
    risk_df["Risk_Level"]
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


# ============================================================
# ISO 27001 CONTROL COVERAGE
# ============================================================

st.subheader("ISO 27001 Control Coverage")

iso_chart = px.pie(
    controls,
    names="Status",
    title="ISO 27001 Control Coverage"
)

st.plotly_chart(
    iso_chart,
    width="stretch"
)


# ============================================================
# RISK REGISTER
# ============================================================

st.subheader("Risk Register")

st.dataframe(
    risk_df,
    width="stretch"
)