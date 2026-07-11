"""
Email Providers Package
Version: 1.0.0

Provides a pluggable email provider abstraction so the GRC
dashboard is not tied to Outlook/Windows. Any provider that
implements BaseEmailProvider can be used interchangeably.

Available Providers:
    OutlookProvider   - Windows Outlook COM (existing behaviour)
    SMTPProvider      - Any SMTP server (Office 365, Gmail, etc.)
    SendGridProvider  - SendGrid HTTP API
    MockProvider      - In-memory mock for testing

Usage:
    from email_providers import get_provider
    from utils.config import config

    provider = get_provider(config)
    result = provider.send(to="...", subject="...", body="...")
"""

from .base_provider import BaseEmailProvider, EmailResult
from .outlook_provider import OutlookProvider
from .smtp_provider import SMTPProvider
from .sendgrid_provider import SendGridProvider
from .mock_provider import MockProvider


def get_provider(config) -> BaseEmailProvider:
    """
    Factory function — returns the correct provider based on config.

    Args:
        config: AppConfig instance from utils.config.

    Returns:
        BaseEmailProvider: The configured provider instance.
    """
    provider_name = getattr(config, "EMAIL_PROVIDER", "outlook")

    if provider_name == "smtp":
        return SMTPProvider(config)
    elif provider_name == "sendgrid":
        return SendGridProvider(config)
    elif provider_name == "mock":
        return MockProvider(config)
    else:
        # Default: Outlook (existing behaviour preserved)
        return OutlookProvider(config)


__all__ = [
    "BaseEmailProvider",
    "EmailResult",
    "OutlookProvider",
    "SMTPProvider",
    "SendGridProvider",
    "MockProvider",
    "get_provider",
]
