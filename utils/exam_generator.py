import random
import re


# =====================================================
# FILTER QUESTIONS
# =====================================================

def filter_questions(questions, difficulty=None, question_types=None):
    filtered = []
    for q in questions:
        if difficulty:
            if q.get("difficulty", "").lower() != difficulty.lower():
                continue
        if question_types:
            if q.get("question_type") not in question_types:
                continue
        filtered.append(q)
    return filtered


# =====================================================
# GENERATE SECTION QUESTIONS
# =====================================================

def generate_section_questions(questions, total_marks, total_questions):
    if not questions:
        return []

    random.shuffle(questions)

    base_marks         = total_marks // total_questions
    remaining          = total_marks % total_questions
    marks_distribution = [base_marks] * total_questions
    for i in range(remaining):
        marks_distribution[i] += 1

    selected = []
    for i in range(min(total_questions, len(questions))):
        q = questions[i]

        # ── Parse options safely ──────────────────────────────
        # options may arrive as:
        #   - a list   (already parsed)
        #   - a JSON string  (from the DB column)
        #   - None / missing
        raw_options = q.get("options", [])
        if isinstance(raw_options, str):
            try:
                import json
                options = json.loads(raw_options)
            except Exception:
                # fallback: extract A) B) C) D) lines from string
                options = [
                    l.strip() for l in raw_options.splitlines()
                    if l.strip() and l.strip()[0] in "ABCD" and ")" in l
                ]
        else:
            options = raw_options or []

        selected.append({
            "question_id":   q.get("question_id"),
            "question_text": q.get("question_text", ""),
            "question_type": q.get("question_type", ""),
            "assigned_marks": marks_distribution[i],
            # ── These two were missing — the root cause ────────
            "correct_answer": q.get("correct_answer", ""),
            "options":        options,
        })

    return selected


# =====================================================
# GENERATE FULL EXAM
# =====================================================

def generate_exam(all_questions, section_data, difficulty):
    exam     = []
    used_ids = set()

    for section in section_data:

        filtered = []
        for q in all_questions:
            if difficulty and q.get("difficulty", "").lower() != difficulty.lower():
                continue
            if q.get("question_type") not in section["question_types"]:
                continue
            if q["question_id"] in used_ids:
                continue
            filtered.append(q)

        section_questions = generate_section_questions(
            filtered,
            section["total_marks"],
            section["num_questions"],
        )

        for q in section_questions:
            used_ids.add(q["question_id"])

        exam.append({
            "section":      section["section"],
            "instructions": f"Answer all {len(section_questions)} questions.",
            "total_marks":  section["total_marks"],
            "questions":    section_questions,
        })

    return exam


# =====================================================
# NORMALIZE + DEDUPLICATE
# =====================================================

def normalize_question(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_duplicate_questions(data):
    seen           = set()
    cleaned_topics = []

    for topic in data.get("topics", []):
        updated_topic = {"topic": topic.get("topic", "")}

        # ── Normal questions ──────────────────────────────────
        if "questions" in topic:
            updated_topic["questions"] = []
            for q in topic["questions"]:
                text       = q if isinstance(q, str) else q.get("question", "")
                normalized = normalize_question(text)
                if normalized in seen:
                    continue
                seen.add(normalized)
                updated_topic["questions"].append(q)

        # ── MCQs ──────────────────────────────────────────────
        elif "mcqs" in topic:
            updated_topic["mcqs"] = []
            for mcq in topic["mcqs"]:
                text       = mcq.get("question", "") if isinstance(mcq, dict) else str(mcq)
                normalized = normalize_question(text)
                if normalized in seen:
                    continue
                seen.add(normalized)
                updated_topic["mcqs"].append(mcq)

        cleaned_topics.append(updated_topic)

    data["topics"] = cleaned_topics
    return data