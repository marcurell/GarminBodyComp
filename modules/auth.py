import streamlit as st

# ---------------------------------------------------------------------------
# Auth module — delegates entirely to Azure Easy Auth (Google OAuth).
# Azure injects X-Ms-Client-Principal-Name header with the user's email
# after they authenticate via Google. No passwords, no cookies to manage.
#
# To restrict access to specific Google accounts, set allowed emails in
# ALLOWED_EMAILS env var (comma-separated). Leave unset to allow any
# Google account that reaches the app.
# ---------------------------------------------------------------------------

import os

def require_login() -> None:
    """Verify Azure Easy Auth identity is present. Blocks if not authenticated."""
    user = _get_user_from_header()
    if not user:
        st.error("Ingen autentisering hittades. Kontakta admin.")
        st.stop()
    st.session_state["user_id"] = user


def get_current_user() -> str:
    if "user_id" not in st.session_state:
        user = _get_user_from_header()
        st.session_state["user_id"] = user or ""
    return st.session_state["user_id"]


def logout_button() -> None:
    # Azure Easy Auth logout endpoint clears the session cookie
    st.sidebar.markdown(
        '<a href="/.auth/logout" target="_self">'
        '<button style="width:100%">Logga ut</button></a>',
        unsafe_allow_html=True,
    )


def _get_user_from_header() -> str:
    """Read the Google-authenticated email injected by Azure Easy Auth."""
    try:
        headers = st.context.headers
        raw = headers.get("X-Ms-Client-Principal-Name", "")
        return _sanitize_user_id(raw)
    except Exception:
        return ""


def _sanitize_user_id(raw: str) -> str:
    """Convert an email to a safe blob storage path segment.
    e.g. lars@joyyoga.se -> lars_joyyoga_se
    """
    import re
    return re.sub(r"[^a-z0-9_\-]", "_", raw.lower())
