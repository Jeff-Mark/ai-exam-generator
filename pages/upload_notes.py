import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import execute_query
from utils.text_processing import read_first_page, extract_unit_details
from utils.uploadnotes import get_file_url, upload_file
import uuid

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
        first_page_text = read_first_page(uploaded_file)
        result = extract_unit_details(first_page_text)

        unit_code = result["unit_code"]
        unit_name = result["unit_name"]

        st.write(unit_code)
        st.write(unit_name)

        if st.button("Save pdf"):

            storage_name = f"{unit_code}_{uuid.uuid4()}_{uploaded_file.name}"

            upload_file(
                storage_name,
                uploaded_file.getvalue()
            )

            file_url = get_file_url(storage_name)

            execute_query(
                """
                INSERT INTO notes
                (
                    user_id,
                    original_name,
                    file_name,
                    file_path,
                    unit_code,
                    unit_name
                )
                VALUES
                (
                    :user_id,
                    :original_name,
                    :file_name,
                    :file_path,
                    :unit_code,
                    :unit_name
                )
                """,
                {
                    "user_id": 2,
                    "original_name": uploaded_file.name,
                    "file_name": storage_name,
                    "file_path": file_url,
                    "unit_code": unit_code,
                    "unit_name": unit_name
                }
            )

            st.success("Notes saved successfully!")


else:
    text = st.text_area("Paste Notes Here", height=300)

st.button("Generate Questions")
