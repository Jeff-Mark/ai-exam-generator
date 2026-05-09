import streamlit as st
from pathlib import Path
from utils.sidebar import show_sidebar

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
    st.markdown("""
    <div class='profile-section'>
        🔔
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png'>
        <span>John Doe</span>
    </div>
    """, unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("<h1 class='main-title'>Dashboard</h1>", unsafe_allow_html=True)

st.markdown("""
<p class='subtitle'>
Welcome back, John! Here's what's happening with your exams.
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
with left:
    st.markdown("""
    <div class='activity-card'>
    <div class='activity-header'>
    <h3>Recent Activity</h3>
    <button>View All</button>
    </div>

    <div class='activity-item'>
    <span>📕 Data Structures Notes.pdf uploaded</span>
    <small>2 hours ago</small>
    </div>

    <div class='activity-item'>
    <span>📙 Operating Systems Notes.txt uploaded</span>
    <small>1 day ago</small>
    </div>

    <div class='activity-item'>
    <span>📘 Machine Learning Exam generated</span>
    <small>2 days ago</small>
    </div>

    <div class='activity-item'>
    <span>📗 AI Fundamentals Exam downloaded</span>
    <small>3 days ago</small>
    </div>
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
