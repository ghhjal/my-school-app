import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المطور", layout="wide", page_icon="🎓")

def get_connection():
    return sqlite3.connect('school_system_final.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, p1 REAL, p2 REAL, performance_part REAL, 
              pos_behavior TEXT, neg_behavior TEXT)''')
conn.commit()

# --- 2. إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 نظام الإدارة المدرسية")
    t1, t2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("دخول الطالب"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("عذراً، الرقم غير مسجل")

# --- 4. واجهة التطبيق بعد الدخول ---
else:
    st.sidebar.button("تسجيل الخروج", on_click=logout)

    if st.session_state.role == 'admin':
        menu = ["إدارة الطلاب", "رصد الدرجات والسلوك"]
        choice = st.sidebar.selectbox("القائمة الإدارية", menu)

        if choice == "إدارة الطلاب":
            st.header("👤 إدارة الطلاب (إضافة / تعديل / حذف)")
            
            # قسم الإضافة
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("add_form"):
                    c1, c2, c3 = st.columns(3)
                    nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                    nname = c2.text_input("اسم الطالب")
                    nlevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    if st.form_submit_button("إضافة الطالب"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?)", (int(nid), nname, nlevel))
                        conn.commit()
                        st.success("تمت الإضافة بنجاح")
                        st.rerun()

            st.write("---")
            
            # عرض الطلاب مع خيارات التعديل والحذف
            df_students = pd.read_sql_query("SELECT * FROM students", conn)
            if not df_students.empty:
                st.subheader("قائمة الطلاب الحالية")
                for index, row in df_students.iterrows():
                    with st.container(border=True):
                        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
                        col1.write(f"ID: {row['id']}")
                        col2.write(f"الاسم: {row['name']}")
                        col3.write(f"المرحلة: {row['level']}")
                        
                        # زر التعديل
                        if col4.button("تعديل", key=f"edit_{row['id']}"):
                            st.session_state[f"editing_{row['id']}"] = True
                        
                        # زر الحذف
                        if col5.button("حذف", key=f"del_{row['id']}"):
                            c.execute("DELETE FROM students WHERE id = ?", (row['id'],))
                            c.execute("DELETE FROM grades WHERE student_id = ?", (row['id'],))
                            conn.commit()
                            st.warning(f"تم حذف الطالب {row['name']} بنجاح")
                            st.rerun()

                        # نموذج التعديل (يظهر فقط عند الضغط على زر تعديل)
                        if st.session_state.get(f"editing_{row['id']}", False):
                            with st.form(key=f"form_edit_{row['id']}"):
                                up_name = st.text_input("الاسم الجديد", value=row['name'])
                                up_level = st.selectbox("المرحلة الجديدة", ["ابتدائي", "متوسط", "ثانوي"], index=["ابتدائي", "متوسط", "ثانوي"].index(row['level']))
                                if st.form_submit_button("تحديث البيانات"):
                                    c.execute("UPDATE students SET name=?, level=? WHERE id=?", (up_name, up_level, row['id']))
                                    conn.commit()
                                    st.session_state[f"editing_{row['id']}"] = False
                                    st.success("تم التحديث")
                                    st.rerun()
            else:
                st.info("لا يوجد طلاب مسجلين حالياً.")

        elif choice == "رصد الدرجات والسلوك":
            # (نفس كود رصد الدرجات السابق لضمان الاستمرارية)
            st.header("📝 رصد الدرجات والملاحظات")
            students_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not students_df.empty:
                s_name = st.selectbox("اختر الطالب", students_df['name'])
                sid = int(students_df[students_df['name'] == s_name]['id'].values[0])
                with st.form("grade_form"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    perf_part = col3.number_input("المهام والمشاركة", 0.0, 40.0)
                    pos_b = st.text_area("إيجابيات")
                    neg_b = st.text_area("ملاحظات للتحسين")
                    if st.form_submit_button("حفظ"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?,?,?)", (sid, p1, p2, perf_part, pos_b, neg_b))
                        conn.commit()
                        st.success("تم الحفظ")
            else: st.warning("أضف طلاباً أولاً")

    elif st.session_state.role == 'student':
        # (نفس كود الطالب السابق)
        sid = int(st.session_state.user_id)
        name_df = pd.read_sql_query("SELECT name FROM students WHERE id = ?", conn, params=(sid,))
        st.title("🎓 كشف الدرجات والسلوك")
        if not name_df.empty:
            st.subheader(f"الطالب: {name_df.iloc[0,0]} | الرقم: {sid}")
            res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
            if not res.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة 1", res.iloc[0]['p1'])
                c2.metric("الفترة 2", res.iloc[0]['p2'])
                c3.metric("المهام والمشاركة", res.iloc[0]['performance_part'])
                st.write("---")
                ca, cb = st.columns(2)
                ca.success(f"🌟 إيجابيات: {res.iloc[0]['pos_behavior']}")
                cb.error(f"⚠️ تحسين: {res.iloc[0]['neg_behavior']}")
            else: st.warning("لم ترصد درجات بعد")
