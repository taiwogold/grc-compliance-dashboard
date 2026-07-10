"""
GRC Compliance Dashboard
Version: 2.1.1
Author: Taiwo Durodola-Tunde

Main application file — handles layout, UI components, and
orchestration. All business logic lives in the utils/ package.

Release Notes:
    v2.2.0 - Audit, History & Intelligence
    v2.1.1 - Modular refactor (no feature changes)
    v2.1.0 - Outlook Integration & Automated Reminder Dispatch
    v2.0.2 - Monthly Management Reports & Enhanced PDF Exports
    v2.0.1 - Overdue Risk Escalation Tracking
    v2.0.0 - Initial release with KPI dashboard

Architecture:
    dashboard.py          - UI layout and orchestration (this file)
    utils/data_loader.py  - CSV loading, validation, caching
    utils/metrics.py      - Compliance scoring, escalation, summaries
    utils/charts.py       - Plotly chart generation
    utils/pdf_generator.py - PDF report generation
    utils/email_dispatcher.py - Secure Outlook email dispatch
"""

import sys
sys.dont_write_bytecode = True

from datetime import datetime

import pandas as pd
import streamlit as st

# Import all utilities from the modular package
from utils import (
    # Data loading
    load_risk_register,
    load_controls,
    load_compliance_history,
    validate_dataframe,
    RISK_REGISTER_REQUIRED_COLUMNS,
    # Metrics & calculations
    calculate_compliance_score,
    calculate_risk_metrics,
    calculate_escalation,
    determine_health_rating,
    generate_monthly_summary,
    # Charts
    create_compliance_trend_chart,
    create_control_pie_chart,
    create_risk_bar_chart,
    create_risk_status_pie,
    create_heatmap,
    create_escalation_bar_chart,
    create_overdue_timeline,
    create_management_trend_chart,
    create_score_distribution_chart,
    create_score_waterfall_chart,
    # PDF
    generate_pdf,
    generate_enhanced_pdf,
    set_version,
    # Email
    OutlookDispatcher,
    # Risk Scoring
    calculate_risk_scores,
    get_top_risks,
    get_score_distribution,
    # Database / History
    init_database,
    capture_snapshot,
    get_snapshots,
    get_snapshot_detail,
    get_risk_history,
    get_latest_delta,
    get_snapshot_count,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

APP_VERSION = "2.2.0-alpha.2"

# Set version in PDF module
set_version(APP_VERSION)

st.set_page_config(
    page_title="GRC Compliance Dashboard",
    layout="wide"
)

# Optional Banner
try:
    st.image("assets/banner.png", width="stretch")
except Exception:
    pass

st.title("🛡️ GRC Compliance Dashboard")
st.caption(f"Version {APP_VERSION}")
st.caption(
    f"Last Refreshed: {datetime.now().strftime('%d %b %Y %H:%M')}"
)


# ==========================================================
# LOAD DATA
# ==========================================================

try:
    risk_df = load_risk_register()
    controls_df = load_controls()
except Exception as e:
    st.error(f"Unable to load source files: {e}")
    st.stop()


# ==========================================================
# SIDEBAR: UPLOAD & ACTIONS
# ==========================================================

st.sidebar.header("Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload Risk Register CSV", type=["csv"]
)

if uploaded_file:
    risk_df = pd.read_csv(uploaded_file)

if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()


# ==========================================================
# DATA VALIDATION
# ==========================================================

missing_columns = validate_dataframe(
    risk_df, RISK_REGISTER_REQUIRED_COLUMNS
)

if missing_columns:
    st.error(
        f"Missing required columns: {', '.join(missing_columns)}"
    )
    st.stop()


# ==========================================================
# SIDEBAR: FILTERS
# ==========================================================

st.sidebar.header("Filters")

owners = sorted(risk_df["Risk_Owner"].dropna().unique())

selected_owners = st.sidebar.multiselect(
    "Risk Owner", options=owners, default=owners
)

filtered_risk_df = risk_df[
    risk_df["Risk_Owner"].isin(selected_owners)
]

if filtered_risk_df.empty:
    st.warning("No records found for the selected filters.")
    st.stop()


# ==========================================================
# KPI CALCULATIONS
# ==========================================================

compliance_score = calculate_compliance_score(controls_df)
metrics = calculate_risk_metrics(filtered_risk_df)
rating = determine_health_rating(compliance_score)


# ==========================================================
# KPI DASHBOARD
# ==========================================================

c1, c2, c3, c4 = st.columns(4)
c1.metric("Compliance Score", f"{compliance_score}%")
c2.metric("Open Risks", metrics["open_risks"])
c3.metric("Closed Risks", metrics["closed_risks"])
c4.metric("High Risks", metrics["high_risks"])


# ==========================================================
# EXECUTIVE SUMMARY
# ==========================================================

st.subheader("Executive Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.info(f"""
### Compliance Position
**Compliance Score:** {compliance_score}%

**Current Status:** {rating}
""")

with summary_col2:
    st.info(f"""
### Risk Overview
**Open Risks:** {metrics['open_risks']}

**Closed Risks:** {metrics['closed_risks']}

**High Risks:** {metrics['high_risks']}
""")


# ==========================================================
# COMPLIANCE TREND + ISO COVERAGE
# ==========================================================

chart_left, chart_right = st.columns(2)

with chart_left:
    st.subheader("Compliance Trend")
    try:
        trend_df = load_compliance_history()
        trend_chart = create_compliance_trend_chart(trend_df)
        st.plotly_chart(trend_chart, width="stretch", key="trend_chart")
    except Exception:
        trend_df = None
        st.warning("compliance_history.csv not found")

with chart_right:
    st.subheader("ISO 27001 Control Coverage")
    iso_chart = create_control_pie_chart(controls_df)
    st.plotly_chart(iso_chart, width="stretch", key="iso_chart")


# ==========================================================
# CONTROL STATUS
# ==========================================================

st.subheader("Control Status")
control_chart = create_control_pie_chart(
    controls_df, title="Control Implementation Status"
)
st.plotly_chart(control_chart, width="stretch", key="control_chart")


# ==========================================================
# RISK ANALYSIS
# ==========================================================

left, right = st.columns(2)

with left:
    risk_chart = create_risk_bar_chart(filtered_risk_df)
    st.plotly_chart(risk_chart, width="stretch", key="risk_distribution")

with right:
    status_chart = create_risk_status_pie(filtered_risk_df)
    st.plotly_chart(status_chart, width="stretch", key="risk_status")


# ==========================================================
# RISK HEAT MAP
# ==========================================================

st.subheader("Risk Heat Map")
heatmap = create_heatmap(filtered_risk_df)
st.plotly_chart(heatmap, width="stretch", key="heatmap")


# ==========================================================
# RISK SCORING ENGINE
# ==========================================================

st.subheader("🎯 Risk Scoring Engine")

st.markdown("""
Quantitative risk scoring using a weighted formula:
**Score = (Likelihood × Impact) × Overdue Modifier × Control Modifier**

Overdue risks are penalised up to 2× their base score. Implemented
controls reduce the score by 50%.
""")

# Apply scoring
scored_df = calculate_risk_scores(filtered_risk_df)

# --- Initialise database and capture daily snapshot ---
init_database()
capture_snapshot(
    risk_df=filtered_risk_df,
    compliance_score=compliance_score,
    scored_df=scored_df
)

# Score KPIs
score_dist = get_score_distribution(scored_df)
sc1, sc2, sc3, sc4 = st.columns(4)
sc1.metric("🟣 Critical", score_dist["Critical"])
sc2.metric("🔴 High", score_dist["High"])
sc3.metric("🟡 Medium", score_dist["Medium"])
sc4.metric("🟢 Low", score_dist["Low"])

# Top 5 Risks
st.markdown("#### Top 5 Risks by Residual Score")
top_risks = get_top_risks(scored_df, n=5)
st.dataframe(
    top_risks,
    width="stretch",
    column_config={
        "Residual_Risk_Score": st.column_config.NumberColumn(
            "Risk Score", format="%.1f"
        ),
        "Base_Score": st.column_config.NumberColumn(
            "Base (L×I)", format="%.0f"
        ),
        "Overdue_Modifier": st.column_config.NumberColumn(
            "Overdue ×", format="%.2f"
        ),
        "Control_Modifier": st.column_config.NumberColumn(
            "Control ×", format="%.2f"
        ),
    }
)

# Score Charts
score_left, score_right = st.columns(2)

with score_left:
    score_dist_chart = create_score_distribution_chart(scored_df)
    st.plotly_chart(score_dist_chart, width="stretch", key="score_dist")

with score_right:
    score_top_chart = create_score_waterfall_chart(top_risks)
    st.plotly_chart(score_top_chart, width="stretch", key="score_top")


# ==========================================================
# RISK OWNER SUMMARY
# ==========================================================

st.subheader("Risk Owner Summary")

owner_summary = (
    filtered_risk_df
    .groupby("Risk_Owner")
    .agg(
        Open_Risks=("Status", lambda x: (x == "Open").sum()),
        High_Risks=("Risk_Level", lambda x: (x == "High").sum()),
    )
    .reset_index()
)

st.dataframe(owner_summary, width="stretch")


# ==========================================================
# ESCALATION TRACKING & OVERDUE RISK DASHBOARD
# ==========================================================

st.subheader("⚠️ Overdue Risk Escalation Dashboard")

# Apply escalation logic
escalated_df = calculate_escalation(filtered_risk_df)

overdue_df = escalated_df[
    escalated_df["Is_Overdue"] == True
].sort_values("Days_Overdue", ascending=False)

# Overdue KPIs
esc_c1, esc_c2, esc_c3, esc_c4 = st.columns(4)
total_overdue = len(overdue_df)
level_counts = overdue_df["Escalation_Level"].value_counts()

esc_c1.metric("🔴 Total Overdue", total_overdue)
esc_c2.metric(
    "⚡ Level 3+",
    level_counts.get("Level 3 - Director Escalation", 0)
    + level_counts.get("Level 4 - Executive Escalation", 0)
)
esc_c3.metric(
    "📅 Most Overdue (Days)",
    int(overdue_df["Days_Overdue"].max()) if not overdue_df.empty else 0
)
esc_c4.metric(
    "📊 Escalation Rate",
    f"{round(total_overdue / len(escalated_df) * 100, 1)}%"
    if len(escalated_df) > 0 else "0%"
)

# Overdue Risks Table
if not overdue_df.empty:
    st.markdown("#### Overdue Risks by Escalation Level")

    display_cols = [
        "Risk_ID", "Risk_Name", "Risk_Level", "Risk_Owner",
        "Due_Date", "Days_Overdue", "Escalation_Level", "Control_Status"
    ]
    available_cols = [c for c in display_cols if c in overdue_df.columns]
    overdue_display = overdue_df[available_cols].copy()

    if "Due_Date" in overdue_display.columns:
        overdue_display["Due_Date"] = (
            overdue_display["Due_Date"].dt.strftime("%Y-%m-%d")
        )

    st.dataframe(
        overdue_display,
        width="stretch",
        column_config={
            "Days_Overdue": st.column_config.NumberColumn(
                "Days Overdue", help="Days past the due date"
            ),
            "Escalation_Level": st.column_config.TextColumn(
                "Escalation Level", help="Current escalation tier"
            ),
        }
    )

    # Charts
    esc_left, esc_right = st.columns(2)

    with esc_left:
        st.markdown("#### Escalation Level Distribution")
        esc_chart = create_escalation_bar_chart(overdue_df)
        st.plotly_chart(
            esc_chart, width="stretch", key="escalation_distribution"
        )

    with esc_right:
        st.markdown("#### Overdue Risks by Owner")
        owner_overdue = (
            overdue_df.groupby("Risk_Owner")
            .agg(
                Overdue_Count=("Risk_ID", "count"),
                Max_Days_Overdue=("Days_Overdue", "max"),
                Highest_Escalation=("Escalation_Level", "max"),
            )
            .reset_index()
            .sort_values("Max_Days_Overdue", ascending=False)
        )
        st.dataframe(owner_overdue, width="stretch")

    # Timeline
    st.markdown("#### Overdue Risk Timeline")
    timeline_chart = create_overdue_timeline(overdue_df)
    st.plotly_chart(
        timeline_chart, width="stretch", key="overdue_timeline"
    )

else:
    st.success(
        "✅ No overdue risks. All open risks are within their due dates."
    )

# Upcoming Due Dates
st.markdown("#### 📅 Risks Due Within 14 Days")

upcoming_df = escalated_df[
    (escalated_df["Days_Remaining"] >= 0)
    & (escalated_df["Days_Remaining"] <= 14)
    & (escalated_df["Status"] == "Open")
].sort_values("Days_Remaining")

if not upcoming_df.empty:
    upcoming_display = upcoming_df[
        ["Risk_ID", "Risk_Name", "Risk_Level",
         "Risk_Owner", "Due_Date", "Days_Remaining"]
    ].copy()
    upcoming_display["Due_Date"] = (
        upcoming_display["Due_Date"].dt.strftime("%Y-%m-%d")
    )
    st.dataframe(
        upcoming_display,
        width="stretch",
        column_config={
            "Days_Remaining": st.column_config.NumberColumn(
                "Days Until Due", help="Days until the due date"
            )
        }
    )
else:
    st.info("No risks due within the next 14 days.")


# ==========================================================
# RISK REGISTER
# ==========================================================

st.subheader("Risk Register")
st.dataframe(filtered_risk_df, width="stretch")
st.caption(f"Displaying {len(filtered_risk_df)} risk records.")


# ==========================================================
# RISK HISTORY & SNAPSHOTS
# ==========================================================

st.subheader("📸 Risk History & Snapshots")

st.markdown("""
The dashboard captures a daily snapshot of the risk register
to enable historical comparison, trend analysis, and audit evidence.
Snapshots are stored locally in `data/grc_history.db`.
""")

# Snapshot summary
snapshot_count = get_snapshot_count()
snapshots_df = get_snapshots()

hist_c1, hist_c2, hist_c3 = st.columns(3)
hist_c1.metric("Total Snapshots", snapshot_count)

if not snapshots_df.empty:
    hist_c2.metric("First Snapshot", snapshots_df["snapshot_date"].iloc[-1])
    hist_c3.metric("Latest Snapshot", snapshots_df["snapshot_date"].iloc[0])

# Delta since last snapshot
delta = get_latest_delta()
if delta:
    st.markdown("#### Changes Since Last Snapshot")
    d_c1, d_c2, d_c3, d_c4, d_c5 = st.columns(5)
    d_c1.metric(
        "Total Risks",
        filtered_risk_df.shape[0],
        delta=f"{delta['delta_total']:+d}" if delta["delta_total"] != 0 else None
    )
    d_c2.metric(
        "Open Risks",
        metrics["open_risks"],
        delta=f"{delta['delta_open']:+d}" if delta["delta_open"] != 0 else None,
        delta_color="inverse"
    )
    d_c3.metric(
        "Closed Risks",
        metrics["closed_risks"],
        delta=f"{delta['delta_closed']:+d}" if delta["delta_closed"] != 0 else None
    )
    d_c4.metric(
        "High Risks",
        metrics["high_risks"],
        delta=f"{delta['delta_high']:+d}" if delta["delta_high"] != 0 else None,
        delta_color="inverse"
    )
    d_c5.metric(
        "Compliance",
        f"{compliance_score}%",
        delta=f"{delta['delta_compliance']:+.1f}%" if delta["delta_compliance"] != 0 else None
    )
    st.caption(
        f"Comparing {delta['date_current']} vs {delta['date_previous']}"
    )

# Snapshot history table
if not snapshots_df.empty:
    st.markdown("#### Snapshot History")
    st.dataframe(
        snapshots_df[
            ["snapshot_date", "total_risks", "open_risks",
             "closed_risks", "high_risks", "compliance_score"]
        ],
        width="stretch",
        column_config={
            "snapshot_date": "Date",
            "total_risks": "Total",
            "open_risks": "Open",
            "closed_risks": "Closed",
            "high_risks": "High",
            "compliance_score": st.column_config.NumberColumn(
                "Compliance %", format="%.1f"
            ),
        }
    )

# Individual risk tracking
st.markdown("#### 🔍 Track Individual Risk")

all_risk_ids = sorted(filtered_risk_df["Risk_ID"].unique())
selected_risk_id = st.selectbox(
    "Select Risk ID to view history",
    all_risk_ids,
    key="risk_history_select"
)

if selected_risk_id:
    risk_hist_df = get_risk_history(selected_risk_id)

    if not risk_hist_df.empty:
        st.dataframe(
            risk_hist_df,
            width="stretch",
            column_config={
                "snapshot_date": "Date",
                "risk_level": "Level",
                "status": "Status",
                "risk_owner": "Owner",
                "residual_score": st.column_config.NumberColumn(
                    "Risk Score", format="%.1f"
                ),
            }
        )

        # Score trend for this risk
        if "residual_score" in risk_hist_df.columns and risk_hist_df["residual_score"].notna().any():
            import plotly.express as px
            score_trend = px.line(
                risk_hist_df,
                x="snapshot_date",
                y="residual_score",
                markers=True,
                title=f"Risk Score Trend: {selected_risk_id}"
            )
            st.plotly_chart(score_trend, width="stretch", key="risk_score_trend")
    else:
        st.info(
            f"No history available for {selected_risk_id}. "
            f"History builds over time as daily snapshots are captured."
        )


# ==========================================================
# MONTHLY MANAGEMENT REPORT
# ==========================================================

st.subheader("📊 Monthly Management Report")

st.markdown("""
This section provides a comprehensive monthly overview for senior
management and governance committees. Use the enhanced PDF export
below to generate the full report.
""")

# Load trend data
try:
    trend_df = load_compliance_history()
except Exception:
    trend_df = None

# Generate monthly summary
monthly_summary = generate_monthly_summary(
    compliance_score, metrics, rating,
    filtered_risk_df, escalated_df, trend_df
)

# Monthly KPIs
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
        trend_fig = create_management_trend_chart(trend_df)
        st.plotly_chart(
            trend_fig, width="stretch", key="mgmt_trend"
        )
    else:
        st.info("Compliance trend data not available.")

with mgmt_right:
    st.markdown(f"""
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
""")

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
        st.success("✅ All governance indicators within acceptable limits.")


# ==========================================================
# EXPORTS
# ==========================================================

st.subheader("📥 Exports")

st.markdown("""
Download reports in CSV or PDF format. The **Enhanced PDF** includes
a full multi-page management report with executive summary, risk
breakdown, escalation status, control coverage, and recommendations.
""")

export_c1, export_c2, export_c3 = st.columns(3)

with export_c1:
    st.download_button(
        "📥 Risk Register (CSV)",
        filtered_risk_df.to_csv(index=False),
        "risk_register_export.csv",
        "text/csv",
        key="csv_export"
    )

with export_c2:
    legacy_pdf = generate_pdf(compliance_score, metrics, rating)
    st.download_button(
        "📄 Quick Summary (PDF)",
        legacy_pdf,
        "executive_summary.pdf",
        "application/pdf",
        key="legacy_pdf_export"
    )

with export_c3:
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
# AUTOMATED REMINDER DISPATCH (OUTLOOK INTEGRATION)
# ==========================================================

st.subheader("📨 Automated Reminder Dispatch")

st.markdown("""
Send risk remediation reminders directly via Outlook. Emails are
dispatched through your authenticated Outlook desktop client —
**no credentials are stored or transmitted**.

🔒 **Security:** All emails route through corporate Exchange with
full DLP, retention policies, and audit trail.
""")

# Initialise dispatcher (cached per session)
if "email_dispatcher" not in st.session_state:
    st.session_state.email_dispatcher = OutlookDispatcher()

dispatcher = st.session_state.email_dispatcher

# Connection status
status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    if dispatcher.is_available:
        st.success("🟢 Outlook Connected")
    else:
        st.error("🔴 Outlook Not Available")
with status_col2:
    stats = dispatcher.get_session_stats()
    st.metric("Emails Sent (Session)", stats["emails_sent"])
with status_col3:
    st.metric("Remaining Quota", stats["remaining_quota"])

# --- Individual Reminder ---
st.markdown("#### Send Individual Reminder")

available_owners = sorted(filtered_risk_df["Risk_Owner"].unique())
selected_owner = st.selectbox(
    "Select Risk Owner", available_owners, key="reminder_owner_select"
)

owner_risks = filtered_risk_df[
    filtered_risk_df["Risk_Owner"] == selected_owner
]
owner_email = owner_risks["Owner_Email"].iloc[0]
open_risks = owner_risks[owner_risks["Status"] == "Open"]

# Build email content
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
        f"- {row['Risk_ID']} : {row['Risk_Name']} "
        f"({row['Risk_Level']}){due_info}"
    )

risk_list = "\n".join(risk_lines)
email_subject = "Risk Remediation Status Update Required"
email_body = (
    f"Hello {selected_owner},\n\n"
    f"Please review the following open risks assigned to your team:\n\n"
    f"{risk_list}\n\n"
    f"Please provide an update on:\n\n"
    f"  - Current remediation progress\n"
    f"  - Expected completion date\n"
    f"  - Any blockers preventing resolution\n\n"
    f"Your response will support Governance & Assurance reporting.\n\n"
    f"Kind Regards,\n"
    f"Cyber Security Governance & Assurance\n\n"
    f"---\n"
    f"Sent via GRC Compliance Dashboard v{APP_VERSION}"
)

# Preview
st.markdown("**Preview:**")
preview_col1, preview_col2 = st.columns([1, 3])
with preview_col1:
    st.markdown(f"**To:** {owner_email}")
    st.markdown(f"**Subject:** {email_subject}")
    st.markdown("**Priority:** High")
with preview_col2:
    st.text_area(
        "Email Body", email_body, height=250,
        key="email_preview", disabled=True
    )

# Send controls
st.markdown("---")
send_col1, send_col2 = st.columns([1, 3])

with send_col1:
    confirm_send = st.checkbox(
        "I confirm this email is correct", key="confirm_individual_send"
    )

with send_col2:
    if st.button(
        "📧 Send Reminder via Outlook",
        disabled=not confirm_send,
        key="send_individual_btn"
    ):
        if not dispatcher.is_available:
            st.error(
                "Outlook is not available. Ensure the desktop "
                "client is running and try again."
            )
        else:
            result = dispatcher.send_reminder(
                to=owner_email,
                subject=email_subject,
                body=email_body,
                importance="High"
            )
            if result["success"]:
                st.success(f"✅ {result['message']}")
            else:
                st.error(f"❌ {result['message']}")


# --- Bulk Reminder for Overdue Risks ---
st.markdown("---")
st.markdown("#### 🚨 Bulk Dispatch: All Overdue Risk Owners")

st.markdown("""
Send reminders to **all** owners with overdue risks. Each owner
receives an individual email (no BCC) for full transparency.
""")

if not overdue_df.empty:
    overdue_owners = (
        overdue_df[["Risk_Owner", "Owner_Email"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    st.dataframe(
        overdue_owners, width="stretch",
        column_config={
            "Risk_Owner": "Recipient",
            "Owner_Email": "Email Address"
        }
    )
    st.caption(f"{len(overdue_owners)} owner(s) will receive reminders.")

    bulk_col1, bulk_col2 = st.columns([1, 3])
    with bulk_col1:
        confirm_bulk = st.checkbox(
            "I authorise bulk dispatch", key="confirm_bulk_send"
        )
    with bulk_col2:
        if st.button(
            f"🚨 Send {len(overdue_owners)} Reminder(s)",
            disabled=not confirm_bulk,
            key="send_bulk_btn"
        ):
            if not dispatcher.is_available:
                st.error("Outlook is not available.")
            else:
                recipients = [
                    {"email": r["Owner_Email"], "name": r["Risk_Owner"]}
                    for _, r in overdue_owners.iterrows()
                ]
                bulk_body_template = (
                    "Hello {name},\n\n"
                    "This is an automated reminder that one or more "
                    "risks assigned to your team have exceeded their "
                    "remediation due date.\n\n"
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
                results = dispatcher.send_bulk_reminders(
                    recipients=recipients,
                    subject="URGENT: Overdue Risk Remediation Required",
                    body_template=bulk_body_template,
                    importance="High"
                )
                sent = sum(1 for r in results if r["success"])
                failed = len(results) - sent
                if sent > 0:
                    st.success(f"✅ {sent} reminder(s) sent successfully.")
                if failed > 0:
                    st.error(f"❌ {failed} email(s) failed to send.")
                for r in results:
                    if not r["success"]:
                        st.warning(f"⚠️ {r['recipient']}: {r['message']}")
else:
    st.info("✅ No overdue risks — no bulk reminders required.")


# --- Audit Log ---
st.markdown("---")
st.markdown("#### 📋 Email Audit Log")
st.markdown("""
All dispatch activity is recorded at `logs/email_audit.csv`
for governance and compliance purposes.
""")

audit_entries = dispatcher.get_audit_log()
if audit_entries:
    audit_df = pd.DataFrame(audit_entries)
    st.dataframe(audit_df, width="stretch")
    st.caption(f"Showing {len(audit_entries)} audit entries.")
else:
    st.info("No email dispatch activity recorded yet.")


# ==========================================================
# RISK OWNER EMAIL DIRECTORY
# ==========================================================

st.subheader("📧 Risk Owner Email Directory")

owner_directory = (
    risk_df[["Risk_Owner", "Owner_Email"]]
    .drop_duplicates()
    .sort_values("Risk_Owner")
)
st.dataframe(owner_directory, width="stretch")


# ==========================================================
# FOOTER
# ==========================================================

st.divider()
st.caption(f"GRC Compliance Dashboard | Version {APP_VERSION}")
