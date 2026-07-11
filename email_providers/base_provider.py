"""
Base Email Provider - Abstract Interface
Version: 1.0.0

All email providers must implement this interface. This ensures
that swapping providers (Outlook → SMTP → SendGrid) requires
zero changes in the rest of the codebase.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """
    Standardised result returned by every provider's send method.

    Attributes:
        success:    Whether the email was sent successfully.
        message:    Human-readable status or error description.
        recipient:  The target email address.
        timestamp:  When the attempt was made (ISO format).
        provider:   Name of the provider that handled the send.
    """
    success: bool
    message: str
    recipient: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    provider: str = "unknown"


class BaseEmailProvider(ABC):
    """
    Abstract base class for all email providers.

    Any new provider must subclass this and implement:
        - send()
        - is_available (property)

    Shared behaviour provided here:
        - validate_email()
        - sanitise_content()
        - session rate limiting
    """

    def __init__(self, config):
        """
        Initialise base provider with application config.

        Args:
            config: AppConfig instance from utils.config.
        """
        self.config = config
        self.session_count = 0
        self.max_per_session = getattr(config, "MAX_EMAILS", 20)

    # ----------------------------------------------------------
    # ABSTRACT METHODS — must be implemented by each provider
    # ----------------------------------------------------------

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is ready to send emails."""
        pass

    @abstractmethod
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        importance: str = "High",
        cc: Optional[str] = None,
    ) -> EmailResult:
        """
        Send a single email.

        Args:
            to:         Recipient email address.
            subject:    Email subject line.
            body:       Plain text body.
            importance: Priority ('Low', 'Normal', 'High').
            cc:         Optional CC address.

        Returns:
            EmailResult: Standardised result object.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of this provider."""
        pass

    # ----------------------------------------------------------
    # SHARED METHODS — available to all providers
    # ----------------------------------------------------------

    def validate_email(self, email: str) -> bool:
        """
        Basic email address format validation.

        Args:
            email: Email address to validate.

        Returns:
            bool: True if format is valid.
        """
        if not email or not isinstance(email, str):
            return False

        email = email.strip()

        if " " in email or "@" not in email:
            return False

        parts = email.split("@")
        if len(parts) != 2:
            return False

        local, domain = parts
        if not local or not domain or "." not in domain:
            return False

        # Block injection characters
        for char in [";", "|", "&", "`", "$", "\\"]:
            if char in email:
                return False

        return True

    def sanitise_content(self, text: str) -> str:
        """
        Remove dangerous characters from email content.

        Args:
            text: Raw content string.

        Returns:
            str: Sanitised content.
        """
        if not text:
            return ""
        return text.replace("\x00", "").strip()

    def check_rate_limit(self) -> bool:
        """Return True if more emails can be sent this session."""
        return self.session_count < self.max_per_session

    def get_remaining_quota(self) -> int:
        """Return number of emails remaining in session quota."""
        return max(0, self.max_per_session - self.session_count)

    def get_session_stats(self) -> dict:
        """Return session statistics dictionary."""
        return {
            "emails_sent": self.session_count,
            "remaining_quota": self.get_remaining_quota(),
            "max_per_session": self.max_per_session,
            "provider": self.provider_name,
            "available": self.is_available,
        }

    def _pre_send_checks(
        self, to: str, subject: str, cc: Optional[str] = None
    ) -> Optional[EmailResult]:
        """
        Run all pre-send validation checks.

        Returns an EmailResult with failure details if any check
        fails, or None if all checks pass (proceed with send).

        Args:
            to:      Recipient email address.
            subject: Email subject line.
            cc:      Optional CC address.

        Returns:
            EmailResult on failure, None on success.
        """
        if not self.is_available:
            return EmailResult(
                success=False,
                message=f"{self.provider_name} is not available.",
                recipient=to,
                provider=self.provider_name
            )

        if not self.check_rate_limit():
            return EmailResult(
                success=False,
                message=(
                    f"Session rate limit reached "
                    f"({self.max_per_session} emails). "
                    f"Restart the dashboard to reset."
                ),
                recipient=to,
                provider=self.provider_name
            )

        if not self.validate_email(to):
            return EmailResult(
                success=False,
                message=f"Invalid recipient email address: {to}",
                recipient=to,
                provider=self.provider_name
            )

        if cc and not self.validate_email(cc):
            return EmailResult(
                success=False,
                message=f"Invalid CC email address: {cc}",
                recipient=to,
                provider=self.provider_name
            )

        if not subject:
            return EmailResult(
                success=False,
                message="Subject line cannot be empty.",
                recipient=to,
                provider=self.provider_name
            )

        return None  # All checks passed
