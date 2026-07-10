"""
GRC Compliance Dashboard
Version: 2.1.0
Author: Taiwo Durodola-Tunde

Release Notes:
    v2.1.0 - Outlook Integration & Automated Reminder Dispatch
    v2.0.2 - Monthly Management Reports & Enhanced PDF Exports
    v2.0.1 - Overdue Risk Escalation Tracking
    v2.0.0 - Initial release with KPI dashboard

Security Notes:
    - Email dispatch uses win32com.client (COM automation) to
      interface with the user's locally authenticated Outlook client.
    - NO credentials are stored, transmitted, or hardcoded.
    - All emails route through the corporate Exchange server.
    - Session rate limiting prevents accidental mass-mailing.
    - Full audit trail maintained in logs/email_audit.csv.
"""

from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image
)

# Import secure email dispatcher
from utils.email_dispatcher import OutlookDispatcher


# ==========================================================
# CONFIGURATION
# ==========================================================

APP_VERSION = "2.1.0"

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
    """
    Legacy PDF generator — produces a single-page executive summary.
    Retained for backward compatibility with existing integrations.

    Args:
        compliance_score (float): Current compliance percentage.
        metrics (dict): Dictionary containing open_risks, closed_risks, high_risks.
        rating (str): Health rating string with emoji indicator.

    Returns:
        BytesIO: Buffer containing the generated PDF document.
    """

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
        f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}"
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


def generate_enhanced_pdf(
    compliance_score,
    metrics,
    rating,
    risk_df,
    controls_df,
    escalated_df,
    trend_df=None
):
    """
    Enhanced multi-page PDF report for monthly management reporting.

    Generates a comprehensive PDF including:
        - Page 1: Executive Summary with KPIs and health rating
        - Page 2: Risk Register breakdown by level and owner
        - Page 3: Escalation Status with overdue risk details
        - Page 4: Control Coverage and compliance trend analysis
        - Page 5: Recommendations and next steps

    Args:
        compliance_score (float): Current compliance percentage.
        metrics (dict): Dictionary with open_risks, closed_risks, high_risks counts.
        rating (str): Health rating string (e.g. "Healthy", "Critical").
        risk_df (DataFrame): Full risk register data.
        controls_df (DataFrame): Control implementation data.
        escalated_df (DataFrame): Risk data with escalation calculations applied.
        trend_df (DataFrame, optional): Compliance history with Month and Score columns.

    Returns:
        BytesIO: Buffer containing the multi-page PDF document.
    """

    buffer = BytesIO()

    # Document setup with professional margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    # Stylesheet configuration
    styles = getSampleStyleSheet()

    # Custom styles for the report
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=20,
        textColor=colors.HexColor("#1a237e")
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=16,
        textColor=colors.HexColor("#283593")
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=8,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name="ReportFooter",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey
    ))

    # Build document elements
    elements = []

    # ======================================================
    # PAGE 1: EXECUTIVE SUMMARY
    # ======================================================

    elements.append(
        Paragraph(
            "Monthly GRC Management Report",
            styles["ReportTitle"]
        )
    )

    elements.append(
        Paragraph(
            f"Report Period: {datetime.now().strftime('%B %Y')}",
            styles["ReportBody"]
        )
    )

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}",
            styles["ReportBody"]
        )
    )

    elements.append(
        Paragraph(
            f"Dashboard Version: {APP_VERSION}",
            styles["ReportBody"]
        )
    )

    elements.append(Spacer(1, 0.5 * inch))

    # Executive Summary Section
    elements.append(
        Paragraph(
            "1. Executive Summary",
            styles["SectionHeader"]
        )
    )

    # Clean rating text (remove emoji for PDF)
    rating_text = rating.replace(
        "🟢 ", ""
    ).replace(
        "🟠 ", ""
    ).replace(
        "🔴 ", ""
    )

    elements.append(
        Paragraph(
            f"The current compliance posture is rated as "
            f"<b>{rating_text}</b> with an overall score of "
            f"<b>{compliance_score}%</b>.",
            styles["ReportBody"]
        )
    )

    elements.append(Spacer(1, 0.3 * inch))

    # KPI Summary Table
    kpi_data = [
        ["Metric", "Value", "Status"],
        [
            "Compliance Score",
            f"{compliance_score}%",
            rating_text
        ],
        [
            "Total Open Risks",
            str(metrics["open_risks"]),
            "Action Required" if metrics["open_risks"] > 0 else "Clear"
        ],
        [
            "High Priority Risks",
            str(metrics["high_risks"]),
            "Critical" if metrics["high_risks"] > 3 else "Manageable"
        ],
        [
            "Closed Risks",
            str(metrics["closed_risks"]),
            "Resolved"
        ],
        [
            "Total Risks Tracked",
            str(len(risk_df)),
            "Active Monitoring"
        ],
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[
            2.5 * inch,
            1.5 * inch,
            2.0 * inch
        ]
    )

    kpi_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        # Body styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        # Alternating row colours
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e8eaf6")),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#e8eaf6")),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#e8eaf6")),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(kpi_table)

    # ======================================================
    # PAGE 2: RISK REGISTER BREAKDOWN
    # ======================================================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "2. Risk Register Analysis",
            styles["SectionHeader"]
        )
    )

    elements.append(
        Paragraph(
            "The following table summarises the current risk register "
            "by owner and severity level.",
            styles["ReportBody"]
        )
    )

    elements.append(Spacer(1, 0.3 * inch))

    # Risk by Owner Table
    owner_agg = (
        risk_df.groupby("Risk_Owner")
        .agg(
            Total=("Risk_ID", "count"),
            High=("Risk_Level", lambda x: (x == "High").sum()),
            Medium=("Risk_Level", lambda x: (x == "Medium").sum()),
            Low=("Risk_Level", lambda x: (x == "Low").sum()),
            Open=("Status", lambda x: (x == "Open").sum()),
            Closed=("Status", lambda x: (x == "Closed").sum()),
        )
        .reset_index()
    )

    risk_table_data = [
        ["Risk Owner", "Total", "High", "Medium", "Low", "Open", "Closed"]
    ]

    for _, row in owner_agg.iterrows():
        risk_table_data.append([
            str(row["Risk_Owner"]),
            str(row["Total"]),
            str(row["High"]),
            str(row["Medium"]),
            str(row["Low"]),
            str(row["Open"]),
            str(row["Closed"]),
        ])

    risk_table = Table(
        risk_table_data,
        colWidths=[
            2.0 * inch,
            0.7 * inch,
            0.7 * inch,
            0.9 * inch,
            0.7 * inch,
            0.7 * inch,
            0.8 * inch
        ]
    )

    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c62828")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(risk_table)

    elements.append(Spacer(1, 0.4 * inch))

    # Risk Level Summary
    elements.append(
        Paragraph(
            "2.1 Risk Level Distribution",
            styles["SectionHeader"]
        )
    )

    level_summary = risk_df["Risk_Level"].value_counts()

    for level in ["High", "Medium", "Low"]:
        count = level_summary.get(level, 0)
        elements.append(
            Paragraph(
                f"<b>{level}:</b> {count} risks "
                f"({round(count / len(risk_df) * 100, 1)}% of total)",
                styles["ReportBody"]
            )
        )

    # ======================================================
    # PAGE 3: ESCALATION STATUS
    # ======================================================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "3. Escalation Status Report",
            styles["SectionHeader"]
        )
    )

    # Overdue risks summary
    overdue_risks = escalated_df[
        escalated_df["Is_Overdue"] == True
    ]

    total_overdue = len(overdue_risks)

    elements.append(
        Paragraph(
            f"There are currently <b>{total_overdue}</b> overdue risks "
            f"requiring escalation action.",
            styles["ReportBody"]
        )
    )

    elements.append(Spacer(1, 0.2 * inch))

    if total_overdue > 0:

        # Escalation breakdown table
        esc_table_data = [
            ["Risk ID", "Risk Name", "Owner", "Days Overdue", "Escalation"]
        ]

        for _, row in overdue_risks.sort_values(
            "Days_Overdue", ascending=False
        ).iterrows():
            esc_table_data.append([
                str(row["Risk_ID"]),
                str(row["Risk_Name"])[:30],
                str(row["Risk_Owner"])[:20],
                str(int(row["Days_Overdue"])),
                str(row["Escalation_Level"]).replace(
                    "Level ", "L"
                )[:25],
            ])

        esc_table = Table(
            esc_table_data,
            colWidths=[
                0.8 * inch,
                2.0 * inch,
                1.5 * inch,
                1.0 * inch,
                1.8 * inch
            ]
        )

        esc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e65100")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))

        elements.append(esc_table)

    else:
        elements.append(
            Paragraph(
                "No overdue risks at this time. All open risks "
                "are within their remediation deadlines.",
                styles["ReportBody"]
            )
        )

    # ======================================================
    # PAGE 4: CONTROL COVERAGE & COMPLIANCE TREND
    # ======================================================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "4. Control Coverage & Compliance Trend",
            styles["SectionHeader"]
        )
    )

    # Control status breakdown
    elements.append(
        Paragraph(
            "4.1 ISO 27001 Control Implementation Status",
            styles["SectionHeader"]
        )
    )

    control_counts = controls_df["Status"].value_counts()
    total_controls = len(controls_df)

    ctrl_table_data = [
        ["Control Status", "Count", "Percentage"]
    ]

    for status in ["Implemented", "In Progress", "Planned"]:
        count = control_counts.get(status, 0)
        pct = round(count / total_controls * 100, 1) if total_controls > 0 else 0
        ctrl_table_data.append([
            status,
            str(count),
            f"{pct}%"
        ])

    ctrl_table = Table(
        ctrl_table_data,
        colWidths=[2.0 * inch, 1.5 * inch, 1.5 * inch]
    )

    ctrl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(ctrl_table)

    elements.append(Spacer(1, 0.4 * inch))

    # Compliance Trend (if available)
    elements.append(
        Paragraph(
            "4.2 Compliance Score Trend",
            styles["SectionHeader"]
        )
    )

    if trend_df is not None and not trend_df.empty:

        trend_table_data = [["Month", "Score (%)", "Movement"]]

        prev_score = None

        for _, row in trend_df.iterrows():
            score = row["Score"]
            if prev_score is not None:
                movement = score - prev_score
                movement_str = (
                    f"+{movement}" if movement > 0
                    else str(movement)
                )
            else:
                movement_str = "-"

            trend_table_data.append([
                str(row["Month"]),
                str(score),
                movement_str
            ])

            prev_score = score

        trend_table = Table(
            trend_table_data,
            colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch]
        )

        trend_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        elements.append(trend_table)

    else:
        elements.append(
            Paragraph(
                "Compliance trend data not available for this period.",
                styles["ReportBody"]
            )
        )

    # ======================================================
    # PAGE 5: RECOMMENDATIONS & SIGN-OFF
    # ======================================================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "5. Recommendations & Next Steps",
            styles["SectionHeader"]
        )
    )

    # Generate dynamic recommendations based on data
    recommendations = []

    if metrics["high_risks"] > 0:
        recommendations.append(
            f"Prioritise remediation of {metrics['high_risks']} "
            f"high-severity risks currently in the register."
        )

    if total_overdue > 0:
        recommendations.append(
            f"Escalate {total_overdue} overdue risk(s) to the "
            f"appropriate governance forum for immediate action."
        )

    if compliance_score < 80:
        recommendations.append(
            "Target 80% compliance threshold by accelerating "
            "control implementation for In Progress and Planned items."
        )

    planned_controls = control_counts.get("Planned", 0)
    if planned_controls > 0:
        recommendations.append(
            f"Initiate implementation planning for {planned_controls} "
            f"controls currently in 'Planned' status."
        )

    if not recommendations:
        recommendations.append(
            "Maintain current compliance posture and continue "
            "monitoring risk register for emerging threats."
        )

    for i, rec in enumerate(recommendations, 1):
        elements.append(
            Paragraph(
                f"{i}. {rec}",
                styles["ReportBody"]
            )
        )

    elements.append(Spacer(1, 0.5 * inch))

    # Sign-off section
    elements.append(
        Paragraph(
            "6. Report Sign-Off",
            styles["SectionHeader"]
        )
    )

    signoff_data = [
        ["Role", "Name", "Date", "Signature"],
        ["Report Author", "", datetime.now().strftime("%d/%m/%Y"), ""],
        ["Reviewed By", "", "", ""],
        ["Approved By", "", "", ""],
    ]

    signoff_table = Table(
        signoff_data,
        colWidths=[1.5 * inch, 2.0 * inch, 1.2 * inch, 1.8 * inch]
    )

    signoff_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(signoff_table)

    elements.append(Spacer(1, 0.5 * inch))

    # Footer
    elements.append(
        Paragraph(
            "CONFIDENTIAL - For internal governance use only.",
            styles["ReportFooter"]
        )
    )

    elements.append(
        Paragraph(
            f"Generated by GRC Compliance Dashboard v{APP_VERSION}",
            styles["ReportFooter"]
        )
    )

    # Build the PDF document
    doc.build(elements)

    buffer.seek(0)

    return buffer


def generate_monthly_summary(
    compliance_score,
    metrics,
    rating,
    risk_df,
    escalated_df,
    trend_df=None
):
    """
    Generates a structured monthly management summary dictionary.

    This function compiles all key governance metrics into a single
    summary object used for both the dashboard display and report
    generation.

    Args:
        compliance_score (float): Current compliance percentage.
        metrics (dict): Risk count metrics.
        rating (str): Health rating string.
        risk_df (DataFrame): Full risk register.
        escalated_df (DataFrame): Risks with escalation data.
        trend_df (DataFrame, optional): Historical compliance scores.

    Returns:
        dict: Comprehensive monthly summary with all key metrics.
    """

    # Calculate month-over-month change
    mom_change = 0.0

    if trend_df is not None and len(trend_df) >= 2:
        current_score = trend_df["Score"].iloc[-1]
        previous_score = trend_df["Score"].iloc[-2]
        mom_change = current_score - previous_score

    # Overdue analysis
    overdue_risks = escalated_df[
        escalated_df["Is_Overdue"] == True
    ]

    # Calculate average days overdue
    avg_days_overdue = (
        overdue_risks["Days_Overdue"].mean()
        if not overdue_risks.empty else 0
    )

    # Build summary structure
    summary = {
        "report_period": datetime.now().strftime("%B %Y"),
        "generated_at": datetime.now().strftime(
            "%d %B %Y %H:%M"
        ),
        "compliance": {
            "score": compliance_score,
            "rating": rating,
            "month_over_month_change": mom_change,
            "target": 80.0,
            "gap_to_target": max(
                0, 80.0 - compliance_score
            ),
        },
        "risks": {
            "total": len(risk_df),
            "open": metrics["open_risks"],
            "closed": metrics["closed_risks"],
            "high": metrics["high_risks"],
            "closure_rate": round(
                metrics["closed_risks"] / len(risk_df) * 100, 1
            ) if len(risk_df) > 0 else 0,
        },
        "escalation": {
            "total_overdue": len(overdue_risks),
            "avg_days_overdue": round(avg_days_overdue, 1),
            "max_days_overdue": int(
                overdue_risks["Days_Overdue"].max()
            ) if not overdue_risks.empty else 0,
            "escalation_rate": round(
                len(overdue_risks) / len(escalated_df) * 100, 1
            ) if len(escalated_df) > 0 else 0,
        },
    }

    return summary


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
# MONTHLY MANAGEMENT REPORT
# ==========================================================

st.subheader(
    "📊 Monthly Management Report"
)

st.markdown(
    """
    This section provides a comprehensive monthly overview
    for senior management and governance committees. Use the
    enhanced PDF export below to generate the full report.
    """
)

# Load trend data for monthly analysis
try:
    trend_df = load_compliance_history()
except Exception:
    trend_df = None

# Generate monthly summary metrics
monthly_summary = generate_monthly_summary(
    compliance_score,
    metrics,
    rating,
    filtered_risk_df,
    escalated_df,
    trend_df
)

# Monthly Report KPI Row
mgmt_c1, mgmt_c2, mgmt_c3, mgmt_c4 = st.columns(4)

mgmt_c1.metric(
    "Compliance Score",
    f"{monthly_summary['compliance']['score']}%",
    delta=f"{monthly_summary['compliance']['month_over_month_change']:+.0f}% MoM"
)

mgmt_c2.metric(
    "Risk Closure Rate",
    f"{monthly_summary['risks']['closure_rate']}%"
)

mgmt_c3.metric(
    "Escalation Rate",
    f"{monthly_summary['escalation']['escalation_rate']}%"
)

mgmt_c4.metric(
    "Gap to Target (80%)",
    f"{monthly_summary['compliance']['gap_to_target']}%"
)

# Month-over-Month Analysis
st.markdown("#### Month-over-Month Analysis")

mgmt_left, mgmt_right = st.columns(2)

with mgmt_left:

    if trend_df is not None and not trend_df.empty:

        # Compliance trend with target line
        trend_fig = go.Figure()

        # Actual compliance scores
        trend_fig.add_trace(
            go.Scatter(
                x=trend_df["Month"],
                y=trend_df["Score"],
                mode="lines+markers",
                name="Compliance Score",
                line=dict(
                    color="#1a237e",
                    width=3
                ),
                marker=dict(size=8)
            )
        )

        # Target threshold line
        trend_fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            annotation_text="Target: 80%"
        )

        trend_fig.update_layout(
            title="Compliance Score Trend vs Target",
            yaxis_title="Score (%)",
            xaxis_title="Month",
            yaxis_range=[0, 100]
        )

        st.plotly_chart(
            trend_fig,
            use_container_width=True,
            key="mgmt_trend"
        )

    else:
        st.info(
            "Compliance trend data not available."
        )

with mgmt_right:

    # Management summary card
    st.markdown(
        f"""
**Report Period:** {monthly_summary['report_period']}

**Overall Position:** {monthly_summary['compliance']['rating']}

---

| Metric | Value |
|--------|-------|
| Total Risks | {monthly_summary['risks']['total']} |
| Open Risks | {monthly_summary['risks']['open']} |
| High Risks | {monthly_summary['risks']['high']} |
| Overdue Risks | {monthly_summary['escalation']['total_overdue']} |
| Avg Days Overdue | {monthly_summary['escalation']['avg_days_overdue']} |
| Max Days Overdue | {monthly_summary['escalation']['max_days_overdue']} |

---

**Key Actions Required:**
"""
    )

    # Dynamic recommendations
    if monthly_summary["escalation"]["total_overdue"] > 0:
        st.warning(
            f"⚠️ {monthly_summary['escalation']['total_overdue']} "
            f"risk(s) require escalation action."
        )

    if monthly_summary["compliance"]["gap_to_target"] > 0:
        st.warning(
            f"📈 {monthly_summary['compliance']['gap_to_target']}% "
            f"improvement needed to reach 80% target."
        )

    if monthly_summary["risks"]["high"] > 3:
        st.error(
            f"🔴 {monthly_summary['risks']['high']} high-severity "
            f"risks exceed acceptable threshold."
        )

    if (
        monthly_summary["escalation"]["total_overdue"] == 0
        and monthly_summary["compliance"]["gap_to_target"] == 0
    ):
        st.success(
            "✅ All governance indicators within acceptable limits."
        )


# ==========================================================
# EXPORTS (ENHANCED)
# ==========================================================

st.subheader(
    "📥 Exports"
)

st.markdown(
    """
    Download reports in CSV or PDF format. The **Enhanced PDF**
    includes a full multi-page management report with executive
    summary, risk breakdown, escalation status, control coverage,
    and recommendations.
    """
)

export_c1, export_c2, export_c3 = st.columns(3)

with export_c1:

    # CSV Export
    st.download_button(
        "📥 Risk Register (CSV)",
        filtered_risk_df.to_csv(index=False),
        "risk_register_export.csv",
        "text/csv",
        key="csv_export"
    )

with export_c2:

    # Legacy single-page PDF
    legacy_pdf = generate_pdf(
        compliance_score,
        metrics,
        rating
    )

    st.download_button(
        "📄 Quick Summary (PDF)",
        legacy_pdf,
        "executive_summary.pdf",
        "application/pdf",
        key="legacy_pdf_export"
    )

with export_c3:

    # Enhanced multi-page PDF report
    enhanced_pdf = generate_enhanced_pdf(
        compliance_score=compliance_score,
        metrics=metrics,
        rating=rating,
        risk_df=filtered_risk_df,
        controls_df=controls_df,
        escalated_df=escalated_df,
        trend_df=trend_df
    )

    st.download_button(
        "📑 Full Management Report (PDF)",
        enhanced_pdf,
        f"grc_management_report_{datetime.now().strftime('%Y_%m')}.pdf",
        "application/pdf",
        key="enhanced_pdf_export"
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
# ==========================================================
# AUTOMATED REMINDER DISPATCH (OUTLOOK INTEGRATION)
# ==========================================================

st.subheader(
    "📨 Automated Reminder Dispatch"
)

st.markdown(
    """
    Send risk remediation reminders directly via Outlook.
    Emails are dispatched through your authenticated Outlook
    desktop client — **no credentials are stored or transmitted**.

    🔒 **Security:** All emails route through corporate Exchange
    with full DLP, retention policies, and audit trail.
    """
)

# Initialise the Outlook dispatcher (cached per session)
if "email_dispatcher" not in st.session_state:
    st.session_state.email_dispatcher = OutlookDispatcher()

dispatcher = st.session_state.email_dispatcher

# Show connection status
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    if dispatcher.is_available:
        st.success("🟢 Outlook Connected")
    else:
        st.error("🔴 Outlook Not Available")

with status_col2:
    stats = dispatcher.get_session_stats()
    st.metric(
        "Emails Sent (Session)",
        stats["emails_sent"]
    )

with status_col3:
    st.metric(
        "Remaining Quota",
        stats["remaining_quota"]
    )

# --- Individual Reminder ---
st.markdown("#### Send Individual Reminder")

available_owners = sorted(
    filtered_risk_df[
        "Risk_Owner"
    ].unique()
)

selected_owner = st.selectbox(
    "Select Risk Owner",
    available_owners,
    key="reminder_owner_select"
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

# Build the email content with overdue information
risk_lines = []

for _, row in open_risks.iterrows():

    due_info = ""
    if "Due_Date" in row and pd.notna(row.get("Due_Date")):
        due_date = pd.to_datetime(row["Due_Date"])
        days_diff = (datetime.now() - due_date).days
        if days_diff > 0:
            due_info = f" [OVERDUE by {days_diff} days]"
        else:
            due_info = f" [Due: {due_date.strftime('%Y-%m-%d')}]"

    risk_lines.append(
        f"- {row['Risk_ID']} : "
        f"{row['Risk_Name']} "
        f"({row['Risk_Level']}){due_info}"
    )

risk_list = "\n".join(risk_lines)

email_subject = "Risk Remediation Status Update Required"

email_body = (
    f"Hello {selected_owner},\n\n"
    f"Please review the following open risks assigned "
    f"to your team:\n\n"
    f"{risk_list}\n\n"
    f"Please provide an update on:\n\n"
    f"  - Current remediation progress\n"
    f"  - Expected completion date\n"
    f"  - Any blockers preventing resolution\n\n"
    f"Your response will support Governance & "
    f"Assurance reporting activities.\n\n"
    f"Kind Regards,\n"
    f"Cyber Security Governance & Assurance\n\n"
    f"---\n"
    f"Sent via GRC Compliance Dashboard v{APP_VERSION}"
)

# Email preview
st.markdown("**Preview:**")

preview_col1, preview_col2 = st.columns([1, 3])

with preview_col1:
    st.markdown(f"**To:** {owner_email}")
    st.markdown(f"**Subject:** {email_subject}")
    st.markdown("**Priority:** High")

with preview_col2:
    st.text_area(
        "Email Body",
        email_body,
        height=250,
        key="email_preview",
        disabled=True
    )

# Confirmation and send controls
st.markdown("---")

send_col1, send_col2 = st.columns([1, 3])

with send_col1:

    # Explicit confirmation checkbox (security measure)
    confirm_send = st.checkbox(
        "I confirm this email is correct",
        key="confirm_individual_send"
    )

with send_col2:

    if st.button(
        "📧 Send Reminder via Outlook",
        disabled=not confirm_send,
        key="send_individual_btn"
    ):
        if not dispatcher.is_available:
            st.error(
                "Outlook is not available. Ensure the "
                "desktop client is running and try again."
            )
        elif not confirm_send:
            st.warning(
                "Please confirm the email before sending."
            )
        else:
            # Dispatch the email
            result = dispatcher.send_reminder(
                to=owner_email,
                subject=email_subject,
                body=email_body,
                importance="High"
            )

            if result["success"]:
                st.success(
                    f"✅ {result['message']}"
                )
            else:
                st.error(
                    f"❌ {result['message']}"
                )


# --- Bulk Reminder for Overdue Risks ---
st.markdown("---")
st.markdown("#### 🚨 Bulk Dispatch: All Overdue Risk Owners")

st.markdown(
    """
    Send reminders to **all** owners with overdue risks in a single
    action. Each owner receives an individual email (no BCC) for
    full transparency and audit compliance.
    """
)

if not overdue_df.empty:

    # Show who will receive emails
    overdue_owners = (
        overdue_df[["Risk_Owner", "Owner_Email"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    st.dataframe(
        overdue_owners,
        use_container_width=True,
        column_config={
            "Risk_Owner": "Recipient",
            "Owner_Email": "Email Address"
        }
    )

    st.caption(
        f"{len(overdue_owners)} owner(s) will receive reminders."
    )

    # Bulk send controls with double confirmation
    bulk_col1, bulk_col2 = st.columns([1, 3])

    with bulk_col1:
        confirm_bulk = st.checkbox(
            "I authorise bulk dispatch",
            key="confirm_bulk_send"
        )

    with bulk_col2:

        if st.button(
            f"🚨 Send {len(overdue_owners)} Reminder(s)",
            disabled=not confirm_bulk,
            key="send_bulk_btn"
        ):
            if not dispatcher.is_available:
                st.error(
                    "Outlook is not available."
                )
            else:
                # Build recipient list
                recipients = []
                for _, owner_row in overdue_owners.iterrows():
                    recipients.append({
                        "email": owner_row["Owner_Email"],
                        "name": owner_row["Risk_Owner"]
                    })

                # Bulk dispatch template
                bulk_subject = (
                    "URGENT: Overdue Risk Remediation Required"
                )

                bulk_body_template = (
                    "Hello {name},\n\n"
                    "This is an automated reminder that one or more "
                    "risks assigned to your team have exceeded their "
                    "remediation due date.\n\n"
                    "Please review your overdue risks in the GRC "
                    "Compliance Dashboard and provide an immediate "
                    "status update.\n\n"
                    "Required actions:\n"
                    "  - Review all overdue risks assigned to you\n"
                    "  - Provide revised completion dates\n"
                    "  - Escalate any blockers to your line manager\n\n"
                    "Failure to respond may result in further "
                    "escalation per the GRC Escalation Policy.\n\n"
                    "Kind Regards,\n"
                    "Cyber Security Governance & Assurance\n\n"
                    "---\n"
                    f"Sent via GRC Compliance Dashboard v{APP_VERSION}"
                )

                # Send bulk reminders
                results = dispatcher.send_bulk_reminders(
                    recipients=recipients,
                    subject=bulk_subject,
                    body_template=bulk_body_template,
                    importance="High"
                )

                # Display results
                sent_count = sum(
                    1 for r in results if r["success"]
                )
                failed_count = len(results) - sent_count

                if sent_count > 0:
                    st.success(
                        f"✅ {sent_count} reminder(s) sent successfully."
                    )

                if failed_count > 0:
                    st.error(
                        f"❌ {failed_count} email(s) failed to send."
                    )

                # Show detailed results
                for r in results:
                    if not r["success"]:
                        st.warning(
                            f"⚠️ {r['recipient']}: {r['message']}"
                        )

else:
    st.info(
        "✅ No overdue risks — no bulk reminders required."
    )


# --- Audit Log Viewer ---
st.markdown("---")
st.markdown("#### 📋 Email Audit Log")

st.markdown(
    """
    All email dispatch activity is recorded for governance
    and compliance purposes. This log is stored locally at
    `logs/email_audit.csv`.
    """
)

audit_entries = dispatcher.get_audit_log()

if audit_entries:
    audit_df = pd.DataFrame(audit_entries)
    st.dataframe(
        audit_df,
        use_container_width=True
    )
    st.caption(
        f"Showing {len(audit_entries)} audit entries."
    )
else:
    st.info(
        "No email dispatch activity recorded yet."
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
    use_container_width=True
)


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption(
    f"GRC Compliance Dashboard | Version {APP_VERSION}"
)