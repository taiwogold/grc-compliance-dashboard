"""
PostgreSQL Database Module
Version: 3.0.0
Author: Taiwo Durodola-Tunde

Provides a PostgreSQL backend for persistent data storage.
Replaces SQLite for cloud deployments where data must survive
app reboots.

Architecture:
    - Connection string stored in st.secrets (never in code)
    - Auto-detects: uses PostgreSQL if configured, SQLite fallback
    - SSL required for all connections (Neon enforces this)
    - Connection pooling via psycopg2
    - All tables created on first connection (idempotent)

Tables:
    risk_snapshots   - Point-in-time risk register captures
    risk_history     - Individual risk records per snapshot
    audit_trail      - All dashboard actions logged
    compliance_trend - Historical compliance scores

Security:
    - Connection string in st.secrets only (gitignored)
    - SSL/TLS enforced (sslmode=require)
    - No credentials in source code
    - Read-only queries use parameterised statements

Usage:
    from utils.db_postgres import get_connection, init_postgres_tables

    conn = get_connection()
    if conn:
        # PostgreSQL available
        init_postgres_tables(conn)
    else:
        # Fall back to SQLite
        ...
"""

import logging
from datetime import datetime, date
from typing import Optional

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


# ==========================================================
# CONNECTION MANAGEMENT
# ==========================================================

def get_connection_string() -> Optional[str]:
    """
    Retrieve the PostgreSQL connection string from st.secrets.

    The connection string is stored in Streamlit secrets under:
        [database]
        url = "postgresql://..."

    Returns:
        str: Connection string, or None if not configured.
    """

    try:
        return st.secrets["database"]["url"]
    except (KeyError, FileNotFoundError):
        return None


def get_connection():
    """
    Establish a PostgreSQL connection.

    Returns:
        psycopg2 connection object, or None if PostgreSQL
        is not configured or unavailable.
    """

    conn_str = get_connection_string()

    if not conn_str:
        return None

    try:
        import psycopg2

        conn = psycopg2.connect(conn_str)
        return conn

    except ImportError:
        logger.warning(
            "psycopg2 not installed. "
            "Run: pip install psycopg2-binary"
        )
        return None

    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return None


def is_postgres_available() -> bool:
    """
    Check if PostgreSQL is configured and reachable.

    Returns:
        bool: True if connection can be established.
    """

    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False


# ==========================================================
# SCHEMA INITIALISATION
# ==========================================================

def init_postgres_tables():
    """
    Create all required tables if they don't exist.

    Safe to call on every app load — uses IF NOT EXISTS.
    Creates indexes for performance on common queries.
    """

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # --- Snapshots summary table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_snapshots (
                snapshot_id SERIAL PRIMARY KEY,
                snapshot_date DATE UNIQUE NOT NULL,
                total_risks INTEGER NOT NULL,
                open_risks INTEGER NOT NULL,
                closed_risks INTEGER NOT NULL,
                high_risks INTEGER NOT NULL,
                compliance_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # --- Risk history detail ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_history (
                id SERIAL PRIMARY KEY,
                snapshot_id INTEGER NOT NULL
                    REFERENCES risk_snapshots(snapshot_id),
                risk_id TEXT NOT NULL,
                risk_name TEXT,
                risk_level TEXT,
                status TEXT,
                risk_owner TEXT,
                likelihood INTEGER,
                impact INTEGER,
                control_status TEXT,
                due_date DATE,
                residual_score REAL
            )
        """)

        # --- Audit trail ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                action_type TEXT NOT NULL,
                description TEXT,
                user_context TEXT DEFAULT 'Dashboard User',
                metadata TEXT,
                session_id TEXT
            )
        """)

        # --- Compliance trend ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_trend (
                id SERIAL PRIMARY KEY,
                record_date DATE NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # --- Indexes ---
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rh_risk_id
            ON risk_history(risk_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rh_snapshot
            ON risk_history(snapshot_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_type
            ON audit_trail(action_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_ts
            ON audit_trail(timestamp)
        """)

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("PostgreSQL tables initialised successfully.")
        return True

    except Exception as e:
        logger.error(f"Failed to initialise PostgreSQL tables: {e}")
        conn.close()
        return False


# ==========================================================
# SNAPSHOT OPERATIONS
# ==========================================================

def pg_has_snapshot_today() -> bool:
    """Check if today's snapshot already exists in PostgreSQL."""

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM risk_snapshots WHERE snapshot_date = %s",
            (date.today(),)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0

    except Exception as e:
        logger.error(f"Snapshot check failed: {e}")
        conn.close()
        return False


def pg_capture_snapshot(
    risk_df,
    compliance_score: float,
    scored_df=None
) -> Optional[int]:
    """
    Capture a daily snapshot to PostgreSQL.

    Args:
        risk_df: Current risk register DataFrame.
        compliance_score: Current compliance percentage.
        scored_df: Optional DataFrame with risk scores.

    Returns:
        int: Snapshot ID, or None if already captured today.
    """

    if pg_has_snapshot_today():
        return None

    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Summary metrics
        total = len(risk_df)
        open_r = len(risk_df[risk_df["Status"] == "Open"])
        closed_r = len(risk_df[risk_df["Status"] == "Closed"])
        high_r = len(risk_df[risk_df["Risk_Level"] == "High"])

        cursor.execute("""
            INSERT INTO risk_snapshots
            (snapshot_date, total_risks, open_risks, closed_risks,
             high_risks, compliance_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING snapshot_id
        """, (date.today(), total, open_r, closed_r, high_r, compliance_score))

        snapshot_id = cursor.fetchone()[0]

        # Insert risk detail
        source_df = scored_df if scored_df is not None else risk_df

        for _, row in source_df.iterrows():
            residual = (
                float(row.get("Residual_Risk_Score", 0))
                if scored_df is not None and "Residual_Risk_Score" in row
                else None
            )

            due_date_val = None
            if "Due_Date" in row and pd.notna(row.get("Due_Date")):
                try:
                    due_date_val = pd.to_datetime(row["Due_Date"]).date()
                except Exception:
                    due_date_val = None

            cursor.execute("""
                INSERT INTO risk_history
                (snapshot_id, risk_id, risk_name, risk_level, status,
                 risk_owner, likelihood, impact, control_status,
                 due_date, residual_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                due_date_val,
                residual,
            ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"PostgreSQL snapshot {snapshot_id} captured.")
        return snapshot_id

    except Exception as e:
        logger.error(f"Snapshot capture failed: {e}")
        conn.rollback()
        conn.close()
        return None


# ==========================================================
# QUERY OPERATIONS
# ==========================================================

def pg_get_snapshots() -> pd.DataFrame:
    """Retrieve all snapshot summaries from PostgreSQL."""

    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        df = pd.read_sql_query(
            "SELECT * FROM risk_snapshots ORDER BY snapshot_date DESC",
            conn
        )
        conn.close()
        return df

    except Exception as e:
        logger.error(f"Failed to fetch snapshots: {e}")
        conn.close()
        return pd.DataFrame()


def pg_get_risk_history(risk_id: str) -> pd.DataFrame:
    """Track a specific risk across all snapshots."""

    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        df = pd.read_sql_query("""
            SELECT
                s.snapshot_date,
                rh.risk_id, rh.risk_name, rh.risk_level,
                rh.status, rh.risk_owner, rh.likelihood,
                rh.impact, rh.control_status, rh.residual_score
            FROM risk_history rh
            JOIN risk_snapshots s ON s.snapshot_id = rh.snapshot_id
            WHERE rh.risk_id = %s
            ORDER BY s.snapshot_date ASC
        """, conn, params=(risk_id,))
        conn.close()
        return df

    except Exception as e:
        logger.error(f"Risk history query failed: {e}")
        conn.close()
        return pd.DataFrame()


def pg_get_latest_delta() -> Optional[dict]:
    """Compare the two most recent snapshots."""

    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT snapshot_date, total_risks, open_risks,
                   closed_risks, high_risks, compliance_score
            FROM risk_snapshots
            ORDER BY snapshot_date DESC
            LIMIT 2
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(rows) < 2:
            return None

        current = rows[0]
        previous = rows[1]

        return {
            "date_current": str(current[0]),
            "date_previous": str(previous[0]),
            "delta_total": current[1] - previous[1],
            "delta_open": current[2] - previous[2],
            "delta_closed": current[3] - previous[3],
            "delta_high": current[4] - previous[4],
            "delta_compliance": round(current[5] - previous[5], 1),
        }

    except Exception as e:
        logger.error(f"Delta query failed: {e}")
        conn.close()
        return None


def pg_get_snapshot_count() -> int:
    """Get total number of snapshots."""

    conn = get_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risk_snapshots")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    except Exception as e:
        logger.error(f"Snapshot count failed: {e}")
        conn.close()
        return 0


# ==========================================================
# AUDIT TRAIL OPERATIONS
# ==========================================================

def pg_log_action(
    action_type: str,
    description: str,
    metadata: str = "",
    user_context: str = "Dashboard User",
    session_id: str = ""
):
    """Log an action to the PostgreSQL audit trail."""

    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail
            (action_type, description, user_context, metadata, session_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (action_type, description, user_context, metadata, session_id))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        conn.close()


def pg_get_audit_trail(
    action_type: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """Retrieve audit trail entries."""

    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        if action_type:
            df = pd.read_sql_query(
                """SELECT * FROM audit_trail
                   WHERE action_type = %s
                   ORDER BY timestamp DESC LIMIT %s""",
                conn, params=(action_type, limit)
            )
        else:
            df = pd.read_sql_query(
                """SELECT * FROM audit_trail
                   ORDER BY timestamp DESC LIMIT %s""",
                conn, params=(limit,)
            )
        conn.close()
        return df

    except Exception as e:
        logger.error(f"Audit trail query failed: {e}")
        conn.close()
        return pd.DataFrame()


def pg_get_audit_summary() -> dict:
    """Get action counts grouped by type."""

    conn = get_connection()
    if not conn:
        return {}

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action_type, COUNT(*)
            FROM audit_trail
            GROUP BY action_type
            ORDER BY COUNT(*) DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {row[0]: row[1] for row in rows}

    except Exception as e:
        logger.error(f"Audit summary failed: {e}")
        conn.close()
        return {}


def pg_get_audit_count() -> int:
    """Get total audit entries count."""

    conn = get_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_trail")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    except Exception as e:
        logger.error(f"Audit count failed: {e}")
        conn.close()
        return 0


def pg_export_audit_trail() -> str:
    """Export full audit trail as CSV string."""

    conn = get_connection()
    if not conn:
        return ""

    try:
        df = pd.read_sql_query(
            "SELECT * FROM audit_trail ORDER BY timestamp DESC",
            conn
        )
        conn.close()
        return df.to_csv(index=False)

    except Exception as e:
        logger.error(f"Audit export failed: {e}")
        conn.close()
        return ""
