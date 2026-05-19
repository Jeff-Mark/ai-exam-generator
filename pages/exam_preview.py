import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO
from db import insert_data

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(layout="wide")

load_css()

show_sidebar()

# =====================================================
# SESSION CHECK
# =====================================================
if st.session_state["user"] is None:

    st.warning("Please login first.")

    st.switch_page("app.py")

    st.stop()

if "generated_exam" not in st.session_state:

    st.warning(
        "No generated exam found."
    )

    st.stop()


# =====================================================
# PAGE TITLE
# =====================================================

st.title("📝 Exam Paper Preview")

# =====================================================
# LOAD SESSION DATA
# =====================================================

exam_text = st.session_state.get(
    "generated_exam",
    ""
)
marking_scheme = st.session_state.get(
    "generated_marking_scheme",
    ""
)

metadata = st.session_state.get(
    "exam_metadata",
    {}
)

user = st.session_state["user"]

user_id = user["id"]

# =====================================================
# EXAM TITLE
# =====================================================

exam_title = st.text_input(

    "Exam Title",

    value=(
        f"{metadata.get('unit_name', '')} "
        f"Exam"
    )
)

# =====================================================
# EXAM EDITOR
# =====================================================

st.subheader("📄 Exam Paper")

edited_exam = st.text_area(

    "Edit Exam Paper",

    value=exam_text,

    height=600
)

# SAVE UPDATED VERSION
st.session_state[
    "generated_exam"
] = edited_exam

# =====================================================
# MARKING SCHEME EDITOR
# =====================================================

st.divider()

st.subheader("📘 Marking Scheme")

edited_marking_scheme = st.text_area(

    "Edit Marking Scheme",

    value=marking_scheme,

    height=500
)

# SAVE UPDATED VERSION
st.session_state[
    "generated_marking_scheme"
] = edited_marking_scheme

# =====================================================
# FULL DOCUMENT
# =====================================================

full_document = (
    edited_exam
    + "\n\n\n"
    + edited_marking_scheme
)

# =====================================================
# PDF GENERATOR
# =====================================================

def generate_pdf(text):

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=letter,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    elements = []

    # =================================================
    # SPLIT LINES
    # =================================================

    lines = text.split("\n")

    for line in lines:

        # EMPTY LINE
        if line.strip() == "":

            elements.append(
                Spacer(1, 10)
            )

            continue

        # HEADING STYLE
        if (
            "EXAM" in line
            or "MARKING SCHEME" in line
            or "SECTION" in line.upper()
        ):

            style = styles["Heading2"]

        else:

            style = styles["BodyText"]

        paragraph = Paragraph(

            line.replace(" ", "&nbsp;"),

            style
        )

        elements.append(paragraph)

        elements.append(
            Spacer(1, 6)
        )

    doc.build(elements)

    buffer.seek(0)

    return buffer

# =====================================================
# GENERATE PDF
# =====================================================

pdf_file = generate_pdf(
    full_document
)

# =====================================================
# ACTION BUTTONS
# =====================================================

st.divider()

col1, col2, col3 = st.columns(3)

# =====================================================
# SAVE TO DATABASE
# =====================================================

with col1:

    if st.button(
        "💾 Save Exam",
        key="save_exam_btn"
    ):

        try:

            insert_data(
                "exams_paper",
                {

                    "user_id":
                        user_id,

                    "unit_name":
                        metadata.get(
                            "unit_name",
                            ""
                        ),

                    "exam_title":
                        exam_title,

                    "duration":
                        metadata.get(
                            "duration",
                            1
                        ),

                    "difficulty":
                        metadata.get(
                            "difficulty",
                            "Medium"
                        ),

                    "exam_content":
                        edited_exam,

                    "marking_scheme":
                        edited_marking_scheme
                }
            )

            st.success(
                "Exam and marking "
                "scheme saved successfully!"
            )

        except Exception as e:

            st.error(
                f"Database Error: {str(e)}"
            )

# =====================================================
# DOWNLOAD PDF
# =====================================================

with col2:

    st.download_button(

        label="📥 Download PDF",

        data=pdf_file,

        file_name="exam_paper.pdf",

        mime="application/pdf"
    )

# =====================================================
# DOWNLOAD TEXT
# =====================================================

with col3:

    st.download_button(

        label="📥 Download TXT",

        data=full_document,

        file_name="exam_paper.txt",

        mime="text/plain"
    )

# =====================================================
# LIVE PREVIEW
# =====================================================

st.divider()

st.subheader("👀 Live Preview")

tab1, tab2 = st.tabs([
    "📄 Exam Paper",
    "📘 Marking Scheme"
])

# =====================================================
# EXAM TAB
# =====================================================

with tab1:

    st.text(edited_exam)

# =====================================================
# MARKING TAB
# =====================================================

with tab2:

    st.text(edited_marking_scheme)