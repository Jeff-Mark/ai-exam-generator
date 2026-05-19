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
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- CONFIG ----------------
load_css()

API_BASE_URL = "https://decal-spindle-unpaid.ngrok-free.dev"

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
notes = run_query("notes", filters={"user_id": user_id})

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
    st.session_state.pop("generation_mode", None)
    st.session_state["last_note"] = selected_note["note_id"]

# ================================================================
# QUESTION MODE SELECTOR
# ================================================================
st.divider()
st.subheader("⚙️ Generation Settings")

col_mode1, col_mode2 = st.columns(2)

with col_mode1:
    mode_label = st.radio(
        "Question Type",
        options=["Normal Questions", "MCQ (Multiple Choice)"],
        index=0,
        help=(
            "**Normal Questions** — open-ended questions with bullet-point answers, "
            "true/false with defence, or plain short answers.\n\n"
            "**MCQ** — multiple-choice questions with A/B/C/D options and an answer key."
        ),
    )

# Map label → API mode value
api_mode = "normal" if mode_label == "Normal Questions" else "mcq"

with col_mode2:
    st.info(
        "**Normal mode** generates:\n"
        "- List questions → numbered bullet answers\n"
        "- True/False → verdict + explanation\n"
        "- Plain questions → single answer"
        if api_mode == "normal"
        else
        "**MCQ mode** generates:\n"
        "- A / B / C / D options\n"
        "- Correct answer key included\n"
        "- Distractors from the same notes"
    )

st.divider()

# ================================================================
# GENERATE QUESTIONS
# ================================================================
if st.button("🚀 Generate Questions", type="primary"):
    placeholder = st.empty()
    st.session_state.pop("result", None)
    st.session_state.pop("generation_mode", None)
    placeholder.empty()

    with st.spinner(f"Generating {mode_label}… this may take a few minutes."):
        try:
            file_path = selected_note["file_path"]

            # ── Fetch the PDF from wherever it is stored ──────────
            # Option A: file_path is a URL (Supabase storage, S3, etc.)
            # Option B: file_path is a local path on the same machine
            if file_path.startswith("http"):
                file_response = requests.get(
                    file_path, timeout=60, verify=False)
                file_response.raise_for_status()
                pdf_bytes = file_response.content
                filename = file_path.split("/")[-1] or "notes.pdf"
            else:
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                filename = file_path.split("/")[-1] or "notes.pdf"

            # ── Send to the API ────────────────────────────────────
            response = requests.post(
                f"{API_BASE_URL}/generate",
                files={"file": (filename, pdf_bytes, "application/pdf")},
                data={"mode": api_mode},
                timeout=1200,
                verify=False,
                # localtunnel compat
                headers={"bypass-tunnel-reminder": "true"},
            )

            st.write("Status Code:", response.status_code)

            if response.status_code == 200:
                raw = response.json()

                # ── Normalise API response → UI format ─────────────
                # API returns:
                #   { "mode": "normal"|"mcq", "count": N, "results": [...] }
                # Each result:
                #   Normal list:  { topic, question, type:"list",      points:[...] }
                #   Normal plain: { topic, question, type:"plain",     answer:str }
                #   Normal T/F:   { topic, question, type:"true_false",verdict,defence }
                #   MCQ:          { topic, question, type:"mcq",       options:[...], answer:str }
                #
                # UI expects: { "topics": [ { "topic": str, "questions"|"mcqs": [...] } ] }

                

                results = raw.get("results", [])
                returned_mode = raw.get("mode", api_mode)

                
                # Group by topic
                topics_map = {}
                for item in results:
                    t = item.get("topic", "General")
                    topics_map.setdefault(t, []).append(item)

                
                
                if returned_mode == "mcq":
                    # Build MCQ-style topics
                    topics = []
                    for topic_name, items in topics_map.items():
                        mcqs = []
                        for item in items:
                            mcqs.append({
                                "question": item.get("question", ""),
                                "options":  item.get("options", []),
                                "answer":   item.get("answer", ""),
                            })
                        topics.append({"topic": topic_name, "mcqs": mcqs})
                    data = {"topics": topics}
                else:
                    # Build normal-style topics
                    topics = []
                    for topic_name, items in topics_map.items():
                        questions = []
                        for item in items:
                            q_type = item.get("type", "plain")
                            q_text = item.get("question", "")
                            if q_type == "list":
                                points = item.get("points", [])
                                answer = "\n".join(
                                    f"{k+1}. {p}" for k, p in enumerate(points)
                                )
                            elif q_type == "true_false":
                                verdict = item.get("verdict", "")
                                defence = item.get("defence", "")
                                answer = f"{verdict}. {defence}"
                            else:
                                answer = item.get("answer", "")

                            questions.append({
                                "question":      q_text,
                                "answer":        answer,
                                "marks":         5,
                                "question_type": "MCQ" if q_type == "mcq"
                                                 else ("True/False" if q_type == "true_false"
                                                       else "Short Answer"),
                            })
                        topics.append(
                            {"topic": topic_name, "questions": questions})
                    data = {"topics": topics}

                

                st.success(
                    f"✅ {raw.get('count', len(results))} questions generated "
                    f"({'MCQ' if returned_mode == 'mcq' else 'Normal'} mode)!"
                )

                st.session_state["result"] = data
                st.session_state["generation_mode"] = returned_mode

            else:
                st.error(f"API Error ({response.status_code})")
                st.text(response.text)

        except requests.exceptions.SSLError:
            st.error("SSL Error. Restart ngrok and update API_BASE_URL.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to API server. Is Colab running?")
        except FileNotFoundError:
            st.error(
                f"Could not find the notes file at: {selected_note['file_path']}")
        except Exception as e:
            st.error(str(e))

# ================================================================
# EDITOR UI
# ================================================================
if "result" in st.session_state:

    data = st.session_state["result"]
    generation_mode = st.session_state.get("generation_mode", "normal")

    st.divider()
    st.subheader("✏️ Edit Generated Content")

    # Mode badge
    badge = "🔵 MCQ Mode" if generation_mode == "mcq" else "🟢 Normal Mode"
    st.markdown(f"**Generation mode:** {badge}")

    # ---------------- UNIT DETAILS ----------------
    st.markdown("### 📘 Unit Details")
    unit_code = selected_note.get("unit_code", "")
    unit_name = selected_note.get("unit_name", "")
    st.text_input("Unit Code", value=unit_code, disabled=True)
    st.text_input("Unit Name", value=unit_name, disabled=True)

    updated_topics = []

    # ---------------- TOPICS ----------------
    st.markdown("### 📚 Topics")

    for i, topic in enumerate(data.get("topics", [])):

        with st.expander(
            f"Topic {i+1}: {topic.get('topic', '')}",
            expanded=True
        ):
            topic_name = st.text_input(
                f"Topic Name {i}",
                value=topic.get("topic", ""),
                key=f"topic_{i}"
            )

            # ── NORMAL QUESTIONS ─────────────────────────────────
            if "questions" in topic:
                st.markdown("#### 📝 Questions")
                questions = []

                for j, q in enumerate(topic["questions"]):

                    st.markdown(f"**Question {j+1}**")

                    if isinstance(q, str):
                        question_text = q
                        answer_text = ""
                        marks_value = 5
                        type_value = "Short Answer"
                    else:
                        question_text = q.get("question", "")
                        answer_text = q.get("answer", "")
                        marks_value = q.get("marks", 5)
                        type_value = q.get("question_type", "Short Answer")

                    delete_q = st.checkbox(
                        f"❌ Delete Question {i+1}.{j+1}",
                        key=f"delete_{i}_{j}"
                    )
                    if delete_q:
                        st.warning("Question will be removed.")
                        continue

                    edited_q = st.text_area(
                        f"Question Text {i+1}.{j+1}",
                        value=question_text,
                        key=f"q_{i}_{j}"
                    )

                    # Show answer (read-only, collapsible)
                    if answer_text:
                        with st.expander("📋 View Answer"):
                            st.markdown(answer_text)

                    col1, col2 = st.columns(2)
                    with col1:
                        marks = st.number_input(
                            f"Marks {i+1}.{j+1}",
                            min_value=1, max_value=100,
                            value=marks_value,
                            key=f"marks_{i}_{j}"
                        )
                    with col2:
                        question_type = st.selectbox(
                            f"Question Type {i+1}.{j+1}",
                            QUESTION_TYPES,
                            index=QUESTION_TYPES.index(type_value)
                            if type_value in QUESTION_TYPES else 0,
                            key=f"type_{i}_{j}"
                        )

                    questions.append({
                        "question":      edited_q,
                        "answer":        answer_text,
                        "marks":         marks,
                        "question_type": question_type,
                    })

                updated_topics.append(
                    {"topic": topic_name, "questions": questions})

            # ── MCQ ───────────────────────────────────────────────
            elif "mcqs" in topic:
                st.markdown("#### 🔘 MCQs")
                mcqs = []

                for j, mcq in enumerate(topic["mcqs"]):

                    delete_mcq = st.checkbox(
                        f"❌ Delete MCQ {i+1}.{j+1}",
                        key=f"delete_mcq_{i}_{j}"
                    )
                    if delete_mcq:
                        st.warning("MCQ will be removed.")
                        continue

                    # mcq is a dict: {question, options, answer}
                    if isinstance(mcq, dict):
                        q_text = mcq.get("question", "")
                        options = mcq.get("options", [])
                        answer = mcq.get("answer", "")
                    else:
                        q_text = str(mcq)
                        options = []
                        answer = ""

                    edited_q = st.text_area(
                        f"MCQ Question {i+1}.{j+1}",
                        value=q_text,
                        key=f"mcq_q_{i}_{j}"
                    )

                    # Display options (editable)
                    edited_options = []
                    for k, opt in enumerate(options):
                        edited_opt = st.text_input(
                            f"Option {k+1}",
                            value=opt,
                            key=f"mcq_opt_{i}_{j}_{k}"
                        )
                        edited_options.append(edited_opt)

                    # Correct answer (read-only badge)
                    if answer:
                        st.success(f"✅ Correct Answer: {answer}")

                    mcqs.append({
                        "question": edited_q,
                        "options":  edited_options,
                        "answer":   answer,
                    })

                updated_topics.append({"topic": topic_name, "mcqs": mcqs})

    # ---------------- FINAL OUTPUT ----------------
    final_output = {
        "unit":   {"unit_code": unit_code, "unit_name": unit_name},
        "mode":   generation_mode,
        "topics": updated_topics,
    }

    # ---------------- EXPORT ----------------
    st.divider()
    st.subheader("💾 Export Edited Result")

    st.download_button(
        label="⬇️ Download JSON",
        data=json.dumps(final_output, indent=2),
        file_name="edited_questions.json",
        mime="application/json",
    )

    # ---------------- SAVE TO DATABASE ----------------
    if st.button("💾 Save Questions to Database"):

        try:

            # DELETE OLD QUESTIONS
            delete_data(
                "generatedquestions",
                {
                    "note_id": selected_note["note_id"]
                }
            )

            # SAVE QUESTIONS
            for topic in final_output["topics"]:

                topic_name = topic["topic"]

                # =========================================
                # NORMAL QUESTIONS
                # =========================================
                if "questions" in topic:

                    for q in topic["questions"]:

                        # ---------------- SAVE QUESTION ----------------
                        saved_question = insert_data(
                            "generatedquestions",
                            {
                                "note_id":
                                    selected_note["note_id"],

                                "topic":
                                    topic_name,

                                "question_text":
                                    q["question"],

                                "question_type":
                                    q["question_type"],

                                "marks":
                                    q["marks"],

                                "difficulty":
                                    "Medium"
                            }
                        )

                        # GET QUESTION ID
                        question_id = (
                            saved_question[0]["question_id"]
                        )

                        # ---------------- SAVE ANSWER ----------------
                        insert_data(
                            "question_answers",
                            {
                                "question_id":
                                    question_id,

                                "correct_answer":
                                    q.get("answer", "")
                            }
                        )

                # =========================================
                # MCQS
                # =========================================
                elif "mcqs" in topic:

                    for mcq in topic["mcqs"]:

                        if isinstance(mcq, dict):

                            q_text = mcq.get(
                                "question",
                                ""
                            )

                            options = mcq.get(
                                "options",
                                []
                            )

                            answer = mcq.get(
                                "answer",
                                ""
                            )

                            # SAVE QUESTION
                            saved_question = insert_data(
                                "generatedquestions",
                                {
                                    "note_id":
                                        selected_note["note_id"],

                                    "topic":
                                        topic_name,

                                    "question_text":
                                        q_text,

                                    "question_type":
                                        "MCQ",

                                    "marks":
                                        1,

                                    "difficulty":
                                        "Medium"
                                }
                            )

                            question_id = (
                                saved_question[0]["question_id"]
                            )

                            # SAFE OPTION ACCESS
                            option_a = (
                                options[0]
                                if len(options) > 0
                                else ""
                            )

                            option_b = (
                                options[1]
                                if len(options) > 1
                                else ""
                            )

                            option_c = (
                                options[2]
                                if len(options) > 2
                                else ""
                            )

                            option_d = (
                                options[3]
                                if len(options) > 3
                                else ""
                            )

                            # SAVE ANSWERS
                            insert_data(
                                "question_answers",
                                {
                                    "question_id":
                                        question_id,

                                    "correct_answer":
                                        answer,

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

                st.success(
                    "✅ Questions saved successfully!"
                )

                st.session_state.pop(
                    "result",
                    None
                )

        except Exception as e:

            st.error(
                f"Database Error: {str(e)}"
            )

