"""
SendGrid Email Provider - HTTP API Integration
Version: 1.0.0

Sends emails via the SendGrid HTTP API. Works on any platform
with no desktop client required. Ideal for cloud deployments.

Configuration (via environment variables or .env file):
    GRC_SENDGRID_API_KEY   Your SendGrid API key
    GRC_SENDGRID_FROM      Verified sender email address

Example .env:
    GRC_EMAIL_PROVIDER=sendgrid
    GRC_SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
    GRC_SENDGRID_FROM=grc-alerts@company.com
"""

import logging
from typing import Optional

import requests

from .base_provider import BaseEmailProvider, EmailResult

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


class SendGridProvider(BaseEmailProvider):
    """
    Email provider using the SendGrid REST API.

    No SMTP or desktop client needed. Works on any OS.
    API key is read from environment — never hardcoded.
    """

    def __init__(self, config):
        super().__init__(config)
        self._available = self._check_config()

    def _check_config(self) -> bool:
        """Verify required SendGrid config is present."""
        if not self.config.SENDGRID_API_KEY:
            logger.warning(
                "SendGrid provider: GRC_SENDGRID_API_KEY not set."
            )
            return False
        if not self.config.SENDGRID_FROM:
            logger.warning(
                "SendGrid provider: GRC_SENDGRID_FROM not set."
            )
            return False
        return True

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def provider_name(self) -> str:
        return "SendGrid"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None,
    ) -> EmailResult:
        """Send email via SendGrid API."""

        subject = self.sanitise_content(subject)
        body = self.sanitise_content(body)

        failure = self._pre_send_checks(to, subject, cc)
        if failure:
            return failure

        payload = {
            "personalizations": [
                {
                    "to": [{"email": to}],
                    **({"cc": [{"email": cc}]} if cc else {}),
                }
            ],
            "from": {"email": self.config.SENDGRID_FROM},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }

        headers = {
            "Authorization": f"Bearer {self.config.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                SENDGRID_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            if resp.status_code in (200, 202):
                self.session_count += 1
                logger.info(f"SendGrid: email sent to {to}")
                return EmailResult(
                    success=True,
                    message=(
                        f"Email sent via SendGrid to {to}. "
                        f"({self.get_remaining_quota()} remaining)"
                    ),
                    recipient=to,
                    provider=self.provider_name
                )
            else:
                error = resp.text[:200]
                logger.error(f"SendGrid API error {resp.status_code}: {error}")
                return EmailResult(
                    success=False,
                    message=f"SendGrid error {resp.status_code}: {error}",
                    recipient=to,
                    provider=self.provider_name
                )

        except requests.exceptions.Timeout:
            return EmailResult(
                success=False,
                message="SendGrid request timed out.",
                recipient=to,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return EmailResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                recipient=to,
                provider=self.provider_name
            )
