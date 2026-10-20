import streamlit as st
import pandas as pd

def student_dashboard(conn):
    col_title, col_logout = st.columns([0.8, 0.2])
    with col_title:
        st.title("🎓 Student Dashboard")
    with col_logout:
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()

    student_id = st.session_state.user_id
    
    with st.container():
        st.subheader("📋 My Details")
        details = pd.read_sql(f"SELECT roll_number, class_name, section FROM Students WHERE user_id={student_id}", conn)
        curr_roll = details['roll_number'][0] if not details.empty else ""
        curr_class = details['class_name'][0] if not details.empty else ""
        curr_sec = details['section'][0] if not details.empty else ""
        
        # Display roll number as disabled (read-only)
        st.text_input("Roll Number", value=curr_roll, disabled=True)
        
        class_options = [str(i) for i in range(1, 13)]
        section_options = [chr(i) for i in range(65, 91)] 
        class_idx = class_options.index(curr_class) if curr_class in class_options else 0
        sec_idx = section_options.index(curr_sec) if curr_sec in section_options else 0
        
        col1, col2 = st.columns(2)
        new_class = col1.selectbox("Class", class_options, index=class_idx)
        new_sec = col2.selectbox("Section", section_options, index=sec_idx)
        
        if st.button("Update Details"):
            c = conn.cursor()
            c.execute(f"UPDATE Students SET class_name='{new_class}', section='{new_sec}' WHERE user_id={student_id}")
            conn.commit()
            st.success("Details updated!")

    st.divider()
    
    with st.container():
        st.subheader("📈 My Attendance")
        
        my_logs = pd.read_sql(f"""
            SELECT al.date, t.subject as Subject, tu.name as Teacher, al.status as Status, t.attendance_required as Req
            FROM AttendanceLogs al 
            JOIN Teachers t ON al.teacher_id = t.user_id
            JOIN Users tu ON t.user_id = tu.id
            WHERE al.student_id={student_id}
            ORDER BY al.date DESC
        """, conn)
        
        if not my_logs.empty:
            my_logs['date'] = pd.to_datetime(my_logs['date']).dt.date
            
            subject_list = ["All Subjects"] + my_logs['Subject'].unique().tolist()
            selected_subject = st.selectbox("Filter by Subject", subject_list)
            
            filtered_logs = my_logs.copy()
            
            if selected_subject != "All Subjects":
                filtered_logs = filtered_logs[filtered_logs['Subject'] == selected_subject]
                target_req = filtered_logs['Req'].iloc[0]
            else:
                target_req = filtered_logs[['Subject', 'Req']].drop_duplicates()['Req'].mean()
                
            total_classes = len(filtered_logs)
            if total_classes > 0:
                present_count = len(filtered_logs[filtered_logs['Status'] == 'Present'])
                attendance_percentage = (present_count / total_classes) * 100
                
                pct_val = float(f"{attendance_percentage:.1f}")
                req_val = float(f"{target_req:.1f}")
                
                if pct_val < req_val:
                    color = "#ff4b4b" # Red
                elif pct_val > req_val:
                    color = "#09ab3b" # Green
                else:
                    color = "#ffc107" # Yellow
                    
                st.markdown(f"### Total Attendance: <span style='color:{color}; font-weight:bold;'>{pct_val}%</span>", unsafe_allow_html=True)
                st.caption(f"Required Target: **{req_val}%** &nbsp;|&nbsp; Classes Attended: **{present_count} / {total_classes}**")
                
                display_df = filtered_logs.drop(columns=['Req'])
                st.dataframe(display_df, hide_index=True, use_container_width=True)
            else:
                st.warning("No attendance records match your selection.")
        else:
            st.info("No attendance records found yet.")