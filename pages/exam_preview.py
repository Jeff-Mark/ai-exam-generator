
import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(layout="wide")

load_css()

show_sidebar()

# =====================================================
# SESSION CHECK
# =====================================================

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
# LOAD EXAM
# =====================================================

exam_text = st.session_state[
    "generated_exam"
]

# =====================================================
# EDITABLE TEXT AREA
# =====================================================

edited_exam = st.text_area(
    "Edit Exam Paper",
    value=exam_text,
    height=700
)

# SAVE UPDATED VERSION
st.session_state[
    "generated_exam"
] = edited_exam

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

    # SPLIT INTO LINES
    lines = text.split("\n")

    for line in lines:

        p = Paragraph(
            line.replace(" ", "&nbsp;"),
            styles['BodyText']
        )

        elements.append(p)

        elements.append(
            Spacer(1, 8)
        )

    doc.build(elements)

    buffer.seek(0)

    return buffer


# =====================================================
# ACTION BUTTONS
# =====================================================

col1, col2 = st.columns(2)

# ---------------- PDF DOWNLOAD ----------------
with col1:

    pdf_file = generate_pdf(
        edited_exam
    )

    st.download_button(

        label="📥 Download PDF",

        data=pdf_file,

        file_name="exam_paper.pdf",

        mime="application/pdf"
    )

# ---------------- TEXT DOWNLOAD ----------------
with col2:

    st.download_button(

        label="📥 Download TXT",

        data=edited_exam,

        file_name="exam_paper.txt",

        mime="text/plain"
    )
