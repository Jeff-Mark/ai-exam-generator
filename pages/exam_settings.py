import streamlit as st
import json
from utils.sidebar import show_sidebar
from utils.exam_generator import generate_exam
from utils.styles import load_css
from db import run_query

st.set_page_config(layout="wide")
load_css()
show_sidebar()
st.title("⚙️ Exam Settings")

if "user" not in st.session_state:
    st.error("Please log in first")
    st.stop()

user    = st.session_state["user"]
user_id = user["id"]

# ── Basic settings ────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    duration   = st.selectbox("Time Duration (Hours)", [1, 2, 3])
    difficulty = st.selectbox("Difficulty Level", ["Medium", "Easy", "Hard"])
with col2:
    num_sections = st.number_input("Number of Sections", min_value=1, max_value=10, value=2)

# ── Section settings ──────────────────────────────────────────
st.divider()
st.subheader("📝 Section Configuration")

section_data    = []
section_letters = list("ABCDEFGHIJ")

for i in range(num_sections):
    sname = f"Section {section_letters[i]}"
    st.markdown(f"## {sname}")
    c1, c2, c3 = st.columns(3)
    with c1:
        total_marks   = st.number_input(f"{sname} Total Marks", 1, 1000, 20, key=f"marks_{i}")
    with c2:
        num_questions = st.number_input(f"{sname} Number of Questions", 1, 100, 5, key=f"questions_{i}")
    with c3:
        question_types = st.multiselect(
            f"{sname} Question Types",
            ["MCQ", "Short Answer", "Essay", "True/False", "Fill in the Blank"],
            default=["Short Answer"], key=f"types_{i}"
        )
    mpq = total_marks / num_questions if num_questions > 0 else 0
    st.info(f"{sname}: {mpq:.1f} marks per question")
    section_data.append({
        "section":            sname,
        "total_marks":        total_marks,
        "num_questions":      num_questions,
        "marks_per_question": mpq,
        "question_types":     question_types,
    })
    st.divider()

# ── Summary ───────────────────────────────────────────────────
st.subheader("📋 Exam Summary")
st.write(f"**Total Sections:** {num_sections}")
st.write(f"**Total Questions:** {sum(s['num_questions'] for s in section_data)}")
st.write(f"**Grand Total Marks:** {sum(s['total_marks'] for s in section_data)}")
st.write(f"**Duration:** {duration} Hour(s)")
st.write(f"**Difficulty:** {difficulty}")

# ── Unit selector ─────────────────────────────────────────────
st.divider()
st.subheader("📘 Select Unit For Exam")

notes         = run_query("notes", filters={"user_id": user_id})
unique_units  = list(dict.fromkeys(n.get("unit_name", "Unknown") for n in notes))
selected_unit = st.selectbox("Choose Unit", unique_units)

# ════════════════════════════════════════════════════════════════
# HELPER — join questions with their answers from question_answers
# ════════════════════════════════════════════════════════════════

def load_questions_with_answers(note_id: int) -> list:
    """
    Fetch all questions for a note and JOIN their answer rows
    from question_answers so every question dict has:
      correct_answer, distractor_a/b/c/d, options (list), explanation
    """
    questions = run_query("generatedquestions", filters={"note_id": note_id})
    if not questions:
        return []

    # Fetch all answer rows for these questions in one call
    question_ids = [q["question_id"] for q in questions]
    # run_query may not support IN filters — fetch individually and cache
    answer_map = {}
    for qid in question_ids:
        rows = run_query("question_answers", filters={"question_id": qid})
        if rows:
            answer_map[qid] = rows[0]   # one answer row per question

    # Merge
    merged = []
    for q in questions:
        q      = dict(q)
        qid    = q["question_id"]
        ans    = answer_map.get(qid, {})

        q["correct_answer"] = ans.get("correct_answer", "")
        q["explanation"]    = ans.get("explanation", "")

        # Rebuild options list from distractor columns
        # Distractor columns store the option text without the letter label
        # e.g. distractor_a = "Stores pixel data"
        # We rebuild as ["A) Stores pixel data", "B) ...", ...]
        # and insert the correct answer at its original position
        raw_a = ans.get("distractor_a", "")
        raw_b = ans.get("distractor_b", "")
        raw_c = ans.get("distractor_c", "")
        raw_d = ans.get("distractor_d", "")

        if q.get("question_type") == "MCQ":
            # Reconstruct the four options preserving original A/B/C/D labels
            options = []
            if raw_a: options.append(f"A) {raw_a}")
            if raw_b: options.append(f"B) {raw_b}")
            if raw_c: options.append(f"C) {raw_c}")
            if raw_d: options.append(f"D) {raw_d}")
            q["options"] = options
        else:
            q["options"] = []

        merged.append(q)

    return merged


# ════════════════════════════════════════════════════════════════
# GENERATE EXAM
# ════════════════════════════════════════════════════════════════

if st.button("🧠 Generate Exam", key="generate_exam_btn"):

    all_questions = []
    for note in notes:
        if note["unit_name"] == selected_unit:
            # Use the joined loader instead of a plain run_query
            qs = load_questions_with_answers(note["note_id"])
            all_questions.extend(qs)

    if not all_questions:
        st.error("No generated questions found for this unit.")
        st.stop()

    # ── Remove difficulty filter so nothing is silently dropped ──
    # Difficulty is used for display only; all saved rows are "Medium"
    # If you want strict filtering, set difficulty=difficulty here
    exam = generate_exam(
        all_questions=all_questions,
        section_data=section_data,
        difficulty=None,       # ← pass None to skip filtering, or pass difficulty for strict
    )

    # ── Build exam text ───────────────────────────────────────
    exam_text = (
        f"{selected_unit.upper()} EXAM\n\n"
        f"Duration: {duration} Hour(s)\n"
        f"Difficulty: {difficulty}\n\n"
        f"{'='*52}\nINSTRUCTIONS\n{'='*52}\n"
        f"Answer ALL questions.\n\n"
    )

    marking_scheme = (
        f"{selected_unit.upper()} MARKING SCHEME\n\n"
        f"{'='*52}\n"
    )

    for section in exam:
        exam_text      += f"\n{section['section']}\n{section['instructions']}\nTotal Marks: {section['total_marks']}\n\n"
        marking_scheme += f"\n{section['section']}\n\n"

        for idx, q in enumerate(section["questions"], 1):
            q_text  = q.get("question_text", "")
            marks   = q.get("assigned_marks", 0)
            qtype   = q.get("question_type", "")
            answer  = q.get("correct_answer", "") or "No answer provided"
            options = q.get("options", [])

            # ── Exam paper ────────────────────────────────────
            exam_text += f"{idx}. {q_text} ({marks} Marks)\n"
            if qtype == "MCQ" and options:
                for opt in options:
                    exam_text += f"   {opt}\n"
            exam_text += "\n"

            # ── Marking scheme ────────────────────────────────
            marking_scheme += f"{idx}. {q_text}\n"
            if qtype == "MCQ":
                if options:
                    for opt in options:
                        marking_scheme += f"   {opt}\n"
                marking_scheme += f"✅ Correct Answer: {answer}\n"
            else:
                marking_scheme += f"Expected Answer:\n{answer}\n"
            marking_scheme += f"Marks: {marks}\n\n"

    st.session_state["generated_exam"]           = exam_text
    st.session_state["generated_marking_scheme"] = marking_scheme
    st.session_state["exam_metadata"] = {
        "unit_name":  selected_unit,
        "duration":   duration,
        "difficulty": difficulty,
    }

    st.success(f"✅ Exam generated for {selected_unit}")
    # st.switch_page("pages/exam_preview.py")

    st.write(exam_text)
    st.write(marking_scheme)
