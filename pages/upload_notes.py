import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import insert_data, run_query
from utils.text_processing import read_first_page, extract_unit_details
from utils.uploadnotes import get_file_url, upload_file
import uuid

# ============================================
# INIT SESSION
# ============================================

if "user" not in st.session_state:

    st.session_state["user"] = None

# ============================================
# PROTECT PAGE
# ============================================

if st.session_state["user"] is None:

    st.warning("Please login first.")

    st.switch_page("app.py")

# ============================================
# USER DATA
# ============================================

user = st.session_state["user"]
user_id = user["id"]

load_css()
# ---------------------------------------------------------------------
API_URL = "https://abcd-12-34-56-78.ngrok-free.app/generate"

notes = run_query("notes", filters={"user_id": user_id})

selected_note = st.selectbox(
    "Choose Notes",
    notes,
    format_func=lambda x: x["unit_name"]
)
# ---------------------------------------------------------------------
st.set_page_config(layout="wide")
show_sidebar()

st.title("📄 Upload Notes")
st.write("Upload your study materials to generate exam questions ")

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

            insert_data("notes", {
                "user_id": user_id,
                "original_name": uploaded_file.name,
                "file_name": storage_name,
                "file_path": file_url,
                "unit_code": unit_code,
                "unit_name": unit_name
            })

            st.success("Notes saved successfully!")


else:
    text = st.text_area("Paste Notes Here", height=300)

if st.button("Generate Questions"):
    st.switch_page("pages/generate_questions.py")
