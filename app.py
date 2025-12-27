import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام رصد الدرجات والسلوك", layout="wide", page_icon="📝")

def get_connection():
    return sqlite3.connect('school_system_v5.db', check_same_thread=False)

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
            st.header("👤 تسجيل وتعديل الطلاب")
            with st.form("add_student_form"):
                c1, c2, c3 = st.columns(3)
                nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                nname = c2.text_input("اسم الطالب")
                nlevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?)", (int(nid), nname, nlevel))
                    conn.commit()
                    st.success("تم الحفظ بنجاح")
            
            st.write("---")
            st.subheader("جدول الطلاب المسجلين")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

        elif choice == "رصد الدرجات والسلوك":
            st.header("📝 رصد الدرجات والملاحظات")
            students_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            
            if not students_df.empty:
                s_name = st.selectbox("اختر الطالب", students_df['name'])
                sid = int(students_df[students_df['name'] == s_name]['id'].values[0])
                
                with st.form("grade_form"):
                    st.subheader("📊 درجات اللغة الإنجليزية")
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة الأولى (20)", 0.0, 20.0)
                    p2 = col2.number_input("الفترة الثانية (20)", 0.0, 20.0)
                    perf_part = col3.number_input("المهام والمشاركة (40)", 0.0, 40.0)
                    
                    st.subheader("🎭 السلوك والملاحظات")
                    pos_b = st.text_area("إيجابيات وملاحظات تميز")
                    neg_b = st.text_area("ملاحظات تحتاج تحسين")
                    
                    if st.form_submit_button("حفظ السجل"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?,?,?)", 
                                  (sid, p1, p2, perf_part, pos_b, neg_b))
                        conn.commit()
                        st.success(f"تم حفظ بيانات الطالب {s_name} بنجاح")
            else: st.warning("لا يوجد طلاب مسجلين.")

    elif st.session_state.role == 'student':
        sid = int(st.session_state.user_id)
        name = pd.read_sql_query("SELECT name FROM students WHERE id = ?", conn, params=(sid,)).iloc[0,0]
        
        st.title("🎓 كشف الدرجات والسلوك")
        st.subheader(f"الطالب: {name} | الرقم الأكاديمي: {sid}")

        res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
        
        if not res.empty:
            st.write("---")
            # عرض الدرجات فقط بدون المجموع
            st.subheader("📊 تفاصيل الدرجات")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1 (20)", res.iloc[0]['p1'])
            c2.metric("الفترة 2 (20)", res.iloc[0]['p2'])
            c3.metric("المهام والمشاركة (40)", res.iloc[0]['performance_part'])
            
            # عرض السلوك
            st.write("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.success("🌟 ملاحظات التميز")
                st.write(res.iloc[0]['pos_behavior'] if res.iloc[0]['pos_behavior'] else "لا يوجد")
            with col_b:
                st.error("⚠️ ملاحظات للتحسين")
                st.write(res.iloc[0]['neg_behavior'] if res.iloc[0]['neg_behavior'] else "لا يوجد")
        else:
            st.warning("لم يتم رصد درجاتك بعد.")
