"""
Email Dispatcher Module - Multi-Provider Email Dispatch
Version: 2.4.0
Author: Taiwo Durodola-Tunde

Replaces the hard Outlook-only dependency with a pluggable
provider abstraction. The provider is selected at runtime
based on configuration — defaulting to Outlook for backwards
compatibility, with SMTP, SendGrid, and Mock as alternatives.

Provider Selection (set in .env or environment):
    GRC_EMAIL_PROVIDER=outlook     Windows Outlook COM (default)
    GRC_EMAIL_PROVIDER=smtp        Any SMTP server
    GRC_EMAIL_PROVIDER=sendgrid    SendGrid HTTP API
    GRC_EMAIL_PROVIDER=mock        In-memory mock (testing)

Security Architecture (unchanged from v2.1.0):
    - Outlook provider: uses existing authenticated session
    - SMTP provider: credentials from environment only
    - SendGrid: API key from environment only
    - No credentials stored in code or on disk
    - Rate limiting, input validation, audit trail all preserved

Usage:
    from utils.email_dispatcher import OutlookDispatcher

    dispatcher = OutlookDispatcher()
    result = dispatcher.send_reminder(
        to="owner@company.com",
        subject="Risk Remediation Update Required",
        body="Please review your open risks...",
        importance="High"
    )

    # Result is now a dict for backwards compatibility
    # result["success"], result["message"]
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import config as app_config
from email_providers import get_provider

logger = logging.getLogger(__name__)


# ==========================================================
# OUTLOOK DISPATCHER — backwards-compatible wrapper
# ==========================================================

class OutlookDispatcher:
    """
    Backwards-compatible email dispatcher.

    Internally delegates to the configured email provider
    (Outlook, SMTP, SendGrid, or Mock) but exposes the same
    interface as the original OutlookDispatcher so no changes
    are needed in dashboard.py.

    The name is kept as OutlookDispatcher for compatibility.
    The actual provider used depends on GRC_EMAIL_PROVIDER.
    """

    def __init__(
        self,
        max_per_session: int = None,
        audit_dir: str = None
    ):
        """
        Initialise the dispatcher with the configured provider.

        Args:
            max_per_session: Override max emails per session.
            audit_dir: Override audit log directory.
        """
        # Apply overrides to config if provided
        if max_per_session is not None:
            app_config.MAX_EMAILS = max_per_session

        # Set up audit log
        self.audit_path = (
            Path(audit_dir) / "email_audit.csv"
            if audit_dir
            else app_config.AUDIT_LOG_PATH
        )
        self._ensure_audit_log()

        # Initialise the provider (auto-selected from config)
        self._provider = get_provider(app_config)

        logger.info(
            f"Email dispatcher initialised with provider: "
            f"{self._provider.provider_name}"
        )

    # ----------------------------------------------------------
    # PROPERTIES — expose provider state as before
    # ----------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """Return True if the active provider is ready."""
        return self._provider.is_available

    @property
    def provider_name(self) -> str:
        """Return the name of the active provider."""
        return self._provider.provider_name

    # ----------------------------------------------------------
    # AUDIT LOG
    # ----------------------------------------------------------

    def _ensure_audit_log(self):
        """Create audit log file with headers if not present."""
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.audit_path.exists():
            with open(self.audit_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Recipient", "Subject",
                    "Importance", "Status", "Provider", "Error"
                ])

    def _log_audit(
        self,
        recipient: str,
        subject: str,
        importance: str,
        status: str,
        provider: str = "",
        error: str = ""
    ):
        """Write an entry to the CSV audit log."""
        try:
            with open(self.audit_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    recipient,
                    subject,
                    importance,
                    status,
                    provider or self._provider.provider_name,
                    error
                ])
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    # ----------------------------------------------------------
    # SEND METHODS — same interface as before
    # ----------------------------------------------------------

    def send_reminder(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None
    ) -> dict:
        """
        Send a reminder email via the active provider.

        Returns the same dict format as the original dispatcher
        for full backwards compatibility with dashboard.py.

        Args:
            to:         Recipient email address.
            subject:    Email subject line.
            body:       Plain text email body.
            importance: Priority ('Low', 'Normal', 'High').
            cc:         Optional CC address.

        Returns:
            dict: {success, message, timestamp, recipient}
        """
        result = self._provider.send(
            to=to,
            subject=subject,
            body=body,
            importance=importance,
            cc=cc
        )

        # Log to audit trail
        self._log_audit(
            recipient=to,
            subject=subject,
            importance=importance,
            status="Sent" if result.success else "Failed",
            provider=result.provider,
            error="" if result.success else result.message
        )

        # Return as dict for backwards compatibility
        return {
            "success": result.success,
            "message": result.message,
            "timestamp": result.timestamp,
            "recipient": result.recipient,
        }

    def send_bulk_reminders(
        self,
        recipients: list,
        subject: str,
        body_template: str,
        importance: str = "High"
    ) -> list:
        """
        Send reminders to multiple recipients with rate limiting.

        Each recipient receives an individual email. Stops if
        session rate limit is reached.

        Args:
            recipients:     List of dicts with 'email' and 'name'.
            subject:        Email subject line.
            body_template:  Body text with {name} placeholder.
            importance:     Priority for all emails.

        Returns:
            list: List of result dicts, one per recipient.
        """
        results = []

        for recipient in recipients:
            email = recipient.get("email", "")
            name = recipient.get("name", "Risk Owner")

            personalised_body = body_template.replace("{name}", name)

            result = self.send_reminder(
                to=email,
                subject=subject,
                body=personalised_body,
                importance=importance
            )
            results.append(result)

            # Stop if rate limit hit
            if not self._provider.check_rate_limit():
                break

        return results

    # ----------------------------------------------------------
    # STATS & AUDIT
    # ----------------------------------------------------------

    def get_session_stats(self) -> dict:
        """Return current session statistics."""
        stats = self._provider.get_session_stats()
        # Add backwards-compatible key
        stats["outlook_available"] = self._provider.is_available
        return stats

    def get_audit_log(self) -> Optional[list]:
        """Read the current email audit log entries."""
        try:
            if not self.audit_path.exists():
                return []

            entries = []
            with open(self.audit_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append(row)
            return entries

        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            return None

    def get_remaining_quota(self) -> int:
        """Return emails remaining in this session."""
        return self._provider.get_remaining_quota()
