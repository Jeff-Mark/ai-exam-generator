import random
import re

# =====================================================
# FILTER QUESTIONS
# =====================================================


def filter_questions(
    questions,
    difficulty=None,
    question_types=None
):

    filtered = []

    for q in questions:

        # ---------------- DIFFICULTY ----------------
        if difficulty:

            if (
                q.get("difficulty", "").lower()
                != difficulty.lower()
            ):
                continue

        # ---------------- QUESTION TYPE ----------------
        if question_types:

            if (
                q.get("question_type")
                not in question_types
            ):
                continue

        filtered.append(q)

    return filtered


# =====================================================
# GENERATE SECTION QUESTIONS
# =====================================================

def generate_section_questions(
    questions,
    total_marks,
    total_questions
):

    if not questions:
        return []

    random.shuffle(questions)

    selected = []

    # ---------------- MARKS DISTRIBUTION ----------------
    base_marks = total_marks // total_questions

    remaining = total_marks % total_questions

    marks_distribution = [
        base_marks
        for _ in range(total_questions)
    ]

    for i in range(remaining):

        marks_distribution[i] += 1

    # ---------------- SELECT QUESTIONS ----------------
    for i in range(
        min(total_questions, len(questions))
    ):

        q = questions[i]

        selected.append({

            "question_id":
                q.get("question_id"),

            "question_text":
                q.get("question_text", ""),

            "question_type":
                q.get("question_type", ""),

            "assigned_marks":
                marks_distribution[i]
        })

    return selected


# =====================================================
# GENERATE FULL EXAM
# =====================================================

def generate_exam(
    all_questions,
    section_data,
    difficulty
):

    exam = []

    used_ids = set()

    for section in section_data:

        # ---------------- FILTER ----------------
        filtered = []

        for q in all_questions:

            # DIFFICULTY
            if (
                difficulty
                and
                q.get(
                    "difficulty",
                    ""
                ).lower()
                != difficulty.lower()
            ):
                continue

            # QUESTION TYPE
            if (
                q.get("question_type")
                not in section[
                    "question_types"
                ]
            ):
                continue

            # REMOVE USED
            if (
                q["question_id"]
                in used_ids
            ):
                continue

            filtered.append(q)

        # ---------------- GENERATE ----------------
        section_questions = (
            generate_section_questions(

                filtered,

                section["total_marks"],

                section["num_questions"]
            )
        )

        # TRACK USED
        for q in section_questions:

            used_ids.add(
                q["question_id"]
            )

        exam.append({

            "section":
                section["section"],

            "instructions":
                f"Answer all "
                f"{len(section_questions)} "
                f"questions.",

            "total_marks":
                section["total_marks"],

            "questions":
                section_questions
        })

    return exam


# =====================================================
# NORMALIZE QUESTION
# =====================================================

def normalize_question(text):

    if not text:
        return ""

    # LOWERCASE
    text = text.lower()

    # REMOVE PUNCTUATION
    text = re.sub(
        r"[^\w\s]",
        "",
        text
    )

    # REMOVE EXTRA SPACES
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =====================================================
# REMOVE DUPLICATE QUESTIONS
# =====================================================

def remove_duplicate_questions(data):

    seen = set()

    cleaned_topics = []

    for topic in data.get("topics", []):

        updated_topic = {
            "topic": topic.get("topic", ""),
            "questions": []
        }

        # ---------------- QUESTIONS ----------------
        if "questions" in topic:

            for q in topic["questions"]:

                # HANDLE STRING QUESTIONS
                if isinstance(q, str):

                    question_text = q

                    normalized = normalize_question(
                        question_text
                    )

                    if normalized in seen:
                        continue

                    seen.add(normalized)

                    updated_topic[
                        "questions"
                    ].append(q)

                # HANDLE OBJECT QUESTIONS
                else:

                    question_text = q.get(
                        "question",
                        ""
                    )

                    normalized = normalize_question(
                        question_text
                    )

                    if normalized in seen:
                        continue

                    seen.add(normalized)

                    updated_topic[
                        "questions"
                    ].append(q)

        cleaned_topics.append(
            updated_topic
        )

    data["topics"] = cleaned_topics

    return data
