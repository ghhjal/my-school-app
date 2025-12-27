import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام مدرستي - النسخة المستقرة", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام قاعدة بيانات موحدة وثابتة
    return sqlite3.connect('school_data_v1.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية إذا لم تكن موجودة
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. نظام إدارة الجلسة (Login) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🛡️ بوابة الدخول")
    tab1, tab2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
    
    with tab1:
        pwd = st.text_input("كلمة السر الخاصة بالإدارة", type="password")
        if st.button("دخول كمدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
            else:
                st.error("كلمة السر غير صحيحة")
                
    with tab2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("عرض التقرير"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else:
                st.error("هذا الرقم الأكاديمي غير مسجل")

# --- 4. واجهات البرنامج بعد الدخول ---
else:
    # زر تسجيل الخروج في الجانب
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- واجهة المدير ---
    if st.session_state.role == 'admin':
        st.sidebar.title("لوحة التحكم")
        choice = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # قسم إدارة الطلاب (الإضافة، التعديل، الحذف)
        if choice == "👥 إدارة الطلاب":
            st.header("👤 إدارة ملفات الطلاب")
            
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("new_student_form"):
                    c1, c2 = st.columns(2)
                    nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                    nname = c2.text_input("اسم الطالب")
                    nlevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    nclass = c2.text_input("الصف الدراسي")
                    if st.form_submit_button("إضافة الطالب للنظام"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, nclass))
                        conn.commit()
                        st.success("تمت الإضافة بنجاح")
                        st.rerun()

            st.write("---")
            st.subheader("قائمة الطلاب المسجلين")
            df_st = pd.read_sql_query("SELECT * FROM students", conn)
            
            if df_st.empty:
                st.info("لا يوجد طلاب مسجلين حالياً.")
            else:
                for index, row in df_st.iterrows():
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"**{row['name']}** (الرقم الأكاديمي: {row['id']})")
                        col2.write(f"{row['level']} - {row['grade_class']}")
                        
                        # زر الحذف
                        if col3.button("🗑️ حذف", key=f"del_{row['id']}"):
                            c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                            c.execute("DELETE FROM grades WHERE student_id=?", (row['id'],))
                            c.execute("DELETE FROM behavior WHERE student_id=?", (row['id'],))
                            conn.commit()
                            st.rerun()

        # قسم رصد الدرجات
        elif choice == "📝 رصد الدرجات":
            st.header("📝 رصد الدرجات الدراسية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                student_choice = st.selectbox("اختر الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == student_choice]['id'].values[0])
                
                with st.form("grades_form"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    perf = col3.number_input("المهام والمشاركة", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (sid, p1, p2, perf))
                        conn.commit()
                        st.success(f"تم رصد درجات الطالب {student_choice}")
            else:
                st.warning("يجب إضافة طلاب أولاً قبل رصد الدرجات.")

        # قسم سجل السلوك
        elif choice == "📅 سجل السلوك":
            st.header("📅 سجل المواقف السلوكية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                student_choice = st.selectbox("اختر الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == student_choice]['id'].values[0])
                
                with st.form("behavior_form"):
                    b_date = st.date_input("تاريخ الموقف")
                    days_mapping = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                    b_day = days_mapping[b_date.strftime('%A')]
                    b_type = st.selectbox("نوع الموقف", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("تفاصيل الملاحظة")
                    
                    if st.form_submit_button("إضافة للسجل"):
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (sid, b_date.isoformat(), b_day, b_type, b_note))
                        conn.commit()
                        st.success("تم تسجيل الموقف بنجاح")
                
                # عرض السجل للمدير للتأكد
                logs = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
                if not logs.empty:
                    st.write("السجل السلوكي الحالي لهذا الطالب:")
                    st.table(logs)
            else:
                st.warning("يجب إضافة طلاب أولاً.")

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        student_info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 كشف الدرجات والسلوك لـ: {student_info['name']}")
        st.write(f"المرحلة: {student_info['level']} | الصف: {student_info['grade_class']} | الرقم الأكاديمي: {student_info['id']}")
        
        st.divider()
        
        # عرض الدرجات
        grades_df = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        st.subheader("📊 النتائج الدراسية")
        if not grades_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", grades_df.iloc[0]['p1'])
            c2.metric("الفترة 2", grades_df.iloc[0]['p2'])
            c3.metric("المهام والمشاركة", grades_df.iloc[0]['perf'])
        else:
            st.info("لم يتم رصد درجات لك حتى الآن.")
            
        st.divider()
        
        # عرض سجل السلوك في جدول
        st.subheader("📅 سجل السلوك والملاحظات")
        behavior_df = pd.read_sql_query("SELECT date as التاريخ, day as اليوم, type as النوع, note as الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not behavior_df.empty:
            st.table(behavior_df)
        else:
            st.info("لا توجد ملاحظات سلوكية مسجلة.")
