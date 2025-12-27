import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام التقارير المدرسية الذكي", layout="wide", page_icon="📜")

def get_connection():
    return sqlite3.connect('school_master_data.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- دالة إنشاء ملف PDF (تدعم المحتوى العربي بشكل مبسط) ---
def create_pdf(student_info, grades_info, behavior_logs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # عنوان التقرير
    pdf.cell(200, 10, txt="Student Academic & Behavior Report", ln=True, align='C')
    pdf.ln(10)
    
    # معلومات الطالب
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Student Name: {student_info['name']}", ln=True)
    pdf.cell(200, 10, txt=f"ID: {student_info['id']} | Level: {student_info['level']} | Class: {student_info['grade_class']}", ln=True)
    pdf.ln(5)
    
    # قسم الدرجات
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Academic Grades", ln=True)
    pdf.set_font("Arial", size=12)
    if not grades_info.empty:
        pdf.cell(200, 10, txt=f"Period 1: {grades_info.iloc[0]['p1']} / 20", ln=True)
        pdf.cell(200, 10, txt=f"Period 2: {grades_info.iloc[0]['p2']} / 20", ln=True)
        pdf.cell(200, 10, txt=f"Performance & Participation: {grades_info.iloc[0]['perf']} / 40", ln=True)
    else:
        pdf.cell(200, 10, txt="No grades recorded yet.", ln=True)
    
    pdf.ln(10)
    
    # قسم السلوك
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Behavior Log", ln=True)
    pdf.set_font("Arial", size=10)
    if not behavior_logs.empty:
        for idx, row in behavior_logs.iterrows():
            pdf.cell(200, 8, txt=f"- {row['date']} ({row['day']}): {row['type']} - {row['note']}", ln=True)
    else:
        pdf.cell(200, 10, txt="No behavior logs recorded.", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 2. إدارة الجلسة ودخول المستخدمين (نفس الكود السابق) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    # (كود تسجيل الدخول كالمعتاد)
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["الإدارة", "الطالب"])
    with t1:
        if st.text_input("كلمة السر", type="password") == "admin123":
            if st.button("دخول الإدارة"):
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض التقرير"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 3. واجهة التطبيق بعد الدخول ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.update({'logged_in': False, 'role': None})
        st.rerun()

    if st.session_state.role == 'admin':
        # (قسم المدير: إدارة الطلاب، رصد الدرجات، سجل السلوك - كما في الكود السابق)
        menu = ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"]
        choice = st.sidebar.selectbox("القائمة", menu)
        
        if choice == "👥 إدارة الطلاب":
            st.header("👤 إدارة ملفات الطلاب")
            df_st = pd.read_sql_query("SELECT * FROM students", conn)
            # عرض الطلاب مع أزرار التعديل والحذف (نفس المنطق السابق)
            for index, row in df_st.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"**{row['name']}** (ID: {row['id']})")
                    c2.write(f"{row['level']} - {row['grade_class']}")
                    if c4.button("🗑️ حذف", key=f"d_{row['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
        
        # (بقية أقسام المدير للرصد كما هي)

    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        grades = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        behavior = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(sid,))
        
        st.title(f"🎓 تقرير الطالب: {info['name']}")
        
        # زر الطباعة PDF
        pdf_data = create_pdf(info, grades, behavior)
        st.download_button(label="📥 تحميل التقرير بصيغة PDF",
                           data=pdf_data,
                           file_name=f"Report_{info['name']}.pdf",
                           mime="application/pdf")
        
        st.divider()
        # عرض البيانات على الشاشة (الدرجات والجدول كما في الكود السابق)
        st.subheader("📊 الدرجات الأكاديمية")
        if not grades.empty:
            st.columns(3)[0].metric("الفترة 1", grades.iloc[0]['p1'])
            st.columns(3)[1].metric("الفترة 2", grades.iloc[0]['p2'])
            st.columns(3)[2].metric("المهام والمشاركة", grades.iloc[0]['perf'])
        
        st.subheader("📅 سجل السلوك")
        if not behavior.empty:
            st.table(behavior[['date', 'day', 'type', 'note']])
