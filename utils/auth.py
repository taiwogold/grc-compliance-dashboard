"""
Authentication Module - Login Screen & Session Management
Version: 1.0.0
Author: Taiwo Durodola-Tunde

Provides a login screen for the GRC dashboard using
streamlit-authenticator. Authentication is controlled by
GRC_AUTH_ENABLED in the environment/.env file.

When GRC_AUTH_ENABLED=0 (default), the login screen is
bypassed entirely — existing behaviour is preserved.

When GRC_AUTH_ENABLED=1, users must log in before accessing
the dashboard. Credentials are stored as bcrypt hashes in
.streamlit/credentials.yaml — never plain text.

Usage:
    from utils.auth import require_auth, get_current_user

    # Call at the top of dashboard.py before any content
    require_auth()

    # Anywhere in the app
    user = get_current_user()  # Returns username or None

Credential Setup:
    Run this once to generate a hashed credentials file:

        python -c "
        from utils.auth import create_credentials_file
        create_credentials_file(
            users={
                'admin': {
                    'name': 'Admin User',
                    'password': 'your_password_here',
                    'email': 'admin@company.com',
                    'role': 'admin',
                },
                'viewer': {
                    'name': 'Read Only User',
                    'password': 'viewer_password',
                    'email': 'viewer@company.com',
                    'role': 'viewer',
                }
            }
        )
        "

    This creates .streamlit/credentials.yaml with hashed passwords.
"""

import logging
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

from .config import config as app_config

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path(".streamlit") / "credentials.yaml"


# ==========================================================
# CREDENTIAL FILE MANAGEMENT
# ==========================================================

def create_credentials_file(users: dict):
    """
    Generate a credentials.yaml file with bcrypt-hashed passwords.

    Run this once from the command line to set up user accounts.
    Passwords are never stored in plain text.

    Args:
        users: Dict of username -> {name, password, email, role}

    Example:
        create_credentials_file({
            "admin": {
                "name": "Admin User",
                "password": "secure_password_123",
                "email": "admin@company.com",
                "role": "admin"
            }
        })
    """
    try:
        import bcrypt
    except ImportError:
        print(
            "bcrypt not installed. Run: pip install bcrypt"
        )
        return

    credentials = {"usernames": {}}

    for username, details in users.items():
        hashed = bcrypt.hashpw(
            details["password"].encode(),
            bcrypt.gensalt()
        ).decode()

        credentials["usernames"][username] = {
            "name":     details.get("name", username),
            "password": hashed,
            "email":    details.get("email", ""),
            "role":     details.get("role", "viewer"),
        }

    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CREDENTIALS_PATH, "w") as f:
        yaml.dump({"credentials": credentials}, f, default_flow_style=False)

    print(f"Credentials saved to {CREDENTIALS_PATH}")
    print("Passwords have been hashed — never stored in plain text.")


def _load_credentials() -> Optional[dict]:
    """
    Load credentials from .streamlit/credentials.yaml.

    Returns:
        dict: Credentials config, or None if file not found.
    """
    if not CREDENTIALS_PATH.exists():
        return None

    try:
        with open(CREDENTIALS_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return None


# ==========================================================
# AUTHENTICATION
# ==========================================================

def require_auth():
    """
    Enforce authentication before the dashboard loads.

    If GRC_AUTH_ENABLED=0 (default), does nothing.
    If GRC_AUTH_ENABLED=1, shows the login screen and calls
    st.stop() until the user successfully authenticates.

    Call this at the very top of dashboard.py, before any
    content is rendered.
    """
    if not app_config.AUTH_ENABLED:
        # Auth disabled — set a default anonymous user and return
        if "auth_user" not in st.session_state:
            st.session_state.auth_user = "anonymous"
            st.session_state.auth_name = "Guest"
            st.session_state.auth_role = "admin"
        return

    # --- Auth is enabled ---
    try:
        import streamlit_authenticator as stauth
    except ImportError:
        st.error(
            "streamlit-authenticator is not installed. "
            "Run: pip install streamlit-authenticator"
        )
        st.stop()

    credentials = _load_credentials()

    if not credentials:
        _show_first_run_message()
        st.stop()

    # Build authenticator
    authenticator = stauth.Authenticate(
        credentials=credentials["credentials"],
        cookie_name="grc_dashboard",
        cookie_key=app_config.SECRET_KEY,
        cookie_expiry_days=1,
    )

    # Store in session so other parts of the app can access it
    if "authenticator" not in st.session_state:
        st.session_state.authenticator = authenticator

    # Show login widget
    name, auth_status, username = authenticator.login(
        location="main",
        fields={
            "Form name": "🛡️ GRC Dashboard — Sign In",
            "Username":  "Username",
            "Password":  "Password",
            "Login":     "Sign In",
        }
    )

    if auth_status is False:
        st.error("Incorrect username or password.")
        st.stop()

    if auth_status is None:
        st.info("Please enter your credentials to continue.")
        st.stop()

    # Authenticated — store user context
    st.session_state.auth_user = username
    st.session_state.auth_name = name
    st.session_state.auth_role = (
        credentials["credentials"]
        .get("usernames", {})
        .get(username, {})
        .get("role", "viewer")
    )


def _show_first_run_message():
    """Show setup instructions when no credentials file exists."""
    st.warning("⚙️ Authentication is enabled but no credentials file found.")
    st.markdown("""
    ### First-Time Setup

    Run the following command once to create your credentials file:

    ```bash
    python -c "
    from utils.auth import create_credentials_file
    create_credentials_file({
        'admin': {
            'name': 'Admin User',
            'password': 'change_me_now',
            'email': 'admin@company.com',
            'role': 'admin'
        }
    })
    "
    ```

    Then restart the dashboard.

    Alternatively, set `GRC_AUTH_ENABLED=0` in your `.env` file
    to disable authentication during development.
    """)


def get_current_user() -> dict:
    """
    Get the currently authenticated user's details.

    Returns:
        dict: User info with keys: username, name, role.
            Returns anonymous user if auth is disabled.
    """
    return {
        "username": st.session_state.get("auth_user", "anonymous"),
        "name":     st.session_state.get("auth_name", "Guest"),
        "role":     st.session_state.get("auth_role", "viewer"),
    }


def show_logout_button():
    """
    Render a logout button in the sidebar.

    Only shown when auth is enabled and user is logged in.
    """
    if not app_config.AUTH_ENABLED:
        return

    authenticator = st.session_state.get("authenticator")
    if authenticator:
        authenticator.logout(button_name="Sign Out", location="sidebar")


def is_admin() -> bool:
    """Return True if the current user has admin role."""
    return get_current_user().get("role") == "admin"
