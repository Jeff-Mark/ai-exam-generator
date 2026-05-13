import streamlit as st
import pandas as pd
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query, update_data, delete_data

# ---------------- SESSION CHECK ----------------
if "user" not in st.session_state:

    st.error("Please log in first")

    st.stop()

user = st.session_state["user"]

user_id = user["id"]

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

load_css()

show_sidebar()

st.title("🧠 Editable Generated Questions")

# =====================================================
# LOAD NOTES
# =====================================================

notes = run_query(
    "notes",
    filters={"user_id": user_id}
)

# =====================================================
# GET UNIQUE UNIT NAMES
# =====================================================

unique_units = []

seen_units = set()

for note in notes:

    unit_name = note.get("unit_name", "Unknown Unit")

    if unit_name not in seen_units:

        seen_units.add(unit_name)

        unique_units.append(unit_name)

# =====================================================
# UNIT SELECTOR
# =====================================================

selected_unit = st.selectbox(
    "📘 Select Unit",
    unique_units
)

# =====================================================
# GET ALL NOTE IDS FOR THIS UNIT
# =====================================================

matching_notes = [
    note for note in notes
    if note.get("unit_name") == selected_unit
]

note_ids = [
    note["note_id"]
    for note in matching_notes
]

# =====================================================
# LOAD QUESTIONS FROM ALL NOTES
# =====================================================

all_questions = []

for note_id in note_ids:

    questions = run_query(
        "generatedquestions",
        filters={"note_id": note_id}
    )

    if questions:

        all_questions.extend(questions)

# =====================================================
# DISPLAY QUESTIONS
# =====================================================

if all_questions:

    df = pd.DataFrame([

        {
            "question_id": q["question_id"],

            "Delete": False,

            "Question": q.get(
                "question_text",
                ""
            ),

            "Type": q.get(
                "question_type",
                ""
            ),

            "Marks": q.get(
                "marks",
                0
            ),

            "Difficulty": q.get(
                "difficulty",
                ""
            ),

            "Topic": q.get(
                "topic",
                ""
            )
        }

        for q in all_questions

    ])

    st.success(
        f"{len(df)} questions loaded "
        f"from {len(note_ids)} note(s)"
    )

    # =====================================================
    # EDITABLE TABLE
    # =====================================================

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

    # =====================================================
    # SAVE BUTTON
    # =====================================================

    if st.button("💾 Save Changes to Database"):

        for _, row in edited_df.iterrows():

            question_id = int(
                row["question_id"]
            )

            # =================================================
            # DELETE QUESTION
            # =================================================

            if row["Delete"] == True:

                delete_data(
                    "generatedquestions",
                    {
                        "question_id": question_id
                    }
                )

                continue

            # =================================================
            # SAFE VALUES
            # =================================================

            question_text = (
                row["Question"] or ""
            )

            question_type = (
                row["Type"] or
                "Short Answer"
            )

            difficulty = (
                row["Difficulty"] or
                "Medium"
            )

            topic = (
                row["Topic"] or
                ""
            )

            try:

                marks = int(row["Marks"])

            except:

                marks = 0

            # =================================================
            # UPDATE DATABASE
            # =================================================

            update_data(
                "generatedquestions",

                filters={
                    "question_id": question_id
                },

                data={
                    "question_text": question_text,

                    "question_type": question_type,

                    "marks": marks,

                    "difficulty": difficulty,

                    "topic": topic
                }
            )

        st.success(
            "Database updated successfully!"
        )

else:

    st.warning(
        "No questions found for this unit."
    )
