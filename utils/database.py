"""
Database Module - SQLite Risk History Tracking
Version: 2.2.0-alpha.2
Author: Taiwo Durodola-Tunde

Provides point-in-time snapshot storage for the risk register
using a local SQLite database. Enables historical comparison,
trend analysis, and audit evidence for governance committees.

Architecture:
    - SQLite file stored at data/grc_history.db
    - Snapshots captured automatically on each dashboard load
    - One snapshot per calendar day (avoids duplicates)
    - Full risk register state preserved per snapshot
    - Query functions for delta analysis and history retrieval

Tables:
    snapshots:
        - snapshot_id (INTEGER PRIMARY KEY)
        - snapshot_date (TEXT UNIQUE) - ISO date
        - total_risks (INTEGER)
        - open_risks (INTEGER)
        - closed_risks (INTEGER)
        - high_risks (INTEGER)
        - compliance_score (REAL)
        - created_at (TEXT) - ISO timestamp

    risk_history:
        - id (INTEGER PRIMARY KEY)
        - snapshot_id (INTEGER FK -> snapshots)
        - risk_id (TEXT)
        - risk_name (TEXT)
        - risk_level (TEXT)
        - status (TEXT)
        - risk_owner (TEXT)
        - likelihood (INTEGER)
        - impact (INTEGER)
        - control_status (TEXT)
        - due_date (TEXT)
        - residual_score (REAL)

Functions:
    init_database: Create tables if they don't exist.
    capture_snapshot: Save current risk register state.
    get_snapshots: Retrieve all snapshot summaries.
    get_snapshot_detail: Get full risk data for a snapshot.
    get_risk_history: Track a specific risk over time.
    get_latest_delta: Compare current vs previous snapshot.
    has_snapshot_today: Check if today's snapshot already exists.
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


# ==========================================================
# DATABASE INITIALISATION
# ==========================================================

def init_database(db_path: Path = DB_PATH):
    """
    Create the SQLite database and tables if they don't exist.

    This is safe to call on every dashboard load — it uses
    CREATE TABLE IF NOT EXISTS.

    Args:
        db_path: Path to the SQLite database file.
            Defaults to 'data/grc_history.db'.
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Snapshots summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT UNIQUE NOT NULL,
            total_risks INTEGER NOT NULL,
            open_risks INTEGER NOT NULL,
            closed_risks INTEGER NOT NULL,
            high_risks INTEGER NOT NULL,
            compliance_score REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Risk history detail table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            risk_id TEXT NOT NULL,
            risk_name TEXT,
            risk_level TEXT,
            status TEXT,
            risk_owner TEXT,
            likelihood INTEGER,
            impact INTEGER,
            control_status TEXT,
            due_date TEXT,
            residual_score REAL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)

    # Index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_risk_history_risk_id
        ON risk_history(risk_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_risk_history_snapshot
        ON risk_history(snapshot_id)
    """)

    conn.commit()
    conn.close()


# ==========================================================
# SNAPSHOT CAPTURE
# ==========================================================

def has_snapshot_today(db_path: Path = DB_PATH) -> bool:
    """
    Check if a snapshot has already been captured today.

    Prevents duplicate snapshots on repeated dashboard refreshes.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        bool: True if today's snapshot already exists.
    """

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    today_str = date.today().isoformat()

    cursor.execute(
        "SELECT COUNT(*) FROM snapshots WHERE snapshot_date = ?",
        (today_str,)
    )
    count = cursor.fetchone()[0]

    conn.close()

    return count > 0


def capture_snapshot(
    risk_df,
    compliance_score: float,
    scored_df=None,
    db_path: Path = DB_PATH
) -> Optional[int]:
    """
    Capture a point-in-time snapshot of the risk register.

    Saves both the summary metrics and the full risk detail
    to the SQLite database. Only one snapshot per day is
    allowed to prevent bloat from repeated refreshes.

    Args:
        risk_df: Current risk register DataFrame.
        compliance_score: Current compliance percentage.
        scored_df: Optional DataFrame with Residual_Risk_Score.
            If provided, scores are stored in history.
        db_path: Path to the SQLite database file.

    Returns:
        int: The snapshot_id of the new record, or None if
            today's snapshot already exists.
    """

    # Skip if already captured today
    if has_snapshot_today(db_path):
        return None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    today_str = date.today().isoformat()
    now_str = datetime.now().isoformat()

    # Calculate summary metrics
    total_risks = len(risk_df)
    open_risks = len(risk_df[risk_df["Status"] == "Open"])
    closed_risks = len(risk_df[risk_df["Status"] == "Closed"])
    high_risks = len(risk_df[risk_df["Risk_Level"] == "High"])

    # Insert snapshot summary
    cursor.execute("""
        INSERT INTO snapshots
        (snapshot_date, total_risks, open_risks, closed_risks,
         high_risks, compliance_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        today_str, total_risks, open_risks,
        closed_risks, high_risks, compliance_score, now_str
    ))

    snapshot_id = cursor.lastrowid

    # Determine source for risk scores
    source_df = scored_df if scored_df is not None else risk_df

    # Insert risk detail rows
    for _, row in source_df.iterrows():
        residual_score = (
            row.get("Residual_Risk_Score", None)
            if scored_df is not None else None
        )

        cursor.execute("""
            INSERT INTO risk_history
            (snapshot_id, risk_id, risk_name, risk_level, status,
             risk_owner, likelihood, impact, control_status,
             due_date, residual_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id,
            str(row.get("Risk_ID", "")),
            str(row.get("Risk_Name", "")),
            str(row.get("Risk_Level", "")),
            str(row.get("Status", "")),
            str(row.get("Risk_Owner", "")),
            int(row.get("Likelihood", 0)),
            int(row.get("Impact", 0)),
            str(row.get("Control_Status", "")),
            str(row.get("Due_Date", "")),
            float(residual_score) if residual_score is not None else None,
        ))

    conn.commit()
    conn.close()

    return snapshot_id


# ==========================================================
# QUERY FUNCTIONS
# ==========================================================

def get_snapshots(db_path: Path = DB_PATH) -> pd.DataFrame:
    """
    Retrieve all snapshot summaries ordered by date.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: All snapshots with columns:
            snapshot_id, snapshot_date, total_risks, open_risks,
            closed_risks, high_risks, compliance_score, created_at.
    """

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query(
        "SELECT * FROM snapshots ORDER BY snapshot_date DESC",
        conn
    )

    conn.close()

    return df


def get_snapshot_detail(
    snapshot_id: int,
    db_path: Path = DB_PATH
) -> pd.DataFrame:
    """
    Get the full risk register for a specific snapshot.

    Args:
        snapshot_id: The ID of the snapshot to retrieve.
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: All risk records from that snapshot.
    """

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query(
        "SELECT * FROM risk_history WHERE snapshot_id = ?",
        conn,
        params=(snapshot_id,)
    )

    conn.close()

    return df


def get_risk_history(
    risk_id: str,
    db_path: Path = DB_PATH
) -> pd.DataFrame:
    """
    Track a specific risk across all snapshots over time.

    Shows how a risk's status, level, score, and owner
    have changed across captured snapshots.

    Args:
        risk_id: The Risk_ID to track (e.g. 'R001').
        db_path: Path to the SQLite database file.

    Returns:
        DataFrame: Historical records for the risk with
            snapshot dates joined in.
    """

    conn = sqlite3.connect(str(db_path))

    df = pd.read_sql_query("""
        SELECT
            s.snapshot_date,
            rh.risk_id,
            rh.risk_name,
            rh.risk_level,
            rh.status,
            rh.risk_owner,
            rh.likelihood,
            rh.impact,
            rh.control_status,
            rh.residual_score
        FROM risk_history rh
        JOIN snapshots s ON s.snapshot_id = rh.snapshot_id
        WHERE rh.risk_id = ?
        ORDER BY s.snapshot_date ASC
    """, conn, params=(risk_id,))

    conn.close()

    return df


def get_latest_delta(db_path: Path = DB_PATH) -> Optional[dict]:
    """
    Compare the two most recent snapshots to calculate deltas.

    Returns the change in key metrics between the current and
    previous snapshot for dashboard display.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict: Delta values, or None if fewer than 2 snapshots exist.
            Keys: date_current, date_previous, delta_total,
            delta_open, delta_closed, delta_high, delta_compliance.
    """

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM snapshots
        ORDER BY snapshot_date DESC
        LIMIT 2
    """)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    conn.close()

    if len(rows) < 2:
        return None

    current = dict(zip(columns, rows[0]))
    previous = dict(zip(columns, rows[1]))

    return {
        "date_current": current["snapshot_date"],
        "date_previous": previous["snapshot_date"],
        "delta_total": current["total_risks"] - previous["total_risks"],
        "delta_open": current["open_risks"] - previous["open_risks"],
        "delta_closed": current["closed_risks"] - previous["closed_risks"],
        "delta_high": current["high_risks"] - previous["high_risks"],
        "delta_compliance": round(
            current["compliance_score"] - previous["compliance_score"], 1
        ),
    }


def get_snapshot_count(db_path: Path = DB_PATH) -> int:
    """
    Get the total number of snapshots in the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        int: Number of snapshots stored.
    """

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM snapshots")
    count = cursor.fetchone()[0]

    conn.close()

    return count
