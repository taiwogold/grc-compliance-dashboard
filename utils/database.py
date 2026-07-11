"""
Database Module - SQLite Risk History with Multi-Org Support
Version: 2.4.0
Author: Taiwo Durodola-Tunde

Adds multi-tenant organisation support to the SQLite database.
Every table now carries an organization_id so data from
different tenants is fully isolated at the query layer.

Backwards Compatibility:
    All existing functions work unchanged — organization_id
    defaults to 1 (the default single-tenant org). Existing
    databases are migrated automatically on first load.

Architecture:
    - SQLite path read from utils.config (no hardcoding)
    - One snapshot per calendar day per organisation
    - Full risk register state preserved per snapshot
    - Row-level org isolation on all queries

Tables:
    organizations:
        - org_id (INTEGER PRIMARY KEY)
        - org_name (TEXT UNIQUE)
        - created_at (TEXT)

    snapshots:
        - snapshot_id (INTEGER PRIMARY KEY)
        - organization_id (INTEGER FK -> organizations)
        - snapshot_date (TEXT)
        - total_risks, open_risks, closed_risks, high_risks
        - compliance_score (REAL)
        - created_at (TEXT)
        UNIQUE (organization_id, snapshot_date)

    risk_history:
        - id (INTEGER PRIMARY KEY)
        - organization_id (INTEGER FK -> organizations)
        - snapshot_id (INTEGER FK -> snapshots)
        - risk_id, risk_name, risk_level, status
        - risk_owner, likelihood, impact
        - control_status, due_date, residual_score
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import config as app_config

logger = logging.getLogger(__name__)

# Default org_id for single-tenant / backwards-compatible usage
DEFAULT_ORG_ID = 1
DEFAULT_ORG_NAME = "Default Organisation"


# ==========================================================
# CONNECTION MANAGEMENT
# ==========================================================

@contextmanager
def get_db_connection(db_path: Path = None):
    """
    Context manager for SQLite connections.

    Opens a connection, yields it, then closes it cleanly
    whether or not an exception occurred.

    Args:
        db_path: Path to SQLite file. Defaults to config value.

    Yields:
        sqlite3.Connection
    """
    path = db_path or app_config.DB_PATH
    conn = sqlite3.connect(str(path), check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


# ==========================================================
# DATABASE INITIALISATION
# ==========================================================

def init_database(db_path: Path = None):
    """
    Create all tables and run any pending migrations.

    Safe to call on every dashboard load — all statements
    use CREATE TABLE IF NOT EXISTS and ALTER TABLE only
    when columns are missing.

    Args:
        db_path: Path to SQLite file. Defaults to config value.
    """
    path = db_path or app_config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection(path) as conn:
        cursor = conn.cursor()

        # --- Organizations table (new in v2.4.0) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                org_name    TEXT    UNIQUE NOT NULL,
                created_at  TEXT    NOT NULL
            )
        """)

        # Ensure default org exists
        cursor.execute("""
            INSERT OR IGNORE INTO organizations (org_name, created_at)
            VALUES (?, ?)
        """, (DEFAULT_ORG_NAME, datetime.now().isoformat()))

        # --- Snapshots table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id  INTEGER NOT NULL DEFAULT 1,
                snapshot_date    TEXT    NOT NULL,
                total_risks      INTEGER NOT NULL,
                open_risks       INTEGER NOT NULL,
                closed_risks     INTEGER NOT NULL,
                high_risks       INTEGER NOT NULL,
                compliance_score REAL    NOT NULL,
                created_at       TEXT    NOT NULL,
                UNIQUE (organization_id, snapshot_date),
                FOREIGN KEY (organization_id)
                    REFERENCES organizations(org_id)
            )
        """)

        # --- Risk history table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_history (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id  INTEGER NOT NULL DEFAULT 1,
                snapshot_id      INTEGER NOT NULL,
                risk_id          TEXT    NOT NULL,
                risk_name        TEXT,
                risk_level       TEXT,
                status           TEXT,
                risk_owner       TEXT,
                likelihood       INTEGER,
                impact           INTEGER,
                control_status   TEXT,
                due_date         TEXT,
                residual_score   REAL,
                FOREIGN KEY (snapshot_id)
                    REFERENCES snapshots(snapshot_id),
                FOREIGN KEY (organization_id)
                    REFERENCES organizations(org_id)
            )
        """)

        # --- Indexes ---
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risk_history_risk_id
            ON risk_history(risk_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risk_history_snapshot
            ON risk_history(snapshot_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_org
            ON snapshots(organization_id, snapshot_date)
        """)

        # --- Migration: add organization_id to existing tables ---
        _migrate_add_org_id(cursor, "snapshots")
        _migrate_add_org_id(cursor, "risk_history")

        conn.commit()

    logger.info(f"Database initialised at {path}")


def _migrate_add_org_id(cursor, table_name: str):
    """
    Add organization_id column to an existing table if missing.

    This handles upgrading databases created before v2.4.0.

    Args:
        cursor:     Active SQLite cursor.
        table_name: Table to check and migrate.
    """
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]

        if "organization_id" not in columns:
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1
            """)
            logger.info(
                f"Migration: added organization_id to {table_name}"
            )
    except sqlite3.OperationalError as e:
        logger.warning(f"Migration skipped for {table_name}: {e}")


# ==========================================================
# ORGANISATION MANAGEMENT
# ==========================================================

def get_or_create_org(
    org_name: str = DEFAULT_ORG_NAME,
    db_path: Path = None
) -> int:
    """
    Get the org_id for an organisation, creating it if needed.

    Args:
        org_name: Organisation display name.
        db_path:  Path to SQLite file.

    Returns:
        int: The org_id for the organisation.
    """
    path = db_path or app_config.DB_PATH

    with get_db_connection(path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO organizations (org_name, created_at)
            VALUES (?, ?)
        """, (org_name, datetime.now().isoformat()))

        cursor.execute(
            "SELECT org_id FROM organizations WHERE org_name = ?",
            (org_name,)
        )
        row = cursor.fetchone()
        conn.commit()

    return row[0] if row else DEFAULT_ORG_ID


def list_organisations(db_path: Path = None) -> pd.DataFrame:
    """
    List all registered organisations.

    Args:
        db_path: Path to SQLite file.

    Returns:
        DataFrame: org_id, org_name, created_at columns.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM organizations ORDER BY org_name",
            conn
        )


# ==========================================================
# SNAPSHOT CAPTURE
# ==========================================================

def has_snapshot_today(
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> bool:
    """
    Check if today's snapshot already exists for this org.

    Args:
        org_id:  Organisation ID to check.
        db_path: Path to SQLite file.

    Returns:
        bool: True if today's snapshot already exists.
    """
    today_str = date.today().isoformat()

    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) FROM snapshots
               WHERE snapshot_date = ? AND organization_id = ?""",
            (today_str, org_id)
        )
        return cursor.fetchone()[0] > 0


def capture_snapshot(
    risk_df,
    compliance_score: float,
    scored_df=None,
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> Optional[int]:
    """
    Capture a point-in-time snapshot of the risk register.

    One snapshot per calendar day per organisation. Subsequent
    calls on the same day are silently ignored.

    Args:
        risk_df:          Current risk register DataFrame.
        compliance_score: Current compliance percentage.
        scored_df:        Optional DataFrame with residual scores.
        org_id:           Organisation ID. Defaults to 1.
        db_path:          Path to SQLite file.

    Returns:
        int: New snapshot_id, or None if already captured today.
    """
    if has_snapshot_today(org_id, db_path):
        return None

    path = db_path or app_config.DB_PATH
    today_str = date.today().isoformat()
    now_str = datetime.now().isoformat()

    total_risks  = len(risk_df)
    open_risks   = len(risk_df[risk_df["Status"] == "Open"])
    closed_risks = len(risk_df[risk_df["Status"] == "Closed"])
    high_risks   = len(risk_df[risk_df["Risk_Level"] == "High"])

    with get_db_connection(path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO snapshots
            (organization_id, snapshot_date, total_risks, open_risks,
             closed_risks, high_risks, compliance_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_id, today_str, total_risks, open_risks,
            closed_risks, high_risks, compliance_score, now_str
        ))

        snapshot_id = cursor.lastrowid

        source_df = scored_df if scored_df is not None else risk_df

        for _, row in source_df.iterrows():
            residual_score = (
                row.get("Residual_Risk_Score")
                if scored_df is not None else None
            )

            cursor.execute("""
                INSERT INTO risk_history
                (organization_id, snapshot_id, risk_id, risk_name,
                 risk_level, status, risk_owner, likelihood, impact,
                 control_status, due_date, residual_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                org_id,
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
                float(residual_score)
                    if residual_score is not None else None,
            ))

        conn.commit()

    logger.info(
        f"Snapshot {snapshot_id} captured for org {org_id} "
        f"on {today_str}"
    )
    return snapshot_id


# ==========================================================
# QUERY FUNCTIONS
# ==========================================================

def get_snapshots(
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> pd.DataFrame:
    """
    Retrieve all snapshot summaries for an organisation.

    Args:
        org_id:  Organisation ID to filter by.
        db_path: Path to SQLite file.

    Returns:
        DataFrame: Snapshot summaries ordered by date desc.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        return pd.read_sql_query(
            """SELECT * FROM snapshots
               WHERE organization_id = ?
               ORDER BY snapshot_date DESC""",
            conn,
            params=(org_id,)
        )


def get_snapshot_detail(
    snapshot_id: int,
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> pd.DataFrame:
    """
    Get full risk register for a specific snapshot.

    Args:
        snapshot_id: Snapshot ID to retrieve.
        org_id:      Organisation ID (security check).
        db_path:     Path to SQLite file.

    Returns:
        DataFrame: All risk records from that snapshot.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        return pd.read_sql_query(
            """SELECT * FROM risk_history
               WHERE snapshot_id = ? AND organization_id = ?""",
            conn,
            params=(snapshot_id, org_id)
        )


def get_risk_history(
    risk_id: str,
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> pd.DataFrame:
    """
    Track a specific risk across all snapshots over time.

    Args:
        risk_id: The Risk_ID to track (e.g. 'R001').
        org_id:  Organisation ID to filter by.
        db_path: Path to SQLite file.

    Returns:
        DataFrame: Historical records for the risk.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        return pd.read_sql_query("""
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
              AND rh.organization_id = ?
            ORDER BY s.snapshot_date ASC
        """, conn, params=(risk_id, org_id))


def get_latest_delta(
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> Optional[dict]:
    """
    Compare the two most recent snapshots for delta analysis.

    Args:
        org_id:  Organisation ID to filter by.
        db_path: Path to SQLite file.

    Returns:
        dict: Delta values, or None if fewer than 2 snapshots.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM snapshots
            WHERE organization_id = ?
            ORDER BY snapshot_date DESC
            LIMIT 2
        """, (org_id,))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

    if len(rows) < 2:
        return None

    current  = dict(zip(columns, rows[0]))
    previous = dict(zip(columns, rows[1]))

    return {
        "date_current":      current["snapshot_date"],
        "date_previous":     previous["snapshot_date"],
        "delta_total":       current["total_risks"]      - previous["total_risks"],
        "delta_open":        current["open_risks"]       - previous["open_risks"],
        "delta_closed":      current["closed_risks"]     - previous["closed_risks"],
        "delta_high":        current["high_risks"]       - previous["high_risks"],
        "delta_compliance":  round(
            current["compliance_score"] - previous["compliance_score"], 1
        ),
    }


def get_snapshot_count(
    org_id: int = DEFAULT_ORG_ID,
    db_path: Path = None
) -> int:
    """
    Get total number of snapshots for an organisation.

    Args:
        org_id:  Organisation ID to filter by.
        db_path: Path to SQLite file.

    Returns:
        int: Number of snapshots stored.
    """
    with get_db_connection(db_path or app_config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM snapshots WHERE organization_id = ?",
            (org_id,)
        )
        return cursor.fetchone()[0]
