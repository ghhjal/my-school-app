import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام التقارير المدرسية الاحترافي", layout="wide", page_icon="📜")

def get_connection():
    return sqlite3.connect('school_master_data.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- دالة إنشاء ملف PDF بتنسيق جمالي ---
class PDF(FPDF):
    def header(self):
        # إضافة إطار للصفحة
        self.rect(5, 5, 200, 287)
        # العنوان الرئيسي
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 51, 102) # لون أزرق داكن
        self.cell(0, 20, 'STUDENT EVALUATION REPORT', 0, 1, 'C')
        self.set_draw_color(0, 51, 102)
        self.line(10, 30, 200, 30) # خط تحت العنوان
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d")}', 0, 0, 'C')

def create_styled_pdf(student_info, grades_info, behavior_logs):
    pdf = PDF()
    pdf.add_page()
    
    # قسم معلومات الطالب
    pdf.set_fill_color(240, 240, 240) # خلفية رمادية فاتحة
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f" Student Name: {student_info['name']}", ln=True, fill=True)
    pdf.cell(0, 10, f" Student ID: {student_info['id']}  |  Level: {student_info['level']}  |  Class: {student_info['grade_class']}", ln=True, fill=True)
    pdf.ln(10)
    
    # قسم الدرجات
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "ACADEMIC PERFORMANCE", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 12)
    
    if not grades_info.empty:
        # رسم جدول صغير للدرجات
        pdf.cell(60, 10, "Period 1 (20)", 1, 0, 'C')
        pdf.cell(60, 10, "Period 2 (20)", 1, 0, 'C')
        pdf.cell(70, 10, "Tasks & Participation (40)", 1, 1, 'C')
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(60, 15, str(grades_info.iloc[0]['p1']), 1, 0, 'C')
        pdf.cell(60, 15, str(grades_info.iloc[0]['p2']), 1, 0, 'C')
        pdf.cell(70, 15, str(grades_info.iloc[0]['perf']), 1, 1, 'C')
    else:
        pdf.cell(0, 10, "No academic data available.", ln=True)
    
    pdf.ln(10)
    
    # قسم السلوك بجدول ملون
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "BEHAVIOR & OBSERVATIONS LOG", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # ترويسة جدول السلوك
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 10, "Date", 1, 0, 'C', True)
    pdf.cell(30, 10, "Day", 1, 0, 'C', True)
    pdf.cell(30, 10, "Type", 1, 0, 'C', True)
    pdf.cell(100, 10, "Observation / Note", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    
    if not behavior_logs.empty:
        for idx, row in behavior_logs.iterrows():
            pdf.cell(30, 10, row['date'], 1, 0, 'C')
            pdf.cell(30, 10, row['day'], 1, 0, 'C')
            # تلوين النوع
            type_text = "Positive" if "إيجابي" in row['type'] else "Notice"
            pdf.cell(30, 10, type_text, 1, 0, 'C')
            pdf.cell(100, 10, row['note'][:50], 1, 1, 'L')
    else:
        pdf.cell(190, 10, "No behavior notes recorded.", 1, 1, 'C')
        
    return pdf.output(dest='S').encode('latin-1')

# --- المربعات والأدوات والمنطق (نفس كود الإدارة والطالب السابق) ---
# ... (كود تسجيل الدخول والقوائم كما هو في الإصدار السابق) ...

# إضافة زر التحميل في واجهة الطالب:
if st.session_state.logged_in and st.session_state.role == 'student':
    sid = st.session_state.user_id
    info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
    grades = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
    behavior = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(sid,))
    
    st.title(f"🎓 تقرير الطالب: {info['name']}")
    
    # زر التحميل الملون
    pdf_bytes = create_styled_pdf(info, grades, behavior)
    st.download_button(
        label="📥 تحميل الشهادة الرسمية (PDF)",
        data=pdf_bytes,
        file_name=f"Certificate_{info['name']}.pdf",
        mime="application/pdf",
        help="اضغط هنا لتحميل نسخة قابلة للطباعة من تقريرك الدراسي والسلوكي"
    )
    
    # باقي عرض البيانات على Streamlit
    # ...
