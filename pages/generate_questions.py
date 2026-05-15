import streamlit as st
from utils.sidebar import show_sidebar
from utils.styles import load_css
from db import run_query, insert_data, delete_data
from utils.exam_generator import remove_duplicate_questions
import requests
import json
import urllib3

user = st.session_state["user"]
user_id = user["id"]

# ---------------- DISABLE SSL WARNINGS ----------------
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ---------------- CONFIG ----------------
load_css()

API_URL = "https://decal-spindle-unpaid.ngrok-free.dev/generate"

QUESTION_TYPES = [
    "Short Answer",
    "Long Answer",
    "Essay",
    "MCQ",
    "True/False",
    "Fill in the Blank"
]

st.set_page_config(layout="wide")

show_sidebar()

st.title("📄 Upload Notes & Generate Questions")

# ---------------- LOAD NOTES ----------------
notes = run_query(
    "notes",
    filters={"user_id": user_id, }
)

# ---------------- SELECT NOTE ----------------
selected_note = st.selectbox(
    "Choose Notes",
    notes,
    format_func=lambda x: x["original_name"]
)

# ---------------- CLEAR OLD RESULT IF NOTE CHANGES ----------------
if (
    "last_note" not in st.session_state
    or st.session_state["last_note"] != selected_note["note_id"]
):

    st.session_state.pop("result", None)

    st.session_state["last_note"] = selected_note["note_id"]

# ---------------- GENERATE QUESTIONS ----------------
if st.button("Generate Questions"):
    # REMOVE OLD EDITOR UI IMMEDIATELY
    placeholder = st.empty()

    # CLEAR OLD RESULT
    st.session_state.pop("result", None)

    # FORCE OLD UI TO DISAPPEAR
    placeholder.empty()

    # CLEAR OLD RESULTS
    st.session_state.pop("result", None)

    with st.spinner("Generating questions..."):

        payload = {
            "file_url": selected_note["file_path"]
        }

        try:

            response = requests.post(
                API_URL,
                json=payload,
                timeout=600,
                verify=False
            )

            st.write(
                "Status Code:",
                response.status_code
            )

            if response.status_code == 200:

                data = response.json()

                # REMOVE DUPLICATES
                data = remove_duplicate_questions(data)

                st.success(
                    "Questions generated!"
                )

                # SAVE TEMPORARILY
                st.session_state["result"] = data

                # FORCE UI REFRESH
                st.rerun()

            else:

                st.error("API Error")

                st.text(response.text)

        except requests.exceptions.SSLError:

            st.error(
                "SSL Error. Restart ngrok and update API URL."
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to API server."
            )

        except Exception as e:

            st.error(str(e))

# ---------------- EDITOR UI ----------------
if "result" in st.session_state:

    data = st.session_state["result"]

    st.divider()

    st.subheader(
        "✏️ Edit Generated Content"
    )

    # ---------------- UNIT DETAILS ----------------
    # ---------------- UNIT DETAILS ----------------
    st.markdown("### 📘 Unit Details")

    # GET DIRECTLY FROM NOTES TABLE
    unit_code = selected_note.get("unit_code", "")
    unit_name = selected_note.get("unit_name", "")

    # DISPLAY ONLY
    st.text_input(
        "Unit Code",
        value=unit_code,
        disabled=True
    )

    st.text_input(
        "Unit Name",
        value=unit_name,
        disabled=True
    )

    updated_topics = []

    # ---------------- TOPICS ----------------
    st.markdown("### 📚 Topics")

    for i, topic in enumerate(
        data.get("topics", [])
    ):

        with st.expander(
            f"Topic {i+1}: {topic.get('topic', '')}",
            expanded=True
        ):

            topic_name = st.text_input(
                f"Topic Name {i}",
                value=topic.get("topic", ""),
                key=f"topic_{i}"
            )

            # ---------------- QUESTIONS ----------------
            if "questions" in topic:

                st.markdown("### Questions")

                questions = []

                for j, q in enumerate(
                    topic["questions"]
                ):

                    st.markdown(
                        f"#### Question {j+1}"
                    )

                    # ---------------- HANDLE FORMATS ----------------
                    if isinstance(q, str):

                        question_text = q
                        marks_value = 5
                        type_value = "Short Answer"

                    else:

                        question_text = q.get(
                            "question",
                            ""
                        )

                        marks_value = q.get(
                            "marks",
                            5
                        )

                        type_value = q.get(
                            "question_type",
                            "Short Answer"
                        )

                    # ---------------- DELETE OPTION ----------------
                    delete_question = st.checkbox(
                        f"❌ Delete Question {i+1}.{j+1}",
                        key=f"delete_{i}_{j}"
                    )

                    # SKIP DELETED QUESTION
                    if delete_question:

                        st.warning(
                            "Question will be removed."
                        )

                        continue

                    # ---------------- QUESTION TEXT ----------------
                    edited_q = st.text_area(
                        f"Question Text {i+1}.{j+1}",
                        value=question_text,
                        key=f"q_{i}_{j}"
                    )

                    col1, col2 = st.columns(2)

                    # ---------------- MARKS ----------------
                    with col1:

                        marks = st.number_input(
                            f"Marks {i+1}.{j+1}",
                            min_value=1,
                            max_value=100,
                            value=marks_value,
                            key=f"marks_{i}_{j}"
                        )

                    # ---------------- QUESTION TYPE ----------------
                    with col2:

                        question_type = st.selectbox(
                            f"Question Type {i+1}.{j+1}",
                            QUESTION_TYPES,
                            index=QUESTION_TYPES.index(type_value)
                            if type_value in QUESTION_TYPES
                            else 0,
                            key=f"type_{i}_{j}"
                        )

                    # ---------------- SAVE QUESTION ----------------
                    questions.append({
                        "question": edited_q,
                        "marks": marks,
                        "question_type": question_type
                    })

                updated_topics.append({
                    "topic": topic_name,
                    "questions": questions
                })

            # ---------------- MCQS ----------------
            elif "mcqs" in topic:

                st.markdown("### MCQs")

                mcqs = []

                for j, mcq in enumerate(
                    topic["mcqs"]
                ):

                    delete_mcq = st.checkbox(
                        f"❌ Delete MCQ {i+1}.{j+1}",
                        key=f"delete_mcq_{i}_{j}"
                    )

                    if delete_mcq:

                        st.warning(
                            "MCQ will be removed."
                        )

                        continue

                    edited_mcq = st.text_area(
                        f"MCQ {i+1}.{j+1}",
                        value=str(mcq),
                        key=f"mcq_{i}_{j}"
                    )

                    mcqs.append(edited_mcq)

                updated_topics.append({
                    "topic": topic_name,
                    "mcqs": mcqs
                })

    # ---------------- FINAL OUTPUT ----------------
    final_output = {
        "unit": {
            "unit_code": unit_code,
            "unit_name": unit_name
        },
        "topics": updated_topics
    }

    # ---------------- EXPORT ----------------
    st.divider()

    st.subheader(
        "💾 Export Edited Result"
    )

    st.download_button(
        label="Download JSON",
        data=json.dumps(
            final_output,
            indent=2
        ),
        file_name="edited_questions.json",
        mime="application/json"
    )

    # ---------------- SAVE TO DATABASE ----------------
    if st.button(
        "💾 Save Questions to Database"
    ):

        try:

            # DELETE OLD QUESTIONS
            delete_data(
                "generatedquestions",
                {
                    "note_id": selected_note["note_id"]
                }
            )

            # SAVE NEW QUESTIONS
            for topic in final_output["topics"]:

                topic_name = topic["topic"]

                # ---------------- NORMAL QUESTIONS ----------------
                if "questions" in topic:

                    for q in topic["questions"]:

                        insert_data(
                            "generatedquestions",
                            {
                                "note_id": selected_note["note_id"],
                                "topic": topic_name,
                                "question_text": q["question"],
                                "question_type": q["question_type"],
                                "marks": q["marks"],
                                "difficulty": "Medium"
                            }
                        )

                # ---------------- MCQS ----------------
                elif "mcqs" in topic:

                    for mcq in topic["mcqs"]:

                        insert_data(
                            "generatedquestions",
                            {
                                "note_id": selected_note["note_id"],
                                "topic": topic_name,
                                "question_text": str(mcq),
                                "question_type": "MCQ",
                                "marks": 1,
                                "difficulty": "Medium"
                            }
                        )

            st.success(
                "Questions saved successfully!"
            )

            # OPTIONAL:
            # clear after saving
            st.session_state.pop(
                "result",
                None
            )

        except Exception as e:

            st.error(
                f"Database Error: {str(e)}"
            )

    # ---------------- DEBUG OUTPUT ----------------
    st.divider()

    st.subheader(
        "📦 Final JSON Output"
    )

    st.json(final_output)
