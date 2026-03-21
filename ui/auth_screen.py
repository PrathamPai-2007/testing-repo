import streamlit as st  # type: ignore

from services.auth_service import authenticate_user, create_user
from services.supabase_client import has_supabase_config
from state import log_in_guest_user, log_in_user


def render_auth_screen() -> None:
    st.title("AI Quiz")
    st.write("Create an account, sign in, or continue as a guest to jump straight into the quiz.")

    guest_col, _ = st.columns([1, 2])
    with guest_col:
        if st.button("Continue as Guest", use_container_width=True):
            log_in_guest_user()
            st.rerun()

    if not has_supabase_config():
        st.info("Supabase auth is not configured yet. Guest mode is still available.")
        return

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email address", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            try:
                user = authenticate_user(email=email, password=password)
            except ValueError as exc:
                st.error(str(exc))
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                if user is None:
                    st.error("Invalid email or password.")
                else:
                    log_in_user(user)
                    st.success("Login successful.")
                    st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email address", key="signup_email")
            password = st.text_input("Choose a password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password")
            submitted = st.form_submit_button("Create Account", type="primary")

        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    user = create_user(email=email, password=password)
                except (ValueError, RuntimeError) as exc:
                    st.error(str(exc))
                else:
                    log_in_user(user)
                    st.success("Account created successfully.")
                    st.rerun()
