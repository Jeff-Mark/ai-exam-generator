import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import insert_data, run_query
from utils.text_processing import (
    read_first_page,
    extract_unit_details
)
from utils.uploadnotes import (
    get_file_url,
    upload_file
)
import uuid

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(layout="wide")

load_css()

show_sidebar()

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

    st.stop()

# ============================================
# USER DATA
# ============================================

user = st.session_state["user"]

user_id = user["id"]

# ============================================
# LOAD NOTES
# ============================================

notes = run_query(
    "notes",
    filters={"user_id": user_id}
)

# ============================================
# PAGE UI
# ============================================

st.title("📄 Upload Notes")

st.write(
    "Upload your study materials to generate exam questions"
)


# ============================================
# MULTIPLE FILE UPLOAD
# ============================================


uploaded_files = st.file_uploader(
    "Upload PDF/DOCX/TXT Files",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

# ----------------------------------------
# FILE PREVIEW
# ----------------------------------------

if uploaded_files:

    st.success(
        f"{len(uploaded_files)} file(s) selected"
    )

    processed_files = []

    for uploaded_file in uploaded_files:

        try:

            # READ FIRST PAGE
            first_page_text = read_first_page(
                uploaded_file
            )

            # EXTRACT UNIT DETAILS
            result = extract_unit_details(
                first_page_text
            )

            unit_code = result.get(
                "unit_code",
                "UNKNOWN"
            )

            unit_name = result.get(
                "unit_name",
                "Unknown Unit"
            )

            processed_files.append({
                "file": uploaded_file,
                "unit_code": unit_code,
                "unit_name": unit_name
            })

            # DISPLAY PREVIEW
            st.markdown("---")

            st.markdown(
                f"### 📘 {uploaded_file.name}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Unit Code:** {unit_code}"
                )

            with col2:
                st.write(
                    f"**Unit Name:** {unit_name}"
                )

        except Exception as e:

            st.error(
                f"Error processing "
                f"{uploaded_file.name}: {str(e)}"
            )

    # ----------------------------------------
    # SAVE ALL FILES
    # ----------------------------------------

    if st.button("💾 Save All Notes"):

        saved_count = 0

        for item in processed_files:

            try:

                uploaded_file = item["file"]

                unit_code = item["unit_code"]

                unit_name = item["unit_name"]

                # UNIQUE STORAGE NAME
                storage_name = (
                    f"{unit_code}_"
                    f"{uuid.uuid4()}_"
                    f"{uploaded_file.name}"
                )

                original_name = (
                    f"{unit_name}_"
                    f"{uploaded_file.name}"
                )

                # UPLOAD TO STORAGE
                upload_file(
                    storage_name,
                    uploaded_file.getvalue()
                )

                # GET FILE URL
                file_url = get_file_url(
                    storage_name
                )

                # SAVE TO DATABASE
                insert_data(
                    "notes",
                    {
                        "user_id": user_id,
                        "original_name": original_name,
                        "file_name": storage_name,
                        "file_path": file_url,
                        "unit_code": unit_code,
                        "unit_name": unit_name
                    }
                )

                saved_count += 1

            except Exception as e:

                st.error(
                    f"Failed saving "
                    f"{uploaded_file.name}: {str(e)}"
                )

        st.success(
            f"{saved_count} note(s) saved successfully!"
        )

# ============================================
# GENERATE QUESTIONS
# ============================================

if st.button("🧠 Generate Questions"):

    st.switch_page(
        "pages/generate_questions.py"
    )
