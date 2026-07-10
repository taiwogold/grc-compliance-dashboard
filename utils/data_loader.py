"""
Data Loader Module
Version: 2.1.0
Author: Taiwo Durodola-Tunde

Handles all CSV data loading, validation, and preprocessing
for the GRC Compliance Dashboard.

Functions:
    load_risk_register: Load and validate the risk register CSV.
    load_controls: Load the ISO 27001 controls CSV.
    load_compliance_history: Load historical compliance scores.
    validate_dataframe: Validate required columns exist.
"""

import pandas as pd
import streamlit as st


# ==========================================================
# DATA LOADING FUNCTIONS
# ==========================================================

@st.cache_data
def load_risk_register(filepath: str = "data/risk_register.csv"):
    """
    Load the risk register CSV file with validation.

    Ensures the Owner_Email column exists (adds empty column
    if missing for backward compatibility with older CSVs).

    Args:
        filepath: Path to the risk register CSV file.
            Defaults to 'data/risk_register.csv'.

    Returns:
        DataFrame: Validated risk register data.
    """

    risk_df = pd.read_csv(filepath)

    # Ensure Owner_Email column exists for backward compat
    if "Owner_Email" not in risk_df.columns:
        risk_df["Owner_Email"] = ""

    return risk_df


@st.cache_data
def load_controls(filepath: str = "data/controls.csv"):
    """
    Load the ISO 27001 controls CSV file.

    Args:
        filepath: Path to the controls CSV file.
            Defaults to 'data/controls.csv'.

    Returns:
        DataFrame: Controls implementation data.
    """

    return pd.read_csv(filepath)


@st.cache_data
def load_compliance_history(
    filepath: str = "data/compliance_history.csv"
):
    """
    Load historical compliance scores for trend analysis.

    Args:
        filepath: Path to the compliance history CSV.
            Defaults to 'data/compliance_history.csv'.

    Returns:
        DataFrame: Monthly compliance scores with columns
            'Month' and 'Score'.
    """

    return pd.read_csv(filepath)


def load_all_data():
    """
    Load all data sources required by the dashboard.

    Convenience function that loads risk register and controls
    in a single call. Compliance history is loaded separately
    as it may not always exist.

    Returns:
        tuple: (risk_df, controls_df) DataFrames.

    Raises:
        Exception: If source files cannot be read.
    """

    risk_df = load_risk_register()
    controls_df = load_controls()

    return risk_df, controls_df


# ==========================================================
# VALIDATION FUNCTIONS
# ==========================================================

def validate_dataframe(
    df,
    required_columns: list
) -> list:
    """
    Validate that a DataFrame contains all required columns.

    Args:
        df: DataFrame to validate.
        required_columns: List of column name strings that
            must be present.

    Returns:
        list: List of missing column names. Empty list if
            all columns are present.
    """

    return [
        col for col in required_columns
        if col not in df.columns
    ]


# Required columns for risk register validation
RISK_REGISTER_REQUIRED_COLUMNS = [
    "Risk_Level",
    "Status",
    "Risk_Owner",
    "Likelihood",
    "Impact"
]
