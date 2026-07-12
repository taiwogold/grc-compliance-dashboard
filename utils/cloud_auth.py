"""
Cloud Authentication Module - Simple Password Gate
Version: 2.5.0
Author: Taiwo Durodola-Tunde

Provides a lightweight password gate for Streamlit Cloud
deployment. Uses st.secrets for credential storage — no
passwords in code.

How it works:
    - On Streamlit Cloud: password is stored in the app's
      Secrets panel (Settings → Secrets → [passwords])
    - Locally: password is in .streamlit/secrets.toml
      (which is .gitignored and never committed)
    - User enters password once, stored in session state
    - No usernames required — single shared password

This is a "visitor gate" — not enterprise auth. It prevents
casual access without requiring user accounts. For full RBAC
authentication, use utils/auth.py with GRC_AUTH_ENABLED=1.

Usage:
    from utils.cloud_auth import check_password

    if not check_password():
        st.stop()

    # ... rest of the dashboard
"""

import streamlit as st


def check_password() -> bool:
    """
    Show a password input and validate against st.secrets.

    Returns True if the user has entered the correct password.
    Returns False if still waiting for input or wrong password.

    The password is read from:
        st.secrets["passwords"]["dashboard_password"]

    Set this in:
        - Local: .streamlit/secrets.toml
        - Cloud: Streamlit Cloud → Settings → Secrets
    """

    # If already authenticated this session, skip
    if st.session_state.get("password_correct", False):
        return True

    # Check if secrets are configured
    try:
        correct_password = st.secrets["passwords"]["dashboard_password"]
    except (KeyError, FileNotFoundError):
        # No password configured — allow access (dev mode)
        st.session_state.password_correct = True
        return True

    # Show the login form
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px;">
            <h1 style="font-size: 2.8rem; font-weight: 800; margin-bottom: 4px;">
                <span style="color: #F59E0B;">Govern</span>IQ
            </h1>
            <p style="color: #78716C; font-size: 1.05em; margin-top: 0;">
                Intelligent Governance. Clear Risk.
            </p>
            <p style="color: #A8A29E; font-size: 0.9em; margin-top: 20px;">
                Enter your password to access the dashboard
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Password input
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        password_input = st.text_input(
            "Password",
            type="password",
            key="password_input",
            placeholder="Enter dashboard password"
        )

        if st.button("🔶 Access Dashboard", use_container_width=True):
            if password_input == correct_password:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
                return False

    # Footer
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 20px; color: #A8A29E;">
            <small>
                <span style="color: #F59E0B; font-weight: 600;">Govern</span><span style="font-weight: 600;">IQ</span><br>
                Cyber Security Governance & Assurance<br>
                Contact your administrator for access
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )

    return False
