# --- استبدل قسم واجهة الطالب بهذا الكود المطور ---
elif st.session_state['role'] == 'student':
    st.title("🎓 كشف الدرجات التفصيلي")
    sid = int(st.session_state['user_id']) # التأكد من أنه رقم صحيح
    
    # جلب معلومات الطالب للتأكد من الاتصال
    student_data = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(sid,))
    
    if not student_data.empty:
        s_info = student_data.iloc[0]
        st.success(f"مرحباً {s_info['name']} (رقمك: {sid})")
        
        # جلب الدرجات مع التأكد من الربط الصحيح
        query = "SELECT subject, period_1, period_2, participation, projects, total FROM grades WHERE student_id = ?"
        df_grades = pd.read_sql_query(query, conn, params=(sid,))
        
        if not df_grades.empty:
            st.subheader("تفاصيل درجات اللغة الإنجليزية")
            st.table(df_grades) # عرض الجدول
            
            # عرض المجموع بشكل بارز
            total_score = df_grades['total'].iloc[0]
            st.metric("المجموع من 60", f"{total_score}")
        else:
            st.warning("⚠️ لم يتم رصد درجات لك بعد. يرجى مراجعة الإدارة.")
    else:
        st.error("خطأ في جلب بيانات الطالب.")
