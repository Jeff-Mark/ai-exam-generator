import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css

load_css()

st.set_page_config(layout="wide")
show_sidebar()

st.title("📄 Upload Notes")
st.write("Upload your study materials to generate exam questions")

option = st.radio("Choose Input Method", ["Upload File", "Paste Text"])

if option == "Upload File":
    uploaded_file = st.file_uploader(
        "Upload PDF/DOCX/TXT",
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:
        st.success("File uploaded successfully")

else:
    text = st.text_area("Paste Notes Here", height=300)

st.button("Generate Questions")
