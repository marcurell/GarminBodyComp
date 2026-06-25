import os
import bcrypt
import streamlit as st
import streamlit_authenticator as stauth

# ---------------------------------------------------------------------------
# Auth module with persistent browser cookie (30-day session).
# Uses streamlit-authenticator 0.2.3 which has stable cookie support.
# Fails loudly if required env vars are missing — no insecure defaults.
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        st.error(f"Konfigurationsfel: miljövariabeln {name} saknas. Kontakta admin.")
        st.stop()
    return value


def _build_authenticator() -> stauth.Authenticate:
    username = _require_env("AUTH_USERNAME")
    raw_password = _require_env("AUTH_PASSWORD")
    cookie_key = _require_env("AUTH_COOKIE_KEY")

    hashed = bcrypt.hashpw(raw_password.encode()[:72], bcrypt.gensalt()).decode()

    credentials = {
        "usernames": {
            username: {
                "name": username.capitalize(),
                "password": hashed,
            }
        }
    }

    # 0.2.3 API: Authenticate(credentials, cookie_name, cookie_key, cookie_expiry_days)
    return stauth.Authenticate(
        credentials,
        "bodycomp_session",
        cookie_key,
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
    return st.session_state.get("user_id", "")


def logout_button() -> None:
    authenticator: stauth.Authenticate | None = st.session_state.get("authenticator")
    if authenticator:
        authenticator.logout("Logga ut", "sidebar")
