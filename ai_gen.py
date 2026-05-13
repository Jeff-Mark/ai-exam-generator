import streamlit as st
import bcrypt

from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query

# ============================================
# CONFIG
# ============================================

load_css()

st.set_page_config(
    page_title="Login - AI Exam Generator",
    layout="wide"
)

show_sidebar()

# ============================================
# INIT SESSION
# ============================================

if "user" not in st.session_state:

    st.session_state["user"] = None

# ============================================
# PROTECT ROUTE
# ============================================

if st.session_state["user"] is not None:

    st.success(
        f"Already logged in as "
        f"{st.session_state['user']['email']}"
    )

    st.stop()

# ============================================
# UI
# ============================================

left_col, right_col = st.columns([1.2, 1])

# ============================================
# LEFT SIDE
# ============================================

with left_col:

    st.markdown("# Welcome Back!")

    st.write(
        "Login to your account to continue"
    )

    st.image(
        "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        width=350
    )

# ============================================
# RIGHT SIDE
# ============================================

with right_col:

    st.markdown("## Login")

    email = st.text_input(
        "Email",
        placeholder="Enter your email"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password"
    )

    remember = st.checkbox(
        "Remember me"
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # ============================================
    # BUTTONS
    # ============================================

    log_col, reg_col = st.columns([1, 1])

    # ============================================
    # LOGIN BUTTON
    # ============================================

    with log_col:

        if st.button("Login"):

            if not email or not password:

                st.error(
                    "Please enter email and password"
                )

            else:

                users = run_query(
                    "users",
                    filters={
                        "email": email
                    }
                )

                # ---------------- USER EXISTS ----------------

                if users and len(users) > 0:

                    user = users[0]

                    stored_hash = user.get(
                        "password"
                    )

                    # ---------------- VERIFY PASSWORD ----------------

                    if (
                        stored_hash
                        and bcrypt.checkpw(
                            password.encode("utf-8"),
                            stored_hash.encode("utf-8")
                        )
                    ):

                        # SAVE USER SESSION
                        st.session_state["user"] = {
                            "id": user["user_id"],
                            "email": user["email"],
                            "name": user.get(
                                "full_name",
                                ""
                            )
                        }

                        st.success(
                            "Login successful!"
                        )

                        # REDIRECT TO DASHBOARD
                        st.switch_page(
                            "pages/dashboard.py"
                        )

                    else:

                        st.error(
                            "Invalid password"
                        )

                else:

                    st.error(
                        "User not found"
                    )

    # ============================================
    # REGISTER BUTTON
    # ============================================

    with reg_col:

        if st.button("Create Account"):

            st.switch_page(
                "pages/registration.py"
            )
