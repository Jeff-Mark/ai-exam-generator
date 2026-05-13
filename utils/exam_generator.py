import random


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
