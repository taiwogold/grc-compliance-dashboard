"""
Configuration Module - Centralised Environment-Based Config
Version: 1.0.0
Author: Taiwo Durodola-Tunde

Replaces all hardcoded paths and settings with environment
variables and a single source of truth. Supports .env files
for local development and environment variables for production.

Usage:
    from utils.config import config

    db_path    = config.DB_PATH
    data_dir   = config.DATA_DIR
    log_dir    = config.LOG_DIR

Environment Variables (all optional — defaults shown):
    GRC_DATA_DIR       Path to data directory         ./data
    GRC_DB_NAME        SQLite database filename        grc_history.db
    GRC_LOG_DIR        Path to log directory           ./logs
    GRC_AUDIT_LOG      Audit log filename              email_audit.csv
    GRC_MAX_EMAILS     Max emails per session          20
    GRC_APP_ENV        Environment name                development
    GRC_SECRET_KEY     Secret key for auth tokens      (auto-generated)
    GRC_AUTH_ENABLED   Enable login screen (1/0)       0
"""

import os
import secrets
from pathlib import Path

# ==========================================================
# LOAD .env FILE IF PRESENT (local development)
# ==========================================================

def _load_dotenv():
    """
    Load .env file into os.environ if it exists.
    Pure Python implementation — no dotenv dependency required.
    """
    env_file = Path(".env")
    if not env_file.exists():
        return

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Only set if not already in environment
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv()


# ==========================================================
# CONFIGURATION CLASS
# ==========================================================

class AppConfig:
    """
    Centralised application configuration.

    All settings are read from environment variables with
    sensible defaults. Use this class instead of hardcoding
    paths or values anywhere in the codebase.

    Attributes:
        BASE_DIR:        Project root directory.
        DATA_DIR:        Directory for data files (CSV, SQLite).
        LOG_DIR:         Directory for log files.
        DB_PATH:         Full path to the SQLite database.
        AUDIT_LOG_PATH:  Full path to the email audit CSV.
        MAX_EMAILS:      Maximum emails per session.
        APP_ENV:         Environment name (development/production).
        AUTH_ENABLED:    Whether login screen is enabled.
        SECRET_KEY:      Secret key for session tokens.
    """

    def __init__(self):
        # --- Base directories ---
        self.BASE_DIR = Path(__file__).parent.parent

        self.DATA_DIR = Path(
            os.getenv("GRC_DATA_DIR", self.BASE_DIR / "data")
        )

        self.LOG_DIR = Path(
            os.getenv("GRC_LOG_DIR", self.BASE_DIR / "logs")
        )

        # --- Database ---
        self.DB_NAME = os.getenv("GRC_DB_NAME", "grc_history.db")
        self.DB_PATH = self.DATA_DIR / self.DB_NAME

        # --- CSV Data Files ---
        self.RISK_REGISTER_PATH = self.DATA_DIR / os.getenv(
            "GRC_RISK_REGISTER", "risk_register.csv"
        )
        self.CONTROLS_PATH = self.DATA_DIR / os.getenv(
            "GRC_CONTROLS", "controls.csv"
        )
        self.COMPLIANCE_HISTORY_PATH = self.DATA_DIR / os.getenv(
            "GRC_COMPLIANCE_HISTORY", "compliance_history.csv"
        )

        # --- Audit log ---
        self.AUDIT_LOG_NAME = os.getenv(
            "GRC_AUDIT_LOG", "email_audit.csv"
        )
        self.AUDIT_LOG_PATH = self.LOG_DIR / self.AUDIT_LOG_NAME

        # --- Email settings ---
        self.MAX_EMAILS = int(os.getenv("GRC_MAX_EMAILS", "20"))

        # --- Email provider ---
        # Options: "outlook", "smtp", "sendgrid", "mock"
        self.EMAIL_PROVIDER = os.getenv(
            "GRC_EMAIL_PROVIDER", "outlook"
        ).lower()

        # --- SMTP settings (used when EMAIL_PROVIDER=smtp) ---
        self.SMTP_HOST = os.getenv("GRC_SMTP_HOST", "")
        self.SMTP_PORT = int(os.getenv("GRC_SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("GRC_SMTP_USER", "")
        self.SMTP_PASSWORD = os.getenv("GRC_SMTP_PASSWORD", "")
        self.SMTP_FROM = os.getenv("GRC_SMTP_FROM", "")
        self.SMTP_USE_TLS = os.getenv(
            "GRC_SMTP_TLS", "true"
        ).lower() == "true"

        # --- SendGrid settings (used when EMAIL_PROVIDER=sendgrid) ---
        self.SENDGRID_API_KEY = os.getenv("GRC_SENDGRID_API_KEY", "")
        self.SENDGRID_FROM = os.getenv("GRC_SENDGRID_FROM", "")

        # --- Authentication ---
        self.AUTH_ENABLED = os.getenv(
            "GRC_AUTH_ENABLED", "0"
        ) == "1"

        # Secret key — use env var in production, auto-generate in dev
        self.SECRET_KEY = os.getenv(
            "GRC_SECRET_KEY", secrets.token_hex(32)
        )

        # --- Application environment ---
        self.APP_ENV = os.getenv("GRC_APP_ENV", "development")

        # --- Ensure required directories exist ---
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Return True if running in production environment."""
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Return True if running in development environment."""
        return self.APP_ENV.lower() == "development"

    def summary(self) -> dict:
        """
        Return a safe summary of current config (no secrets).

        Returns:
            dict: Configuration values safe for logging/display.
        """
        return {
            "app_env": self.APP_ENV,
            "data_dir": str(self.DATA_DIR),
            "db_path": str(self.DB_PATH),
            "log_dir": str(self.LOG_DIR),
            "email_provider": self.EMAIL_PROVIDER,
            "max_emails": self.MAX_EMAILS,
            "auth_enabled": self.AUTH_ENABLED,
        }


# ==========================================================
# SINGLETON INSTANCE
# ==========================================================

# Import this everywhere instead of hardcoding paths:
#   from utils.config import config
#   db_path = config.DB_PATH
config = AppConfig()
