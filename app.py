import streamlit as st

st.set_page_config(page_title="EduTrack | Attendance", page_icon="🏫", layout="wide")

# Updated Custom CSS for Dark Mode Professional UI
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Dark Mode Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

from database import init_db
from auth import auth_page
from teacher import teacher_dashboard
from student import student_dashboard

conn = init_db()

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.role = None

if st.session_state.user_id is None:
    auth_page(conn)
elif st.session_state.role == 'Teacher':
    teacher_dashboard(conn)
elif st.session_state.role == 'Student':
    student_dashboard(conn)