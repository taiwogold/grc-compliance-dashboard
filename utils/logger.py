"""
Unified Logging Framework
Version: 3.0.3
Author: Taiwo Durodola-Tunde

Provides consistent, structured logging across all modules.
Replaces ad-hoc logging.getLogger() calls with a centralised
factory that ensures:

    - Consistent format across all modules
    - File + console output
    - Configurable log levels
    - Automatic log directory creation
    - Log rotation (max 5MB per file, 3 backups)

Usage:
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Dashboard loaded")
    logger.warning("Threshold breached")
    logger.error("Connection failed", exc_info=True)

Log Format:
    2026-07-11 19:30:45 | INFO | utils.metrics | Compliance score: 80.0%
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import config as app_config


# ==========================================================
# CONFIGURATION
# ==========================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File rotation settings
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3

# Log file path
LOG_FILE = app_config.LOG_DIR / "grc_dashboard.log"

# Track if root logger already configured (prevent duplicates)
_configured = False


# ==========================================================
# LOGGER FACTORY
# ==========================================================

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance for a module.

    Creates a logger with both file and console handlers.
    File handler uses rotation to prevent unbounded growth.

    Args:
        name: Logger name (typically __name__ of the module).
        level: Logging level. Defaults to INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """

    global _configured

    logger = logging.getLogger(name)

    # Only configure the root handlers once
    if not _configured:
        _setup_root_logger(level)
        _configured = True

    return logger


def _setup_root_logger(level: int = logging.INFO):
    """
    Configure the root logger with file and console handlers.

    Only called once — subsequent get_logger() calls inherit
    this configuration automatically.

    Args:
        level: Base logging level.
    """

    # Ensure log directory exists
    app_config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Prevent duplicate handlers on rerun
    if root_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- File Handler (rotating) ---
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_FILE_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception:
        # If file logging fails (permissions), continue with console only
        pass

    # --- Console Handler (stderr) ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)  # Only warnings+ to console
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def set_log_level(level: int):
    """
    Change the logging level for all handlers.

    Args:
        level: New logging level (e.g. logging.DEBUG).
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(level)
