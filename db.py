from sqlalchemy import create_engine, text
import os

try:
    import streamlit as st
    HAS_STREAMLIT = True
except:
    HAS_STREAMLIT = False


# ---------------- LOAD DATABASE URL ----------------
if HAS_STREAMLIT and "DATABASE_URL" in st.secrets:
    DATABASE_URL = st.secrets["DATABASE_URL"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# ---------------- ENGINE ----------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# ---------------- CONNECTION ----------------


def get_connection():
    return engine.connect()

# ---------------- QUERY ----------------


def run_query(query, params=None):
    with get_connection() as conn:
        result = conn.execute(text(query), params or {})
        return result.mappings().all()

# ---------------- EXECUTE ----------------


def execute_query(query, params=None):
    with get_connection() as conn:
        conn.execute(text(query), params or {})
        conn.commit()
