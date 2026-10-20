import streamlit as st
import pandas as pd
from datetime import date

def teacher_dashboard(conn):
    teacher_id = st.session_state.user_id
    
    c = conn.cursor()
    c.execute(f"SELECT subject, attendance_required FROM Teachers WHERE user_id={teacher_id}")
    subject_row = c.fetchone()
    teacher_subject = subject_row[0] if subject_row else "Unassigned"
    current_req = subject_row[1] if subject_row else 75

    col_title, col_logout = st.columns([0.8, 0.2])
    with col_title:
        st.title("Teacher Dashboard")
        st.caption(f"Assigned Subject: **{teacher_subject}**")
    with col_logout:
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()

    with st.expander("⚙️ Settings: Update Attendance Requirement"):
        new_req = st.number_input("Required Attendance (%)", min_value=1, max_value=100, value=int(current_req))
        if st.button("Save Requirement"):
            c.execute(f"UPDATE Teachers SET attendance_required={new_req} WHERE user_id={teacher_id}")
            conn.commit()
            st.success(f"Requirement updated to {new_req}%!")
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 View & Track", "👥 Assign Students", "📝 Edit Past Records"])
    
    c.execute(f"""
        SELECT DISTINCT s.class_name, s.section 
        FROM Students s 
        JOIN Assignments a ON s.user_id = a.student_id 
        WHERE a.teacher_id = {teacher_id}
    """)
    assigned_class_sec = c.fetchall()

    with tab1:
        st.subheader("Daily Tracking & Percentages")
        today = str(date.today())
        
        if assigned_class_sec:
            classes_t1 = sorted(list(set([row[0] for row in assigned_class_sec])))
            col1, col2 = st.columns(2)
            selected_class_t1 = col1.selectbox("Filter by Class", classes_t1, key="t1_class")
            sections_t1 = sorted(list(set([row[1] for row in assigned_class_sec if row[0] == selected_class_t1])))
            selected_sec_t1 = col2.selectbox("Filter by Section", sections_t1, key="t1_sec")
            
            # ADDED: Fetches roll_number from Students table
            assigned = pd.read_sql(f"""
                SELECT u.id, s.roll_number as 'Roll No.', u.name as 'Name'
                FROM Users u 
                JOIN Assignments a ON u.id = a.student_id 
                JOIN Students s ON u.id = s.user_id
                WHERE a.teacher_id = {teacher_id}
                AND s.class_name = '{selected_class_t1}' 
                AND s.section = '{selected_sec_t1}'
            """, conn)

            if not assigned.empty:
                st.write(f"Mark attendance for **{today}**:")
                
                existing_attendance = pd.read_sql(f"""
                    SELECT student_id, status FROM AttendanceLogs
                    WHERE date = '{today}' AND teacher_id = {teacher_id}
                """, conn)
                
                if not existing_attendance.empty:
                    assigned = assigned.merge(existing_attendance, left_on='id', right_on='student_id', how='left')
                    assigned['status'] = assigned['status'].fillna('Present')
                    assigned = assigned[['id', 'Roll No.', 'Name', 'status']]
                else:
                    assigned['status'] = 'Present'
                
                # Hidden the internal 'id', added status dropdown
                edited_df = st.data_editor(assigned, hide_index=True, use_container_width=True, column_config={
                    "id": None, 
                    "status": st.column_config.SelectboxColumn("Status", options=["Present", "Absent", "Late"])
                })
                
                st.markdown("##### 📅 Today's Overview")
                total_p = len(edited_df[edited_df['status'] == 'Present'])
                total_a = len(edited_df[edited_df['status'] == 'Absent'])
                total_l = len(edited_df[edited_df['status'] == 'Late'])
                
                met1, met2, met3, met4 = st.columns(4)
                met1.metric("Total Assigned", len(assigned))
                met2.metric("✅ Present", total_p)
                met3.metric("❌ Absent", total_a)
                met4.metric("⏱️ Late", total_l)

                if st.button("Save Today's Attendance", type="primary"):
                    c = conn.cursor()
                    c.execute(f"""
                        DELETE FROM AttendanceLogs 
                        WHERE date='{today}' AND teacher_id={teacher_id} 
                        AND student_id IN (
                            SELECT user_id FROM Students 
                            WHERE class_name='{selected_class_t1}' AND section='{selected_sec_t1}'
                        )
                    """)
                    for _, row in edited_df.iterrows():
                        c.execute(f"INSERT INTO AttendanceLogs (date, teacher_id, student_id, status) VALUES ('{today}', {teacher_id}, {row['id']}, '{row['status']}')")
                    conn.commit()
                    st.success(f"Saved attendance for Class {selected_class_t1}-{selected_sec_t1}!")

                st.divider()
                st.subheader(f"Historical Stats ({selected_class_t1}-{selected_sec_t1})")
                stats = pd.read_sql(f"""
                    SELECT s.roll_number as 'Roll No.', u.name as 'Name',
                           COUNT(CASE WHEN al.status='Present' THEN 1 END) as 'Total Present',
                           COUNT(CASE WHEN al.status='Absent' THEN 1 END) as 'Total Absent',
                           COUNT(CASE WHEN al.status='Present' THEN 1 END) * 100.0 / NULLIF(COUNT(al.id), 0) as percentage
                    FROM Assignments a
                    JOIN Users u ON a.student_id = u.id
                    JOIN Students s ON u.id = s.user_id
                    LEFT JOIN AttendanceLogs al ON a.student_id = al.student_id AND a.teacher_id = al.teacher_id
                    WHERE a.teacher_id = {teacher_id}
                    AND s.class_name = '{selected_class_t1}'
                    AND s.section = '{selected_sec_t1}'
                    GROUP BY u.name
                """, conn)
                st.dataframe(stats.fillna(0).style.format({"percentage": "{:.1f}%"}), hide_index=True, use_container_width=True)
        else:
            st.info("You haven't assigned any students yet. Go to the 'Assign Students' tab.")

    with tab2:
        st.subheader("Assign Students to Your Subject")
        c = conn.cursor()
        c.execute(f"SELECT school_name FROM Users WHERE id={teacher_id}")
        teacher_school = c.fetchone()[0]
        
        c.execute(f"""
            SELECT DISTINCT s.class_name, s.section 
            FROM Students s JOIN Users u ON s.user_id = u.id 
            WHERE u.school_name='{teacher_school}'
        """)
        class_sec_data = c.fetchall()
        
        if class_sec_data:
            available_classes = sorted(list(set([row[0] for row in class_sec_data])))
            col1, col2 = st.columns(2)
            selected_class = col1.selectbox("Filter by Class", available_classes, key="t2_class")
            selected_section = col2.selectbox("Filter by Section", sorted(list(set([row[1] for row in class_sec_data if row[0] == selected_class]))), key="t2_sec")
            
            # Fetch Roll Number for the Assignment dropdown
            class_students = pd.read_sql(f"""
                SELECT u.id, s.roll_number, u.name 
                FROM Users u JOIN Students s ON u.id = s.user_id 
                WHERE u.role='Student' AND u.school_name='{teacher_school}' 
                AND s.class_name='{selected_class}' AND s.section='{selected_section}'
            """, conn)
            
            class_students['display_name'] = class_students['roll_number'].astype(str) + " - " + class_students['name']
            
            current_assigned_in_class = pd.read_sql(f"""
                SELECT u.id FROM Users u 
                JOIN Assignments a ON u.id = a.student_id 
                JOIN Students s ON u.id = s.user_id
                WHERE a.teacher_id={teacher_id} 
                AND s.class_name='{selected_class}' AND s.section='{selected_section}'
            """, conn)
            
            current_assigned_ids = current_assigned_in_class['id'].tolist() if not current_assigned_in_class.empty else []
            default_selection = class_students[class_students['id'].isin(current_assigned_ids)]['display_name'].tolist()
            
            selected_display_names = st.multiselect(f"Select Students from Class {selected_class}-{selected_section}:", 
                                      class_students['display_name'].tolist(), 
                                      default=default_selection)
                                      
            if st.button("Update Roster for this Section", type="primary"):
                selected_ids = class_students[class_students['display_name'].isin(selected_display_names)]['id'].tolist()
                
                c.execute(f"""
                    DELETE FROM Assignments 
                    WHERE teacher_id={teacher_id} 
                    AND student_id IN (SELECT user_id FROM Students WHERE class_name='{selected_class}' AND section='{selected_section}')
                """)
                for sid in selected_ids:
                    c.execute(f"INSERT INTO Assignments (teacher_id, student_id) VALUES ({teacher_id}, {sid})")
                conn.commit()
                st.rerun()
        else:
            st.info("No students registered in this school yet.")

    with tab3:
        st.subheader("Edit Past Records")
        if assigned_class_sec:
            edit_date = st.date_input("Select Date")
            
            classes_t3 = sorted(list(set([row[0] for row in assigned_class_sec])))
            col1, col2 = st.columns(2)
            selected_class_t3 = col1.selectbox("Filter by Class", classes_t3, key="t3_class")
            sections_t3 = sorted(list(set([row[1] for row in assigned_class_sec if row[0] == selected_class_t3])))
            selected_sec_t3 = col2.selectbox("Filter by Section", sections_t3, key="t3_sec")
            
            past_records = pd.read_sql(f"""
                SELECT al.id as log_id, s.roll_number as 'Roll No.', u.name as 'Name', al.status as 'Status'
                FROM AttendanceLogs al 
                JOIN Users u ON al.student_id = u.id
                JOIN Students s ON u.id = s.user_id
                WHERE al.date='{edit_date}' AND al.teacher_id={teacher_id}
                AND s.class_name='{selected_class_t3}' AND s.section='{selected_sec_t3}'
            """, conn)
            
            if not past_records.empty:
                edited_past = st.data_editor(past_records, hide_index=True, use_container_width=True, column_config={
                    "log_id": None,
                    "Status": st.column_config.SelectboxColumn("Status", options=["Present", "Absent", "Late"])
                })
                if st.button("Update Records", type="primary"):
                    c = conn.cursor()
                    for _, row in edited_past.iterrows():
                        c.execute(f"UPDATE AttendanceLogs SET status='{row['Status']}' WHERE id={row['log_id']}")
                    conn.commit()
                    st.success("Updated!")
            else:
                st.info("No records found for this date and section.")
        else:
            st.info("You haven't assigned any students yet. Go to the 'Assign Students' tab.")