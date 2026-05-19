import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query, delete_data, update_data
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# =====================================================
# SESSION CHECK
# =====================================================

if "user" not in st.session_state:
    st.error("Please login first")
    st.stop()

user    = st.session_state["user"]
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

exams = run_query("exams_paper", filters={"user_id": user_id})

if not exams:
    st.warning("No saved exams found.")
    st.stop()

# =====================================================
# SEARCH + FILTER
# =====================================================

search = st.text_input("🔍 Search Exams")

filtered_exams = [
    e for e in exams
    if search.lower() in e.get("exam_title", "").lower()
    or search.lower() in e.get("unit_name", "").lower()
]

# =====================================================
# SELECT EXAM
# =====================================================

selected_exam = st.selectbox(
    "Choose Exam",
    filtered_exams,
    format_func=lambda x: (
        f"{x['exam_title']} "
        f"({datetime.fromisoformat(x['created_at']).strftime('%d %b %Y %I:%M %p')})"
    )
)

# =====================================================
# EXAM DETAILS
# =====================================================

st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Unit",       selected_exam["unit_name"])
with col2:
    st.metric("Difficulty", selected_exam["difficulty"])
with col3:
    st.metric("Duration",   f"{selected_exam['duration']} Hour(s)")

# =====================================================
# PDF GENERATOR
# =====================================================

def generate_pdf(text: str) -> BytesIO:
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elems  = []
    for line in text.split("\n"):
        elems.append(Paragraph(line.replace(" ", "&nbsp;"), styles["BodyText"]))
        elems.append(Spacer(1, 8))
    doc.build(elems)
    buffer.seek(0)
    return buffer

# =====================================================
# TABS — Exam Paper | Marking Scheme
# =====================================================

tab_exam, tab_scheme = st.tabs(["📄 Exam Paper", "✅ Marking Scheme"])

# ─────────────────────────────────────────────────────
# TAB 1 — EXAM PAPER
# ─────────────────────────────────────────────────────
with tab_exam:
    st.subheader("✏️ Edit Exam Paper")

    edited_exam = st.text_area(
        "Exam Content",
        value=selected_exam.get("exam_content", ""),
        height=700,
        key="edit_exam_content",
    )

    col_s, col_d = st.columns(2)

    with col_s:
        if st.button("💾 Save Exam Changes", key="save_exam_btn"):
            update_data(
                "exams_paper",
                filters={"exam_id": selected_exam["exam_id"]},
                data={"exam_content": edited_exam},
            )
            st.success("Exam paper updated!")

    with col_d:
        if st.button("🗑️ Delete Exam", key="delete_exam_btn"):
            delete_data("exams_paper", {"exam_id": selected_exam["exam_id"]})
            st.success("Exam deleted.")
            st.rerun()

    st.divider()
    st.subheader("📥 Download Exam Paper")
    dl1, dl2 = st.columns(2)

    with dl1:
        st.download_button(
            label="📥 Download PDF",
            data=generate_pdf(edited_exam),
            file_name=f"{selected_exam['exam_title']}.pdf",
            mime="application/pdf",
            key="dl_exam_pdf",
        )
    with dl2:
        st.download_button(
            label="📥 Download TXT",
            data=edited_exam,
            file_name=f"{selected_exam['exam_title']}.txt",
            mime="text/plain",
            key="dl_exam_txt",
        )

# ─────────────────────────────────────────────────────
# TAB 2 — MARKING SCHEME
# ─────────────────────────────────────────────────────
with tab_scheme:
    st.subheader("✏️ Edit Marking Scheme")

    # marking_scheme column may not exist in older rows — fall back gracefully
    scheme_value = selected_exam.get("marking_scheme", "") or ""

    if not scheme_value:
        st.info(
            "No marking scheme saved for this exam yet. "
            "Generate a new exam from Exam Settings to include one, "
            "or type/paste it below and save."
        )

    edited_scheme = st.text_area(
        "Marking Scheme Content",
        value=scheme_value,
        height=700,
        key="edit_scheme_content",
    )

    col_ss, col_sd = st.columns(2)

    with col_ss:
        if st.button("💾 Save Scheme Changes", key="save_scheme_btn"):
            update_data(
                "exams_paper",
                filters={"exam_id": selected_exam["exam_id"]},
                data={"marking_scheme": edited_scheme},
            )
            st.success("Marking scheme updated!")

    with col_sd:
        # Download buttons for the scheme
        st.divider()
        st.subheader("📥 Download Marking Scheme")
        ds1, ds2 = st.columns(2)

        with ds1:
            st.download_button(
                label="📥 Download PDF",
                data=generate_pdf(edited_scheme) if edited_scheme else generate_pdf("No marking scheme."),
                file_name=f"{selected_exam['exam_title']}_marking_scheme.pdf",
                mime="application/pdf",
                key="dl_scheme_pdf",
            )
        with ds2:
            st.download_button(
                label="📥 Download TXT",
                data=edited_scheme,
                file_name=f"{selected_exam['exam_title']}_marking_scheme.txt",
                mime="text/plain",
                key="dl_scheme_txt",
            )

# =====================================================
# ALL SAVED EXAMS TABLE
# =====================================================

st.divider()
st.subheader("📋 All Saved Exams")

st.dataframe(
    pd.DataFrame([
        {
            "Title":      e["exam_title"],
            "Unit":       e["unit_name"],
            "Difficulty": e["difficulty"],
            "Duration":   e["duration"],
            "Created":    e["created_at"],
        }
        for e in filtered_exams
    ]),
    use_container_width=True,
)