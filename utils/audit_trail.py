"""
Audit Trail Module
Version: 2.2.0-alpha.3
Author: Taiwo Durodola-Tunde

Logs every significant action taken in the dashboard to provide
governance evidence and demonstrate due diligence.

Actions Logged:
    - dashboard_load: Dashboard started/refreshed
    - data_upload: CSV file uploaded by user
    - email_sent: Reminder dispatched via Outlook
    - email_bulk_sent: Bulk reminders dispatched
    - pdf_exported: PDF report downloaded
    - csv_exported: CSV data downloaded
    - snapshot_captured: Risk history snapshot saved
    - filter_applied: Risk owner filter changed

Storage:
    - SQLite table 'audit_trail' in data/grc_history.db
    - Queryable, searchable, exportable
    - Timestamped with action type and metadata

Functions:
    init_audit_table: Create audit trail table if not exists.
    log_action: Record a single action to the audit trail.
    get_audit_trail: Retrieve audit entries with optional filters.
    get_audit_summary: Get action counts grouped by type.
    export_audit_trail: Export audit data as CSV string.
    get_recent_actions: Get the N most recent actions.
"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================

DB_PATH = Path("data") / "grc_history.db"

# Valid action types for validation
VALID_ACTIONS = [
    "dashboard_load",
    "data_upload",
    "email_sent",
    "email_bulk_sent",
    "pdf_exported",
    "csv_exported",
    "snapshot_captured",
    "filter_applied",
    "report_generated",
]


# ==========================================================
# DATABASE INITIALISATION
# ==========================================================

def init_audit_table(db_path: Path = DB_PATH):
    """
    Create the audit trail table if it does not exist.

    Safe to call on every dashboard load — uses
    CREATE TABLE IF NOT EXISTS.

    Args:
        db_path: Path to the SQLite database file.
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT,
            user_context TEXT,
            metadata TEXT,
            session_id TEXT
        )
    """)

    # Index for faster filtering by action type and date
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_action_type
        ON audit_trail(action_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp
        ON audit_trail(timestamp)
    """)

    conn.commit()
    conn.close()


# ==========================================================
# LOGGING FUNCTIONS
# ==========================================================

def log_action(
    action_type: str,
    description: str,
    metadata: str = "",
    user_context: str = "Dashboard User",
    session_id: str = "",
    db_path: Path = DB_PATH
):
    """
    Record a single action to the audit trail.

    Args:
        action_type: Category of action (must be in VALID_ACTIONS).
        description: Human-readable description of what happened.
        metadata: Optional additional context (JSON string, IDs, etc).
        user_context: Who performed the action. Defaults to
            'Dashboard User'.
        session_id: Optional Streamlit session identifier.
        db_path: Path to the SQLite database file.
    """

    # Validate action type
    if action_type not in VALID_ACTIONS:
        action_type = "dashboard_load"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_trail
        (timestamp, action_type, description, user_context,
         metadata, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        action_type,
        description,
        user_context,
        metadata,
        session_id
    ))

    conn.commit()
    conn.close()


# ==========================================================
# QUERY FUNCTIONS
# ==========================================================

def get_audit_trail(
    action_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    db_path: Path = DB_PATH
) -> pd.DataFrame:
    """
    Retrieve audit trail entries with optional filters.

    Args:
        action_type: Filter by specific action type. None for all.
        date_from: Filter entries from this date (ISO format).
        date_to: Filter entries up to this date (ISO format).
        limit: Maximum number of entries to return.
            Defaults to 100.
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: Audit trail entries ordered by timestamp desc.
    """

    conn = sqlite3.connect(str(db_path))

    query = "SELECT * FROM audit_trail WHERE 1=1"
    params = []

    if action_type:
        query += " AND action_type = ?"
        params.append(action_type)

    if date_from:
        query += " AND timestamp >= ?"
        params.append(date_from)

    if date_to:
        query += " AND timestamp <= ?"
        params.append(date_to + " 23:59:59")

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    return df


def get_audit_summary(db_path: Path = DB_PATH) -> dict:
    """
    Get action counts grouped by action type.

    Useful for the dashboard summary widget showing how
    many of each action type has been performed.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict: Action types mapped to their counts.
    """

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action_type, COUNT(*) as count
        FROM audit_trail
        GROUP BY action_type
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in rows}


def get_recent_actions(
    n: int = 10,
    db_path: Path = DB_PATH
) -> pd.DataFrame:
    """
    Get the N most recent audit actions.

    Args:
        n: Number of recent actions to retrieve.
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: Most recent N audit entries.
    """

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query(
        "SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT ?",
        conn,
        params=(n,)
    )

    conn.close()

    return df


def get_audit_count(db_path: Path = DB_PATH) -> int:
    """
    Get total number of audit trail entries.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        int: Total audit entries count.
    """

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM audit_trail")
    count = cursor.fetchone()[0]

    conn.close()

    return count


def export_audit_trail(db_path: Path = DB_PATH) -> str:
    """
    Export the full audit trail as a CSV string.

    Suitable for download via Streamlit download button.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        str: CSV-formatted string of all audit entries.
    """

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query(
        "SELECT * FROM audit_trail ORDER BY timestamp DESC",
        conn
    )

    conn.close()

    return df.to_csv(index=False)


def get_today_actions(db_path: Path = DB_PATH) -> pd.DataFrame:
    """
    Get all audit actions from today.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: Today's audit entries.
    """

    today_str = date.today().isoformat()

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query(
        "SELECT * FROM audit_trail WHERE timestamp >= ? ORDER BY timestamp DESC",
        conn,
        params=(today_str,)
    )

    conn.close()

    return df
