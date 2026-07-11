"""
SMTP Email Provider - Cross-Platform SMTP Support
Version: 1.0.0

Sends emails via any SMTP server — works on Windows, Mac, Linux.
Supports Office 365, Gmail, AWS SES SMTP, or any corporate relay.

Configuration (via environment variables or .env file):
    GRC_SMTP_HOST      SMTP server hostname
    GRC_SMTP_PORT      SMTP port (default: 587)
    GRC_SMTP_USER      SMTP username / email address
    GRC_SMTP_PASSWORD  SMTP password or app password
    GRC_SMTP_FROM      From address (defaults to SMTP_USER)
    GRC_SMTP_TLS       Use TLS (default: true)

Example .env:
    GRC_EMAIL_PROVIDER=smtp
    GRC_SMTP_HOST=smtp.office365.com
    GRC_SMTP_PORT=587
    GRC_SMTP_USER=grc-alerts@company.com
    GRC_SMTP_PASSWORD=your_app_password
    GRC_SMTP_FROM=GRC Dashboard <grc-alerts@company.com>
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .base_provider import BaseEmailProvider, EmailResult

logger = logging.getLogger(__name__)


class SMTPProvider(BaseEmailProvider):
    """
    Cross-platform email provider using Python's built-in smtplib.

    Works with any SMTP server. Credentials are read from
    environment variables — never hardcoded.
    """

    def __init__(self, config):
        super().__init__(config)
        self._available = self._check_config()

    def _check_config(self) -> bool:
        """Verify required SMTP config is present."""
        required = [
            self.config.SMTP_HOST,
            self.config.SMTP_USER,
            self.config.SMTP_PASSWORD,
        ]
        if not all(required):
            logger.warning(
                "SMTP provider: missing required config. "
                "Set GRC_SMTP_HOST, GRC_SMTP_USER, GRC_SMTP_PASSWORD."
            )
            return False
        return True

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def provider_name(self) -> str:
        return "SMTP"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None,
    ) -> EmailResult:
        """Send email via SMTP."""

        subject = self.sanitise_content(subject)
        body = self.sanitise_content(body)

        failure = self._pre_send_checks(to, subject, cc)
        if failure:
            return failure

        from_addr = self.config.SMTP_FROM or self.config.SMTP_USER

        try:
            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to
            msg["Subject"] = subject

            # Map importance to X-Priority header
            priority_map = {"High": "1", "Normal": "3", "Low": "5"}
            msg["X-Priority"] = priority_map.get(importance, "3")

            if cc:
                msg["Cc"] = cc

            msg.attach(MIMEText(body, "plain"))

            # Connect and send
            if self.config.SMTP_USE_TLS:
                server = smtplib.SMTP(
                    self.config.SMTP_HOST,
                    self.config.SMTP_PORT,
                    timeout=10
                )
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(
                    self.config.SMTP_HOST,
                    self.config.SMTP_PORT,
                    timeout=10
                )

            server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)

            recipients = [to] + ([cc] if cc else [])
            server.sendmail(from_addr, recipients, msg.as_string())
            server.quit()

            self.session_count += 1
            logger.info(f"SMTP: email sent to {to}")

            return EmailResult(
                success=True,
                message=(
                    f"Email sent via SMTP to {to}. "
                    f"({self.get_remaining_quota()} remaining)"
                ),
                recipient=to,
                provider=self.provider_name
            )

        except smtplib.SMTPAuthenticationError:
            return EmailResult(
                success=False,
                message=(
                    "SMTP authentication failed. "
                    "Check GRC_SMTP_USER and GRC_SMTP_PASSWORD."
                ),
                recipient=to,
                provider=self.provider_name
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return EmailResult(
                success=False,
                message=f"SMTP error: {str(e)}",
                recipient=to,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return EmailResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                recipient=to,
                provider=self.provider_name
            )
