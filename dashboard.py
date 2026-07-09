"""
GRC Compliance Dashboard
Version: 1.3.1
Author: Taiwo Durodola-Tunde
"""

from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ==========================================================
# CONFIGURATION
# ==========================================================

APP_VERSION = "1.3.1"

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


# ==========================================================
# FUNCTIONS
# ==========================================================

@st.cache_data
def load_data():

    risk_df = pd.read_csv(
        "data/risk_register.csv"
    )

    controls_df = pd.read_csv(
        "data/controls.csv"
    )

    return risk_df, controls_df


@st.cache_data
def load_compliance_history():

    return pd.read_csv(
        "data/compliance_history.csv"
    )


def calculate_compliance_score(
    controls_df
):

    total_controls = len(
        controls_df
    )

    if total_controls == 0:
        return 0

    implemented = len(
        controls_df[
            controls_df["Status"] == "Implemented"
        ]
    )

    return round(
        implemented /
        total_controls * 100,
        1
    )


def generate_pdf(
    compliance_score,
    metrics,
    rating
):

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=letter
    )

    pdf.setTitle(
        "Executive GRC Report"
    )

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        750,
        "Executive GRC Report"
    )

    pdf.setFont(
        "Helvetica",
        12
    )

    pdf.drawString(
        50,
        720,
        f"Generated: {datetime.now()}"
    )

    pdf.drawString(
        50,
        690,
        f"Compliance Score: {compliance_score}%"
    )

    pdf.drawString(
        50,
        670,
        f"Status: {rating}"
    )

    pdf.drawString(
        50,
        650,
        f"Open Risks: {metrics['open_risks']}"
    )

    pdf.drawString(
        50,
        630,
        f"Closed Risks: {metrics['closed_risks']}"
    )

    pdf.drawString(
        50,
        610,
        f"High Risks: {metrics['high_risks']}"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# ==========================================================
# DATA LOAD
# ==========================================================

try:

    risk_df, controls_df = load_data()

except Exception as e:

    st.error(
        f"Unable to load source files: {e}"
    )

    st.stop()


# ==========================================================
# FILE UPLOAD
# ==========================================================

st.sidebar.header(
    "Data Upload"
)

uploaded_file = st.sidebar.file_uploader(
    "Upload Risk Register CSV",
    type=["csv"]
)

if uploaded_file:

    risk_df = pd.read_csv(
        uploaded_file
    )


# ==========================================================
# FILTERS
# ==========================================================

st.sidebar.header(
    "Filters"
)

owners = sorted(
    risk_df["Risk_Owner"]
    .dropna()
    .unique()
)

selected_owners = st.sidebar.multiselect(
    "Risk Owner",
    options=owners,
    default=owners
)

filtered_risk_df = risk_df[
    risk_df["Risk_Owner"]
    .isin(selected_owners)
]


# ==========================================================
# KPI CALCULATIONS
# ==========================================================

compliance_score = (
    calculate_compliance_score(
        controls_df
    )
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


# ==========================================================
# HEALTH RATING
# ==========================================================

if compliance_score >= 80:

    rating = "🟢 Healthy"

elif compliance_score >= 60:

    rating = "🟠 Requires Attention"

else:

    rating = "🔴 Critical"


# ==========================================================
# KPI CARDS
# ==========================================================

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


# ==========================================================
# EXECUTIVE SUMMARY
# ==========================================================

st.subheader(
    "Executive Summary"
)

st.success(
    f"""
Status: {rating}

Compliance Score: {compliance_score}%

Open Risks: {metrics['open_risks']}

Closed Risks: {metrics['closed_risks']}

High Risks: {metrics['high_risks']}
"""
)


# ==========================================================
# COMPLIANCE TREND
# ==========================================================

st.subheader(
    "Compliance Trend"
)

try:

    trend_df = (
        load_compliance_history()
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
        width="stretch",
        key="trend_chart"
    )

except Exception:
    st.warning(
        "compliance_history.csv not found"
    )


# ==========================================================
# CONTROL STATUS
# ==========================================================

st.subheader(
    "Control Status"
)

control_chart = px.pie(
    controls_df,
    names="Status",
    title="Control Implementation Status"
)

st.plotly_chart(
    control_chart,
    width="stretch",
    key="control_chart"
)


# ==========================================================
# RISK ANALYSIS
# ==========================================================

left, right = st.columns(2)

with left:

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
        width="stretch",
        key="risk_distribution"
    )

with right:

    status_chart = px.pie(
        filtered_risk_df,
        names="Status"
    )

    st.plotly_chart(
        status_chart,
        width="stretch",
        key="risk_status"
    )


# ==========================================================
# RISK HEATMAP
# ==========================================================

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
    width="stretch",
    key="heatmap"
)


# ==========================================================
# RISK OWNER SUMMARY
# ==========================================================

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


# ==========================================================
# RISK REGISTER
# ==========================================================

st.subheader(
    "Risk Register"
)

st.dataframe(
    filtered_risk_df,
    width="stretch"
)


# ==========================================================
# EXPORTS
# ==========================================================

st.subheader(
    "Exports"
)

st.download_button(
    "📥 Download CSV",
    filtered_risk_df.to_csv(
        index=False
    ),
    "risk_register_export.csv",
    "text/csv"
)

pdf_buffer = generate_pdf(
    compliance_score,
    metrics,
    rating
)

st.download_button(
    "📄 Download PDF",
    pdf_buffer,
    "executive_report.pdf",
    "application/pdf"
)


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption(
    f"GRC Compliance Dashboard | Version {APP_VERSION}"
)