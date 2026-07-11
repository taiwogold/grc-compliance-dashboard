"""
Mock Email Provider - In-Memory Testing Provider
Version: 1.0.0

Does not send real emails. Stores all sent messages in memory
for inspection. Use during development and testing.

Configuration:
    GRC_EMAIL_PROVIDER=mock
"""

import logging
from typing import Optional

from .base_provider import BaseEmailProvider, EmailResult

logger = logging.getLogger(__name__)


class MockProvider(BaseEmailProvider):
    """
    Mock email provider for development and testing.

    All emails are captured in self.sent_emails list.
    No real emails are dispatched.
    """

    def __init__(self, config):
        super().__init__(config)
        self.sent_emails = []

    @property
    def is_available(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "Mock"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None,
    ) -> EmailResult:
        """Capture email in memory without sending."""

        subject = self.sanitise_content(subject)
        body = self.sanitise_content(body)

        failure = self._pre_send_checks(to, subject, cc)
        if failure:
            return failure

        self.sent_emails.append({
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "importance": importance,
        })

        self.session_count += 1
        logger.info(f"Mock: captured email to {to} (not sent)")

        return EmailResult(
            success=True,
            message=f"[MOCK] Email captured (not sent) to {to}.",
            recipient=to,
            provider=self.provider_name
        )
