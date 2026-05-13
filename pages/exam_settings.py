import streamlit as st
from utils.sidebar import show_sidebar
from utils.exam_generator import filter_questions, generate_section_questions, generate_exam
from utils.styles import load_css
from db import run_query

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(layout="wide")

load_css()

show_sidebar()

st.title("⚙️ Exam Settings")

# ---------------- SESSION CHECK ----------------
if "user" not in st.session_state:

    st.error("Please log in first")

    st.stop()

user = st.session_state["user"]

user_id = user["id"]


# =====================================================
# BASIC SETTINGS
# =====================================================

col1, col2 = st.columns(2)

with col1:

    duration = st.selectbox(
        "Time Duration (Hours)",
        [1, 2, 3]
    )

    difficulty = st.selectbox(
        "Difficulty Level",
        ["Medium", "Easy", "Hard"]
    )

with col2:

    num_sections = st.number_input(
        "Number of Sections",
        min_value=1,
        max_value=10,
        value=2
    )

# =====================================================
# SECTION SETTINGS
# =====================================================

st.divider()

st.subheader("📝 Section Configuration")

section_data = []

section_letters = [
    "A", "B", "C", "D", "E",
    "F", "G", "H", "I", "J"
]

for i in range(num_sections):

    section_name = f"Section {section_letters[i]}"

    st.markdown(f"## {section_name}")

    col1, col2, col3 = st.columns(3)

    with col1:

        total_marks = st.number_input(
            f"{section_name} Total Marks",
            min_value=1,
            max_value=1000,
            value=20,
            key=f"marks_{i}"
        )

    with col2:

        num_questions = st.number_input(
            f"{section_name} Number of Questions",
            min_value=1,
            max_value=100,
            value=5,
            key=f"questions_{i}"
        )

    with col3:

        question_types = st.multiselect(
            f"{section_name} Question Types",
            [
                "MCQ",
                "Short Answer",
                "Essay",
                "True/False",
                "Fill in the Blank"
            ],
            default=["Short Answer"],
            key=f"types_{i}"
        )

    # =================================================
    # AUTO CALCULATE MARKS PER QUESTION
    # =================================================

    if num_questions > 0:

        marks_per_question = (
            total_marks / num_questions
        )

    else:

        marks_per_question = 0

    st.info(
        f"{section_name}: "
        f"{marks_per_question:.1f} marks "
        f"per question"
    )

    section_data.append({

        "section": section_name,

        "total_marks": total_marks,

        "num_questions": num_questions,

        "marks_per_question":
            marks_per_question,

        "question_types":
            question_types
    })

    st.divider()

# =====================================================
# EXAM SUMMARY
# =====================================================

st.subheader("📋 Exam Summary")

grand_total = sum(
    section["total_marks"]
    for section in section_data
)

total_questions = sum(
    section["num_questions"]
    for section in section_data
)

st.write(
    f"**Total Sections:** {num_sections}"
)

st.write(
    f"**Total Questions:** {total_questions}"
)

st.write(
    f"**Grand Total Marks:** {grand_total}"
)

st.write(
    f"**Duration:** {duration} Hour(s)"
)

st.write(
    f"**Difficulty:** {difficulty}"
)

# =====================================================
# DISPLAY SECTION SUMMARY
# =====================================================

st.markdown("### 📊 Section Breakdown")

for section in section_data:

    st.markdown(f"""
    #### {section["section"]}

    - Total Marks:
      {section["total_marks"]}

    - Questions:
      {section["num_questions"]}

    - Marks Per Question:
      {section["marks_per_question"]:.1f}

    - Question Types:
      {", ".join(section["question_types"])}
    """)
# =====================================================
# SELECT UNIT
# =====================================================

st.divider()

st.subheader("📘 Select Unit For Exam")

# LOAD USER NOTES
notes = run_query(
    "notes",
    filters={"user_id": user_id}
)

# GET UNIQUE UNIT NAMES
unique_units = []

seen = set()

for note in notes:

    unit_name = note.get(
        "unit_name",
        "Unknown Unit"
    )

    if unit_name not in seen:

        seen.add(unit_name)

        unique_units.append(unit_name)

# UNIT SELECTBOX
selected_unit = st.selectbox(
    "Choose Unit",
    unique_units
)
# =====================================================
# GENERATE EXAM BUTTON
# =====================================================

if st.button(
    "🧠 Generate Exam",
    key="generate_exam_btn"
):

    # LOAD QUESTIONS
    all_questions = []

    for note in notes:

        if note["unit_name"] == selected_unit:

            qs = run_query(
                "generatedquestions",
                filters={
                    "note_id": note["note_id"]
                }
            )

            if qs:

                all_questions.extend(qs)

    # GENERATE EXAM
    exam = generate_exam(

        all_questions=all_questions,

        section_data=section_data,

        difficulty=difficulty
    )

    # =================================================
    # CONVERT EXAM TO TEXT
    # =================================================

    exam_text = f"""
    {selected_unit.upper()} EXAM

    Duration: {duration} Hour(s)

    Difficulty: {difficulty}
    """

    for section in exam:

        exam_text += (
            f"\n\n"
            f"{section['section']}\n"
        )

        exam_text += (
            f"{section['instructions']}\n"
        )

        exam_text += (
            f"Total Marks: "
            f"{section['total_marks']}\n\n"
        )

        for i, q in enumerate(
            section["questions"],
            start=1
        ):

            exam_text += (
                f"{i}. "
                f"{q['question_text']} "
                f"({q['assigned_marks']} Marks)\n"
            )

    st.success(
        f"Exam generated for {selected_unit}"
    )

    # SAVE TO SESSION
    st.session_state["generated_exam"] = exam_text

    # GO TO PREVIEW PAGE
    st.switch_page(
        "pages/exam_preview.py"
    )
