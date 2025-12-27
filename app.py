import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الدرجات - اللغة الإنجليزية", layout="wide", page_icon="🇬🇧")

# --- تهيئة قاعدة البيانات ---
# استخدمنا اسم ملف جديد لضمان عدم حدوث تداخل مع البيانات القديمة
conn = sqlite3.connect('school_system_new.db', check_same_thread=False)
c = conn.cursor()

# إنشاء جدول الطلاب
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, level TEXT)''')

# إنشاء جدول الدرجات
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, 
              subject TEXT, 
              period_1 REAL, 
              period_2 REAL, 
              participation REAL, 
              projects REAL,
              total REAL,
              FOREIGN KEY(student_id) REFERENCES students(id))''')
conn.commit()

# --- إدارة الجلسة (تسجيل الدخول) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- واجهة تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.title("🔐 نظام الإدارة المدرسية")
    tab1, tab2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
    
    with tab1:
        pwd = st.text_input("كلمة مرور المدير", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
                
    with tab2:
        sid = st.number_input("أدخل رقم الطالب الأكاديمي", min_value=1, step=1)
        if st.button("دخول الطالب"):
            check = pd.read_sql_query(f"SELECT * FROM students WHERE id = {sid}", conn)
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': sid})
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل لدينا")

# --- بعد تسجيل الدخول ---
else:
    st.sidebar.title(f"👤 {st.session_state['role'].upper()}")
    if st.sidebar.button("تسجيل الخروج"): logout()

    # --- واجهة المدير ---
    if st.session_state['role'] == 'admin':
        menu = ["إدارة الطلاب", "رصد درجات اللغة الإنجليزية", "حذف بيانات"]
        choice = st.sidebar.selectbox("القائمة", menu)

        if choice == "إدارة الطلاب":
            st.header("👥 إضافة وتعديل بيانات الطلاب")
            action = st.radio("العملية:", ["إضافة طالب جديد", "تعديل طالب موجود"])
            
            if action == "إضافة طالب جديد":
                with st.form("add_student"):
                    c1, c2, c3 = st.columns(3)
                    nid = c1.number_input("رقم الطالب", min_value=1)
                    nname = c2.text_input("اسم الطالب")
                    nlevel = c3.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"])
                    if st.form_submit_button("حفظ"):
                        try:
                            c.execute("INSERT INTO students VALUES (?,?,?)", (nid, nname, nlevel))
                            conn.commit()
                            st.success("تم تسجيل الطالب بنجاح")
                            st.rerun()
                        except: st.error("رقم الطالب موجود بالفعل")
            
            elif action == "تعديل طالب موجود":
                df_s = pd.read_sql_query("SELECT * FROM students", conn)
                if not df_s.empty:
                    target = st.selectbox("اختر الطالب لتعديله", df_s['name'])
                    old = df_s[df_s['name'] == target].iloc[0]
                    with st.form("edit"):
                        uname = st.text_input("الاسم الجديد", value=old['name'])
                        ulevel = st.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"], index=["ابتدائي", "متوسط", "ثانوي"].index(old['level']))
                        if st.form_submit_button("تحديث"):
                            c.execute("UPDATE students SET name=?, level=? WHERE id=?", (uname, ulevel, old['id']))
                            conn.commit()
                            st.success("تم التحديث")
                            st.rerun()

            st.write("---")
            st.subheader("جدول الطلاب")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

        elif choice == "رصد درجات اللغة الإنجليزية":
            st.header("📝 رصد الدرجات: مادة اللغة الإنجليزية")
            df_s = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not df_s.empty:
                with st.form("grade_form"):
                    s_name = st.selectbox("اختر الطالب", df_s['name'])
                    sid = df_s[df_s['name'] == s_name]['id'].values[0]
                    
                    # تم قصر المادة على اللغة الإنجليزية فقط
                    subj = "اللغة الإنجليزية"
                    st.info(f"المادة الحالية: {subj}")
                    
                    col1, col2 = st.columns(2)
                    p1 = col1.number_input("درجة الفترة الأولى (20)", 0.0, 20.0)
                    p2 = col2.number_input("درجة الفترة الثانية (20)", 0.0, 20.0)
                    part = col1.number_input("المشاركة (40)", 0.0, 40.0)
                    proj = col2.number_input("المشاريع (40)", 0.0, 40.0)
                    
                    total = p1 + p2 + part + proj
                    
                    if st.form_submit_button("حفظ الدرجة"):
                        # تحديث إذا كانت المادة موجودة، أو إضافتها إذا لم تكن موجودة
                        c.execute("DELETE FROM grades WHERE student_id=? AND subject=?", (sid, subj))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?,?,?,?)", (sid, subj, p1, p2, part, proj, total))
                        conn.commit()
                        st.success(f"تم الحفظ! المجموع الكلي للطالب {s_name} هو: {total}")
            else: st.warning("يجب إضافة طلاب أولاً من قائمة 'إدارة الطلاب'")

        elif choice == "حذف بيانات":
            st.header("🗑️ حذف السجلات")
            target = st.radio("نوع الحذف", ["طالب", "سجل درجة"])
            if target == "طالب":
                df_s = pd.read_sql_query("SELECT name FROM students", conn)
                to_del = st.selectbox("اختر الطالب للحذف", df_s)
                if st.button("حذف الطالب نهائياً"):
                    c.execute("DELETE FROM students WHERE name=?", (to_del,))
                    conn.commit()
                    st.rerun()
            else:
                df_g = pd.read_sql_query("SELECT rowid, student_id, subject, total FROM grades", conn)
                st.dataframe(df_g)
                rid = st.number_input("رقم السجل (rowid) لحذفه", min_value=1)
                if st.button("حذف الدرجة"):
                    c.execute("DELETE FROM grades WHERE rowid=?", (rid,))
                    conn.commit()
                    st.rerun()

    # --- واجهة الطالب ---
    elif st.session_state['role'] == 'student':
        st.title("🎓 كشف الدرجات التفصيلي")
        sid = st.session_state['user_id']
        
        s_info = pd.read_sql_query(f"SELECT * FROM students WHERE id = {sid}", conn).iloc[0]
        st.markdown(f"**اسم الطالب:** {s_info['name']} | **الرقم الأكاديمي:** {sid}")
        
        # جلب درجات اللغة الإنجليزية
        df_grades = pd.read_sql_query(f"""SELECT subject as 'المادة', 
                                              period_1 as 'الفترة 1', 
                                              period_2 as 'الفترة 2', 
                                              participation as 'المشاركة', 
                                              projects as 'المشاريع', 
                                              total as 'المجموع' 
                                       FROM grades WHERE student_id = {sid}""", conn)
        
        if not df_grades.empty:
            st.table(df_grades)
            total_sum = df_grades['المجموع'].values[0]
            st.metric("المجموع النهائي", f"{total_sum} / 60")
            
            if total_sum >= 30:
                st.success("النتيجة: ناجح (Passed)")
            else:
                st.error("النتيجة: لم يكمل متطلبات النجاح")
        else:
            st.info("لم يتم رصد درجات مادة اللغة الإنجليزية لك حتى الآن.")
