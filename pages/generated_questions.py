import streamlit as st
import pandas as pd
from utils.sidebar import show_sidebar
from utils.styles import load_css

load_css()

st.set_page_config(layout="wide")
show_sidebar()

st.title("🧠 Generated Questions")

sample_data = {
    "Question": [
        "Define Artificial Intelligence",
        "Explain Machine Learning",
        "Describe Neural Networks"
    ],
    "Type": ["Short", "Short", "Essay"],
    "Marks": [2, 5, 10],
    "Difficulty": ["Easy", "Medium", "Hard"]
}


df = pd.DataFrame(sample_data)

st.dataframe(df, use_container_width=True)

st.button("Export Questions")
