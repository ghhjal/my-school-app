import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide")

def get_connection():
    return sqlite3.connect('school_v7.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. دالة تفريغ الحقول ---
# الحل: نقوم بمسح القيم من session_state مباشرة باستخدام الـ keys
def clear_form_action():
    st.session_state["id_key"] = 1
    st.session_state["name_key"] = ""
    st.session_state["class_key"] = ""
    st.session_state["level_key"] = "ابتدائي"

# --- 3. واجهة المدير ---
if 'role' not in st.session_state:
    st.session_state.role = 'admin'

if st.session_state.role == 'admin':
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👤 تسجيل وتعديل بيانات الطلاب")
        
        # زر إضافة طالب جديد (تفريغ الحقول)
        # عند الضغط عليه يتم استدعاء الدالة التي تمسح الـ keys
        st.button("➕ إضافة طالب جديد (تفريغ الحقول)", on_click=clear_form_action)

        with st.form("student_form"):
            col1, col2 = st.columns(2)
            
            # ربط كل حقل بـ key لضمان استجابته لعملية المسح
            fid = col1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
            fname = col2.text_input("اسم الطالب الكامل", key="name_key")
            flevel = col1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
            fclass = col2.text_input("الصف (مثلاً: أول/أ)", key="class_key")
            
            submit = st.form_submit_button("حفظ بيانات الطالب")
            
            if submit:
                if fname == "":
                    st.error("يرجى إدخال اسم الطالب")
                else:
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                    conn.commit()
                    st.success(f"تم حفظ الطالب: {fname}")
                    st.rerun()

        st.divider()
        st.subheader("📋 الطلاب المسجلون")
        df_s = pd.read_sql_query("SELECT * FROM students", conn)
        
        if df_s.empty:
            st.info("لا يوجد طلاب مسجلين.")
        else:
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    c_1, c_2, c_3 = st.columns([3, 2, 1])
                    # التأكيد على ظهور المرحلة والصف في الأسفل
                    c_1.write(f"👤 **الاسم:** {r['name']} | **الرقم:** {r['id']}")
                    c_2.write(f"🏫 **المرحلة:** {r['level']} | **الصف:** {r['grade_class']}")
                    
                    if c_3.button("🗑️ حذف", key=f"del_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()
