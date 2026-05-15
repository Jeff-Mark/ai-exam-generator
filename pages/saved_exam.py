import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import (
    run_query,
    delete_data,
    update_data
)
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import (
    getSampleStyleSheet
)
from reportlab.lib.pagesizes import letter

# =====================================================
# SESSION CHECK
# =====================================================

if "user" not in st.session_state:

    st.error("Please login first")

    st.stop()

user = st.session_state["user"]

user_id = user["id"]

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(layout="wide")

load_css()

show_sidebar()

st.title("📚 Saved Exams")

# =====================================================
# LOAD EXAMS
# =====================================================

exams = run_query(
    "exams_paper",
    filters={"user_id": user_id}
)

# =====================================================
# NO EXAMS
# =====================================================

if not exams:

    st.warning(
        "No saved exams found."
    )

    st.stop()

# =====================================================
# SEARCH
# =====================================================

search = st.text_input(
    "🔍 Search Exams"
)

# =====================================================
# FILTER EXAMS
# =====================================================

filtered_exams = []

for exam in exams:

    title = exam.get(
        "exam_title",
        ""
    ).lower()

    unit = exam.get(
        "unit_name",
        ""
    ).lower()

    if (
        search.lower() in title
        or
        search.lower() in unit
    ):

        filtered_exams.append(exam)

# =====================================================
# SELECT EXAM
# =====================================================


selected_exam = st.selectbox(

    "Choose Exam",

    filtered_exams,

    format_func=lambda x:
        f"{x['exam_title']} "
        f"({datetime.fromisoformat(x['created_at']).strftime('%d %b %Y %I:%M %p')})"
)

# =====================================================
# EXAM DETAILS
# =====================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Unit",
        selected_exam["unit_name"]
    )

with col2:

    st.metric(
        "Difficulty",
        selected_exam["difficulty"]
    )

with col3:

    st.metric(
        "Duration",
        f"{selected_exam['duration']} Hour(s)"
    )

# =====================================================
# EDIT EXAM
# =====================================================

edited_exam = st.text_area(

    "✏️ Edit Exam",

    value=selected_exam[
        "exam_content"
    ],

    height=700
)

# =====================================================
# SAVE CHANGES
# =====================================================

if st.button(
    "💾 Save Changes",
    key="save_exam_changes"
):

    update_data(

        "exams_paper",

        filters={
            "exam_id":
                selected_exam[
                    "exam_id"
                ]
        },

        data={
            "exam_content":
                edited_exam
        }
    )

    st.success(
        "Exam updated successfully!"
    )


# =====================================================
# DELETE EXAM
# =====================================================

if st.button(
    "🗑️ Delete Exam",
    key="delete_exam_btn"
):

    delete_data(

        "exams_paper",

        {
            "exam_id":
                selected_exam[
                    "exam_id"
                ]
        }
    )

    st.success(
        "Exam deleted successfully!"
    )

    st.rerun()

# =====================================================
# PDF GENERATOR
# =====================================================


def generate_pdf(text):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    lines = text.split("\n")

    for line in lines:

        elements.append(

            Paragraph(
                line.replace(
                    " ",
                    "&nbsp;"
                ),
                styles["BodyText"]
            )
        )

        elements.append(
            Spacer(1, 8)
        )

    doc.build(elements)

    buffer.seek(0)

    return buffer

# =====================================================
# DOWNLOADS
# =====================================================


st.divider()

col1, col2 = st.columns(2)

# ---------------- PDF ----------------

with col1:

    pdf_file = generate_pdf(
        edited_exam
    )

    st.download_button(

        label="📥 Download PDF",

        data=pdf_file,

        file_name=(
            f"{selected_exam['exam_title']}"
            ".pdf"
        ),

        mime="application/pdf"
    )

# ---------------- TXT ----------------

with col2:

    st.download_button(

        label="📥 Download TXT",

        data=edited_exam,

        file_name=(
            f"{selected_exam['exam_title']}"
            ".txt"
        ),

        mime="text/plain"
    )

# =====================================================
# EXAMS TABLE
# =====================================================

st.divider()

st.subheader("📋 All Saved Exams")

table_df = pd.DataFrame([

    {
        "Title":
            exam["exam_title"],

        "Unit":
            exam["unit_name"],

        "Difficulty":
            exam["difficulty"],

        "Duration":
            exam["duration"],

        "Created":
            exam["created_at"]
    }

    for exam in filtered_exams
])

st.dataframe(
    table_df,
    use_container_width=True
)
