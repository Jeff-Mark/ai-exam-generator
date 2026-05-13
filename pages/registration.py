import streamlit as st
import bcrypt

from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query, insert_data

# ============================================
# PAGE CONFIG
# ============================================

load_css()

st.set_page_config(
    page_title="Register",
    layout="wide",
    initial_sidebar_state="collapsed"
)

show_sidebar()

# ============================================
# HIDE STREAMLIT DEFAULT UI
# ============================================

# st.markdown("""
# <style>

# #MainMenu {
#     visibility: hidden;
# }

# footer {
#     visibility: hidden;
# }

# header {
#     visibility: hidden;
# }

# </style>
# """, unsafe_allow_html=True)

# ============================================
# CHECK IF USER EXISTS
# ============================================


def user_exists(email, username):

    users = run_query("users")

    for user in users:

        if user["email"] == email:
            return "email"

        if user["username"] == username:
            return "username"

    return None

# ============================================
# PAGE LAYOUT
# ============================================


left, right = st.columns([1.1, 1])

# ============================================
# LEFT SIDE
# ============================================

with left:

    st.markdown("""
    <div class='register-container'>

    <div class='logo-box'>
    <img src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'>
    <h1>AI Exam Generator</h1>
    </div>

    <h2>Create Account</h2>

    <p class='subtitle'>
    Register to generate intelligent exams from lecture notes.
    </p>

    </div>
    """, unsafe_allow_html=True)

    # ============================================
    # FORM
    # ============================================

    full_name = st.text_input(
        "Full Name"
    )

    username = st.text_input(
        "Username"
    )

    email = st.text_input(
        "Email Address"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password"
    )

    role = st.selectbox(
        "Role",
        ["Lecturer"]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================
    # CREATE ACCOUNT BUTTON
    # ============================================

    if st.button("Create Account"):

        # ---------------- VALIDATION ----------------

        if (
            not full_name
            or not username
            or not email
            or not password
        ):

            st.error(
                "Please fill in all fields."
            )

        elif password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            # ---------------- CHECK EXISTING USER ----------------

            exists = user_exists(
                email,
                username
            )

            if exists == "email":

                st.error(
                    "Email already exists."
                )

            elif exists == "username":

                st.error(
                    "Username already exists."
                )

            else:

                try:

                    # ---------------- HASH PASSWORD ----------------

                    hashed_password = bcrypt.hashpw(
                        password.encode("utf-8"),
                        bcrypt.gensalt()
                    ).decode("utf-8")

                    # ---------------- INSERT USER ----------------

                    result = insert_data(
                        "users",
                        {
                            "full_name": full_name,
                            "username": username,
                            "email": email,
                            "password": hashed_password,
                            "role": role
                        }
                    )

                    # ---------------- SUCCESS ----------------

                    if result:

                        st.success(
                            "Account created successfully!"
                        )

                        st.info(
                            "You can now login."
                        )

                        # OPTIONAL REDIRECT
                        # st.switch_page("pages/login.py")

                    else:

                        st.error(
                            "Failed to create account."
                        )

                except Exception as e:

                    st.error(
                        f"Registration Error: {str(e)}"
                    )

    # ============================================
    # LOGIN LINK
    # ============================================

    st.markdown("""
    <div class='login-link'>
        Already have an account?
        <a href="./">Login</a>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# RIGHT SIDE
# ============================================

with right:

    st.markdown("""
    <div class='image-container'>
        <img src='https://cdn-icons-png.flaticon.com/512/4140/4140048.png'>
    </div>
    """, unsafe_allow_html=True)
