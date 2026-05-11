import os
from supabase import create_client

try:
    import streamlit as st
    HAS_STREAMLIT = True
except:
    HAS_STREAMLIT = False


# ---------------- CONFIG ----------------
if HAS_STREAMLIT and "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
else:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- UPLOAD ----------------
def upload_file(file_name, file_data):
    response = supabase.storage.from_("notes").upload(
        file_name,
        file_data,
        {
            "upsert": "true",
            "content-type": "application/octet-stream"
        }
    )
    return response


# ---------------- GET URL ----------------
def get_file_url(file_name):
    data = supabase.storage.from_("notes").get_public_url(file_name)
    return data["publicURL"]
