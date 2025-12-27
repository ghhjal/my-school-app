import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide")

def get_connection():
    return sqlite3.connect('school_v6.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. إدارة الحالة (تفريغ الحقول) ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = {'id': 1, 'name': '', 'level': 'ابتدائي', 'class': ''}

def clear_form():
    st.session_state.form_data = {'id': 1, 'name': '', 'level': 'ابتدائي', 'class': ''}

# --- 3. تسجيل الدخول (تبسيط للمثال) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True  # للدخول المباشر للتجربة
    st.session_state.role = 'admin'

# --- 4. واجهة المدير ---
if st.session_state.logged_in and st.session_state.role == 'admin':
    choice = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

    if choice == "👥 إدارة الطلاب":
        st.header("👤 تسجيل وتعديل بيانات الطلاب")
        
        # زر إضافة طالب جديد (تفريغ الحقول)
        if st.button("➕ إضافة طالب جديد (تفريغ الحقول)"):
            clear_form()
            st.rerun()

        with st.form("st_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            fid = c1.number_input("الرقم الأكاديمي", min_value=1, value=st.session_state.form_data['id'])
            fname = c2.text_input("اسم الطالب الكامل", value=st.session_state.form_data['name'])
            flevel = c1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"], 
                                 index=["ابتدائي", "متوسط", "ثانوي"].index(st.session_state.form_data['level']))
            fclass = c2.text_input("الصف (مثلاً: أول/أ)", value=st.session_state.form_data['class'])
            
            if st.form_submit_button("حفظ بيانات الطالب"):
                c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                conn.commit()
                st.success(f"تم حفظ الطالب: {fname}")
                st.rerun()

        st.divider()
        st.subheader("📋 الطلاب المسجلون")
        df_s = pd.read_sql_query("SELECT * FROM students", conn)
        
        for _, r in df_s.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                # عرض المرحلة والصف بشكل واضح
                col1.write(f"👤 **الاسم:** {r['name']} | **الرقم:** {r['id']}")
                col2.write(f"🏫 **المرحلة:** {r['level']} | **الصف:** {r['grade_class']}")
                
                if col3.button("🗑️ حذف", key=f"del_{r['id']}"):
                    c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

    # (بقية الأقسام تتبع نفس المنطق البرمجي السابق)
