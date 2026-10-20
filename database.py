import sqlitecloud
import streamlit as st

def get_connection():
    # Grabs your secure connection string from Streamlit Cloud Secrets
    db_url = st.secrets["DATABASE_URL"]
    
    # check_same_thread=False is omitted as Cloud connections handle this differently
    return sqlitecloud.connect(db_url)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS Schools (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, password TEXT, father TEXT, mother TEXT, age INTEGER, dob TEXT, school_name TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Teachers (user_id INTEGER PRIMARY KEY, subject TEXT, attendance_required INTEGER, FOREIGN KEY(user_id) REFERENCES Users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Students (user_id INTEGER PRIMARY KEY, roll_number TEXT, class_name TEXT, section TEXT, FOREIGN KEY(user_id) REFERENCES Users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Assignments (teacher_id INTEGER, student_id INTEGER, PRIMARY KEY (teacher_id, student_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS AttendanceLogs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, teacher_id INTEGER, student_id INTEGER, status TEXT)''')
    
    conn.commit()
    return conn
