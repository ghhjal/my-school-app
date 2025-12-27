import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الرصد الموثق", layout="wide", page_icon="📅")

def get_connection():
    return sqlite3.connect('school_system_v7.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
# جدول الطلاب
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)''')
# جدول الدرجات
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, p1 REAL, p2 REAL, performance_part REAL)''')
# جدول السلوك الجديد (يدعم اليوم والتاريخ)
c.execute('''CREATE TABLE IF NOT EXISTS behavior_logs 
             (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)''')
conn.commit()

# --- 2. إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 نظام الإدارة المدرسية الموثق")
    t1, t2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("دخول الطالب"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 4. واجهة التطبيق بعد الدخول ---
else:
    st.sidebar.button("تسجيل الخروج", on_click=logout)

    if st.session_state.role == 'admin':
        menu = ["إدارة الطلاب", "رصد الدرجات", "رصد السلوك (جدول)"]
        choice = st.sidebar.selectbox("القائمة", menu)

        if choice == "إدارة الطلاب":
            st.header("👤 إدارة ملفات الطلاب")
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("add_form"):
                    nid = st.number_input("الرقم الأكاديمي", min_value=1)
                    nname = st.text_input("اسم الطالب")
                    nlevel = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    ngrade = st.text_input("الصف الدراسي (مثلاً: ثاني متوسط)")
                    if st.form_submit_button("حفظ"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, ngrade))
                        conn.commit()
                        st.success("تم الحفظ")
                        st.rerun()
            
            df_st = pd.read_sql_query("SELECT * FROM students", conn)
            st.dataframe(df_st, use_container_width=True)

        elif choice == "رصد الدرجات":
            st.header("📝 رصد درجات الفترات والمهام")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("اختر الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                with st.form("g_form"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    perf = col3.number_input("المهام والمشاركة", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (sid, p1, p2, perf))
                        conn.commit()
                        st.success("تم الحفظ")
            else: st.warning("لا يوجد طلاب")

        elif choice == "رصد السلوك (جدول)":
            st.header("📅 سجل السلوك والملاحظات اليومي")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("اختر الطالب لرصد سلوك", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                
                with st.form("b_form"):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    b_date = c1.date_input("التاريخ", datetime.now())
                    # تحديد اليوم تلقائياً من التاريخ
                    days_ar = {"Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
                               "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
                    b_day = days_ar[b_date.strftime('%A')]
                    c2.text_input("اليوم", value=b_day, disabled=True)
                    b_type = c3.selectbox("نوع السلوك", ["إيجابي ✅", "سلبي ⚠️"])
                    
                    b_note = st.text_area("الملاحظة السلوكية")
                    
                    if st.form_submit_button("إضافة للملف السلوكي"):
                        c.execute("INSERT INTO behavior_logs VALUES (?,?,?,?,?)", 
                                  (sid, b_date.strftime('%Y-%m-%d'), b_day, b_type, b_note))
                        conn.commit()
                        st.success("تمت إضافة الملاحظة للجدول")
                
                # عرض سجل الطالب الحالي للمدير
                st.subheader(f"السجل السلوكي الحالي لـ {s_name}")
                logs = pd.read_sql_query("SELECT date as التاريخ, day as اليوم, type as النوع, note as الملاحظة FROM behavior_logs WHERE student_id = ?", conn, params=(sid,))
                st.table(logs)
                if st.button("مسح سجل السلوك لهذا الطالب"):
                    c.execute("DELETE FROM behavior_logs WHERE student_id = ?", (sid,))
                    conn.commit()
                    st.rerun()

    elif st.session_state.role == 'student':
        sid = int(st.session_state.user_id)
        info = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 التقرير الدراسي الشامل: {info['name']}")
        st.info(f"المرحلة: {info['level']} | الصف: {info['grade_class']}")
        
        # عرض الدرجات
        res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
        if not res.empty:
            st.subheader("📊 الدرجات الأكاديمية")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", res.iloc[0]['p1'])
            c2.metric("الفترة 2", res.iloc[0]['p2'])
            c3.metric("المهام والمشاركة", res.iloc[0]['performance_part'])
        
        # عرض جدول السلوك (الميزة الجديدة)
        st.write("---")
        st.subheader("📅 سجل المواقف السلوكية (اليوم والتاريخ)")
        logs = pd.read_sql_query("SELECT date as التاريخ, day as اليوم, type as النوع, note as الملاحظة FROM behavior_logs WHERE student_id = ?", conn, params=(sid,))
        
        if not logs.empty:
            # تلوين الجدول (اختياري) وعرضه
            st.table(logs)
        else:
            st.write("لا توجد ملاحظات سلوكية مسجلة حتى الآن.")
