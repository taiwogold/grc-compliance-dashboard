"""
GRC Compliance Dashboard
Version: 2.0.1
Author: Taiwo Durodola-Tunde
"""

from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ==========================================================
# CONFIGURATION
# ==========================================================

APP_VERSION = "2.0.1"

st.set_page_config(
    page_title="GRC Compliance Dashboard",
    layout="wide"
)

# Optional Banner
try:
    st.image(
        "assets/banner.png",
        width="stretch"
    )
except Exception:
    pass

st.title("🛡️ GRC Compliance Dashboard")

st.caption(
    f"Version {APP_VERSION}"
)

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

    if "Owner_Email" not in risk_df.columns:
        risk_df["Owner_Email"] = ""
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
        (
            implemented /
            total_controls
        ) * 100,
        1
    )


def calculate_escalation(risk_df):
    """
    Calculates overdue status and escalation levels for risks.

    Escalation Levels:
    - None: Not overdue (due date in the future or risk closed)
    - Level 1: 1-14 days overdue (owner reminder)
    - Level 2: 15-30 days overdue (manager escalation)
    - Level 3: 31-60 days overdue (director escalation)
    - Level 4: 60+ days overdue (executive escalation)
    """

    today = pd.Timestamp(
        datetime.now().date()
    )

    df = risk_df.copy()

    # Parse Due_Date column
    if "Due_Date" in df.columns:
        df["Due_Date"] = pd.to_datetime(
            df["Due_Date"],
            errors="coerce"
        )
    else:
        df["Due_Date"] = pd.NaT

    # Calculate days overdue (positive = overdue)
    df["Days_Overdue"] = (
        today - df["Due_Date"]
    ).dt.days

    # Only open risks can be overdue
    df.loc[
        df["Status"] == "Closed",
        "Days_Overdue"
    ] = 0

    # Determine escalation level
    conditions = [
        (df["Status"] == "Closed") | (df["Days_Overdue"] <= 0),
        (df["Days_Overdue"] >= 1) & (df["Days_Overdue"] <= 14),
        (df["Days_Overdue"] >= 15) & (df["Days_Overdue"] <= 30),
        (df["Days_Overdue"] >= 31) & (df["Days_Overdue"] <= 60),
        (df["Days_Overdue"] > 60),
    ]

    choices = [
        "None",
        "Level 1 - Owner Reminder",
        "Level 2 - Manager Escalation",
        "Level 3 - Director Escalation",
        "Level 4 - Executive Escalation",
    ]

    df["Escalation_Level"] = pd.Series(
        pd.Categorical(
            pd.array(
                [
                    choices[i]
                    for i in range(len(choices))
                    for _ in range(len(df))
                ][:len(df)],
                dtype="object"
            )
        )
    )

    # Apply conditions using numpy select
    import numpy as np
    df["Escalation_Level"] = np.select(
        conditions,
        choices,
        default="None"
    )

    # Is Overdue flag
    df["Is_Overdue"] = (
        (df["Days_Overdue"] > 0) &
        (df["Status"] == "Open")
    )

    # Days remaining (negative means overdue)
    df["Days_Remaining"] = -df["Days_Overdue"]

    return df


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

    pdf.drawString(
        50,
        580,
        f"Dashboard Version: {APP_VERSION}"
    )

    pdf.drawString(
        50,
        560,
        "Generated by GRC Compliance Dashboard"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# ==========================================================
# LOAD DATA
# ==========================================================

try:

    risk_df, controls_df = load_data()

except Exception as e:

    st.error(
        f"Unable to load source files: {e}"
    )

    st.stop()


# ==========================================================
# CSV UPLOAD
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
# DASHBOARD ACTIONS
# ==========================================================

if st.sidebar.button(
    "🔄 Refresh Dashboard"
):
    st.cache_data.clear()
    st.rerun()


# ==========================================================
# DATA VALIDATION
# ==========================================================

required_columns = [
    "Risk_Level",
    "Status",
    "Risk_Owner",
    "Likelihood",
    "Impact"
]

missing_columns = [
    column
    for column in required_columns
    if column not in risk_df.columns
]

if missing_columns:

    st.error(
        f"Missing required columns: "
        f"{', '.join(missing_columns)}"
    )

    st.stop()


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

if filtered_risk_df.empty:

    st.warning(
        "No records found for the selected filters."
    )

    st.stop()


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
# KPI DASHBOARD
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

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.info(
        f"""
### Compliance Position

**Compliance Score:** {compliance_score}%

**Current Status:** {rating}
"""
    )

with summary_col2:

    st.info(
        f"""
### Risk Overview

**Open Risks:** {metrics['open_risks']}

**Closed Risks:** {metrics['closed_risks']}

**High Risks:** {metrics['high_risks']}
"""
    )


# ==========================================================
# COMPLIANCE TREND + ISO COVERAGE
# ==========================================================

chart_left, chart_right = st.columns(2)

with chart_left:

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

with chart_right:

    st.subheader(
        "ISO 27001 Control Coverage"
    )

    iso_chart = px.pie(
        controls_df,
        names="Status",
        title="ISO 27001 Coverage"
    )

    st.plotly_chart(
        iso_chart,
        width="stretch",
        key="iso_chart"
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
        color="Risk Level",
        color_discrete_map={
            "High": "#dc3545",
            "Medium": "#ffc107",
            "Low": "#198754"
        }
    )

    st.plotly_chart(
        risk_chart,
        width="stretch",
        key="risk_distribution"
    )

with right:

    status_chart = px.pie(
        filtered_risk_df,
        names="Status",
        title="Open vs Closed Actions"
    )

    st.plotly_chart(
        status_chart,
        width="stretch",
        key="risk_status"
    )


# ==========================================================
# RISK HEAT MAP
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
# ESCALATION TRACKING & OVERDUE RISK DASHBOARD
# ==========================================================

st.subheader(
    "⚠️ Overdue Risk Escalation Dashboard"
)

# Apply escalation logic
escalated_df = calculate_escalation(
    filtered_risk_df
)

overdue_df = escalated_df[
    escalated_df["Is_Overdue"] == True
].sort_values(
    "Days_Overdue",
    ascending=False
)

# Overdue KPIs
esc_c1, esc_c2, esc_c3, esc_c4 = st.columns(4)

total_overdue = len(overdue_df)

level_counts = (
    overdue_df["Escalation_Level"]
    .value_counts()
)

esc_c1.metric(
    "🔴 Total Overdue",
    total_overdue
)

esc_c2.metric(
    "⚡ Level 3+",
    level_counts.get(
        "Level 3 - Director Escalation", 0
    ) + level_counts.get(
        "Level 4 - Executive Escalation", 0
    )
)

esc_c3.metric(
    "📅 Most Overdue (Days)",
    int(overdue_df["Days_Overdue"].max())
    if not overdue_df.empty else 0
)

esc_c4.metric(
    "📊 Escalation Rate",
    f"{round(total_overdue / len(escalated_df) * 100, 1)}%"
    if len(escalated_df) > 0 else "0%"
)

# Overdue Risks Table with colour coding
if not overdue_df.empty:

    st.markdown("#### Overdue Risks by Escalation Level")

    display_cols = [
        "Risk_ID",
        "Risk_Name",
        "Risk_Level",
        "Risk_Owner",
        "Due_Date",
        "Days_Overdue",
        "Escalation_Level",
        "Control_Status"
    ]

    available_cols = [
        col for col in display_cols
        if col in overdue_df.columns
    ]

    overdue_display = overdue_df[
        available_cols
    ].copy()

    # Format Due_Date for display
    if "Due_Date" in overdue_display.columns:
        overdue_display["Due_Date"] = (
            overdue_display["Due_Date"]
            .dt.strftime("%Y-%m-%d")
        )

    st.dataframe(
        overdue_display,
        use_container_width=True,
        column_config={
            "Days_Overdue": st.column_config.NumberColumn(
                "Days Overdue",
                help="Number of days past the due date"
            ),
            "Escalation_Level": st.column_config.TextColumn(
                "Escalation Level",
                help="Current escalation tier"
            ),
        }
    )

    # Escalation Level Distribution Chart
    esc_left, esc_right = st.columns(2)

    with esc_left:

        st.markdown("#### Escalation Level Distribution")

        esc_counts = (
            overdue_df["Escalation_Level"]
            .value_counts()
            .reset_index()
        )
        esc_counts.columns = [
            "Escalation Level",
            "Count"
        ]

        esc_chart = px.bar(
            esc_counts,
            x="Escalation Level",
            y="Count",
            color="Escalation Level",
            color_discrete_map={
                "Level 1 - Owner Reminder": "#ffc107",
                "Level 2 - Manager Escalation": "#fd7e14",
                "Level 3 - Director Escalation": "#dc3545",
                "Level 4 - Executive Escalation": "#6f42c1",
            }
        )

        st.plotly_chart(
            esc_chart,
            use_container_width=True,
            key="escalation_distribution"
        )

    with esc_right:

        st.markdown("#### Overdue Risks by Owner")

        owner_overdue = (
            overdue_df
            .groupby("Risk_Owner")
            .agg(
                Overdue_Count=("Risk_ID", "count"),
                Max_Days_Overdue=("Days_Overdue", "max"),
                Highest_Escalation=(
                    "Escalation_Level", "max"
                )
            )
            .reset_index()
            .sort_values(
                "Max_Days_Overdue",
                ascending=False
            )
        )

        st.dataframe(
            owner_overdue,
            use_container_width=True
        )

    # Timeline visualisation
    st.markdown("#### Overdue Risk Timeline")

    timeline_df = overdue_df[
        ["Risk_ID", "Risk_Name", "Due_Date", "Days_Overdue", "Risk_Owner"]
    ].copy()

    timeline_chart = px.bar(
        timeline_df,
        x="Days_Overdue",
        y="Risk_ID",
        color="Risk_Owner",
        orientation="h",
        hover_data=["Risk_Name", "Due_Date"],
        title="Days Overdue by Risk"
    )

    timeline_chart.update_layout(
        yaxis_title="Risk ID",
        xaxis_title="Days Overdue"
    )

    st.plotly_chart(
        timeline_chart,
        use_container_width=True,
        key="overdue_timeline"
    )

else:

    st.success(
        "✅ No overdue risks. All open risks are within their due dates."
    )

# Upcoming Due Dates (next 14 days)
st.markdown("#### 📅 Risks Due Within 14 Days")

upcoming_df = escalated_df[
    (escalated_df["Days_Remaining"] >= 0) &
    (escalated_df["Days_Remaining"] <= 14) &
    (escalated_df["Status"] == "Open")
].sort_values("Days_Remaining")

if not upcoming_df.empty:

    upcoming_display = upcoming_df[
        [
            "Risk_ID",
            "Risk_Name",
            "Risk_Level",
            "Risk_Owner",
            "Due_Date",
            "Days_Remaining"
        ]
    ].copy()

    upcoming_display["Due_Date"] = (
        upcoming_display["Due_Date"]
        .dt.strftime("%Y-%m-%d")
    )

    st.dataframe(
        upcoming_display,
        use_container_width=True,
        column_config={
            "Days_Remaining": st.column_config.NumberColumn(
                "Days Until Due",
                help="Number of days until the due date"
            )
        }
    )

else:

    st.info(
        "No risks due within the next 14 days."
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

st.caption(
    f"Displaying {len(filtered_risk_df)} risk records."
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
# RISK OWNER EMAIL DIRECTORY
# ==========================================================

st.subheader(
    "📧 Risk Owner Email Directory"
)

owner_directory = (
    risk_df[
        [
            "Risk_Owner",
            "Owner_Email"
        ]
    ]
    .drop_duplicates()
    .sort_values("Risk_Owner")
)

st.dataframe(
    owner_directory,
    width="stretch"
)


# ==========================================================
# REMINDER GENERATION
# ==========================================================

st.subheader(
    "📨 Risk Owner Reminder Generation"
)

available_owners = sorted(
    filtered_risk_df[
        "Risk_Owner"
    ].unique()
)

selected_owner = st.selectbox(
    "Select Risk Owner",
    available_owners
)

owner_risks = filtered_risk_df[
    filtered_risk_df["Risk_Owner"]
    == selected_owner
]

owner_email = owner_risks[
    "Owner_Email"
].iloc[0]

open_risks = owner_risks[
    owner_risks["Status"] == "Open"
]

risk_lines = []

for _, row in open_risks.iterrows():

    due_info = ""
    if "Due_Date" in row and pd.notna(row.get("Due_Date")):
        due_date = pd.to_datetime(row["Due_Date"])
        days_diff = (datetime.now() - due_date).days
        if days_diff > 0:
            due_info = f" [⚠️ OVERDUE by {days_diff} days]"
        else:
            due_info = f" [Due: {due_date.strftime('%Y-%m-%d')}]"

    risk_lines.append(
        f"- {row['Risk_ID']} : "
        f"{row['Risk_Name']} "
        f"({row['Risk_Level']}){due_info}"
    )

risk_list = "\n".join(
    risk_lines
)

email_text = f"""
Subject: Risk Remediation Status Update

To: {owner_email}

Hello {selected_owner},

Please review the following open risks assigned
to your team:

{risk_list}

Please provide an update on:

• Current remediation progress

• Expected completion date

• Any blockers preventing resolution

Your response will support Governance &
Assurance reporting activities.

Kind Regards,

Cyber Security Governance & Assurance
"""

st.text_area(
    "Generated Reminder Email",
    email_text,
    height=350
)

st.code(
    email_text,
    language="text"
)

# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption(
    f"GRC Compliance Dashboard | Version {APP_VERSION}"
)