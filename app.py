import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام اللغة الإنجليزية - النسخة المصححة", layout="wide", page_icon="🇬🇧")

# --- تهيئة قاعدة البيانات ---
conn = sqlite3.connect('english_system.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, level TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, 
              subject TEXT, 
              p1 REAL, p2 REAL, part REAL, proj REAL, total REAL)''')
conn.commit()

# --- إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- واجهة تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["المدير", "الطالب"])
    with t1:
        if st.text_input("الرمز السري", type="password") == "admin123":
            if st.button("دخول الإدارة"):
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("أدخل رقمك (ID)", min_value=1, step=1)
        if st.button("عرض النتيجة"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("رقم الطالب غير مسجل!")

# --- بعد الدخول ---
else:
    st.sidebar.button("تسجيل الخروج", on_click=logout)

    if st.session_state['role'] == 'admin':
        menu = ["إدارة الطلاب", "رصد الدرجات", "عرض كافة الدرجات"]
        choice = st.sidebar.selectbox("القائمة", menu)

        if choice == "إدارة الطلاب":
            st.header("👥 إضافة طالب")
            with st.form("add"):
                c1, c2, c3 = st.columns(3)
                nid = c1.number_input("الرقم", min_value=1)
                nname = c2.text_input("الاسم")
                nlevel = c3.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?)", (int(nid), nname, nlevel))
                    conn.commit()
                    st.success("تم الحفظ")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

        elif choice == "رصد الدرجات":
            st.header("📝 رصد درجة الإنجليزية")
            students_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not students_df.empty:
                with st.form("grade"):
                    s_select = st.selectbox("اختر الطالب", students_df['name'])
                    # جلب الـ ID الحقيقي للطالب المختار
                    sid = int(students_df[students_df['name'] == s_select]['id'].values[0])
                    col1, col2 = st.columns(2)
                    v1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    v2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    v3 = col1.number_input("المشاركة", 0.0, 10.0)
                    v4 = col2.number_input("المشاريع", 0.0, 10.0)
                    if st.form_submit_button("حفظ الدرجة"):
                        total = v1+v2+v3+v4
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?,?,?,?)", (sid, "English", v1, v2, v3, v4, total))
                        conn.commit()
                        st.success(f"تم الحفظ للطالب رقم {sid}")
            else: st.warning("لا يوجد طلاب")

        elif choice == "عرض كافة الدرجات":
            st.header("📊 مراجعة البيانات المسجلة")
            all_data = pd.read_sql_query("""
                SELECT students.id, students.name, grades.total 
                FROM students 
                JOIN grades ON students.id = grades.student_id
            """, conn)
            st.dataframe(all_data)

    elif st.session_state['role'] == 'student':
        sid = int(st.session_state['user_id'])
        st.title("🎓 كشف درجات اللغة الإنجليزية")
        
        # جلب اسم الطالب
        name_query = pd.read_sql_query("SELECT name FROM students WHERE id = ?", conn, params=(sid,))
        st.subheader(f"الاسم: {name_query.iloc[0,0]} | الرقم: {sid}")
        
        # جلب الدرجات
        res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
        
        if not res.empty:
            st.write("---")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("الفترة 1", res.iloc[0]['p1'])
            col2.metric("الفترة 2", res.iloc[0]['p2'])
            col3.metric("المشاركة", res.iloc[0]['part'])
            col4.metric("المشاريع", res.iloc[0]['proj'])
            st.divider()
            st.metric("المجموع الكلي", f"{res.iloc[0]['total']} / 60")
        else:
            st.error("⚠️ لم يتم العثور على درجات مسجلة لهذا الرقم في قاعدة البيانات.")
