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
load_css()
st.set_page_config(layout="wide")
show_sidebar()

st.title("🧠 Editable Generated Questions")

# ---------------- LOAD NOTES ----------------
notes = run_query(
    "notes",
    filters={"user_id": user_id}
)

selected_note = st.selectbox(
    "📘 Select Unit",
    notes,
    format_func=lambda x: x["unit_name"]
)

# ---------------- LOAD QUESTIONS ----------------
questions = run_query(
    "generatedquestions",
    filters={"note_id": selected_note["note_id"]}
)

if questions:

    df = pd.DataFrame([
        {
            "question_id": q["question_id"],
            "Delete": False,  # 👈 DELETE FLAG
            "Question": q.get("question_text", ""),
            "Type": q.get("question_type", ""),
            "Marks": q.get("marks", 0),
            "Difficulty": q.get("difficulty", "")
        }
        for q in questions
    ])

    st.success(f"{len(df)} questions loaded")

    # ---------------- EDITABLE TABLE ----------------
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

    # ---------------- SAVE BUTTON ----------------
    if st.button("💾 Save Changes to Database"):

        for _, row in edited_df.iterrows():

            question_id = int(row["question_id"])

            # ---------------- DELETE ----------------
            if row["Delete"] == True:

                delete_data(
                    "generatedquestions",
                    {"question_id": question_id}
                )
                continue

            # ---------------- SAFE UPDATE ----------------
            question_text = row["Question"] or ""
            question_type = row["Type"] or "Short Answer"
            difficulty = row["Difficulty"] or "Medium"

            try:
                marks = int(row["Marks"])
            except:
                marks = 0

            update_data(
                "generatedquestions",
                filters={
                    "question_id": question_id
                },
                data={
                    "question_text": question_text,
                    "question_type": question_type,
                    "marks": marks,
                    "difficulty": difficulty
                }
            )

        st.success("Database updated successfully!")

else:
    st.warning("No questions found for this unit.")
