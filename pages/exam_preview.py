import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css

load_css()

st.set_page_config(layout="wide")
show_sidebar()

st.title("📝 Exam Paper Preview")

exam = st.text_area("""
# AI GENERATED EXAM

### SECTION A
1. Define Artificial Intelligence (2 Marks)
2. List the components of an Expert System (2 Marks)

### SECTION B
3. Explain Machine Learning (5 Marks)

### SECTION C
4. Evaluate Neural Networks (10 Marks)
""")

col1, col2 = st.columns(2)

with col1:
    st.download_button("Download PDF", "Sample PDF")

with col2:
    st.download_button("Download DOCX", "Sample DOCX")
