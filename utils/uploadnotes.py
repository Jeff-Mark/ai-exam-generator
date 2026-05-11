from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# Create client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_file(file_name, file_data):
    """
    Uploads a file to Supabase Storage.

    Example:
        upload_file(
            uploaded_file.name,
            uploaded_file.getvalue()
        )
    """

    response = supabase.storage.from_("notes").upload(
        file_name,
        file_data
    )

    return response


def get_file_url(file_name):
    """
    Returns public URL of uploaded file.

    Example:
        url = get_file_url("notes", "math.pdf")
    """

    return supabase.storage.from_("notes").get_public_url(file_name)
