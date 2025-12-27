import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام مدرستي المحمي", layout="wide", page_icon="🔐")

# --- تهيئة قاعدة البيانات ---
conn = sqlite3.connect('school_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, level TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, subject TEXT, grade REAL, 
             FOREIGN KEY(student_id) REFERENCES students(id))''')
conn.commit()

# --- إدارة الجلسة (Login Session) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- دالة تسجيل الخروج ---
def logout():
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['user_id'] = None
    st.rerun()

# --- شاشة تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.title("🛡️ بوابة الدخول للنظام التعليمي")
    
    tab1, tab2 = st.tabs(["تسجيل دخول المدير", "دخول الطالب"])
    
    with tab1:
        admin_password = st.text_input("أدخل الرقم السري للمدير", type="password")
        if st.button("دخول الإدارة"):
            if admin_password == "admin123": # يمكنك تغيير كلمة السر هنا
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'admin'
                st.rerun()
            else:
                st.error("كلمة السر خاطئة!")
                
    with tab2:
        student_id_input = st.number_input("أدخل رقمك الأكاديمي (ID)", min_value=1, step=1)
        if st.button("عرض درجاتي"):
            # التحقق من وجود الطالب في القاعدة
            check = pd.read_sql_query(f"SELECT * FROM students WHERE id = {student_id_input}", conn)
            if not check.empty:
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'student'
                st.session_state['user_id'] = student_id_input
                st.rerun()
            else:
                st.error("رقم الطالب غير مسجل في النظام!")

# --- منطق التطبيق بعد تسجيل الدخول ---
else:
    st.sidebar.warning(f"مرحباً بك: {st.session_state['role'].upper()}")
    if st.sidebar.button("تسجيل الخروج"):
        logout()

    # --- 1. واجهة المدير (Admin) ---
    if st.session_state['role'] == 'admin':
        menu = ["لوحة التحكم", "إدارة الطلاب", "رصد الدرجات", "حذف بيانات"]
        choice = st.sidebar.selectbox("القائمة الإدارية", menu)

        if choice == "لوحة التحكم":
            st.title("📊 التقارير العامة")
            df_all = pd.read_sql_query('''SELECT students.name, grades.subject, grades.grade 
                                         FROM students JOIN grades ON students.id = grades.student_id''', conn)
            if not df_all.empty:
                fig = px.bar(df_all, x="name", y="grade", color="subject", barmode="group")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات حالياً.")

        elif choice == "إدارة الطلاب":
            st.header("👤 إضافة وتعديل الطلاب")
            col1, col2 = st.columns([1, 2])
            with col1:
                s_id = st.number_input("رقم الطالب", min_value=1)
                s_name = st.text_input("اسم الطالب")
                s_level = st.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"])
                if st.button("حفظ"):
                    try:
                        c.execute("INSERT INTO students VALUES (?,?,10,?)", (s_id, s_name, s_level))
                        conn.commit()
                        st.success("تم الحفظ")
                    except: st.error("الرقم موجود مسبقاً!")
            with col2:
                df = pd.read_sql_query("SELECT * FROM students", conn)
                st.dataframe(df)

        elif choice == "رصد الدرجات":
            st.header("📝 إدخال الدرجات")
            df_s = pd.read_sql_query("SELECT id, name FROM students", conn)
            s_choice = st.selectbox("اختر الطالب", df_s['name'])
            s_id = df_s[df_s['name'] == s_choice]['id'].values[0]
            subj = st.selectbox("المادة", ["الرياضيات", "العلوم", "العربية"])
            grd = st.number_input("الدرجة", 0, 100)
            if st.button("رصد"):
                c.execute("INSERT INTO grades VALUES (?,?,?)", (s_id, subj, grd))
                conn.commit()
                st.success("تم الرصد")

        elif choice == "حذف بيانات":
            st.header("🗑️ منطقة الحذف")
            target = st.radio("ماذا تريد أن تحذف؟", ["طالب", "درجة مادة"])
            
            if target == "طالب":
                df_s = pd.read_sql_query("SELECT * FROM students", conn)
                to_del = st.selectbox("اختر الطالب لحذفه نهائياً", df_s['name'])
                if st.button("⚠️ تأكيد الحذف"):
                    c.execute(f"DELETE FROM students WHERE name = '{to_del}'")
                    conn.commit()
                    st.warning(f"تم حذف {to_del} وجميع بياناته.")
            
            else:
                df_g = pd.read_sql_query('''SELECT grades.rowid, students.name, grades.subject, grades.grade 
                                           FROM grades JOIN students ON grades.student_id = students.id''', conn)
                st.write("اختر السجل المراد حذفه:")
                st.dataframe(df_g)
                row_to_del = st.number_input("أدخل رقم السجل (rowid) للحذف", min_value=1)
                if st.button("حذف السجل"):
                    c.execute(f"DELETE FROM grades WHERE rowid = {row_to_del}")
                    conn.commit()
                    st.success("تم حذف الدرجة")

    # --- 2. واجهة الطالب (Student) ---
    elif st.session_state['role'] == 'student':
        st.title("🎓 لوحة نتائج الطالب")
        s_id = st.session_state['user_id']
        
        # جلب بيانات الطالب
        student_info = pd.read_sql_query(f"SELECT * FROM students WHERE id = {s_id}", conn).iloc[0]
        st.subheader(f"الاسم: {student_info['name']} | الرقم الأكاديمي: {s_id}")
        
        # جلب الدرجات
        df_grades = pd.read_sql_query(f"SELECT subject as 'المادة', grade as 'الدرجة' FROM grades WHERE student_id = {s_id}", conn)
        
        if df_grades.empty:
            st.info("لم يتم رصد درجات لك بعد.")
        else:
            st.table(df_grades)
            avg = df_grades['الدرجة'].mean()
            st.metric("المعدل التراكمي", f"{avg:.2f}%")
            
            if avg >= 50:
                st.success("الحالة: ناجح 🎉")
            else:
                st.error("الحالة: راسب ⚠️")

        st.info("نصيحة: يمكنك تصوير الشاشة أو طباعتها كشهادة رسمية.")
