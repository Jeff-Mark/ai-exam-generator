import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query, update_data, delete_data

# ==========================================================
# SESSION CHECK
# ==========================================================
if "user" not in st.session_state:

    st.error("Please log in first")

    st.stop()

user = st.session_state["user"]

user_id = user["id"]

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(layout="wide")

load_css()

show_sidebar()

st.title("🧠 Editable Generated Questions")

QUESTION_TYPES = [

    "Short Answer",

    "Long Answer",

    "Essay",

    "MCQ",

    "True/False",

    "Fill in the Blank"
]

# ==========================================================
# LOAD NOTES
# ==========================================================
notes = run_query(

    "notes",

    filters={
        "user_id": user_id
    }
)

# ==========================================================
# GET UNIQUE UNITS
# ==========================================================
unique_units = []

seen_units = set()

for note in notes:

    unit_name = note.get(

        "unit_name",

        "Unknown Unit"
    )

    if unit_name not in seen_units:

        seen_units.add(unit_name)

        unique_units.append(unit_name)

# ==========================================================
# SELECT UNIT
# ==========================================================
selected_unit = st.selectbox(

    "📘 Select Unit",

    unique_units
)

# ==========================================================
# GET NOTES FOR UNIT
# ==========================================================
matching_notes = [

    note for note in notes

    if note.get("unit_name")
    == selected_unit
]

note_ids = [

    note["note_id"]

    for note in matching_notes
]

# ==========================================================
# LOAD QUESTIONS
# ==========================================================
all_questions = []

for note_id in note_ids:

    questions = run_query(

        "generatedquestions",

        filters={
            "note_id": note_id
        }
    )

    if questions:

        all_questions.extend(questions)

# ==========================================================
# DISPLAY QUESTIONS
# ==========================================================
if all_questions:

    # ======================================================
    # QUESTION TYPE FILTER
    # ======================================================
    all_types = sorted(list(set([

        q.get(
            "question_type",
            "Unknown"
        )

        for q in all_questions

    ])))

    selected_types = st.multiselect(

        "🎯 Select Question Types",

        options=all_types,

        default=all_types
    )

    # ======================================================
    # FILTER QUESTIONS
    # ======================================================
    filtered_questions = [

        q for q in all_questions

        if q.get("question_type")
        in selected_types
    ]

    # =====================================================
    # LOAD ALL ANSWERS ONCE
    # =====================================================

    all_answers = run_query(
        "question_answers"
    )

    # =====================================================
    # CREATE ANSWER MAP
    # =====================================================

    answer_map = {}

    for ans in all_answers:

        question_id = ans["question_id"]

        answer_map[question_id] = ans

    # =====================================================
    # USE MAP
    # =====================================================

    for q in all_questions:

        question_id = q["question_id"]

        answer_data = answer_map.get(
            question_id,
            {}
        )

        correct_answer = answer_data.get(
            "correct_answer",
            ""
        )

    # ======================================================
    # SUCCESS
    # ======================================================
    st.success(

        f"{len(filtered_questions)} questions loaded"
    )

    # ======================================================
    # GROUP BY TOPIC
    # ======================================================
    topics_map = {}

    for q in filtered_questions:

        topic = q.get(

            "topic",

            "General"
        )

        if topic not in topics_map:

            topics_map[topic] = []

        topics_map[topic].append(q)

    # ======================================================
    # DISPLAY TOPICS
    # ======================================================
    for topic_name, questions in topics_map.items():

        st.divider()

        st.subheader(f"📘 {topic_name}")

        # ==================================================
        # LOOP QUESTIONS
        # ==================================================
        for i, q in enumerate(questions):

            question_id = q["question_id"]

            answer_data = answer_map.get(

                question_id,

                {}
            )

            with st.container(border=True):

                st.markdown(
                    f"## Question {i+1}"
                )

                # ==========================================
                # QUESTION TEXT
                # ==========================================
                edited_question = st.text_area(

                    "Question",

                    value=q.get(
                        "question_text",
                        ""
                    ),

                    key=f"question_{question_id}"
                )

                # ==========================================
                # META DATA
                # ==========================================
                col1, col2, col3 = st.columns(3)

                with col1:

                    current_type = q.get(

                        "question_type",

                        "Short Answer"
                    )

                    if current_type not in QUESTION_TYPES:

                        current_type = "Short Answer"

                    edited_type = st.selectbox(

                        "Question Type",

                        QUESTION_TYPES,

                        index=QUESTION_TYPES.index(
                            current_type
                        ),

                        key=f"type_{question_id}"
                    )

                with col2:

                    edited_marks = st.number_input(

                        "Marks",

                        min_value=1,

                        max_value=100,

                        value=int(
                            q.get(
                                "marks",
                                1
                            )
                        ),

                        key=f"marks_{question_id}"
                    )

                with col3:

                    difficulty_options = [

                        "Easy",

                        "Medium",

                        "Hard"
                    ]

                    current_difficulty = q.get(

                        "difficulty",

                        "Medium"
                    )

                    if current_difficulty not in difficulty_options:

                        current_difficulty = "Medium"

                    edited_difficulty = st.selectbox(

                        "Difficulty",

                        difficulty_options,

                        index=difficulty_options.index(
                            current_difficulty
                        ),

                        key=f"difficulty_{question_id}"
                    )

                # ==========================================
                # TOPIC
                # ==========================================
                edited_topic = st.text_input(

                    "Topic",

                    value=q.get(
                        "topic",
                        ""
                    ),

                    key=f"topic_{question_id}"
                )

                # ==========================================
                # MCQ DISPLAY
                # ==========================================
                if edited_type == "MCQ":

                    st.markdown(
                        "### 🔘 MCQ Options"
                    )

                    option_a = st.text_input(

                        "Option A",

                        value=answer_data.get(
                            "distractor_a",
                            ""
                        ),

                        key=f"a_{question_id}"
                    )

                    option_b = st.text_input(

                        "Option B",

                        value=answer_data.get(
                            "distractor_b",
                            ""
                        ),

                        key=f"b_{question_id}"
                    )

                    option_c = st.text_input(

                        "Option C",

                        value=answer_data.get(
                            "distractor_c",
                            ""
                        ),

                        key=f"c_{question_id}"
                    )

                    option_d = st.text_input(

                        "Option D",

                        value=answer_data.get(
                            "distractor_d",
                            ""
                        ),

                        key=f"d_{question_id}"
                    )

                    correct_answer = st.text_input(

                        "Correct Answer",

                        value=answer_data.get(
                            "correct_answer",
                            ""
                        ),

                        key=f"answer_{question_id}"
                    )

                # ==========================================
                # NORMAL ANSWERS
                # ==========================================
                else:

                    correct_answer = st.text_area(

                        "Answer",

                        value=answer_data.get(
                            "correct_answer",
                            ""
                        ),

                        key=f"answer_{question_id}"
                    )

                # ==========================================
                # DELETE
                # ==========================================
                delete_question = st.checkbox(

                    "❌ Delete Question",

                    key=f"delete_{question_id}"
                )

                # ==========================================
                # SAVE BUTTON
                # ==========================================
                if st.button(

                    "💾 Save Changes",

                    key=f"save_{question_id}"
                ):

                    # ======================================
                    # DELETE QUESTION
                    # ======================================
                    if delete_question:

                        delete_data(

                            "generatedquestions",

                            {
                                "question_id":
                                    question_id
                            }
                        )

                        st.success(
                            "Question deleted"
                        )

                        st.rerun()

                    # ======================================
                    # UPDATE QUESTION TABLE
                    # ======================================
                    update_data(

                        "generatedquestions",

                        filters={
                            "question_id":
                                question_id
                        },

                        data={

                            "question_text":
                                edited_question,

                            "question_type":
                                edited_type,

                            "marks":
                                edited_marks,

                            "difficulty":
                                edited_difficulty,

                            "topic":
                                edited_topic
                        }
                    )

                    # ======================================
                    # UPDATE ANSWER TABLE
                    # ======================================
                    if edited_type == "MCQ":

                        update_data(

                            "question_answers",

                            filters={
                                "question_id":
                                    question_id
                            },

                            data={

                                "correct_answer":
                                    correct_answer,

                                "distractor_a":
                                    option_a,

                                "distractor_b":
                                    option_b,

                                "distractor_c":
                                    option_c,

                                "distractor_d":
                                    option_d
                            }
                        )

                    else:

                        update_data(

                            "question_answers",

                            filters={
                                "question_id":
                                    question_id
                            },

                            data={

                                "correct_answer":
                                    correct_answer
                            }
                        )

                    st.success(
                        "✅ Changes saved successfully!"
                    )

                    st.rerun()

# ==========================================================
# NO QUESTIONS
# ==========================================================
else:

    st.warning(
        "No questions found for this unit."
    )