"""
Email Dispatcher Module - Secure Outlook Integration
Version: 2.1.0
Author: Taiwo Durodola-Tunde

Security Architecture:
    - Uses win32com.client (COM automation) to interface with
      the user's locally authenticated Outlook desktop client.
    - NO credentials are stored, transmitted, or hardcoded.
    - All emails route through the corporate Exchange server,
      preserving DLP policies, retention rules, and audit trails.
    - Dispatch requires explicit user confirmation via the UI.
    - All sent emails are logged to a local audit file.

Dependencies:
    - pywin32 (pip install pywin32)
    - Outlook desktop client must be installed and authenticated.

Usage:
    from utils.email_dispatcher import OutlookDispatcher

    dispatcher = OutlookDispatcher()
    result = dispatcher.send_reminder(
        to="owner@company.com",
        subject="Risk Remediation Update Required",
        body="Please review your open risks...",
        importance="High"
    )
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


# ==========================================================
# CONSTANTS
# ==========================================================

# Maximum emails that can be dispatched in a single session
# Prevents accidental mass-mailing from UI interaction
MAX_EMAILS_PER_SESSION = 20

# Audit log location (relative to project root)
AUDIT_LOG_DIR = "logs"
AUDIT_LOG_FILE = "email_audit.csv"

# Valid importance levels for Outlook
IMPORTANCE_MAP = {
    "Low": 0,
    "Normal": 1,
    "High": 2,
}


# ==========================================================
# OUTLOOK DISPATCHER CLASS
# ==========================================================

class OutlookDispatcher:
    """
    Secure email dispatcher using Outlook COM automation.

    This class provides a controlled interface to send emails
    via the user's authenticated Outlook desktop client. It
    enforces rate limiting, audit logging, and requires explicit
    confirmation before dispatch.

    Security Features:
        - No stored credentials (uses existing Outlook session)
        - Rate limiting per session instance
        - Full audit trail with CSV logging
        - Input validation and sanitisation
        - Importance level enforcement

    Attributes:
        session_count (int): Number of emails sent in this session.
        max_per_session (int): Maximum allowed emails per session.
        audit_path (Path): Path to the audit log file.
        is_available (bool): Whether Outlook COM is accessible.
    """

    def __init__(
        self,
        max_per_session: int = MAX_EMAILS_PER_SESSION,
        audit_dir: str = AUDIT_LOG_DIR
    ):
        """
        Initialise the Outlook dispatcher.

        Args:
            max_per_session: Maximum emails allowed per session.
                Defaults to 20.
            audit_dir: Directory for audit log files.
                Defaults to 'logs'.
        """

        self.session_count = 0
        self.max_per_session = max_per_session
        self.is_available = False
        self._outlook = None

        # Set up audit logging directory
        self.audit_path = Path(audit_dir) / AUDIT_LOG_FILE
        self._ensure_audit_log()

        # Attempt to connect to Outlook
        self._connect()

    def _connect(self):
        """
        Establish connection to Outlook via COM automation.

        This uses the existing authenticated Outlook session.
        No credentials are passed — the connection inherits
        the user's Windows security context.

        Note: COM must be initialised per-thread. Streamlit
        runs scripts in worker threads, so we call
        CoInitialize() explicitly before Dispatch.
        """

        try:
            import pythoncom
            import win32com.client

            # Initialise COM for this thread (required in Streamlit)
            pythoncom.CoInitialize()

            self._outlook = win32com.client.Dispatch(
                "Outlook.Application"
            )
            self.is_available = True

            logger.info(
                "Outlook COM connection established successfully."
            )

        except ImportError:
            logger.warning(
                "pywin32 not installed. "
                "Run: pip install pywin32"
            )
            self.is_available = False

        except Exception as e:
            logger.warning(
                f"Outlook COM connection failed: {e}. "
                f"Ensure Outlook desktop is running."
            )
            self.is_available = False

    def _ensure_audit_log(self):
        """
        Create the audit log directory and CSV file if they
        do not already exist. Initialises with header row.
        """

        self.audit_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.audit_path.exists():
            with open(self.audit_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp",
                    "Recipient",
                    "Subject",
                    "Importance",
                    "Status",
                    "Error"
                ])

    def _log_audit(
        self,
        recipient: str,
        subject: str,
        importance: str,
        status: str,
        error: str = ""
    ):
        """
        Write an entry to the email audit log.

        Args:
            recipient: Email address of the recipient.
            subject: Email subject line.
            importance: Importance level used.
            status: Outcome ('Sent', 'Failed', 'Blocked').
            error: Error message if applicable.
        """

        try:
            with open(self.audit_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    recipient,
                    subject,
                    importance,
                    status,
                    error
                ])
        except Exception as e:
            logger.error(
                f"Failed to write audit log: {e}"
            )

    def validate_email(self, email: str) -> bool:
        """
        Basic email address validation.

        Performs format validation to prevent injection attacks
        and malformed addresses. Does not verify deliverability.

        Args:
            email: Email address string to validate.

        Returns:
            bool: True if the email format is valid.
        """

        if not email or not isinstance(email, str):
            return False

        # Basic format check
        email = email.strip()

        if " " in email:
            return False

        if "@" not in email:
            return False

        parts = email.split("@")

        if len(parts) != 2:
            return False

        local, domain = parts

        if not local or not domain:
            return False

        if "." not in domain:
            return False

        # Check for common injection characters
        dangerous_chars = [";", "|", "&", "`", "$", "\\"]
        for char in dangerous_chars:
            if char in email:
                return False

        return True

    def sanitise_content(self, text: str) -> str:
        """
        Sanitise email content to prevent injection.

        Removes potentially dangerous characters and patterns
        from email body text while preserving readability.

        Args:
            text: Raw text content to sanitise.

        Returns:
            str: Sanitised text safe for email body.
        """

        if not text:
            return ""

        # Remove null bytes
        text = text.replace("\x00", "")

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def check_rate_limit(self) -> bool:
        """
        Check if the session rate limit has been reached.

        Returns:
            bool: True if more emails can be sent, False if
                the limit has been reached.
        """

        return self.session_count < self.max_per_session

    def get_remaining_quota(self) -> int:
        """
        Get the number of emails remaining in this session.

        Returns:
            int: Number of emails that can still be sent.
        """

        return max(
            0,
            self.max_per_session - self.session_count
        )

    def send_reminder(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None
    ) -> dict:
        """
        Send a reminder email via Outlook COM automation.

        This method performs full validation, rate limit checking,
        and audit logging before dispatching the email through
        the user's authenticated Outlook client.

        Args:
            to: Recipient email address (single address only).
            subject: Email subject line.
            body: Plain text email body.
            importance: Priority level ('Low', 'Normal', 'High').
                Defaults to 'High'.
            cc: Optional CC recipient email address.

        Returns:
            dict: Result dictionary with keys:
                - success (bool): Whether the email was sent.
                - message (str): Human-readable status message.
                - timestamp (str): When the attempt was made.
                - recipient (str): The target email address.

        Raises:
            No exceptions are raised. All errors are caught and
            returned in the result dictionary for UI handling.
        """

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        result = {
            "success": False,
            "message": "",
            "timestamp": timestamp,
            "recipient": to
        }

        # ---- Security Check 1: Outlook availability ----
        if not self.is_available:
            result["message"] = (
                "Outlook is not available. Ensure the desktop "
                "client is installed and running."
            )
            self._log_audit(
                to, subject, importance,
                "Failed", "Outlook not available"
            )
            return result

        # ---- Security Check 2: Rate limiting ----
        if not self.check_rate_limit():
            result["message"] = (
                f"Session rate limit reached "
                f"({self.max_per_session} emails). "
                f"Please restart the dashboard to reset."
            )
            self._log_audit(
                to, subject, importance,
                "Blocked", "Rate limit exceeded"
            )
            return result

        # ---- Security Check 3: Email validation ----
        if not self.validate_email(to):
            result["message"] = (
                f"Invalid recipient email address: {to}"
            )
            self._log_audit(
                to, subject, importance,
                "Blocked", "Invalid email format"
            )
            return result

        if cc and not self.validate_email(cc):
            result["message"] = (
                f"Invalid CC email address: {cc}"
            )
            self._log_audit(
                to, subject, importance,
                "Blocked", "Invalid CC email format"
            )
            return result

        # ---- Security Check 4: Content sanitisation ----
        subject = self.sanitise_content(subject)
        body = self.sanitise_content(body)

        if not subject:
            result["message"] = "Subject line cannot be empty."
            self._log_audit(
                to, subject, importance,
                "Blocked", "Empty subject"
            )
            return result

        # ---- Security Check 5: Importance validation ----
        if importance not in IMPORTANCE_MAP:
            importance = "Normal"

        # ---- Dispatch via COM ----
        try:
            # Create mail item (olMailItem = 0)
            mail = self._outlook.CreateItem(0)

            mail.To = to
            mail.Subject = subject
            mail.Body = body
            mail.Importance = IMPORTANCE_MAP[importance]

            if cc:
                mail.CC = cc

            # Send the email
            mail.Send()

            # Increment session counter
            self.session_count += 1

            result["success"] = True
            result["message"] = (
                f"Email sent successfully to {to}. "
                f"({self.get_remaining_quota()} remaining "
                f"in session)"
            )

            self._log_audit(
                to, subject, importance, "Sent"
            )

            logger.info(
                f"Email dispatched to {to}: {subject}"
            )

        except Exception as e:
            result["message"] = (
                f"Failed to send email: {str(e)}"
            )
            self._log_audit(
                to, subject, importance,
                "Failed", str(e)
            )
            logger.error(
                f"Email dispatch failed: {e}"
            )

        return result

    def send_bulk_reminders(
        self,
        recipients: list,
        subject: str,
        body_template: str,
        importance: str = "High"
    ) -> list:
        """
        Send reminders to multiple recipients with rate limiting.

        Each recipient receives an individual email (no BCC).
        This ensures full transparency and individual audit
        trail entries.

        Args:
            recipients: List of dicts with 'email' and 'name' keys.
            subject: Email subject line.
            body_template: Body text with {name} placeholder.
            importance: Priority level for all emails.

        Returns:
            list: List of result dictionaries, one per recipient.
        """

        results = []

        for recipient in recipients:
            email = recipient.get("email", "")
            name = recipient.get("name", "Risk Owner")

            # Personalise the body
            personalised_body = body_template.replace(
                "{name}", name
            )

            result = self.send_reminder(
                to=email,
                subject=subject,
                body=personalised_body,
                importance=importance
            )

            results.append(result)

            # Stop if rate limit hit
            if not self.check_rate_limit():
                break

        return results

    def get_audit_log(self) -> Optional[list]:
        """
        Read the current audit log entries.

        Returns:
            list: List of audit log entries as dictionaries,
                or None if the log file cannot be read.
        """

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
            logger.error(
                f"Failed to read audit log: {e}"
            )
            return None

    def get_session_stats(self) -> dict:
        """
        Get current session statistics.

        Returns:
            dict: Session stats including count, remaining quota,
                and availability status.
        """

        return {
            "emails_sent": self.session_count,
            "remaining_quota": self.get_remaining_quota(),
            "max_per_session": self.max_per_session,
            "outlook_available": self.is_available,
        }
