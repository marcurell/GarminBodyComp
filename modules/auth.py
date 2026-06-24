import os
import hmac
import hashlib
import streamlit as st

# ---------------------------------------------------------------------------
# Auth module
#
# Currently: single user via AUTH_USERNAME / AUTH_PASSWORD env vars.
#
# To expand to multi-user later:
#   - Replace _verify_credentials() with a lookup against a database or
#     Entra B2C token validation.
#   - get_current_user() already returns a user_id string that flows through
#     the rest of the app — no other changes needed.
# ---------------------------------------------------------------------------

def _verify_credentials(username: str, password: str) -> bool:
    expected_user = os.environ.get("AUTH_USERNAME", "lars")
    expected_pass = os.environ.get("AUTH_PASSWORD", "")
    user_ok = hmac.compare_digest(username.lower(), expected_user.lower())
    pass_ok = hmac.compare_digest(
        hashlib.sha256(password.encode()).digest(),
        hashlib.sha256(expected_pass.encode()).digest(),
    )
    return user_ok and pass_ok


def require_login() -> None:
    """Show login form if not authenticated. Blocks the rest of the app."""
    if st.session_state.get("authenticated"):
        return

    st.title("🔐 Logga in")
    with st.form("login_form"):
        username = st.text_input("Användarnamn")
        password = st.text_input("Lösenord", type="password")
        submitted = st.form_submit_button("Logga in")

    if submitted:
        if _verify_credentials(username, password):
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = username.lower()
            st.rerun()
        else:
            st.error("Fel användarnamn eller lösenord.")

    st.stop()


def get_current_user() -> str:
    """Returns the logged-in user_id. Call only after require_login()."""
    return st.session_state.get("user_id", "lars")
