from supabase import create_client
import os
import streamlit as st

# -----------------------------
# Load credentials (Streamlit Cloud + local support)
# -----------------------------
if "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# -----------------------------
# Create Supabase client
# -----------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- QUERY ----------------


def run_query(table, select="*", filters=None):
    query = supabase.table(table).select(select)

    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)

    return query.execute().data

# ---------------- EXECUTE ----------------


def insert_data(table, data):
    return supabase.table(table).insert(data).execute().data


def update_data(table, filters, data):
    query = supabase.table(table)

    for key, value in filters.items():
        query = query.eq(key, value)

    return query.update(data).execute().data


def delete_data(table, filters):
    query = supabase.table(table)

    for key, value in filters.items():
        query = query.eq(key, value)

    return query.delete().execute().data
