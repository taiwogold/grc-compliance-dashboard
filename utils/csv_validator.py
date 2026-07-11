"""
CSV Upload Security Validator
Version: 3.0.2
Author: Taiwo Durodola-Tunde

Validates uploaded CSV files for security threats, format
compliance, and data integrity before allowing them into
the risk register pipeline.

Security Checks:
    - File size limit (max 10MB)
    - File extension validation (.csv only)
    - Content-type verification
    - Column injection prevention (no formulas in cells)
    - Required column validation
    - Row count limits (max 10,000 rows)
    - Null byte detection
    - Encoding validation (UTF-8)

Usage:
    from utils.csv_validator import validate_uploaded_csv

    result = validate_uploaded_csv(uploaded_file)
    if result["valid"]:
        risk_df = result["dataframe"]
    else:
        st.error(result["error"])
"""

import logging
import re
from typing import Optional

import pandas as pd

from .data_loader import RISK_REGISTER_REQUIRED_COLUMNS

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURATION
# ==========================================================

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_ROW_COUNT = 10000
MAX_COLUMN_COUNT = 50

# Characters that indicate formula injection in CSV cells
# These can trigger code execution in Excel/Sheets
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


# ==========================================================
# VALIDATION FUNCTION
# ==========================================================

def validate_uploaded_csv(uploaded_file) -> dict:
    """
    Perform comprehensive security validation on an uploaded CSV.

    Runs all checks in sequence and returns on first failure.
    If all checks pass, returns the parsed DataFrame.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        dict with keys:
            - valid (bool): Whether the file passed all checks.
            - dataframe (DataFrame or None): Parsed data if valid.
            - error (str): Error message if invalid.
            - warnings (list): Non-blocking warnings.
    """

    result = {
        "valid": False,
        "dataframe": None,
        "error": "",
        "warnings": [],
    }

    # --- Check 1: File size ---
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        result["error"] = (
            f"File too large ({uploaded_file.size / 1024 / 1024:.1f}MB). "
            f"Maximum allowed: {MAX_FILE_SIZE_MB}MB."
        )
        logger.warning(f"Upload rejected: oversized file ({uploaded_file.size} bytes)")
        return result

    # --- Check 2: File extension ---
    if not uploaded_file.name.lower().endswith(".csv"):
        result["error"] = (
            f"Invalid file type: {uploaded_file.name}. "
            f"Only .csv files are accepted."
        )
        logger.warning(f"Upload rejected: wrong extension ({uploaded_file.name})")
        return result

    # --- Check 3: Read raw content for null bytes ---
    try:
        raw_content = uploaded_file.getvalue()

        if b"\x00" in raw_content:
            result["error"] = (
                "File contains null bytes — possible binary file "
                "or corrupted data. Upload rejected."
            )
            logger.warning("Upload rejected: null bytes detected")
            return result

        # Reset file pointer for pandas
        uploaded_file.seek(0)

    except Exception as e:
        result["error"] = f"Could not read file: {str(e)}"
        return result

    # --- Check 4: Parse CSV ---
    try:
        df = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        result["error"] = (
            "File encoding error. Please ensure the file is "
            "saved as UTF-8 CSV."
        )
        logger.warning("Upload rejected: encoding error")
        return result
    except Exception as e:
        result["error"] = f"Failed to parse CSV: {str(e)}"
        logger.warning(f"Upload rejected: parse error ({e})")
        return result

    # --- Check 5: Empty file ---
    if df.empty:
        result["error"] = "Uploaded file is empty (no data rows)."
        return result

    # --- Check 6: Row count limit ---
    if len(df) > MAX_ROW_COUNT:
        result["error"] = (
            f"File contains {len(df)} rows. "
            f"Maximum allowed: {MAX_ROW_COUNT}."
        )
        logger.warning(f"Upload rejected: too many rows ({len(df)})")
        return result

    # --- Check 7: Column count limit ---
    if len(df.columns) > MAX_COLUMN_COUNT:
        result["error"] = (
            f"File contains {len(df.columns)} columns. "
            f"Maximum allowed: {MAX_COLUMN_COUNT}."
        )
        return result

    # --- Check 8: Required columns ---
    missing = [
        col for col in RISK_REGISTER_REQUIRED_COLUMNS
        if col not in df.columns
    ]
    if missing:
        result["error"] = (
            f"Missing required columns: {', '.join(missing)}. "
            f"Required: {', '.join(RISK_REGISTER_REQUIRED_COLUMNS)}"
        )
        return result

    # --- Check 9: Formula injection ---
    injection_found = False
    for col in df.select_dtypes(include=["object"]).columns:
        for val in df[col].dropna():
            val_str = str(val).strip()
            if val_str and val_str[0] in FORMULA_PREFIXES:
                # Allow negative numbers in numeric-looking fields
                if val_str[0] == "-" and _looks_numeric(val_str):
                    continue
                injection_found = True
                result["warnings"].append(
                    f"Potential formula injection in column '{col}': "
                    f"'{val_str[:20]}...'"
                )
                # Sanitise the cell
                df.loc[df[col] == val, col] = "'" + val_str
                break  # One warning per column is enough

    if injection_found:
        result["warnings"].append(
            "Potentially dangerous cell values were sanitised."
        )
        logger.warning("Upload: formula injection detected and sanitised")

    # --- All checks passed ---
    result["valid"] = True
    result["dataframe"] = df

    logger.info(
        f"CSV validated: {uploaded_file.name} "
        f"({len(df)} rows, {len(df.columns)} cols)"
    )

    return result


def _looks_numeric(value: str) -> bool:
    """Check if a string looks like a negative number."""
    try:
        float(value)
        return True
    except ValueError:
        return False
