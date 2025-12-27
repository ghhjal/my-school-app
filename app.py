import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام قاعدة بيانات ثابتة ومستقرة
    return sqlite3.connect('school_system_v1.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. إدارة الجلسة (تسجيل الدخول) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 3. واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول للنظام")
    tab1, tab2 = st.tabs(["بوابة الإدارة", "بوابة الطالب"])
    
    with tab1:
        pwd = st.text_input("كلمة مرور المدير", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
            else:
                st.error("كلمة السر خاطئة")
                
    with tab2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض التقرير"):
            user_check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not user_check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else:
                st.error("الرقم الأكاديمي غير مسجل")

# --- 4. واجهات البرنامج بعد الدخول ---
else:
    # خيار تسجيل الخروج
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- لوحة تحكم المدير ---
    if st.session_state.role == 'admin':
        st.sidebar.title("🛠️ لوحة التحكم")
        choice = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # القسم الأول: إدارة الطلاب
        if choice == "👥 إدارة الطلاب":
            st.header("👤 ملفات الطلاب")
            
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("add_student"):
                    c1, c2 = st.columns(2)
                    nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                    nname = c2.text_input("اسم الطالب")
                    nlevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    nclass = c2.text_input("الصف")
                    if st.form_submit_button("حفظ الطالب"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(nid), nname, nlevel, nclass))
                        conn.commit()
                        st.success("تم الحفظ بنجاح")
                        st.rerun()

            st.write("---")
            st.subheader("قائمة الطلاب الحالية")
            st_list = pd.read_sql_query("SELECT * FROM students", conn)
            for _, row in st_list.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{row['name']}** (ID: {row['id']})")
                    col2.write(f"{row['level']} - {row['grade_class']}")
                    if col3.button("🗑️ حذف", key=f"del_{row['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (row['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

        # القسم الثاني: رصد الدرجات وعرضها بالأسفل
        elif choice == "📝 رصد الدرجات":
            st.header("📝 رصد الدرجات الدراسية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                target_id = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                with st.form("grade_entry"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    perf = col3.number_input("المهام والمشاركة", 0.0, 40.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (target_id,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?)", (target_id, p1, p2, perf))
                        conn.commit()
                        st.success(f"تم تحديث درجات {target_name}")

                # عرض الدرجات بالأسفل مباشرة
                st.divider()
                st.subheader(f"📊 الدرجات المسجلة لـ: {target_name}")
                display_grades = pd.read_sql_query(
                    "SELECT p1 AS 'الفترة 1', p2 AS 'الفترة 2', perf AS 'المهام والمشاركة' FROM grades WHERE student_id=?", 
                    conn, params=(target_id,)
                )
                if not display_grades.empty:
                    st.table(display_grades)
                else:
                    st.info("لا توجد درجات مسجلة لهذا الطالب بعد.")
            else:
                st.warning("يرجى إضافة طلاب أولاً.")

        # القسم الثالث: سجل السلوك
        elif choice == "📅 سجل السلوك":
            st.header("📅 سجل السلوك والملاحظات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                target_id = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                with st.form("behavior_entry"):
                    b_date = st.date_input("التاريخ")
                    day_map = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}
                    b_day = day_map[b_date.strftime('%A')]
                    b_type = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة للسجل"):
                        c.execute("INSERT INTO behavior VALUES (?,?,?,?,?)", (target_id, b_date.isoformat(), b_day, b_type, b_note))
                        conn.commit()
                        st.success("تم تسجيل الموقف")

                st.divider()
                st.subheader(f"📅 السجل السلوكي لـ: {target_name}")
                logs = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(target_id,))
                if not logs.empty:
                    st.table(logs)
            else:
                st.warning("يرجى إضافة طلاب أولاً.")

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 التقرير الدراسي: {info['name']}")
        st.write(f"الصف: {info['level']} - {info['grade_class']} | الرقم: {info['id']}")
        
        st.divider()
        st.subheader("📊 نتائج الفترات")
        g_df = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_df.iloc[0]['p1'])
            c2.metric("الفترة 2", g_df.iloc[0]['p2'])
            c3.metric("المهام والمشاركة", g_df.iloc[0]['perf'])
        else:
            st.info("لم ترصد درجاتك بعد.")
            
        st.divider()
        st.subheader("📅 سجل السلوك")
        b_df = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_df.empty:
            st.table(b_df)
        else:
            st.info("سجل السلوك نظيف.")
