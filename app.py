# https://ai-exam-generator-baufvky4fcevfrrzoatusc.streamlit.app/generated_questions
import streamlit as st
from pathlib import Path
from utils.sidebar import show_sidebar
from db import run_query, execute_query

# ------------------RUN SQL---------------------
user = run_query("SELECT * FROM public.users WHERE user_id = 2")[0]
notes = run_query("SELECT * FROM public.notes where user_id = 2")

username = user["username"]
# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- LOAD CSS ----------------
css_path = Path(__file__).parent / "styles.css"

with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------

show_sidebar()
# ---------------- TOP BAR ----------------
top1, top2 = st.columns([10, 2])

with top1:
    st.markdown("<div class='menu-icon'>☰</div>", unsafe_allow_html=True)

with top2:
    st.markdown(f"""
    <div class='profile-section'>
        🔔
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png'>
        <span>{username}</span>
    </div>
    """, unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("<h1 class='main-title'>Dashboard</h1>", unsafe_allow_html=True)

st.markdown(f"""
<p class='subtitle'>
Welcome back, {username}! Here's what's happening with your exams.
</p>
""", unsafe_allow_html=True)

# ---------------- METRICS ----------------
col1, col2, col3, col4 = st.columns(4)

cards = [
    ("📄", "12", "Notes Uploaded"),
    ("🧠", "45", "Questions Generated"),
    ("📝", "8", "Exams Created"),
    ("⬇", "5", "Exams Downloaded")
]

cols = [col1, col2, col3, col4]

for col, card in zip(cols, cards):
    icon, number, text = card

    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>{icon}</div>
            <div>
                <h2>{number}</h2>
                <p>{text}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------- MAIN SECTION ----------------
left, right = st.columns([1.1, 1])

# -------- RECENT ACTIVITIES --------
activity_html = ""

for note in notes:

    activity_html += f"""
    <div class='activity-item'>
        <span>📕{note["unit_name"]}_{note["original_name"]} uploaded</span>
        <small>
            {note["uploaded_at"].strftime("%d %b %Y, %I:%M %p")}
        </small>
    </div>
    """
with left:

    st.markdown(f"""
    <div class='activity-card'>

    <div class='activity-header'>
    <h3>Recent Activity</h3>
    <button>View All</button>
    </div>

    {activity_html}

    </div>
    """, unsafe_allow_html=True)

# -------- QUICK START --------
with right:
    st.markdown("""
    <div class='quick-card'>
    <div class='quick-content'>
    <h2>Quick Start</h2>
    <p>
    Upload your notes and generate
    exam questions instantly.
    </p>

    <button>⬆ Upload Notes</button>
    </div>

    <div class='quick-image'>
    <img src='https://cdn-icons-png.flaticon.com/512/3767/3767084.png'>
    </div>
    </div>
    """, unsafe_allow_html=True)
