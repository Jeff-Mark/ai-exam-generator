import streamlit as st
from pathlib import Path
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import execute_query

# ============================================
# PAGE CONFIG
# ============================================
load_css()


# ============================================
# Create new user sql
# ============================================

def create_user(full_name, username, email, password):

    query = """
            INSERT INTO public.users(full_name, username, email, password_hash)
            VALUES (:full_name, :username, :email, :password)
            """

    params = {
        "full_name": full_name,
        "username": username,
        "email": email,
        "password": password
    }

    execute_query(query, params)


show_sidebar()
st.set_page_config(
    page_title="Register",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# HIDE DEFAULT STREAMLIT MENU
# ============================================

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# REGISTRATION PAGE
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

    full_name = st.text_input("Full Name")

    username = st.text_input("Username")

    email = st.text_input("Email Address")

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

    if st.button("Create Account"):

        if not full_name or not username or not email or not password:
            st.error("Please fill in all fields.")

        elif password != confirm_password:
            st.error("Passwords do not match.")

        else:
            st.success("Account created successfully!")
            create_user(full_name, username, email, password)
            # Add database insert here
            # Example:
            # save_user(full_name, username, email, password)

    st.markdown("""
    <div class='login-link'>
        Already have an account?
        <a href="/login">Login</a>
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
