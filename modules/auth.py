import streamlit as st

from modules.auth_core import sanitize_user_id, check_allowed

# ---------------------------------------------------------------------------
# Auth module — delegates entirely to Azure Easy Auth (Google OAuth).
# Azure injects X-Ms-Client-Principal-Name header with the user's email
# after they authenticate via Google. No passwords, no cookies to manage.
#
# To restrict access to specific Google accounts, set allowed emails in
# ALLOWED_EMAILS env var (comma-separated). Leave unset to allow any
# Google account that reaches the app.
# ---------------------------------------------------------------------------


def require_login() -> None:
    """Verify Azure Easy Auth identity is present and on the allowlist."""
    user = _get_user_from_header()
    if not user:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-size:3rem;">🔐</div>
            <h2 style="color:#FFFFFF;">Autentisering krävs</h2>
            <p style="color:#8A94B8;margin-bottom:24px;">Du behöver logga in med ditt Google-konto för att fortsätta.</p>
            <a href="/.auth/login/google?post_login_redirect_uri=/" target="_self"
               style="background:#1DB9E8;color:#000;padding:12px 28px;border-radius:8px;
                      font-weight:600;text-decoration:none;font-size:1rem;">
               Logga in med Google
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if not check_allowed(user):
        st.error("Du har inte behörighet att använda denna app.")
        st.markdown(
            '<a href="/.auth/logout" target="_self">Logga ut</a>',
            unsafe_allow_html=True,
        )
        st.stop()

    st.session_state["user_id"] = user


def get_current_user() -> str:
    user = st.session_state.get("user_id", "")
    if not user:
        raise RuntimeError("get_current_user() called before require_login()")
    return user


def logout_button() -> None:
    st.sidebar.markdown(
        '<a href="/.auth/logout" target="_self" style="display:block;width:100%;'
        'background:#1DB9E8;color:#000;padding:8px 20px;border-radius:8px;'
        'font-weight:600;text-decoration:none;font-size:0.9rem;text-align:center;">'
        'Logga ut</a>',
        unsafe_allow_html=True,
    )


def _get_user_from_header() -> str:
    """Read the Google-authenticated email injected by Azure Easy Auth."""
    try:
        headers = st.context.headers
        raw = headers.get("X-Ms-Client-Principal-Name", "")
        if raw:
            return sanitize_user_id(raw)
    except Exception:
        pass
    return ""
