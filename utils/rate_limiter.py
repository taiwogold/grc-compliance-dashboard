"""
Database-Backed Rate Limiter
Version: 3.1.0
Author: Taiwo Durodola-Tunde

Provides persistent rate limiting for email dispatch and other
actions. Unlike session-based limits (which reset on page refresh),
this uses the database to enforce daily/hourly quotas that persist
across sessions and reboots.

Architecture:
    - Stores rate limit counters in SQLite or PostgreSQL
    - Supports per-organisation and per-action-type limits
    - Daily and hourly windows
    - Configurable limits per action type
    - Graceful fallback to session-based if DB unavailable

Rate Limit Types:
    - email_send: Max emails per day (default: 100)
    - email_bulk: Max bulk dispatches per day (default: 10)
    - csv_upload: Max uploads per day (default: 50)
    - pdf_export: Max PDF exports per day (default: 50)
    - api_request: Max API calls per hour (default: 1000)

Usage:
    from utils.rate_limiter import RateLimiter

    limiter = RateLimiter()
    limiter.init_tables()

    if limiter.check_limit("email_send"):
        # Proceed with send
        limiter.record_action("email_send")
    else:
        remaining = limiter.get_reset_time("email_send")
        st.error(f"Rate limit reached. Resets in {remaining}")

Functions:
    RateLimiter.init_tables: Create rate limit tables.
    RateLimiter.check_limit: Check if action is allowed.
    RateLimiter.record_action: Increment counter for action.
    RateLimiter.get_usage: Get current usage for an action.
    RateLimiter.get_reset_time: Time until limit resets.
    RateLimiter.get_all_limits: Get all configured limits.
"""

import logging
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from .config import config as app_config

logger = logging.getLogger(__name__)


# ==========================================================
# DEFAULT RATE LIMITS
# ==========================================================

DEFAULT_LIMITS = {
    "email_send": {
        "max_per_day": 100,
        "max_per_hour": 20,
        "description": "Individual email sends",
    },
    "email_bulk": {
        "max_per_day": 10,
        "max_per_hour": 5,
        "description": "Bulk email dispatches",
    },
    "csv_upload": {
        "max_per_day": 50,
        "max_per_hour": 10,
        "description": "CSV file uploads",
    },
    "pdf_export": {
        "max_per_day": 50,
        "max_per_hour": 20,
        "description": "PDF report exports",
    },
    "api_request": {
        "max_per_day": 5000,
        "max_per_hour": 1000,
        "description": "API endpoint requests",
    },
}


# ==========================================================
# RATE LIMITER CLASS
# ==========================================================

class RateLimiter:
    """
    Database-backed rate limiter with daily and hourly windows.

    Persists rate limit counters in the database so limits
    survive page refreshes, session resets, and app reboots.

    Supports both SQLite (local) and PostgreSQL (cloud) backends
    via the database manager.

    Attributes:
        db_path (Path): Path to SQLite database.
        limits (dict): Configured limits per action type.
        org_id (int): Organisation ID for multi-tenant isolation.
    """

    def __init__(
        self,
        db_path: Path = None,
        org_id: int = 1,
        custom_limits: dict = None
    ):
        """
        Initialise the rate limiter.

        Args:
            db_path: Path to SQLite file. Defaults to config.
            org_id: Organisation ID for isolation.
            custom_limits: Override default limits with custom values.
        """

        self.db_path = db_path or app_config.DB_PATH
        self.org_id = org_id
        self.limits = custom_limits or DEFAULT_LIMITS

    def init_tables(self):
        """
        Create the rate_limits table if it doesn't exist.

        Safe to call on every app load.
        """

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER NOT NULL DEFAULT 1,
                    action_type TEXT NOT NULL,
                    action_date TEXT NOT NULL,
                    action_hour INTEGER NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    last_updated TEXT NOT NULL,
                    UNIQUE(org_id, action_type, action_date, action_hour)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup
                ON rate_limits(org_id, action_type, action_date)
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to init rate limit tables: {e}")

    def check_limit(self, action_type: str) -> bool:
        """
        Check if an action is within its rate limit.

        Checks both daily and hourly limits.

        Args:
            action_type: The action to check (e.g. 'email_send').

        Returns:
            bool: True if action is allowed, False if limit reached.
        """

        if action_type not in self.limits:
            # Unknown action type — allow by default
            return True

        limit_config = self.limits[action_type]
        today_str = date.today().isoformat()
        current_hour = datetime.now().hour

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Check daily limit
            cursor.execute("""
                SELECT COALESCE(SUM(count), 0)
                FROM rate_limits
                WHERE org_id = ? AND action_type = ? AND action_date = ?
            """, (self.org_id, action_type, today_str))

            daily_count = cursor.fetchone()[0]

            if daily_count >= limit_config["max_per_day"]:
                conn.close()
                return False

            # Check hourly limit
            cursor.execute("""
                SELECT COALESCE(SUM(count), 0)
                FROM rate_limits
                WHERE org_id = ? AND action_type = ?
                AND action_date = ? AND action_hour = ?
            """, (self.org_id, action_type, today_str, current_hour))

            hourly_count = cursor.fetchone()[0]

            conn.close()

            if hourly_count >= limit_config["max_per_hour"]:
                return False

            return True

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the action (fail open)
            return True

    def record_action(self, action_type: str):
        """
        Record that an action was performed (increment counter).

        Uses UPSERT logic — creates a new row if none exists
        for this org/action/date/hour, or increments the count.

        Args:
            action_type: The action performed.
        """

        today_str = date.today().isoformat()
        current_hour = datetime.now().hour
        now_str = datetime.now().isoformat()

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Try to update existing row
            cursor.execute("""
                UPDATE rate_limits
                SET count = count + 1, last_updated = ?
                WHERE org_id = ? AND action_type = ?
                AND action_date = ? AND action_hour = ?
            """, (now_str, self.org_id, action_type, today_str, current_hour))

            # If no row existed, insert new one
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO rate_limits
                    (org_id, action_type, action_date, action_hour,
                     count, last_updated)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (self.org_id, action_type, today_str, current_hour, now_str))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record rate limit action: {e}")

    def get_usage(self, action_type: str) -> dict:
        """
        Get current usage stats for an action type.

        Args:
            action_type: The action to check.

        Returns:
            dict: Usage data with keys:
                - daily_used (int)
                - daily_limit (int)
                - daily_remaining (int)
                - hourly_used (int)
                - hourly_limit (int)
                - hourly_remaining (int)
                - percentage_used (float)
        """

        if action_type not in self.limits:
            return {
                "daily_used": 0, "daily_limit": 0,
                "daily_remaining": 0, "hourly_used": 0,
                "hourly_limit": 0, "hourly_remaining": 0,
                "percentage_used": 0.0,
            }

        limit_config = self.limits[action_type]
        today_str = date.today().isoformat()
        current_hour = datetime.now().hour

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Daily count
            cursor.execute("""
                SELECT COALESCE(SUM(count), 0)
                FROM rate_limits
                WHERE org_id = ? AND action_type = ? AND action_date = ?
            """, (self.org_id, action_type, today_str))
            daily_used = cursor.fetchone()[0]

            # Hourly count
            cursor.execute("""
                SELECT COALESCE(SUM(count), 0)
                FROM rate_limits
                WHERE org_id = ? AND action_type = ?
                AND action_date = ? AND action_hour = ?
            """, (self.org_id, action_type, today_str, current_hour))
            hourly_used = cursor.fetchone()[0]

            conn.close()

            daily_limit = limit_config["max_per_day"]
            hourly_limit = limit_config["max_per_hour"]

            return {
                "daily_used": daily_used,
                "daily_limit": daily_limit,
                "daily_remaining": max(0, daily_limit - daily_used),
                "hourly_used": hourly_used,
                "hourly_limit": hourly_limit,
                "hourly_remaining": max(0, hourly_limit - hourly_used),
                "percentage_used": round(
                    daily_used / daily_limit * 100, 1
                ) if daily_limit > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Usage query failed: {e}")
            return {
                "daily_used": 0, "daily_limit": 0,
                "daily_remaining": 0, "hourly_used": 0,
                "hourly_limit": 0, "hourly_remaining": 0,
                "percentage_used": 0.0,
            }

    def get_reset_time(self, action_type: str) -> str:
        """
        Get human-readable time until the limit resets.

        Daily limits reset at midnight. Hourly limits reset
        at the top of the next hour.

        Args:
            action_type: The action type.

        Returns:
            str: e.g. "Resets in 2h 15m" or "Resets at midnight"
        """

        now = datetime.now()
        usage = self.get_usage(action_type)

        # Check if hourly limit is hit
        if action_type in self.limits:
            limit_config = self.limits[action_type]
            if usage["hourly_used"] >= limit_config["max_per_hour"]:
                # Resets at next hour
                next_hour = now.replace(
                    minute=0, second=0, microsecond=0
                ) + timedelta(hours=1)
                diff = next_hour - now
                minutes = int(diff.total_seconds() / 60)
                return f"Hourly limit resets in {minutes}m"

        # Daily limit
        midnight = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        diff = midnight - now
        hours = int(diff.total_seconds() / 3600)
        minutes = int((diff.total_seconds() % 3600) / 60)

        return f"Daily limit resets in {hours}h {minutes}m"

    def get_all_limits(self) -> dict:
        """
        Get all configured limits with current usage.

        Returns:
            dict: Action types mapped to their config + usage.
        """

        result = {}

        for action_type, config in self.limits.items():
            usage = self.get_usage(action_type)
            result[action_type] = {
                **config,
                **usage,
            }

        return result

    def cleanup_old_records(self, days_to_keep: int = 30):
        """
        Remove rate limit records older than N days.

        Prevents the table from growing unbounded.

        Args:
            days_to_keep: Number of days of history to retain.
        """

        cutoff = (
            date.today() - timedelta(days=days_to_keep)
        ).isoformat()

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM rate_limits WHERE action_date < ?",
                (cutoff,)
            )

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                logger.info(
                    f"Rate limiter cleanup: removed {deleted} old records"
                )

        except Exception as e:
            logger.error(f"Rate limit cleanup failed: {e}")
