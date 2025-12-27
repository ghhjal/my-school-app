import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام مدرستي المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    # قاعدة بيانات موحدة لضمان عدم ضياع البيانات
    return sqlite3.connect('school_master_data.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
# إنشاء الجداول الأساسية
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🛡️ بوابة الدخول")
    tab1, tab2 = st.tabs(["الإدارة", "الطالب"])
    with tab1:
        if st.text_input("كلمة السر", type="password") == "admin123":
            if st.button("دخول المدير"):
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with tab2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض التقرير"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 4. واجهة التطبيق ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.update({'logged_in': False, 'role': None})
        st.rerun()

    if st.session_state.role == 'admin':
        menu = ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"]
        choice = st.sidebar.selectbox("القائمة", menu)

        # --- قسم إدارة الطلاب (تعديل وحذف) ---
        if choice == "👥 إدارة الطلاب":
            st.header("👤 إدارة ملفات الطلاب")
            
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("new_student"):
                    c1, c2 = st.columns(2)
                    nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                    nname = c2.text_input("اسم الطالب")
                    nlevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    ngrade = c2.text_input("الصف الدراسي")
                    if st.form_submit_button("حفظ"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, ngrade))
                        conn.commit()
                        st.rerun()

            st.write("---")
            st.subheader("قائمة الطلاب (تعديل وحذف)")
            df_st = pd.read_sql_query("SELECT * FROM students", conn)
            
            for index, row in df_st.iterrows():
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    col1.write(f"**{row['name']}** (ID: {row['id']})")
                    col2.write(f"{row['level']} - {row['grade_class']}")
                    
                    if col3.button("📝 تعديل", key=f"edit_{row['id']}"):
                        st.session_state[f"is_editing_{row['id']}"] = True
                    
                    if col4.button("🗑️ حذف", key=f"del_{row['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (row['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
                    
                    # نموذج التعديل في حال الضغط على زر تعديل
                    if st.session_state.get(f"is_editing_{row['id']}", False):
                        with st.form(f"form_{row['id']}"):
                            u_name = st.text_input("الاسم", value=row['name'])
                            u_grade = st.text_input("الصف", value=row['grade_class'])
                            if st.form_submit_button("تحديث"):
                                c.execute("UPDATE students SET name=?, grade_class=? WHERE id=?", (u_name, u_grade, row['id']))
                                conn.commit()
                                st.session_state[f"is_editing_{row['id']}"] = False
                                st.rerun()

        # --- قسم رصد الدرجات ---
        elif choice == "📝 رصد الدرجات":
            st.header("الدرجات الأكاديمية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                with st.form("grades"):
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = c2.number_input("الفترة 2", 0.0, 20.0)
                    perf = c3.number_input("المهام والمشاركة", 0.0, 40.0)
                    if st.form_submit_button("حفظ"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (sid, p1, p2, perf))
                        conn.commit()
                        st.success("تم الحفظ")

        # --- قسم سجل السلوك (الجدول الموثق) ---
        elif choice == "📅 سجل السلوك":
            st.header("سجل المواقف السلوكية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                with st.form("behavior"):
                    b_date = st.date_input("التاريخ")
                    # مصفوفة الأيام بالعربي
                    days = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                    b_day = days[b_date.strftime('%A')]
                    b_type = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة للسجل"):
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (sid, b_date.isoformat(), b_day, b_type, b_note))
                        conn.commit()
                        st.success("تمت الإضافة")
                
                # عرض الجدول للمدير للتأكد
                logs = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
                st.table(logs)

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"🎓 تقرير: {info['name']}")
        st.write(f"الصف: {info['grade_class']} | المرحلة: {info['level']}")
        
        # عرض الدرجات
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g.empty:
            st.subheader("📊 الدرجات")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g.iloc[0]['p1'])
            c2.metric("الفترة 2", g.iloc[0]['p2'])
            c3.metric("المهام والمشاركة", g.iloc[0]['perf'])
        
        # عرض السلوك في جدول
        st.subheader("📅 سجل السلوك والملاحظات")
        b_logs = pd.read_sql_query("SELECT date as التاريخ, day as اليوم, type as النوع, note as الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_logs.empty:
            st.table(b_logs)
        else:
            st.write("لا يوجد ملاحظات مسجلة.")
