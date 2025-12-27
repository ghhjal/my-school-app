import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- 1. إعداد قاعدة البيانات ---
def get_connection():
    return sqlite3.connect('school_final_storage.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. دالة PDF مبسطة (للمدير فقط) ---
def generate_admin_pdf(info, grades, logs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="OFFICIAL STUDENT REPORT", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Student ID: {info['id']}", ln=True)
    pdf.cell(200, 10, txt=f"Academic Level: {info['level']}", ln=True)
    
    if not grades.empty:
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Grades Summary: P1:{grades.iloc[0]['p1']} | P2:{grades.iloc[0]['p2']} | Tasks:{grades.iloc[0]['perf']}", ln=True)
    
    pdf.ln(10)
    pdf.cell(200, 10, txt="Behavioral History:", ln=True)
    for _, row in logs.iterrows():
        # تنظيف الملاحظات من أي رموز عربية أو تعبيرية تسبب خطأ Unicode
        clean_note = "".join(i for i in row['note'] if ord(i) < 128) if row['note'] else "No English Note"
        pdf.cell(200, 8, txt=f"- Date: {row['date']} | Log: {clean_note}", ln=True)
    
    return pdf.output()

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["الإدارة", "الطالب"])
    with t1:
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("دخول الطالب"):
            u = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not u.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()

# --- 4. واجهات البرنامج ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة", ["إدارة الطلاب", "رصد الدرجات", "سجل السلوك", "طباعة التقارير"])
        
        if menu == "إدارة الطلاب":
            st.header("👥 إدارة بيانات الطلاب")
            with st.form("add_st"):
                c1, c2 = st.columns(2)
                nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                nname = c2.text_input("الاسم")
                nlevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nclass = c2.text_input("الصف")
                if st.form_submit_button("حفظ الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, nclass))
                    conn.commit()
                    st.rerun()
            
            st.divider()
            st.subheader("الطلاب المسجلون (تعديل وحذف)")
            st_list = pd.read_sql_query("SELECT * FROM students", conn)
            for _, row in st_list.iterrows():
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
                target = st.selectbox("اختر الطالب", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("gr"):
                    p1, p2, pf = st.columns(3)
                    v1 = p1.number_input("فترة 1", 0.0, 20.0)
                    v2 = p2.number_input("فترة 2", 0.0, 20.0)
                    vf = pf.number_input("مهام", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tsid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (tsid, v1, v2, vf))
                        conn.commit()
                        st.success("تم الحفظ بنجاح")

        elif menu == "سجل السلوك":
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("الطالب", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("beh"):
                    d = st.date_input("التاريخ")
                    t = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    n = st.text_area("الملاحظة (يفضل كتابة كلمة إنجليزية قصيرة لضمان الطباعة)")
                    if st.form_submit_button("إضافة"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (tsid, d.isoformat(), day_ar[d.strftime('%A')], t, n))
                        conn.commit()
                        st.rerun()

        elif menu == "طباعة التقارير":
            st.header("🖨️ إصدار تقارير PDF للطلاب")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب للطباعة", st_df['name'])
                tsid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(tsid,)).iloc[0]
                gr = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tsid,))
                beh = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(tsid,))
                
                if st.button("توليد ملف PDF"):
                    try:
                        pdf_bytes = generate_admin_pdf(info, gr, beh)
                        st.download_button(f"📥 تحميل تقرير {info['name']}", data=pdf_bytes, file_name=f"Report_{tsid}.pdf", mime="application/pdf")
                    except Exception as e:
                        st.error(f"خطأ في الطباعة: تأكد من عدم وجود رموز غريبة في الملاحظات.")

    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info_df = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,))
        if not info_df.empty:
            info = info_df.iloc[0]
            st.title(f"🎓 كشف درجات: {info['name']}")
            
            g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
            if not g.empty:
                st.subheader("📊 الدرجات")
                c1, c2, c3 = st.columns(3)
                c1.metric("فترة 1", g.iloc[0]['p1'])
                c2.metric("فترة 2", g.iloc[0]['p2'])
                c3.metric("مهام", g.iloc[0]['perf'])
            else:
                st.warning("لم يتم رصد درجات بعد.")
            
            b = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
            if not b.empty:
                st.subheader("📅 سجل السلوك")
                st.table(b)
