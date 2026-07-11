"""
Database Manager - Smart Backend Switching
Version: 3.0.0
Author: Taiwo Durodola-Tunde

Provides a unified interface that automatically routes database
operations to PostgreSQL (cloud) or SQLite (local) based on
configuration.

Logic:
    - If st.secrets has [database][url] → use PostgreSQL
    - Otherwise → fall back to SQLite (existing behaviour)

This ensures:
    - Zero code changes needed in dashboard.py
    - Local development works without PostgreSQL
    - Cloud deployment uses persistent PostgreSQL
    - Same API regardless of backend

Usage:
    from utils.db_manager import db

    db.init()
    db.capture_snapshot(risk_df, score, scored_df)
    snapshots = db.get_snapshots()
    db.log_action("dashboard_load", "Started")
"""

import logging
from typing import Optional

import pandas as pd

from .db_postgres import (
    is_postgres_available,
    init_postgres_tables,
    pg_capture_snapshot,
    pg_get_snapshots,
    pg_get_risk_history,
    pg_get_latest_delta,
    pg_get_snapshot_count,
    pg_has_snapshot_today,
    pg_log_action,
    pg_get_audit_trail,
    pg_get_audit_summary,
    pg_get_audit_count,
    pg_export_audit_trail,
)

from .database import (
    init_database,
    capture_snapshot as sqlite_capture_snapshot,
    get_snapshots as sqlite_get_snapshots,
    get_risk_history as sqlite_get_risk_history,
    get_latest_delta as sqlite_get_latest_delta,
    get_snapshot_count as sqlite_get_snapshot_count,
)

from .audit_trail import (
    init_audit_table as sqlite_init_audit,
    log_action as sqlite_log_action,
    get_audit_trail as sqlite_get_audit_trail,
    get_audit_summary as sqlite_get_audit_summary,
    get_audit_count as sqlite_get_audit_count,
    export_audit_trail as sqlite_export_audit_trail,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Unified database interface with automatic backend selection.

    Detects whether PostgreSQL is configured and available,
    then routes all operations to the appropriate backend.

    Attributes:
        backend (str): 'postgresql' or 'sqlite'
        is_ready (bool): Whether the database is initialised
    """

    def __init__(self):
        self.backend = "sqlite"
        self.is_ready = False

    def init(self):
        """
        Initialise the database backend.

        Checks for PostgreSQL configuration first. If available,
        creates tables there. Otherwise falls back to SQLite.
        """

        if is_postgres_available():
            self.backend = "postgresql"
            success = init_postgres_tables()
            if success:
                self.is_ready = True
                logger.info("Database backend: PostgreSQL (Neon)")
            else:
                # Fall back to SQLite if PG init fails
                self.backend = "sqlite"
                init_database()
                sqlite_init_audit()
                self.is_ready = True
                logger.warning(
                    "PostgreSQL init failed — falling back to SQLite"
                )
        else:
            self.backend = "sqlite"
            init_database()
            sqlite_init_audit()
            self.is_ready = True
            logger.info("Database backend: SQLite (local)")

    # ==========================================================
    # SNAPSHOT OPERATIONS
    # ==========================================================

    def capture_snapshot(
        self,
        risk_df,
        compliance_score: float,
        scored_df=None
    ) -> Optional[int]:
        """Capture a daily snapshot to the active backend."""

        if self.backend == "postgresql":
            return pg_capture_snapshot(
                risk_df, compliance_score, scored_df
            )
        else:
            return sqlite_capture_snapshot(
                risk_df, compliance_score, scored_df
            )

    def get_snapshots(self) -> pd.DataFrame:
        """Retrieve all snapshot summaries."""

        if self.backend == "postgresql":
            return pg_get_snapshots()
        else:
            return sqlite_get_snapshots()

    def get_risk_history(self, risk_id: str) -> pd.DataFrame:
        """Track a specific risk over time."""

        if self.backend == "postgresql":
            return pg_get_risk_history(risk_id)
        else:
            return sqlite_get_risk_history(risk_id)

    def get_latest_delta(self) -> Optional[dict]:
        """Compare current vs previous snapshot."""

        if self.backend == "postgresql":
            return pg_get_latest_delta()
        else:
            return sqlite_get_latest_delta()

    def get_snapshot_count(self) -> int:
        """Get total snapshots stored."""

        if self.backend == "postgresql":
            return pg_get_snapshot_count()
        else:
            return sqlite_get_snapshot_count()

    # ==========================================================
    # AUDIT TRAIL OPERATIONS
    # ==========================================================

    def log_action(
        self,
        action_type: str,
        description: str,
        metadata: str = "",
        user_context: str = "Dashboard User"
    ):
        """Log an action to the audit trail."""

        if self.backend == "postgresql":
            pg_log_action(
                action_type, description, metadata, user_context
            )
        else:
            sqlite_log_action(
                action_type, description, metadata, user_context
            )

    def get_audit_trail(
        self,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Retrieve audit trail entries."""

        if self.backend == "postgresql":
            return pg_get_audit_trail(action_type, limit)
        else:
            return sqlite_get_audit_trail(action_type=action_type, limit=limit)

    def get_audit_summary(self) -> dict:
        """Get action counts by type."""

        if self.backend == "postgresql":
            return pg_get_audit_summary()
        else:
            return sqlite_get_audit_summary()

    def get_audit_count(self) -> int:
        """Get total audit entries."""

        if self.backend == "postgresql":
            return pg_get_audit_count()
        else:
            return sqlite_get_audit_count()

    def export_audit_trail(self) -> str:
        """Export audit trail as CSV string."""

        if self.backend == "postgresql":
            return pg_export_audit_trail()
        else:
            return sqlite_export_audit_trail()

    # ==========================================================
    # STATUS
    # ==========================================================

    def get_status(self) -> dict:
        """Return current database status for dashboard display."""

        return {
            "backend": self.backend,
            "is_ready": self.is_ready,
            "display_name": (
                "☁️ PostgreSQL (Neon)"
                if self.backend == "postgresql"
                else "💾 SQLite (Local)"
            ),
        }


# ==========================================================
# SINGLETON INSTANCE
# ==========================================================

db = DatabaseManager()
