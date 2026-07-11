"""
GRC Compliance Dashboard
Version: 3.3.0
Author: Taiwo Durodola-Tunde

Multi-tab enterprise GRC dashboard with professional UI.
All business logic lives in the utils/ package.

Release Notes:
    v3.3.0 - Multi-tab interface, UX overhaul
    v3.2.0 - FastAPI REST API endpoints
    v3.0.0 - PostgreSQL backend, persistent cloud storage
    v2.5.0 - Streamlit Cloud deployment, password gate
    v2.4.0 - Config management, multi-org DB, email providers, auth
    v2.3.0 - Jira integration
    v2.2.0 - Audit, History & Intelligence
    v2.1.0 - Outlook Integration & Automated Reminder Dispatch
    v2.0.0 - Initial release with KPI dashboard

Architecture:
    dashboard.py           - UI orchestration with tabbed layout
    utils/                 - All business logic modules
    api/                   - REST API endpoints
"""

import sys
sys.dont_write_bytecode = True

from datetime import datetime
import logging

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.auth import require_auth, get_current_user, show_logout_button
from utils.cloud_auth import check_password

from utils import (
    load_risk_register, load_controls, load_compliance_history,
    validate_dataframe, RISK_REGISTER_REQUIRED_COLUMNS,
    calculate_compliance_score, calculate_risk_metrics,
    calculate_escalation, determine_health_rating,
    generate_monthly_summary,
    create_compliance_trend_chart, create_control_pie_chart,
    create_risk_bar_chart, create_risk_status_pie,
    create_heatmap, create_escalation_bar_chart,
    create_overdue_timeline, create_management_trend_chart,
    create_score_distribution_chart, create_score_waterfall_chart,
    generate_pdf, generate_enhanced_pdf, set_version,
    OutlookDispatcher,
    calculate_risk_scores, get_top_risks, get_score_distribution,
    init_database, capture_snapshot, get_snapshots,
    get_snapshot_detail, get_risk_history, get_latest_delta,
    get_snapshot_count,
    init_audit_table, log_action, get_audit_trail,
    get_audit_summary, get_audit_count, export_audit_trail,
    get_today_actions,
    evaluate_alerts,
    get_theme, apply_chart_theme, get_custom_css,
    database_manager,
)

_logger = logging.getLogger(__name__)


# ==========================================================
# PAGE CONFIG & AUTH
# ==========================================================

APP_VERSION = "3.3.0"
set_version(APP_VERSION)

st.set_page_config(
    page_title="GRC Compliance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Authentication ---
if not check_password():
    st.stop()
require_auth()

# --- Sidebar: User & Theme ---
current_user = get_current_user()
st.sidebar.markdown(f"👤 **{current_user['name']}** ({current_user['role'].title()})")
show_logout_button()
st.sidebar.divider()

st.sidebar.header("🎨 Appearance")
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False, key="dark_mode_toggle")
active_theme_name = "dark" if dark_mode else "light"
active_theme = get_theme(active_theme_name)
st.markdown(get_custom_css(active_theme), unsafe_allow_html=True)


# ==========================================================
# DATA LOADING
# ==========================================================

try:
    risk_df = load_risk_register()
except Exception as e:
    risk_df = None
    _logger.error(f"Risk register load failed: {e}")

try:
    controls_df = load_controls()
except Exception:
    controls_df = None

# --- Sidebar: Upload & Filters ---
st.sidebar.header("📂 Data")
uploaded_file = st.sidebar.file_uploader("Upload Risk Register CSV", type=["csv"])
if uploaded_file:
    if uploaded_file.size > 10 * 1024 * 1024:
        st.sidebar.error("File too large (max 10MB)")
    else:
        try:
            risk_df = pd.read_csv(uploaded_file)
            st.sidebar.success(f"✅ Loaded {len(risk_df)} rows")
        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")

if risk_df is None:
    st.error("No risk data available. Upload a CSV in the sidebar.")
    st.stop()

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()


# --- Validation ---
missing = validate_dataframe(risk_df, RISK_REGISTER_REQUIRED_COLUMNS)
if missing:
    st.error(f"Missing columns: {', '.join(missing)}")
    st.stop()

# --- Filters ---
st.sidebar.header("🔍 Filters")
owners = sorted(risk_df["Risk_Owner"].dropna().unique())
selected_owners = st.sidebar.multiselect("Risk Owner", options=owners, default=owners)
filtered_df = risk_df[risk_df["Risk_Owner"].isin(selected_owners)]

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ==========================================================
# CALCULATIONS (shared across all tabs)
# ==========================================================

database_manager.init()
if "audit_load_logged" not in st.session_state:
    database_manager.log_action("dashboard_load", "Dashboard session started")
    st.session_state.audit_load_logged = True

compliance_score = calculate_compliance_score(controls_df) if controls_df is not None else 0.0
metrics = calculate_risk_metrics(filtered_df)
rating = determine_health_rating(compliance_score)
escalated_df = calculate_escalation(filtered_df)
scored_df = calculate_risk_scores(filtered_df)

# Capture daily snapshot
database_manager.capture_snapshot(filtered_df, compliance_score, scored_df)


# ==========================================================
# HEADER — Always visible above tabs
# ==========================================================

# Title bar
col_title, col_version = st.columns([4, 1])
with col_title:
    st.title("🛡️ GRC Compliance Dashboard")
with col_version:
    st.caption(f"v{APP_VERSION}")
    st.caption(datetime.now().strftime("%d %b %Y %H:%M"))

# Global KPI strip
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Compliance", f"{compliance_score}%")
k2.metric("Open Risks", metrics["open_risks"])
k3.metric("Closed", metrics["closed_risks"])
k4.metric("High Severity", metrics["high_risks"])
k5.metric("Health", rating)

# Alert banner
delta = get_latest_delta()
alerts = evaluate_alerts(
    compliance_score=compliance_score,
    metrics=metrics,
    escalated_df=escalated_df,
    total_risks=len(filtered_df),
    delta=delta
)
if alerts:
    with st.expander(f"🚨 {len(alerts)} Active Alert(s)", expanded=True):
        for alert in alerts:
            if alert.severity == "CRITICAL":
                st.error(f"**{alert.title}** — {alert.message}")
            elif alert.severity == "WARNING":
                st.warning(f"**{alert.title}** — {alert.message}")
            else:
                st.info(f"**{alert.title}** — {alert.message}")

st.divider()


# ==========================================================
# TABBED INTERFACE
# ==========================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive",
    "⚠️ Risks & Scoring",
    "🔥 Escalations",
    "📈 History & Trends",
    "📧 Communications",
    "📥 Reports & Exports"
])

# ==========================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==========================================================

with tab1:
    st.subheader("Executive Summary")

    sum_left, sum_right = st.columns(2)
    with sum_left:
        st.info(f"""
### Compliance Position
**Score:** {compliance_score}% | **Status:** {rating}
""")
    with sum_right:
        st.info(f"""
### Risk Overview
**Open:** {metrics['open_risks']} | **Closed:** {metrics['closed_risks']} | **High:** {metrics['high_risks']}
""")

    # Compliance Trend + ISO Coverage
    ch_left, ch_right = st.columns(2)
    with ch_left:
        st.markdown("#### Compliance Trend")
        try:
            trend_df = load_compliance_history()
            fig = create_compliance_trend_chart(trend_df)
            st.plotly_chart(fig, width="stretch", key="t1_trend")
        except Exception:
            st.info("Compliance history not available.")
            trend_df = None

    with ch_right:
        st.markdown("#### ISO 27001 Control Coverage")
        if controls_df is not None:
            fig = create_control_pie_chart(controls_df)
            st.plotly_chart(fig, width="stretch", key="t1_iso")
        else:
            st.info("Controls data not available.")


    # Control Status
    if controls_df is not None:
        st.markdown("#### Control Implementation Status")
        fig = create_control_pie_chart(controls_df, title="Control Status")
        st.plotly_chart(fig, width="stretch", key="t1_ctrl")

    # Owner Summary
    st.markdown("#### Risk Owner Summary")
    owner_summary = (
        filtered_df.groupby("Risk_Owner")
        .agg(
            Open=("Status", lambda x: (x == "Open").sum()),
            High=("Risk_Level", lambda x: (x == "High").sum()),
            Total=("Risk_ID", "count"),
        )
        .reset_index()
        .sort_values("Open", ascending=False)
    )
    st.dataframe(owner_summary, width="stretch")


# ==========================================================
# TAB 2: RISKS & SCORING
# ==========================================================

with tab2:
    st.subheader("🎯 Risk Analysis & Scoring")

    # Risk Level Distribution + Status
    r_left, r_right = st.columns(2)
    with r_left:
        st.markdown("#### Risk Level Distribution")
        fig = create_risk_bar_chart(filtered_df)
        st.plotly_chart(fig, width="stretch", key="t2_levels")
    with r_right:
        st.markdown("#### Open vs Closed")
        fig = create_risk_status_pie(filtered_df)
        st.plotly_chart(fig, width="stretch", key="t2_status")

    # Heat Map
    st.markdown("#### Risk Heat Map (Likelihood × Impact)")
    fig = create_heatmap(filtered_df)
    st.plotly_chart(fig, width="stretch", key="t2_heatmap")

    st.divider()

    # Risk Scoring Engine
    st.markdown("#### 🎯 Quantitative Risk Scoring")
    st.caption(
        "Score = (Likelihood × Impact) × Overdue Modifier × Control Modifier"
    )

    score_dist = get_score_distribution(scored_df)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("🟣 Critical", score_dist["Critical"])
    s2.metric("🔴 High", score_dist["High"])
    s3.metric("🟡 Medium", score_dist["Medium"])
    s4.metric("🟢 Low", score_dist["Low"])

    # Top risks table
    st.markdown("#### Top 5 Risks by Score")
    top_risks = get_top_risks(scored_df, n=5)
    st.dataframe(top_risks, width="stretch", column_config={
        "Residual_Risk_Score": st.column_config.NumberColumn("Score", format="%.1f"),
        "Overdue_Modifier": st.column_config.NumberColumn("Overdue ×", format="%.2f"),
        "Control_Modifier": st.column_config.NumberColumn("Control ×", format="%.2f"),
    })


    # Score charts
    sc_left, sc_right = st.columns(2)
    with sc_left:
        fig = create_score_distribution_chart(scored_df)
        st.plotly_chart(fig, width="stretch", key="t2_score_dist")
    with sc_right:
        fig = create_score_waterfall_chart(top_risks)
        st.plotly_chart(fig, width="stretch", key="t2_score_top")

    st.divider()

    # Full Risk Register
    st.markdown("#### Full Risk Register")
    st.dataframe(filtered_df, width="stretch")
    st.caption(f"Showing {len(filtered_df)} records")


# ==========================================================
# TAB 3: ESCALATIONS
# ==========================================================

with tab3:
    st.subheader("⚠️ Overdue Risk Escalation Dashboard")

    overdue_df = escalated_df[
        escalated_df["Is_Overdue"] == True
    ].sort_values("Days_Overdue", ascending=False)

    total_overdue = len(overdue_df)
    level_counts = overdue_df["Escalation_Level"].value_counts()

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("🔴 Total Overdue", total_overdue)
    e2.metric("⚡ Level 3+",
        level_counts.get("Level 3 - Director Escalation", 0)
        + level_counts.get("Level 4 - Executive Escalation", 0))
    e3.metric("📅 Max Days Overdue",
        int(overdue_df["Days_Overdue"].max()) if not overdue_df.empty else 0)
    e4.metric("📊 Escalation Rate",
        f"{round(total_overdue / len(escalated_df) * 100, 1)}%"
        if len(escalated_df) > 0 else "0%")

    if not overdue_df.empty:
        st.markdown("#### Overdue Risks")
        display_cols = ["Risk_ID", "Risk_Name", "Risk_Level", "Risk_Owner",
                        "Due_Date", "Days_Overdue", "Escalation_Level"]
        avail = [c for c in display_cols if c in overdue_df.columns]
        disp = overdue_df[avail].copy()
        if "Due_Date" in disp.columns:
            disp["Due_Date"] = disp["Due_Date"].dt.strftime("%Y-%m-%d")
        st.dataframe(disp, width="stretch")

        # Charts
        esc_l, esc_r = st.columns(2)
        with esc_l:
            st.markdown("#### By Escalation Level")
            fig = create_escalation_bar_chart(overdue_df)
            st.plotly_chart(fig, width="stretch", key="t3_esc_bar")
        with esc_r:
            st.markdown("#### Timeline")
            fig = create_overdue_timeline(overdue_df)
            st.plotly_chart(fig, width="stretch", key="t3_timeline")
    else:
        st.success("✅ No overdue risks — all within due dates.")


    # Upcoming due dates
    st.markdown("#### 📅 Due Within 14 Days")
    upcoming = escalated_df[
        (escalated_df["Days_Remaining"] >= 0)
        & (escalated_df["Days_Remaining"] <= 14)
        & (escalated_df["Status"] == "Open")
    ].sort_values("Days_Remaining")

    if not upcoming.empty:
        up_disp = upcoming[["Risk_ID", "Risk_Name", "Risk_Level",
                            "Risk_Owner", "Due_Date", "Days_Remaining"]].copy()
        up_disp["Due_Date"] = up_disp["Due_Date"].dt.strftime("%Y-%m-%d")
        st.dataframe(up_disp, width="stretch")
    else:
        st.info("No risks due within 14 days.")


# ==========================================================
# TAB 4: HISTORY & TRENDS
# ==========================================================

with tab4:
    st.subheader("📸 Risk History & Snapshots")

    snapshot_count = get_snapshot_count()
    snapshots_df = get_snapshots()

    h1, h2, h3 = st.columns(3)
    h1.metric("Total Snapshots", snapshot_count)
    if not snapshots_df.empty:
        h2.metric("First", snapshots_df["snapshot_date"].iloc[-1])
        h3.metric("Latest", snapshots_df["snapshot_date"].iloc[0])

    # Delta
    if delta:
        st.markdown("#### Changes Since Last Snapshot")
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Total", len(filtered_df),
            delta=f"{delta['delta_total']:+d}" if delta["delta_total"] != 0 else None)
        d2.metric("Open", metrics["open_risks"],
            delta=f"{delta['delta_open']:+d}" if delta["delta_open"] != 0 else None,
            delta_color="inverse")
        d3.metric("Closed", metrics["closed_risks"],
            delta=f"{delta['delta_closed']:+d}" if delta["delta_closed"] != 0 else None)
        d4.metric("High", metrics["high_risks"],
            delta=f"{delta['delta_high']:+d}" if delta["delta_high"] != 0 else None,
            delta_color="inverse")
        d5.metric("Compliance", f"{compliance_score}%",
            delta=f"{delta['delta_compliance']:+.1f}%" if delta["delta_compliance"] != 0 else None)
        st.caption(f"Comparing {delta['date_current']} vs {delta['date_previous']}")

    # Snapshot history
    if not snapshots_df.empty:
        st.markdown("#### Snapshot History")
        st.dataframe(snapshots_df[
            ["snapshot_date", "total_risks", "open_risks",
             "closed_risks", "high_risks", "compliance_score"]
        ], width="stretch")


    # Track individual risk
    st.markdown("#### 🔍 Track Individual Risk")
    all_ids = sorted(filtered_df["Risk_ID"].unique())
    sel_id = st.selectbox("Select Risk ID", all_ids, key="t4_risk_select")
    if sel_id:
        hist_df = get_risk_history(sel_id)
        if not hist_df.empty:
            st.dataframe(hist_df, width="stretch")
            if "residual_score" in hist_df.columns and hist_df["residual_score"].notna().any():
                fig = px.line(hist_df, x="snapshot_date", y="residual_score",
                              markers=True, title=f"Score Trend: {sel_id}")
                st.plotly_chart(fig, width="stretch", key="t4_score_trend")
        else:
            st.info(f"No history for {sel_id} yet. Builds over time with daily snapshots.")

    st.divider()

    # Monthly Management Report
    st.markdown("#### 📊 Monthly Management Summary")
    try:
        trend_data = load_compliance_history()
    except Exception:
        trend_data = None

    monthly = generate_monthly_summary(
        compliance_score, metrics, rating, filtered_df, escalated_df, trend_data
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Score", f"{monthly['compliance']['score']}%",
        delta=f"{monthly['compliance']['month_over_month_change']:+.0f}% MoM")
    m2.metric("Closure Rate", f"{monthly['risks']['closure_rate']}%")
    m3.metric("Escalation Rate", f"{monthly['escalation']['escalation_rate']}%")
    m4.metric("Gap to 80%", f"{monthly['compliance']['gap_to_target']}%")

    if trend_data is not None and not trend_data.empty:
        fig = create_management_trend_chart(trend_data, theme_name=active_theme_name)
        st.plotly_chart(fig, width="stretch", key="t4_mgmt_trend")


# ==========================================================
# TAB 5: COMMUNICATIONS
# ==========================================================

with tab5:
    st.subheader("📨 Automated Reminder Dispatch")
    st.markdown("""
    Send risk remediation reminders via Outlook. Emails route through
    corporate Exchange — **no credentials stored**.
    """)

    # Dispatcher init
    if "email_dispatcher" not in st.session_state:
        st.session_state.email_dispatcher = OutlookDispatcher()
    dispatcher = st.session_state.email_dispatcher

    # Status
    stat1, stat2, stat3 = st.columns(3)
    with stat1:
        if dispatcher.is_available:
            st.success("🟢 Outlook Connected")
        else:
            st.error("🔴 Outlook Not Available")
    with stat2:
        stats = dispatcher.get_session_stats()
        st.metric("Sent (Session)", stats["emails_sent"])
    with stat3:
        st.metric("Remaining", stats["remaining_quota"])

    st.divider()

    # Individual reminder
    st.markdown("#### Send Individual Reminder")
    avail_owners = sorted(filtered_df["Risk_Owner"].unique())
    sel_owner = st.selectbox("Risk Owner", avail_owners, key="t5_owner")

    owner_risks = filtered_df[filtered_df["Risk_Owner"] == sel_owner]
    owner_email = owner_risks["Owner_Email"].iloc[0] if "Owner_Email" in owner_risks.columns else ""
    open_risks = owner_risks[owner_risks["Status"] == "Open"]


    # Build email
    lines = []
    for _, row in open_risks.iterrows():
        due_info = ""
        if "Due_Date" in row and pd.notna(row.get("Due_Date")):
            dd = pd.to_datetime(row["Due_Date"])
            diff = (datetime.now() - dd).days
            due_info = f" [OVERDUE {diff}d]" if diff > 0 else f" [Due: {dd.strftime('%Y-%m-%d')}]"
        lines.append(f"- {row['Risk_ID']}: {row['Risk_Name']} ({row['Risk_Level']}){due_info}")

    email_body = (
        f"Hello {sel_owner},\n\n"
        f"Please review your open risks:\n\n" +
        "\n".join(lines) + "\n\n"
        f"Please provide:\n"
        f"  - Remediation progress\n  - Expected completion\n  - Any blockers\n\n"
        f"Kind Regards,\nCyber Security Governance & Assurance\n---\n"
        f"GRC Dashboard v{APP_VERSION}"
    )

    with st.expander("📧 Preview Email", expanded=False):
        st.markdown(f"**To:** {owner_email}")
        st.markdown(f"**Subject:** Risk Remediation Status Update Required")
        st.text_area("Body", email_body, height=200, disabled=True, key="t5_preview")

    col_confirm, col_send = st.columns([1, 2])
    with col_confirm:
        confirmed = st.checkbox("I confirm this email", key="t5_confirm")
    with col_send:
        if st.button("📧 Send via Outlook", disabled=not confirmed, key="t5_send"):
            if dispatcher.is_available:
                result = dispatcher.send_reminder(to=owner_email,
                    subject="Risk Remediation Status Update Required",
                    body=email_body, importance="High")
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    database_manager.log_action("email_sent",
                        f"Reminder sent to {owner_email}", f"owner={sel_owner}")
                else:
                    st.error(f"❌ {result['message']}")
            else:
                st.error("Outlook not available.")


    st.divider()

    # Bulk dispatch
    st.markdown("#### 🚨 Bulk Dispatch: Overdue Risk Owners")
    overdue_for_email = escalated_df[escalated_df["Is_Overdue"] == True]
    if not overdue_for_email.empty:
        overdue_owners = (
            overdue_for_email[["Risk_Owner", "Owner_Email"]]
            .drop_duplicates().reset_index(drop=True)
        )
        st.dataframe(overdue_owners, width="stretch")
        st.caption(f"{len(overdue_owners)} recipient(s)")

        bulk_confirm = st.checkbox("I authorise bulk dispatch", key="t5_bulk_confirm")
        if st.button(f"🚨 Send {len(overdue_owners)} Reminder(s)",
                     disabled=not bulk_confirm, key="t5_bulk_send"):
            if dispatcher.is_available:
                recipients = [{"email": r["Owner_Email"], "name": r["Risk_Owner"]}
                              for _, r in overdue_owners.iterrows()]
                template = (
                    "Hello {name},\n\nOverdue risks require immediate attention.\n\n"
                    "Actions:\n  - Review overdue risks\n  - Provide revised dates\n"
                    "  - Escalate blockers\n\nKind Regards,\nGRC Team"
                )
                results = dispatcher.send_bulk_reminders(
                    recipients=recipients,
                    subject="URGENT: Overdue Risk Remediation",
                    body_template=template, importance="High")
                sent = sum(1 for r in results if r["success"])
                if sent > 0:
                    st.success(f"✅ {sent} reminder(s) sent")
                    database_manager.log_action("email_bulk_sent",
                        f"Bulk sent to {sent} owners", f"sent={sent}")
            else:
                st.error("Outlook not available.")
    else:
        st.info("✅ No overdue risks — no reminders needed.")

    st.divider()

    # Email directory
    st.markdown("#### 📧 Risk Owner Directory")
    if "Owner_Email" in risk_df.columns:
        directory = risk_df[["Risk_Owner", "Owner_Email"]].drop_duplicates().sort_values("Risk_Owner")
        st.dataframe(directory, width="stretch")


# ==========================================================
# TAB 6: REPORTS & EXPORTS
# ==========================================================

with tab6:
    st.subheader("📥 Reports & Exports")

    # Export buttons
    st.markdown("#### Download Reports")
    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        st.download_button(
            "📥 Risk Register (CSV)",
            filtered_df.to_csv(index=False),
            "risk_register_export.csv", "text/csv",
            key="t6_csv")

    with exp2:
        pdf = generate_pdf(compliance_score, metrics, rating)
        st.download_button(
            "📄 Quick Summary (PDF)",
            pdf, "executive_summary.pdf", "application/pdf",
            key="t6_pdf_quick")

    with exp3:
        try:
            trend_for_pdf = load_compliance_history()
        except Exception:
            trend_for_pdf = None
        enhanced = generate_enhanced_pdf(
            compliance_score=compliance_score,
            metrics=metrics, rating=rating,
            risk_df=filtered_df, controls_df=controls_df,
            escalated_df=escalated_df, trend_df=trend_for_pdf)
        st.download_button(
            "📑 Full Report (PDF)",
            enhanced,
            f"grc_report_{datetime.now().strftime('%Y_%m')}.pdf",
            "application/pdf", key="t6_pdf_full")

    st.divider()

    # Audit Trail
    st.markdown("#### 📋 Audit Trail")
    audit_count = get_audit_count()
    audit_summary = get_audit_summary()

    a1, a2, a3 = st.columns(3)
    a1.metric("Total Actions", audit_count)
    a2.metric("Today", len(get_today_actions()))
    a3.metric("Types", len(audit_summary))


    # Filter and display audit
    filter_type = st.selectbox(
        "Filter by Action",
        options=["All"] + list(audit_summary.keys()),
        key="t6_audit_filter")

    sel_type = None if filter_type == "All" else filter_type
    audit_df = get_audit_trail(action_type=sel_type, limit=50)

    if not audit_df.empty:
        st.dataframe(
            audit_df[["timestamp", "action_type", "description", "metadata"]],
            width="stretch")
        st.caption(f"Showing {len(audit_df)} entries")
    else:
        st.info("No audit entries yet.")

    st.download_button(
        "📥 Export Audit Trail (CSV)",
        export_audit_trail(),
        f"audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv", key="t6_audit_csv")

    st.divider()

    # Database status
    st.markdown("#### 💾 Database Status")
    db_status = database_manager.get_status()
    st.markdown(f"**Backend:** {db_status['display_name']}")
    st.markdown(f"**Ready:** {'✅' if db_status['is_ready'] else '❌'}")


# ==========================================================
# FOOTER
# ==========================================================

st.divider()
st.caption(f"GRC Compliance Dashboard | v{APP_VERSION} | {datetime.now().strftime('%Y')}")
