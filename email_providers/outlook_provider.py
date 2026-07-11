"""
Outlook Email Provider - Windows COM Automation
Version: 1.0.0

Preserves the existing Outlook behaviour exactly as before,
now wrapped in the BaseEmailProvider interface.

Requirements:
    - Windows OS
    - pywin32 installed
    - Outlook desktop client installed and authenticated
"""

import logging
from typing import Optional

from .base_provider import BaseEmailProvider, EmailResult

logger = logging.getLogger(__name__)

IMPORTANCE_MAP = {"Low": 0, "Normal": 1, "High": 2}


class OutlookProvider(BaseEmailProvider):
    """
    Email provider using Outlook COM automation (Windows only).

    Uses the existing authenticated Outlook desktop session.
    No credentials stored or transmitted — inherits Windows
    security context.
    """

    def __init__(self, config):
        super().__init__(config)
        self._outlook = None
        self._available = False
        self._connect()

    def _connect(self):
        """Attempt to connect to Outlook via COM."""
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            self._available = True
            logger.info("Outlook COM connection established.")

        except ImportError:
            logger.warning(
                "pywin32 not installed — Outlook provider unavailable. "
                "Install with: pip install pywin32"
            )
            self._available = False

        except Exception as e:
            logger.warning(
                f"Outlook COM connection failed: {e}. "
                f"Ensure Outlook desktop is running."
            )
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def provider_name(self) -> str:
        return "Outlook"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None,
    ) -> EmailResult:
        """Send email via Outlook COM automation."""

        # Sanitise inputs
        subject = self.sanitise_content(subject)
        body = self.sanitise_content(body)

        # Run pre-send checks
        failure = self._pre_send_checks(to, subject, cc)
        if failure:
            return failure

        if importance not in IMPORTANCE_MAP:
            importance = "Normal"

        try:
            mail = self._outlook.CreateItem(0)
            mail.To = to
            mail.Subject = subject
            mail.Body = body
            mail.Importance = IMPORTANCE_MAP[importance]

            if cc:
                mail.CC = cc

            mail.Send()
            self.session_count += 1

            logger.info(f"Outlook: email sent to {to}")

            return EmailResult(
                success=True,
                message=(
                    f"Email sent via Outlook to {to}. "
                    f"({self.get_remaining_quota()} remaining)"
                ),
                recipient=to,
                provider=self.provider_name
            )

        except Exception as e:
            logger.error(f"Outlook send failed: {e}")
            return EmailResult(
                success=False,
                message=f"Outlook send failed: {str(e)}",
                recipient=to,
                provider=self.provider_name
            )
