import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام اللغة الإنجليزية المطور", layout="wide")

def get_connection():
    # استخدام اسم قاعدة بيانات جديد لضمان بيانات نظيفة
    return sqlite3.connect('english_school_v3.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, part REAL, proj REAL, total REAL)')
conn.commit()

# --- 2. نظام إدارة الجلسة (بدون استخدام callbacks المعقدة) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None

# --- 3. واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول للنظام")
    tab1, tab2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
    
    with tab1:
        pwd = st.text_input("كلمة السر", type="password", key="admin_pwd")
        if st.button("دخول كمدير"):
            if pwd == "admin123":
                st.session_state.logged_in = True
                st.session_state.role = 'admin'
                st.rerun()
            else: st.error("كلمة السر خاطئة")

    with tab2:
        std_id = st.number_input("أدخل رقمك الأكاديمي", min_value=1, step=1, key="std_login_id")
        if st.button("دخول الطالب"):
            user = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(std_id),))
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.role = 'student'
                st.session_state.user_id = int(std_id)
                st.rerun()
            else: st.error("هذا الرقم غير مسجل!")

# --- 4. واجهة التطبيق بعد الدخول ---
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    # --- واجهة المدير ---
    if st.session_state.role == 'admin':
        st.sidebar.success("وضع المدير")
        menu = ["إدارة الطلاب", "رصد درجات الإنجليزية"]
        choice = st.sidebar.selectbox("القائمة", menu)

        if choice == "إدارة الطلاب":
            st.header("👥 تسجيل الطلاب")
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                nid = c1.number_input("الرقم الأكاديمي", min_value=1, step=1)
                nname = c2.text_input("اسم الطالب")
                nlevel = c3.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"])
                if st.button("حفظ الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?, ?, ?)", (int(nid), nname, nlevel))
                    conn.commit()
                    st.success(f"تم تسجيل {nname} بنجاح")
            
            st.subheader("قائمة الطلاب المسجلين")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

        elif choice == "رصد درجات الإنجليزية":
            st.header("📝 رصد الدرجات")
            st.info("تأكد من الضغط على زر 'حفظ الدرجة' بعد الإدخال")
            students = pd.read_sql_query("SELECT id, name FROM students", conn)
            
            if not students.empty:
                # اختيار الطالب بالاسم واستخراج الـ ID الخاص به بدقة
                s_map = dict(zip(students['name'], students['id']))
                selected_name = st.selectbox("اختر الطالب", list(s_map.keys()))
                sid = int(s_map[selected_name])
                
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    p1 = col1.number_input("الفترة الأولى (20)", 0.0, 20.0)
                    p2 = col2.number_input("الفترة الثانية (20)", 0.0, 20.0)
                    part = col1.number_input("المشاركة (10)", 0.0, 10.0)
                    proj = col2.number_input("المشاريع (10)", 0.0, 10.0)
                    
                    total = p1 + p2 + part + proj
                    
                    if st.button("حفظ الدرجة"):
                        c.execute("DELETE FROM grades WHERE student_id = ?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?)", (sid, p1, p2, part, proj, total))
                        conn.commit()
                        st.success(f"تم حفظ درجات {selected_name} بنجاح. المجموع: {total}")
            else: st.warning("لا يوجد طلاب مسجلين.")

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = int(st.session_state.user_id)
        # جلب الاسم
        user_info = pd.read_sql_query("SELECT name FROM students WHERE id = ?", conn, params=(sid,))
        
        st.title("🎓 كشف الدرجات التفصيلي")
        st.subheader(f"اسم الطالب: {user_info.iloc[0,0]} | الرقم الأكاديمي: {sid}")
        
        # جلب الدرجات مع الربط بالـ ID
        df_res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
        
        if not df_res.empty:
            st.write("---")
            # عرض الدرجات في بطاقات جذابة
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("الفترة 1", df_res.iloc[0]['p1'])
            c2.metric("الفترة 2", df_res.iloc[0]['p2'])
            c3.metric("المشاركة", df_res.iloc[0]['part'])
            c4.metric("المشاريع", df_res.iloc[0]['proj'])
            
            st.divider()
            st.subheader(f"المجموع النهائي للغة الإنجليزية: {df_res.iloc[0]['total']} / 60")
            
            if df_res.iloc[0]['total'] >= 30:
                st.balloons()
                st.success("النتيجة: ناجح 🎉")
        else:
            st.error("⚠️ عذراً، لم يتم رصد درجاتك في النظام حتى الآن. يرجى مراجعة المعلم.")
