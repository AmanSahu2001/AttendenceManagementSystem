import streamlit as st
from datetime import date

def auth_page(conn):
    st.title("🏫 EduTrack Platform")
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab_register:
        st.subheader("Create a New Account")
        role = st.radio("Are you a Teacher or Student?", ["Teacher", "Student"])
        st.divider()
        
        name = st.text_input("Full Name")
        password = st.text_input("Create Password", type="password")
        
        c = conn.cursor()
        c.execute("SELECT name FROM Schools ORDER BY name")
        existing_schools = [row[0] for row in c.fetchall()]
        
        school_options = existing_schools.copy()
        if role == 'Teacher':
            school_options.append("+ Add New School")
            
        if not school_options and role == 'Student':
            st.warning("No schools are registered yet. Please ask a Teacher to register your school first.")
            final_school_name = None
        else:
            selected_option = st.selectbox("Search & Select School", school_options)
            if selected_option == "+ Add New School":
                final_school_name = st.text_input("Enter New School Name")
            else:
                final_school_name = selected_option
                
        col1, col2 = st.columns(2)
        father = col1.text_input("Father's Name")
        mother = col2.text_input("Mother's Name")
        
        dob = st.date_input("Date of Birth", value=None, min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        
        age = 0
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            st.caption(f"Calculated Age: **{age} years**")
        
        if role == 'Teacher':
            subject = st.text_input("Subject")
            attendance_required = st.number_input("Attendance Required (%)", min_value=1, max_value=100, value=75)
        else:
            # ADDED: Roll Number input for students
            roll_number = st.text_input("Roll Number")
            class_options = [str(i) for i in range(1, 13)]
            section_options = [chr(i) for i in range(65, 91)] 
            col_cls, col_sec = st.columns(2)
            class_name = col_cls.selectbox("Class", class_options)
            section = col_sec.selectbox("Section", section_options)
            
        if st.button("Register Account", use_container_width=True):
            # Enforce roll number requirement for students
            if name and password and final_school_name and dob and (role == 'Teacher' or roll_number):
                c.execute("INSERT OR IGNORE INTO Schools (name) VALUES (?)", (final_school_name,))
                c.execute('''INSERT INTO Users (name, password, father, mother, age, dob, school_name, role) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (name, password, father, mother, age, str(dob), final_school_name, role))
                user_id = c.lastrowid
                
                if role == 'Teacher':
                    c.execute("INSERT INTO Teachers (user_id, subject, attendance_required) VALUES (?, ?, ?)", 
                              (user_id, subject, attendance_required))
                else:
                    c.execute("INSERT INTO Students (user_id, roll_number, class_name, section) VALUES (?, ?, ?, ?)", 
                              (user_id, roll_number, class_name, section))
                
                conn.commit()
                st.success("Account created successfully! You can now login.")
            else:
                st.error("Please fill out all required fields, including Roll Number if you are a student.")

    with tab_login:
        st.subheader("Login to Your Account")
        login_name = st.text_input("Name")
        login_pass = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            c = conn.cursor()
            c.execute("SELECT id, role FROM Users WHERE name=? AND password=?", (login_name, login_pass))
            result = c.fetchone()
            
            if result:
                st.session_state.user_id = result[0]
                st.session_state.role = result[1]
                st.rerun()
            else:
                st.error("Invalid Name or Password")