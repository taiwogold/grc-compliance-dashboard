"""
Risk Scoring Engine Module
Version: 2.2.0
Author: Taiwo Durodola-Tunde

Provides quantitative risk scoring using a weighted formula
that combines base risk factors with dynamic modifiers for
overdue status and control effectiveness.

Formula:
    Base Score = Likelihood × Impact (range: 1-25)
    Overdue Modifier = 1.0 + (days_overdue × 0.02), capped at 2.0
    Control Modifier:
        - Implemented: 0.5 (50% reduction)
        - In Progress: 0.75 (25% reduction)
        - Planned/None: 1.0 (no reduction)

    Residual Risk Score = Base Score × Overdue Modifier × Control Modifier

    Score Bands:
        - Critical: >= 15
        - High: >= 10
        - Medium: >= 5
        - Low: < 5

Functions:
    calculate_risk_scores: Apply scoring to entire risk register.
    get_top_risks: Return the N highest-scored risks.
    get_score_band: Map a numeric score to a severity band.
    get_score_distribution: Count risks per severity band.
"""

from datetime import datetime

import numpy as np
import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================

# Control effectiveness modifiers
CONTROL_MODIFIERS = {
    "Implemented": 0.5,
    "In Progress": 0.75,
    "Planned": 1.0,
}

# Default modifier when control status is unknown
DEFAULT_CONTROL_MODIFIER = 1.0

# Overdue escalation rate (per day overdue)
OVERDUE_RATE = 0.02

# Maximum overdue multiplier cap
OVERDUE_CAP = 2.0

# Score band thresholds
SCORE_BANDS = {
    "Critical": 15,
    "High": 10,
    "Medium": 5,
    "Low": 0,
}


# ==========================================================
# SCORING FUNCTIONS
# ==========================================================

def get_score_band(score: float) -> str:
    """
    Map a numeric risk score to a severity band.

    Args:
        score: Numeric residual risk score.

    Returns:
        str: Severity band ('Critical', 'High', 'Medium', 'Low').
    """

    if score >= SCORE_BANDS["Critical"]:
        return "Critical"
    elif score >= SCORE_BANDS["High"]:
        return "High"
    elif score >= SCORE_BANDS["Medium"]:
        return "Medium"
    else:
        return "Low"


def calculate_risk_scores(risk_df) -> pd.DataFrame:
    """
    Apply the quantitative risk scoring formula to the register.

    Calculates a residual risk score for each risk based on:
        - Base risk (Likelihood × Impact)
        - Overdue modifier (increases score for overdue risks)
        - Control modifier (reduces score for implemented controls)

    Args:
        risk_df: DataFrame containing risk register data.
            Required columns: Likelihood, Impact, Status.
            Optional columns: Due_Date, Control_Status.

    Returns:
        DataFrame: Copy of input with additional columns:
            - Base_Score (float): Likelihood × Impact.
            - Overdue_Modifier (float): Escalation multiplier.
            - Control_Modifier (float): Control effectiveness factor.
            - Residual_Risk_Score (float): Final calculated score.
            - Score_Band (str): Severity band classification.
    """

    df = risk_df.copy()

    # --- Base Score ---
    df["Base_Score"] = (
        df["Likelihood"].astype(float)
        * df["Impact"].astype(float)
    )

    # --- Overdue Modifier ---
    today = pd.Timestamp(datetime.now().date())

    if "Due_Date" in df.columns:
        df["_due_date_parsed"] = pd.to_datetime(
            df["Due_Date"], errors="coerce"
        )
        df["_days_overdue"] = (
            today - df["_due_date_parsed"]
        ).dt.days.clip(lower=0)
    else:
        df["_days_overdue"] = 0

    # Only open risks get overdue modifier
    df.loc[df["Status"] == "Closed", "_days_overdue"] = 0

    # Calculate modifier: 1.0 + (days × rate), capped
    df["Overdue_Modifier"] = (
        1.0 + df["_days_overdue"] * OVERDUE_RATE
    ).clip(upper=OVERDUE_CAP)

    # --- Control Modifier ---
    if "Control_Status" in df.columns:
        df["Control_Modifier"] = (
            df["Control_Status"]
            .map(CONTROL_MODIFIERS)
            .fillna(DEFAULT_CONTROL_MODIFIER)
        )
    else:
        df["Control_Modifier"] = DEFAULT_CONTROL_MODIFIER

    # Closed risks get full control credit
    df.loc[df["Status"] == "Closed", "Control_Modifier"] = 0.5

    # --- Residual Risk Score ---
    df["Residual_Risk_Score"] = (
        df["Base_Score"]
        * df["Overdue_Modifier"]
        * df["Control_Modifier"]
    ).round(1)

    # --- Score Band ---
    df["Score_Band"] = df["Residual_Risk_Score"].apply(
        get_score_band
    )

    # Clean up temp columns
    df.drop(
        columns=["_due_date_parsed", "_days_overdue"],
        errors="ignore",
        inplace=True
    )

    return df


def get_top_risks(scored_df, n: int = 5) -> pd.DataFrame:
    """
    Return the top N highest-scored risks.

    Args:
        scored_df: DataFrame with Residual_Risk_Score column.
        n: Number of top risks to return. Defaults to 5.

    Returns:
        DataFrame: Top N risks sorted by score descending.
    """

    return (
        scored_df
        .nlargest(n, "Residual_Risk_Score")
        [["Risk_ID", "Risk_Name", "Risk_Owner",
          "Residual_Risk_Score", "Score_Band",
          "Base_Score", "Overdue_Modifier", "Control_Modifier"]]
    )


def get_score_distribution(scored_df) -> dict:
    """
    Count risks per severity band.

    Args:
        scored_df: DataFrame with Score_Band column.

    Returns:
        dict: Band names mapped to counts.
            e.g. {'Critical': 2, 'High': 3, 'Medium': 2, 'Low': 1}
    """

    counts = scored_df["Score_Band"].value_counts()

    return {
        "Critical": counts.get("Critical", 0),
        "High": counts.get("High", 0),
        "Medium": counts.get("Medium", 0),
        "Low": counts.get("Low", 0),
    }
