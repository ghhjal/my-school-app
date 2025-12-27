import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

# --- 1. إعدادات قاعدة البيانات ---
def get_connection():
    return sqlite3.connect('school_master_data.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. دالة إنشاء ملف PDF للشهادة ---
def generate_pdf(info, grades, logs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="STUDENT EVALUATION REPORT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Student: {info['name']} | ID: {info['id']}", ln=True)
    pdf.cell(200, 10, txt=f"Class: {info['level']} - {info['grade_class']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Academic Performance", ln=True)
    pdf.set_font("Arial", size=12)
    if not grades.empty:
        pdf.cell(200, 10, txt=f"Period 1: {grades.iloc[0]['p1']} | Period 2: {grades.iloc[0]['p2']} | Tasks: {grades.iloc[0]['perf']}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Behavior Log", ln=True)
    pdf.set_font("Arial", size=10)
    for _, row in logs.iterrows():
        pdf.cell(200, 8, txt=f"- {row['date']}: {row['type']} - {row['note']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. نظام إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 4. واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    tab1, tab2 = st.tabs(["المدير", "الطالب"])
    with tab1:
        pwd = st.text_input("الرمز السري", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with tab2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض نتيجتي"):
            user = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not user.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 5. واجهة التطبيق بعد الدخول ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.update({'logged_in': False, 'role': None})
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.selectbox("القائمة", ["إدارة الطلاب", "رصد الدرجات", "سجل السلوك"])
        
        if menu == "إدارة الطلاب":
            st.header("👥 إضافة وتعديل الطلاب")
            with st.expander("➕ إضافة طالب"):
                with st.form("add"):
                    nid = st.number_input("الرقم", min_value=1)
                    nname = st.text_input("الاسم")
                    nlevel = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    nclass = st.text_input("الصف")
                    if st.form_submit_button("حفظ"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, nclass))
                        conn.commit()
                        st.rerun()
            
            st.write("---")
            df_st = pd.read_sql_query("SELECT * FROM students", conn)
            for _, row in df_st.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{row['name']}** ({row['id']})")
                    if col3.button("🗑️ حذف", key=f"del_{row['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

        elif menu == "رصد الدرجات":
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("اختر الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                with st.form("grades"):
                    p1 = st.number_input("فترة 1 (20)", 0.0, 20.0)
                    p2 = st.number_input("فترة 2 (20)", 0.0, 20.0)
                    perf = st.number_input("مهام ومشاركة (40)", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (sid, p1, p2, perf))
                        conn.commit()
                        st.success("تم الحفظ")

        elif menu == "سجل السلوك":
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                with st.form("beh"):
                    b_date = st.date_input("التاريخ")
                    b_type = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        days = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                        b_day = days[b_date.strftime('%A')]
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (sid, b_date.isoformat(), b_day, b_type, b_note))
                        conn.commit()
                        st.success("تمت الإضافة")

    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        grades = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        behavior = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(sid,))
        
        st.title(f"🎓 تقرير: {info['name']}")
        
        # عرض الدرجات في كروت (Metrics)
        if not grades.empty:
            st.subheader("📊 الدرجات الأكاديمية")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", grades.iloc[0]['p1'])
            c2.metric("الفترة 2", grades.iloc[0]['p2'])
            c3.metric("المهام والمشاركة", grades.iloc[0]['perf'])
        else:
            st.warning("لم يتم رصد درجاتك بعد.")

        # عرض السلوك
        st.subheader("📅 سجل السلوك")
        if not behavior.empty:
            st.table(behavior[['date', 'day', 'type', 'note']])
        
        # زر التحميل PDF
        pdf_bytes = generate_pdf(info, grades, behavior)
        st.download_button("📥 تحميل التقرير PDF", data=pdf_bytes, file_name=f"Report_{info['id']}.pdf", mime="application/pdf")
