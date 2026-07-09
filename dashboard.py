"""
GRC Compliance Dashboard
===============================================================

Author:
    Taiwo Durodola-Tunde

Version:
    1.3.0

Purpose:
    Interactive Governance, Risk & Compliance dashboard
    providing executive-level compliance and risk reporting.

Features:
    - Compliance Score
    - Executive Summary
    - Risk Owner Filtering
    - Risk Distribution
    - Open vs Closed Actions
    - ISO 27001 Coverage
    - Risk Heat Map
    - Compliance Trend Analysis
    - Risk Owner Summary
    - CSV Upload
    - CSV Export
    - PDF Executive Report

===============================================================
"""

from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURATION
# ============================================================

APP_VERSION = "1.3.0"

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
# PDF REPORT
# ============================================================

def generate_pdf(
    compliance_score,
    metrics,
    rating
):
    """
    Create executive PDF report.
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=letter
    )

    pdf.setTitle(
        "GRC Executive Report"
    )

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        750,
        "GRC Executive Report"
    )

    pdf.setFont(
        "Helvetica",
        12
    )

    pdf.drawString(
        50,
        710,
        f"Generated: {datetime.now()}"
    )

    pdf.drawString(
        50,
        680,
        f"Compliance Score: {compliance_score}%"
    )

    pdf.drawString(
        50,
        660,
        f"Status: {rating}"
    )

    pdf.drawString(
        50,
        640,
        f"Open Risks: {metrics['open_risks']}"
    )

    pdf.drawString(
        50,
        620,
        f"Closed Risks: {metrics['closed_risks']}"
    )

    pdf.drawString(
        50,
        600,
        f"High Risks: {metrics['high_risks']}"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():

    risk_df = pd.read_csv(
        "data/risk_register.csv"
    )

    controls_df = pd.read_csv(
        "data/controls.csv"
    )

    return risk_df, controls_df


risk_df, controls_df = load_data()

# ============================================================
# CSV UPLOAD
# ============================================================

st.sidebar.header("Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload Risk Register CSV",
    type=["csv"]
)

if uploaded_file is not None:
    risk_df = pd.read_csv(uploaded_file)

# ============================================================
# FILTERS
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

implemented = len(
    controls_df[
        controls_df["Status"] == "Implemented"
    ]
)

total_controls = len(
    controls_df
)

compliance_score = round(
    (implemented / total_controls) * 100,
    1
)

metrics = {
    "high_risks": len(
        filtered_risk_df[
            filtered_risk_df["Risk_Level"] == "High"
        ]
    ),
    "open_risks": len(
        filtered_risk_df[
            filtered_risk_df["Status"] == "Open"
        ]
    ),
    "closed_risks": len(
        filtered_risk_df[
            filtered_risk_df["Status"] == "Closed"
        ]
    )
}

# ============================================================
# STATUS
# ============================================================

if compliance_score >= 80:
    rating = "Healthy"
elif compliance_score >= 60:
    rating = "Requires Attention"
else:
    rating = "Critical"

# ============================================================
# KPI DASHBOARD
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Compliance Score",
    f"{compliance_score}%"
)

c2.metric(
    "Open Risks",
    metrics["open_risks"]
)

c3.metric(
    "Closed Risks",
    metrics["closed_risks"]
)

c4.metric(
    "High Risks",
    metrics["high_risks"]
)

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.subheader(
    "Executive Summary"
)

st.info(
    f"""
Compliance Score: {compliance_score}%

Current Status: {rating}

Open Risks: {metrics['open_risks']}

Closed Risks: {metrics['closed_risks']}

High Risks: {metrics['high_risks']}
"""
)

# ============================================================
# COMPLIANCE TREND
# ============================================================

st.subheader(
    "Compliance Trend"
)

trend_df = pd.read_csv(
    "data/compliance_history.csv"
)

trend_chart = px.line(
    trend_df,
    x="Month",
    y="Score",
    markers=True,
    title="Compliance Trend"
)

st.plotly_chart(
    trend_chart,
    width="stretch"
)

# ============================================================
# CONTROL STATUS
# ============================================================

st.subheader(
    "Control Implementation Status"
)

control_chart = px.pie(
    controls_df,
    names="Status"
)

st.plotly_chart(
    control_chart,
    width="stretch"
)

# ============================================================
# DISTRIBUTION + STATUS
# ============================================================

left_col, right_col = st.columns(2)

with left_col:

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
        color="Risk Level"
    )

    st.plotly_chart(
        risk_chart,
        width="stretch"
    )

with right_col:

    status_chart = px.pie(
        filtered_risk_df,
        names="Status"
    )

    st.plotly_chart(
        status_chart,
        width="stretch"
    )

# ============================================================
# ISO COVERAGE
# ============================================================

st.subheader(
    "ISO 27001 Control Coverage"
)

iso_chart = px.pie(
    controls_df,
    names="Status"
)

st.plotly_chart(
    iso_chart,
    width="stretch"
)

# ============================================================
# HEAT MAP
# ============================================================

st.subheader(
    "Risk Heat Map"
)

heatmap = px.density_heatmap(
    filtered_risk_df,
    x="Likelihood",
    y="Impact",
    color_continuous_scale="Reds"
)

st.plotly_chart(
    heatmap,
    width="stretch"
)

# ============================================================
# RISK OWNER SUMMARY
# ============================================================

st.subheader(
    "Risk Owner Summary"
)

owner_summary = (
    filtered_risk_df
    .groupby("Risk_Owner")
    .agg(
        Open_Risks=(
            "Status",
            lambda x: (x == "Open").sum()
        ),
        High_Risks=(
            "Risk_Level",
            lambda x: (x == "High").sum()
        )
    )
    .reset_index()
)

st.dataframe(
    owner_summary,
    width="stretch"
)

# ============================================================
# RISK REGISTER
# ============================================================

st.subheader(
    "Risk Register"
)

st.dataframe(
    filtered_risk_df,
    width="stretch"
)

# ============================================================
# EXPORTS
# ============================================================

st.subheader(
    "Exports"
)

csv_export = (
    filtered_risk_df
    .to_csv(index=False)
)

st.download_button(
    label="📥 Download Risk Register CSV",
    data=csv_export,
    file_name="risk_register_export.csv",
    mime="text/csv"
)

pdf_buffer = generate_pdf(
    compliance_score,
    metrics,
    rating
)

st.download_button(
    label="📄 Download Executive PDF Report",
    data=pdf_buffer,
    file_name="executive_report.pdf",
    mime="application/pdf"
)

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"GRC Compliance Dashboard | Version {APP_VERSION}"
)