import os
import bcrypt
import streamlit as st
import streamlit_authenticator as stauth

# ---------------------------------------------------------------------------
# Auth module with persistent browser cookie (30-day session).
#
# To expand to multi-user later:
#   - Build the credentials dict from a database instead of env vars.
#   - get_current_user() already returns a user_id that flows through
#     the rest of the app — no other changes needed.
# ---------------------------------------------------------------------------

def _build_authenticator() -> stauth.Authenticate:
    username = os.environ.get("AUTH_USERNAME", "lars")
    raw_password = os.environ.get("AUTH_PASSWORD", "")
    cookie_key = os.environ.get("AUTH_COOKIE_KEY", "change-me-in-azure")

    hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    credentials = {
        "usernames": {
            username: {
                "name": username.capitalize(),
                "password": hashed,
            }
        }
    }

    return stauth.Authenticate(
        credentials,
        cookie_name="bodycomp_session",
        key=cookie_key,
        cookie_expiry_days=30,
    )


def require_login() -> None:
    """Show login form if not authenticated. Blocks the rest of the app."""
    if "authenticator" not in st.session_state:
        st.session_state["authenticator"] = _build_authenticator()

    authenticator: stauth.Authenticate = st.session_state["authenticator"]

    name, auth_status, username = authenticator.login("Logga in", "main")

    if auth_status is False:
        st.error("Fel användarnamn eller lösenord.")
        st.stop()
    elif auth_status is None:
        st.stop()
    else:
        st.session_state["user_id"] = username


def get_current_user() -> str:
    return st.session_state.get("user_id", "lars")


def logout_button() -> None:
    authenticator: stauth.Authenticate | None = st.session_state.get("authenticator")
    if authenticator:
        authenticator.logout("Logga ut", "sidebar")
