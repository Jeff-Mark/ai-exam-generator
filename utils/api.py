

# ── Standard library ──────────────────────────────────────────
import re
import random
import tempfile
import os
from typing import List

# ── Third-party ───────────────────────────────────────────────
import numpy as np
import faiss
import PyPDF2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer

# ── App setup ─────────────────────────────────────────────────
app = FastAPI(title="Exam Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════
# MODEL LOADING  (happens once at startup)
# ══════════════════════════════════════════════════════════════

print("Loading models…")
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

qa_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
qa_model     = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

para_tokenizer = AutoTokenizer.from_pretrained("ramsrigouthamg/t5_paraphraser")
para_model     = AutoModelForSeq2SeqLM.from_pretrained("ramsrigouthamg/t5_paraphraser")

print("Models ready.")

# ══════════════════════════════════════════════════════════════
# TEXT PROCESSING HELPERS
# ══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    patterns = [
        r"JKUAT", r"SODeL", r"JI", r"JJII", r"JDocDocI", r"Back Close",
        r": Setting trends in higher Education, Research and Innovation",
        r"JOMO KENYATTA UNIVERSITY OF AGRICULTURE TECHNOLOGY",
        r"SCHOOL OF OPEN, DISTANCE AND eLEARNING",
        r"LAST REVISION ON.*?\d{4}",
        r"This presentation is intended.*?solution answer\.",
        r"Errors and omissions.*?mailed to",
    ]
    for p in patterns:
        text = re.sub(p, " ", text, flags=re.IGNORECASE | re.DOTALL)
    replacements = {
        r"\bDi erent\b": "Different", r"\bdi erent\b": "different",
        r"\bDe ne\b": "Define",       r"\bcon-\s*tinue\b": "continue",
        r"\bAIDs\b": "AIDS",          r"\bthere no\b": "there is no",
        r"\bdon know\b": "don't know",
    }
    for old, new in replacements.items():
        text = re.sub(old, new, text)
    text = re.sub(r"\b\d+\b", " ", text)
    text = re.sub(r"[^A-Za-z0-9.,?!:\-\n ]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def split_by_topics(text: str) -> list:
    pattern = r"LESSON\s+\d+\s*\n+([^\n]+)"
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    sections = []
    for i in range(1, len(parts), 2):
        topic   = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append({"topic": topic, "content": content})
    # If no LESSON headings found, treat entire text as one section
    if not sections:
        sections.append({"topic": "General", "content": text})
    return sections


def chunk_text(content: str, size: int = 300, overlap: int = 100) -> list:
    words = content.split()
    step  = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]


def build_index(pdf_bytes: bytes):
    """
    Parse PDF bytes → documents list + FAISS index.
    Returns (documents, faiss_index).
    """
    # Write to a temp file so PyPDF2 can open it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    raw_text = ""
    try:
        with open(tmp_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                raw_text += page.extract_text() or ""
    finally:
        os.unlink(tmp_path)

    sections  = split_by_topics(raw_text)
    documents = []
    for section in sections:
        cleaned = clean_text(section["content"])
        for chunk in chunk_text(cleaned, size=300, overlap=200):
            documents.append({"topic": section["topic"], "content": chunk})

    texts      = [doc["content"] for doc in documents]
    embeddings = embedding_model.encode(texts)
    index      = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))
    return documents, index


# ══════════════════════════════════════════════════════════════
# RETRIEVAL
# ══════════════════════════════════════════════════════════════

def retrieve(question: str, documents: list, index, k: int = 3) -> list:
    q_emb = embedding_model.encode([question])
    _, indices = index.search(np.array(q_emb).astype("float32"), k)
    return [
        f"Topic: {documents[i]['topic']}\n{documents[i]['content']}"
        for i in indices[0] if i < len(documents)
    ]


# ══════════════════════════════════════════════════════════════
# QUESTION CLASSIFICATION
# ══════════════════════════════════════════════════════════════

TRUE_FALSE_RE = re.compile(
    r"\btrue or false\b|\bis it true\b|\bstate whether\b|\btrue\b.*\bfalse\b",
    re.IGNORECASE,
)
LIST_RE = re.compile(
    r"\bwhat are\b|\blist\b|\btypes of\b|\bkinds of\b|\bexamples of\b"
    r"|\bcharacteristics\b|\bfeatures\b|\bstages\b|\bsteps\b|\bcauses\b"
    r"|\beffects\b|\badvantages\b|\bdisadvantages\b",
    re.IGNORECASE,
)

def is_true_false(q: str) -> bool:
    return bool(TRUE_FALSE_RE.search(q))

def is_list_question(q: str) -> bool:
    return bool(LIST_RE.search(q))


# ══════════════════════════════════════════════════════════════
# QUESTION GENERATION
# ══════════════════════════════════════════════════════════════

QUESTION_TEMPLATES = [
    (
        "From the notes below, write one exam question that starts with "
        "'What are' or 'List the'. The question must have multiple answers.\n"
        "Notes: {content}\nQuestion:"
    ),
    (
        "From the notes below, write one exam question that starts with "
        "'Explain' or 'Describe'. Do not use 'Which of the following'.\n"
        "Notes: {content}\nQuestion:"
    ),
    (
        "From the notes below, write one exam question that starts with "
        "'How' or 'Why'. Do not use 'Which of the following'.\n"
        "Notes: {content}\nQuestion:"
    ),
]


def generate_questions_raw(documents: list) -> list:
    """Returns list of {topic, output} dicts — one question string per chunk."""
    results = []
    for i, doc in enumerate(documents):
        template = QUESTION_TEMPLATES[i % len(QUESTION_TEMPLATES)]
        prompt   = template.format(content=doc["content"])
        inputs   = qa_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs  = qa_model.generate(
            **inputs, max_new_tokens=60,
            no_repeat_ngram_size=3, repetition_penalty=1.3,
        )
        result = qa_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        result = re.sub(r"^(question|q\d*)[:\s]+", "", result, flags=re.IGNORECASE).strip()
        if result and not result.endswith("?"):
            result += "?"
        results.append({"topic": doc["topic"], "output": result})
    return results


def filter_and_clean(raw: str, mode: str) -> list:
    bad = ["main idea", "best title", "purpose of this passage",
           "this passage", "according to the passage"]
    candidates = re.split(r"\n+", raw.strip()) if "\n" in raw else [raw.strip()]
    out = []
    for q in candidates:
        q = q.strip()
        if not q or len(q.split()) < 4:
            continue
        if not q.endswith("?"):
            q += "?"
        if any(p in q.lower() for p in bad):
            continue
        if mode == "normal":
            rewrites = [
                (r"which of the following (are|is)", r"What \1"),
                (r"which of the following (were|was)", r"What \1"),
                (r"which (is|are) not", r"What \1"),
                (r"what is NOT", "What is"),
                (r"what are NOT", "What are"),
                (r"true or false[:\s]*", "Is it true that "),
            ]
            for pat, rep in rewrites:
                q = re.sub(pat, rep, q, flags=re.IGNORECASE)
        for word in ["most important", "most common", "best", "primary",
                     "major", "critical", "top", "leading"]:
            q = re.sub(word, "", q, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip()
        if len(q) >= 10 and "http" not in q.lower():
            out.append(q)
    return out


# ══════════════════════════════════════════════════════════════
# ANSWERING — NORMAL MODE
# ══════════════════════════════════════════════════════════════

def _qa_call(prompt: str, max_new_tokens: int = 80,
             do_sample: bool = False, temperature: float = 1.0) -> str:
    inputs  = qa_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    outputs = qa_model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else 1.0,
        top_k=50 if do_sample else None,
        no_repeat_ngram_size=3,
        repetition_penalty=1.3,
    )
    return qa_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def answer_normal(question: str, documents: list, index) -> dict:
    context = " ".join(retrieve(question, documents, index))

    if is_true_false(question):
        verdict = _qa_call(
            f"Answer True or False only.\nQuestion: {question}\nNotes: {context}\nAnswer (True or False):",
            max_new_tokens=5,
        )
        verdict = "True" if "true" in verdict.lower() else "False"
        defence = _qa_call(
            f"Explain why the statement is {verdict}. Use the notes below.\n"
            f"Statement: {question}\nNotes: {context}\nExplanation:",
            max_new_tokens=120,
        )
        return {"type": "true_false", "verdict": verdict, "defence": defence}

    if is_list_question(question):
        point_prompts = [
            f"Name one answer to: {question} Notes: {context} Answer:",
            f"Give another answer to: {question} Notes: {context} Answer:",
            f"What else answers: {question} Notes: {context} Answer:",
            f"List one item for: {question} Notes: {context} Item:",
            f"Another item for: {question} Notes: {context} Item:",
        ]
        seen, points = set(), []
        for prompt in point_prompts:
            raw = _qa_call(prompt, max_new_tokens=30, do_sample=True, temperature=0.85)
            raw = re.split(r"[.\n]", raw)[0].strip()
            if raw and raw.lower() not in seen and len(raw.split()) >= 2:
                points.append(raw)
                seen.add(raw.lower())
        return {"type": "list", "points": points or ["See notes"]}

    answer = _qa_call(
        f"Answer from the notes only. Question: {question} Notes: {context} Answer:",
        max_new_tokens=80,
    )
    return {"type": "plain", "answer": answer}


# ══════════════════════════════════════════════════════════════
# ANSWERING — MCQ MODE
# ══════════════════════════════════════════════════════════════

def _ask_short(prompt: str) -> str:
    inputs  = qa_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=400)
    outputs = qa_model.generate(
        **inputs, max_new_tokens=30,
        do_sample=True, temperature=0.9, top_k=50, repetition_penalty=1.4,
    )
    raw = qa_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    return re.split(r"[.\n]", raw)[0].strip()


def answer_mcq(question: str, documents: list, index) -> dict:
    context = " ".join(retrieve(question, documents, index))

    # Correct answer
    correct = _qa_call(
        f"Answer from the notes only. Question: {question} Notes: {context} Answer:",
        max_new_tokens=60,
    )

    # Distractors
    fallbacks = ["None of the above", "All of the above",
                 "It cannot be determined", "The notes do not specify"]
    phrasings = [
        f"What is something related to but different from '{correct}'? Notes: {context}",
        f"Name a different term related to this question: {question} Notes: {context}",
        f"What is another concept mentioned in these notes? Notes: {context}",
    ]
    seen, distractors = {correct.lower()}, []
    for attempt in range(15):
        if len(distractors) >= 3:
            break
        candidate = _ask_short(phrasings[attempt % len(phrasings)])
        if candidate and candidate.lower() not in seen and len(candidate.split()) >= 2:
            distractors.append(candidate)
            seen.add(candidate.lower())
    for fb in fallbacks:
        if len(distractors) >= 3:
            break
        if fb.lower() not in seen:
            distractors.append(fb)

    all_options = [correct] + distractors[:3]
    random.shuffle(all_options)
    letters  = ["A", "B", "C", "D"]
    options  = [f"{letters[i]}) {opt}" for i, opt in enumerate(all_options)]
    answer   = f"{letters[all_options.index(correct)]}) {correct}"

    return {"type": "mcq", "options": options, "answer": answer}


# ══════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════

def run_pipeline_sync(pdf_bytes: bytes, mode: str) -> list:
    documents, index = build_index(pdf_bytes)
    raw_items = generate_questions_raw(documents)
    results   = []

    for item in raw_items:
        questions = filter_and_clean(item["output"], mode)
        for q in questions:
            record = {"topic": item["topic"], "question": q, "mode": mode}
            if mode == "normal":
                record.update(answer_normal(q, documents, index))
            else:
                record.update(answer_mcq(q, documents, index))
            results.append(record)

    return results


# ══════════════════════════════════════════════════════════════
# PARAPHRASE
# ══════════════════════════════════════════════════════════════

def paraphrase_sync(questions: list, num_variants: int) -> list:
    output = []
    for question in questions:
        input_text = f"paraphrase: {question} </s>"
        inputs = para_tokenizer(
            input_text, return_tensors="pt",
            truncation=True, max_length=256, padding="max_length",
        )
        raw_outputs = para_model.generate(
            **inputs,
            max_new_tokens=128,
            num_beams=max(num_variants * 3, 6),
            num_return_sequences=num_variants,
            temperature=1.5,
            do_sample=True,
            repetition_penalty=1.3,
            no_repeat_ngram_size=2,
        )
        variants = []
        for out in raw_outputs:
            decoded = para_tokenizer.decode(out, skip_special_tokens=True).strip()
            if decoded and not decoded.endswith("?"):
                decoded += "?"
            variants.append(decoded)
        output.append({"original": question, "variants": variants})
    return output


# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════

@app.get("/")
def health():
    return {"status": "running"}


@app.post("/generate")
async def generate(
    file: UploadFile = File(..., description="PDF notes file"),
    mode: str        = Form("mcq", description="'normal' or 'mcq'"),
):
    """
    Upload a PDF and choose a mode.

    Returns:
        {
          "mode": "normal" | "mcq",
          "count": int,
          "results": [
            # Normal list question
            {"topic": str, "question": str, "mode": "normal",
             "type": "list", "points": [str, ...]},

            # Normal plain question
            {"topic": str, "question": str, "mode": "normal",
             "type": "plain", "answer": str},

            # Normal true/false question
            {"topic": str, "question": str, "mode": "normal",
             "type": "true_false", "verdict": str, "defence": str},

            # MCQ question
            {"topic": str, "question": str, "mode": "mcq",
             "type": "mcq",
             "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
             "answer": "B) ..."},
          ]
        }
    """
    if mode not in ("normal", "mcq"):
        raise HTTPException(status_code=400, detail="mode must be 'normal' or 'mcq'")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()

    # Run the heavy CPU work off the async event loop
    results = await run_in_threadpool(run_pipeline_sync, pdf_bytes, mode)

    return {"mode": mode, "count": len(results), "results": results}


class ParaphraseRequest(BaseModel):
    questions:    List[str]
    num_variants: int = 1


@app.post("/paraphrase")
async def paraphrase(body: ParaphraseRequest):
    """
    Reword a list of questions.

    Body:
        {
          "questions": ["What are the types of EJB?", ...],
          "num_variants": 2
        }

    Returns:
        {
          "results": [
            {"original": "What are the types of EJB?",
             "variants": ["Which types does EJB define?", "How many EJB types exist?"]},
            ...
          ]
        }
    """
    if not body.questions:
        raise HTTPException(status_code=400, detail="questions list cannot be empty")
    if not (1 <= body.num_variants <= 5):
        raise HTTPException(status_code=400, detail="num_variants must be between 1 and 5")

    results = await run_in_threadpool(paraphrase_sync, body.questions, body.num_variants)
    return {"results": results}


# ══════════════════════════════════════════════════════════════
# COLAB STARTUP CELL  (paste this into a new Colab cell)
# ══════════════════════════════════════════════════════════════
#
#   !pip install fastapi uvicorn pyngrok nest_asyncio PyPDF2 \
#               transformers sentence-transformers faiss-cpu torch
#
#   import nest_asyncio, threading, uvicorn
#   from pyngrok import ngrok
#
#   nest_asyncio.apply()
#   ngrok.kill()
#
#   # Import the app (if this file is saved as api.py):
#   # from api import app
#   # OR paste everything above into the cell, then:
#
#   def run():
#       uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
#
#   threading.Thread(target=run, daemon=True).start()
#   public_url = ngrok.connect(8000)
#   print("API URL:", public_url)
#
