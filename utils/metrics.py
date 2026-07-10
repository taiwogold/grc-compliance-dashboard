"""
Metrics & Calculations Module
Version: 2.1.0
Author: Taiwo Durodola-Tunde

Contains all business logic for compliance scoring, risk
escalation calculations, and monthly management summaries.

Functions:
    calculate_compliance_score: Compute compliance percentage.
    calculate_escalation: Apply escalation logic to risk data.
    calculate_risk_metrics: Compute KPI metrics from risk data.
    determine_health_rating: Map compliance score to RAG status.
    generate_monthly_summary: Build monthly management summary.
"""

from datetime import datetime

import numpy as np
import pandas as pd


# ==========================================================
# COMPLIANCE SCORING
# ==========================================================

def calculate_compliance_score(controls_df) -> float:
    """
    Calculate the overall compliance score as a percentage.

    The score represents the proportion of controls that have
    been fully implemented versus the total number of controls.

    Args:
        controls_df: DataFrame with a 'Status' column containing
            values like 'Implemented', 'In Progress', 'Planned'.

    Returns:
        float: Compliance score as a percentage (0-100),
            rounded to 1 decimal place.
    """

    total_controls = len(controls_df)

    if total_controls == 0:
        return 0.0

    implemented = len(
        controls_df[
            controls_df["Status"] == "Implemented"
        ]
    )

    return round(
        (implemented / total_controls) * 100,
        1
    )


# ==========================================================
# RISK METRICS
# ==========================================================

def calculate_risk_metrics(risk_df) -> dict:
    """
    Calculate key risk metrics from the filtered risk register.

    Args:
        risk_df: Filtered DataFrame containing risk records.

    Returns:
        dict: Dictionary with keys:
            - high_risks (int): Count of high-severity risks.
            - open_risks (int): Count of open risks.
            - closed_risks (int): Count of closed risks.
    """

    return {
        "high_risks": len(
            risk_df[risk_df["Risk_Level"] == "High"]
        ),
        "open_risks": len(
            risk_df[risk_df["Status"] == "Open"]
        ),
        "closed_risks": len(
            risk_df[risk_df["Status"] == "Closed"]
        ),
    }


def determine_health_rating(compliance_score: float) -> str:
    """
    Determine the overall health rating based on compliance score.

    Thresholds:
        - >= 80%: Healthy (green)
        - >= 60%: Requires Attention (amber)
        - < 60%: Critical (red)

    Args:
        compliance_score: The current compliance percentage.

    Returns:
        str: Health rating string with emoji indicator.
    """

    if compliance_score >= 80:
        return "🟢 Healthy"
    elif compliance_score >= 60:
        return "🟠 Requires Attention"
    else:
        return "🔴 Critical"


# ==========================================================
# ESCALATION LOGIC
# ==========================================================

def calculate_escalation(risk_df):
    """
    Calculate overdue status and escalation levels for risks.

    Applies due date logic to determine which risks are overdue
    and assigns escalation tiers based on severity:

    Escalation Levels:
        - None: Not overdue (due date in future or risk closed)
        - Level 1: 1-14 days overdue (owner reminder)
        - Level 2: 15-30 days overdue (manager escalation)
        - Level 3: 31-60 days overdue (director escalation)
        - Level 4: 60+ days overdue (executive escalation)

    Args:
        risk_df: DataFrame containing risk register data.
            Must include 'Due_Date' and 'Status' columns.

    Returns:
        DataFrame: Copy of input with additional columns:
            - Days_Overdue (int): Days past due date.
            - Escalation_Level (str): Current escalation tier.
            - Is_Overdue (bool): Whether the risk is overdue.
            - Days_Remaining (int): Days until due (negative = overdue).
    """

    today = pd.Timestamp(datetime.now().date())
    df = risk_df.copy()

    # Parse Due_Date column
    if "Due_Date" in df.columns:
        df["Due_Date"] = pd.to_datetime(
            df["Due_Date"], errors="coerce"
        )
    else:
        df["Due_Date"] = pd.NaT

    # Calculate days overdue (positive = overdue)
    df["Days_Overdue"] = (today - df["Due_Date"]).dt.days

    # Only open risks can be overdue
    df.loc[
        df["Status"] == "Closed",
        "Days_Overdue"
    ] = 0

    # Determine escalation level using numpy select
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

    df["Escalation_Level"] = np.select(
        conditions, choices, default="None"
    )

    # Boolean overdue flag
    df["Is_Overdue"] = (
        (df["Days_Overdue"] > 0) &
        (df["Status"] == "Open")
    )

    # Days remaining (negative means overdue)
    df["Days_Remaining"] = -df["Days_Overdue"]

    return df


# ==========================================================
# MONTHLY MANAGEMENT SUMMARY
# ==========================================================

def generate_monthly_summary(
    compliance_score,
    metrics,
    rating,
    risk_df,
    escalated_df,
    trend_df=None
) -> dict:
    """
    Generate a structured monthly management summary.

    Compiles all key governance metrics into a single summary
    object used for both dashboard display and report generation.

    Args:
        compliance_score (float): Current compliance percentage.
        metrics (dict): Risk count metrics dictionary.
        rating (str): Health rating string.
        risk_df (DataFrame): Full risk register data.
        escalated_df (DataFrame): Risks with escalation data applied.
        trend_df (DataFrame, optional): Historical compliance scores.

    Returns:
        dict: Comprehensive monthly summary with nested keys:
            - report_period, generated_at
            - compliance: score, rating, mom_change, target, gap
            - risks: total, open, closed, high, closure_rate
            - escalation: total_overdue, avg/max days, escalation_rate
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

    avg_days_overdue = (
        overdue_risks["Days_Overdue"].mean()
        if not overdue_risks.empty else 0
    )

    return {
        "report_period": datetime.now().strftime("%B %Y"),
        "generated_at": datetime.now().strftime("%d %B %Y %H:%M"),
        "compliance": {
            "score": compliance_score,
            "rating": rating,
            "month_over_month_change": mom_change,
            "target": 80.0,
            "gap_to_target": max(0, 80.0 - compliance_score),
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
