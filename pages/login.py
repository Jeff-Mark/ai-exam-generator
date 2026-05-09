import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css

load_css()

st.set_page_config(
    page_title="Login - AI Exam Generator",
    layout="wide"
)
# ---------------- SIDEBAR ----------------

show_sidebar()

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.markdown("# Welcome Back!")
    st.write("Login to your account to continue")

    st.image(
        "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        width=350
    )

with right_col:
    st.markdown("## Login")

    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password"
    )

    remember = st.checkbox("Remember me")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Login"):
        if email and password:
            st.success("Login successful")
        else:
            st.error("Please enter email and password")

    st.markdown(
        "Don't have an account? <span style='color:#6C63FF;font-weight:bold;'>Register</span>",
        unsafe_allow_html=True
    )
