import streamlit as st


def show_sidebar():

    st.sidebar.markdown("""
    <div class='logo-section'>
        <img src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png' width='55'>
        <h2>AI Exam<br>Generator</h2>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.page_link("pages/dashboard.py", label="🏠 Dashboard")
    st.sidebar.page_link("pages/upload_notes.py", label="⬆ Upload Notes")
    st.sidebar.page_link(
        "pages/generated_questions.py",
        label="📄 Generated Questions"
    )

    st.sidebar.page_link(
        "pages/generate_questions.py",
        label="📝 Generate Questions"
    )
    st.sidebar.page_link(
        "pages/exam_settings.py",
        label="⚙ Exam Settings"
    )
    st.sidebar.page_link(
        "pages/exam_preview.py",
        label="📝 Exam Paper"
    )
    st.sidebar.page_link(
        "pages/saved_exam.py",
        label="📝 Saved Exam Papers"
    )
    st.sidebar.page_link(
        "pages/registration.py",
        label="🚪 Registration"
    )
    if st.sidebar.button("🚪 Logout"):

        # Clear session data
        st.session_state.clear()

        # Redirect to login/home page
        st.switch_page("app.py")
