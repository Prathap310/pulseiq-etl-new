import streamlit as st

from Src.kpi_auth import AuthenticationError, verify_access_token


SESSION_TOKEN_KEY = "pulseiq_authenticated_token"


def get_authenticated_session(page_name: str):
    """Reuse a verified token across Streamlit multipage navigation."""

    token = st.session_state.get(SESSION_TOKEN_KEY, "")
    claims = None

    if token:
        try:
            claims = verify_access_token(token)
        except AuthenticationError:
            st.session_state.pop(SESSION_TOKEN_KEY, None)
            token = ""

    if claims is None:
        st.subheader("Authentication")

        entered_token = st.text_input(
            "Paste your signed JWT access token",
            type="password",
            key=f"{page_name}_token_input",
            help="Your verified session will be reused across PulseIQ pages.",
        )

        if entered_token:
            try:
                claims = verify_access_token(entered_token.strip())
                token = entered_token.strip()
                st.session_state[SESSION_TOKEN_KEY] = token
            except AuthenticationError:
                st.error("Authentication failed. Provide a valid access token.")

    if claims is None:
        st.info("Authenticate once to access PulseIQ governed KPI tools.")
        st.stop()

    st.success(
        f"Authenticated: {claims['sub']} | Role: {claims['role']}"
    )

    return claims, token
