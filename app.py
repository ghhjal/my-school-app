# --- 4. واجهة الطالب (تصميم جمالي ملون) ---
elif st.session_state.role == "student":
    st.title(f"🎓 لوحة الطالب: {st.session_state.student_name}")
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("الصف الدراسي", my_info["الصف"])
    c2.metric("المرحلة", my_info["المرحلة"])
    c3.metric("المادة المسجلة", my_info["المادة"])
    
    st.divider()
    st.subheader("📊 تقرير الدرجات")
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    if not my_grades.empty: st.table(my_grades)
    else: st.info("لم ترصد درجات حتى الآن.")
        
    st.divider()
    st.subheader("🎭 السجل السلوكي")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            # تحديد اللون بناءً على نوع السلوك
            if "إيجابي" in row["النوع"]:
                st.success(f"📅 {row['التاريخ']} | ✅ {row['النوع']} : {row['الملاحظة']}")
            else:
                st.error(f"📅 {row['التاريخ']} | ❌ {row['النوع']} : {row['الملاحظة']}")
    else: 
        st.success("سجلك السلوكي متميز وخالٍ من الملاحظات!")
