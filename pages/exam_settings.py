import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css

load_css()

st.set_page_config(layout="wide")
show_sidebar()

st.title("⚙️ Exam Settings")

col1, col2 = st.columns(2)

with col1:
    num_questions = st.number_input(
        "Number of Questions",
        min_value=1,
        max_value=100,
        value=10
    )

    difficulty = st.selectbox(
        "Difficulty Level",
        ["Easy", "Medium", "Hard"]
    )

with col2:
    question_types = st.multiselect(
        "Question Types",
        ["MCQ", "Short Answer", "Essay"],
        default=["Short Answer"]
    )

    duration = st.selectbox(
        "Time Duration (Hours)",
        [1, 2, 3]
    )

st.button("Generate Exam")
