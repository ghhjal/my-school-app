import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- 1. إعداد قاعدة البيانات ---
def get_connection():
    # استخدام اسم جديد للقاعدة لضمان بدء صفحة نظيفة
    return sqlite3.connect('school_final_v10.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. دالة PDF آمنة للمدير ---
def generate_safe_pdf(info, grades, logs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="STUDENT REPORT (ADMIN COPY)", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    # تحويل البيانات لإنجليزية لتجنب خطأ Unicode الظاهر في صورك
    pdf.cell(200, 10, txt=f"Student ID: {info['id']}", ln=True)
    pdf.cell(200, 10, txt=f"Level: {info['level']}", ln=True)
    
    if not grades.empty:
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Grades: P1:{grades.iloc[0]['p1']} | P2:{grades.iloc[0]['p2']} | Tasks:{grades.iloc[0]['perf']}", ln=True)
    
    pdf.ln(10)
    pdf.cell(200, 10, txt="Behavioral Records:", ln=True)
    for _, row in logs.iterrows():
        # تنظيف النص من أي رمز عربي أو إيموجي لضمان عدم تعليق البرنامج
        clean_note = "".join(i for i in str(row['note']) if ord(i) < 128) if row['note'] else "No English Note"
        pdf.cell(200, 8, txt=f"- Date: {row['date']} | Log: {clean_note}", ln=True)
    
    return pdf.output()

# --- 3. نظام الدخول وضبط الواجهة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["المدير", "الطالب"])
    with t1:
        pwd = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("عرض نتيجتي"):
            u = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not u.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل في النظام.")

# --- 4. واجهات البرنامج بعد الدخول ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة الرئيسية", ["إدارة الطلاب", "رصد الدرجات", "سجل السلوك", "طباعة PDF"])
        
        if menu == "إدارة الطلاب":
            st.header("👤 إضافة وتعديل بيانات الطلاب")
            with st.form("new_st"):
                c1, c2 = st.columns(2)
                nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                nname = c2.text_input("اسم الطالب بالكامل")
                nlevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nclass = c2.text_input("الصف الدراسي")
                if st.form_submit_button("إضافة الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, nclass))
                    conn.commit()
                    st.success("تم حفظ بيانات الطالب.")
                    st.rerun()
            
            st.divider()
            st.subheader("قائمة الطلاب (الحذف والتعديل)")
            st_list = pd.read_sql_query("SELECT * FROM students", conn)
            for _, row in st_list.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{row['name']}** - الرقم: {row['id']}")
                    if col3.button("🗑️ حذف", key=f"del_{row['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (row['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

        elif menu == "رصد الدرجات":
            st.header("📝 رصد الدرجات الأكاديمية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("gr_form"):
                    p1, p2, pf = st.columns(3)
                    v1 = p1.number_input("الفترة 1 (20)", 0.0, 20.0)
                    v2 = p2.number_input("الفترة 2 (20)", 0.0, 20.0)
                    vf = pf.number_input("المهام (40)", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tsid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (tsid, v1, v2, vf))
                        conn.commit()
                        st.success(f"تم رصد درجات الطالب: {target}")

        elif menu == "سجل السلوك":
            st.header("📅 رصد السلوك اليومي (جدول)")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("beh_form"):
                    d = st.date_input("تاريخ الموقف")
                    t = st.selectbox("نوع السلوك", ["إيجابي ✅", "سلبي ⚠️"])
                    n = st.text_area("الملاحظة (استخدم الإنجليزية للطباعة)")
                    if st.form_submit_button("إضافة للسجل"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (tsid, d.isoformat(), day_ar[d.strftime('%A')], t, n))
                        conn.commit()
                        st.rerun()

        elif menu == "طباعة PDF":
            st.header("🖨️ إصدار تقارير للمدير")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب لاستخراج تقريره", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(tsid,)).iloc[0]
                gr = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tsid,))
                beh = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(tsid,))
                
                if st.button("تجهيز ملف PDF للطباعة"):
                    try:
                        pdf_bytes = generate_safe_pdf(info, gr, beh)
                        st.download_button(f"📥 تحميل ملف {info['name']}", data=pdf_bytes, file_name=f"Admin_Report_{tsid}.pdf", mime="application/pdf")
                    except Exception as e:
                        st.error("عذراً، هناك رموز غير مدعومة في الملاحظات تمنع الطباعة.")

    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info_df = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,))
        if not info_df.empty:
            info = info_df.iloc[0]
            st.title(f"🎓 التقرير الدراسي لـ: {info['name']}")
            
            g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
            if not g.empty:
                st.subheader("📊 كشف الدرجات")
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة الأولى", g.iloc[0]['p1'])
                c2.metric("الفترة الثانية", g.iloc[0]['p2'])
                c3.metric("المهام والمشاركة", g.iloc[0]['perf'])
            
            st.divider()
            b = pd.read_sql_query("SELECT date as التاريخ, day as اليوم, type as النوع, note as الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
            if not b.empty:
                st.subheader("📅 السجل السلوكي")
                st.table(b)
            else:
                st.info("لا توجد ملاحظات سلوكية مسجلة لك حالياً.")
