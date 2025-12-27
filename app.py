import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

# --- إعدادات قاعدة البيانات ---
def get_connection():
    return sqlite3.connect('school_master_data.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
# (تأكد من وجود الجداول كما في الكود السابق)

# --- دالة إنشاء PDF احترافي مع شعار ---
class StyledPDF(FPDF):
    def header(self):
        # إضافة شعار المدرسة إذا وجد
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33)
        
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)
        self.cell(80) # إزاحة للوسط
        self.cell(30, 10, 'OFFICIAL STUDENT REPORT', 0, 0, 'C')
        self.ln(20)
        
        # إطار جمالي للصفحة
        self.set_draw_color(0, 51, 102)
        self.rect(5, 5, 200, 287)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()} | This is an automated official document', 0, 0, 'C')

def generate_final_pdf(student_info, grades_info, behavior_logs):
    pdf = StyledPDF()
    pdf.add_page()
    
    # معلومات الطالب في صندوق ملون
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 12, f" NAME: {student_info['name'].upper()}", ln=True, fill=True)
    pdf.cell(0, 10, f" ID: {student_info['id']} | Level: {student_info['level']} | Class: {student_info['grade_class']}", ln=True, fill=True)
    pdf.ln(10)
    
    # جدول الدرجات
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "1. ACADEMIC PERFORMANCE", ln=True)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255)
    pdf.cell(60, 10, "Period 1", 1, 0, 'C', True)
    pdf.cell(60, 10, "Period 2", 1, 0, 'C', True)
    pdf.cell(70, 10, "Tasks & Participation", 1, 1, 'C', True)
    
    pdf.set_text_color(0)
    if not grades_info.empty:
        pdf.cell(60, 12, str(grades_info.iloc[0]['p1']), 1, 0, 'C')
        pdf.cell(60, 12, str(grades_info.iloc[0]['p2']), 1, 1, 'C')
        # الخانة الثالثة (المهام)
        pdf.set_xy(130, 62) # تعديل الإحداثيات لضبط الجدول
        pdf.cell(70, 12, str(grades_info.iloc[0]['perf']), 1, 1, 'C')
    
    pdf.ln(15)
    
    # جدول السلوك
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(200, 0, 0) if not behavior_logs.empty else pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 10, "2. BEHAVIORAL LOG & NOTES", ln=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(100, 100, 100)
    pdf.set_text_color(255)
    pdf.cell(30, 10, "Date", 1, 0, 'C', True)
    pdf.cell(130, 10, "Observation Note", 1, 0, 'C', True)
    pdf.cell(30, 10, "Status", 1, 1, 'C', True)
    
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    if not behavior_logs.empty:
        for _, row in behavior_logs.iterrows():
            pdf.cell(30, 10, row['date'], 1, 0, 'C')
            pdf.cell(130, 10, row['note'][:65], 1, 0, 'L')
            status = "Positive" if "إيجابي" in row['type'] else "Warning"
            pdf.cell(30, 10, status, 1, 1, 'C')
            
    return pdf.output(dest='S').encode('latin-1')

# --- الجزء الخاص بـ Streamlit (التفاعل) ---
# نفس الكود السابق ولكن مع استدعاء generate_final_pdf عند ضغط الطالب على زر التحميل.
