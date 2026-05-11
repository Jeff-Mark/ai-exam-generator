from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Supabase connection string
DATABASE_URL = "postgresql://postgres:Jeff326mark!@db.qomonefdzhdxugmvtoou.supabase.co:5432/postgres"

# Create engine once
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)


def get_connection():
    """
    Returns a database connection.
    """
    return engine.connect()


def run_query(query, params=None):

    with get_connection() as conn:

        result = conn.execute(
            text(query),
            params or {}
        )

        return result.mappings().all()


def execute_query(query, params=None):
    """
    Runs INSERT, UPDATE, DELETE queries.

    Example:
        execute_query(
            "INSERT INTO Ai_exam_gen.exams(subject) VALUES (:subject)",
            {"subject": "Math"}
        )
    """
    with get_connection() as conn:
        conn.execute(text(query), params or {})
        conn.commit()
