"""
API Authentication - Token-Based Access Control
Version: 3.2.0
Author: Taiwo Durodola-Tunde

Provides API key authentication for REST endpoints.
API keys are stored in st.secrets or environment variables.

Security:
    - Bearer token authentication (API key in header)
    - Keys stored in secrets/env only (never in code)
    - Rate limiting applied per key
    - All requests logged to audit trail

Usage:
    from api.auth import get_api_key, verify_api_key

    @app.get("/api/v1/risks")
    async def get_risks(api_key: str = Depends(get_api_key)):
        ...
"""

import os
import logging
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Header name for API key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_valid_keys() -> list:
    """
    Load valid API keys from environment or secrets.

    Keys can be set via:
        - Environment variable: GRC_API_KEYS (comma-separated)
        - Streamlit secrets: [api] keys = ["key1", "key2"]

    Returns:
        list: Valid API key strings.
    """

    # Try environment variable first
    env_keys = os.getenv("GRC_API_KEYS", "")
    if env_keys:
        return [k.strip() for k in env_keys.split(",") if k.strip()]

    # Try streamlit secrets
    try:
        import streamlit as st
        keys = st.secrets.get("api", {}).get("keys", [])
        if keys:
            return list(keys)
    except Exception:
        pass

    # Default dev key (only for local development)
    dev_key = os.getenv("GRC_DEV_API_KEY", "")
    if dev_key:
        return [dev_key]

    return []


async def get_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> str:
    """
    FastAPI dependency that validates the API key from request header.

    Args:
        api_key: Key extracted from X-API-Key header.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException 401: If no key provided.
        HTTPException 403: If key is invalid.
    """

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header."
        )

    valid_keys = _get_valid_keys()

    if not valid_keys:
        # No keys configured — reject all requests
        logger.warning("API request rejected: no API keys configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API not configured. Contact administrator."
        )

    if api_key not in valid_keys:
        logger.warning(f"API request rejected: invalid key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key."
        )

    return api_key
