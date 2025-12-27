import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام قاعدة بيانات مستقرة لضمان حفظ البيانات
    return sqlite3.connect('school_management_v8.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. وظيفة تفريغ الحقول ---
def clear_form_action():
    """تقوم هذه الدالة بمسح القيم المرتبطة بمفاتيح الحقول في session_state"""
    st.session_state["id_key"] = 1
    st.session_state["name_key"] = ""
    st.session_state["class_key"] = ""
    st.session_state["level_key"] = "ابتدائي"

# --- 3. نظام إدارة الجلسة ودخول المستخدم ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 بوابة تسجيل الدخول")
    t1, t2 = st.tabs(["إدارة المدرسة", "بوابة الطالب"])
    
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول كمسؤول"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
    
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("عرض التقرير"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else:
                st.error("الرقم الأكاديمي غير مسجل في النظام")

# --- 4. واجهات النظام بعد الدخول ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- واجهة مدير النظام ---
    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # القسم الأول: إدارة الطلاب (الإضافة، التعديل، الحذف، والتفريغ)
        if menu == "👥 إدارة الطلاب":
            st.header("👤 إدارة بيانات الطلاب")
            
            # زر تفريغ الحقول (إضافة طالب جديد)
            st.button("➕ إضافة طالب جديد (تفريغ الحقول)", on_click=clear_form_action)

            with st.form("student_mgmt_form"):
                col1, col2 = st.columns(2)
                
                # استخدام keys لربط الحقول بدالة التفريغ
                fid = col1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = col2.text_input("اسم الطالب بالكامل", key="name_key")
                flevel = col1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                fclass = col2.text_input("الصف الدراسي (مثلاً: 1/أ)", key="class_key")
                
                if st.form_submit_button("حفظ بيانات الطالب"):
                    if fname.strip() == "":
                        st.warning("يرجى إدخال اسم الطالب قبل الحفظ")
                    else:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                        conn.commit()
                        st.success(f"تم حفظ بيانات الطالب: {fname}")
                        st.rerun()

            st.divider()
            st.subheader("📋 قائمة الطلاب المسجلين")
            df_students = pd.read_sql_query("SELECT * FROM students", conn)
            
            if df_students.empty:
                st.info("لا يوجد طلاب مسجلين حالياً.")
            else:
                for _, row in df_students.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        # إظهار كافة التفاصيل: الاسم، الرقم، المرحلة، والصف
                        c1.write(f"👤 **الاسم:** {row['name']} | **الرقم:** {row['id']}")
                        c2.write(f"🏫 **المرحلة:** {row['level']} | **الصف:** {row['grade_class']}")
                        
                        if c3.button("🗑️ حذف", key=f"del_st_{row['id']}"):
                            c.execute("DELETE FROM students WHERE id=?", (row['id'],))
                            c.execute("DELETE FROM grades WHERE student_id=?", (row['id'],))
                            c.execute("DELETE FROM behavior WHERE student_id=?", (row['id'],))
                            conn.commit()
                            st.rerun()

        # القسم الثاني: رصد الدرجات
        elif menu == "📝 رصد الدرجات":
            st.header("📝 رصد وتعديل الدرجات")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                target = st.selectbox("اختر الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == target]['id'].values[0])
                
                # جلب الدرجات الحالية
                existing_grades = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if existing_grades.empty else (existing_grades.iloc[0]['p1'], existing_grades.iloc[0]['p2'], existing_grades.iloc[0]['perf'])

                with st.form("grades_entry"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة الأولى", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة الثانية", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة والمهام", 0.0, 40.0, value=v3)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم تحديث الدرجات بنجاح")
                        st.rerun()
                
                if not existing_grades.empty:
                    st.divider()
                    st.write(f"📊 **الدرجات المرصودة حالياً لـ {target}:**")
                    st.table(existing_grades.rename(columns={'p1':'الفترة 1','p2':'الفترة 2','perf':'المشاركة'}))
            else:
                st.warning("يرجى تسجيل الطلاب أولاً.")

        # القسم الثالث: سجل السلوك
        elif menu == "📅 سجل السلوك":
            st.header("📅 إدارة سجل السلوك والملاحظات")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                target = st.selectbox("اختر الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == target]['id'].values[0])
                
                with st.form("behavior_entry"):
                    b_date = st.date_input("تاريخ الموقف")
                    b_type = st.selectbox("نوع الموقف", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("تفاصيل الملاحظة")
                    if st.form_submit_button("إضافة للسجل"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[b_date.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, b_date.isoformat(), day_ar, b_type, b_note))
                        conn.commit()
                        st.success("تمت الإضافة")
                        st.rerun()

                st.divider()
                st.subheader("📋 السجل الحالي")
                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        ca, cb = st.columns([5, 1])
                        ca.write(f"📅 **{ln['date']} ({ln['day']})** | **{ln['type']}**: {ln['note']}")
                        if cb.button("🗑️", key=f"del_beh_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()
            else:
                st.warning("يرجى تسجيل الطلاب أولاً.")

    # --- واجهة الطالب (تم إصلاح عرض الجداول) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        student_info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 تقرير الطالب: {student_info['name']}")
        st.write(f"🏫 **المرحلة:** {student_info['level']} | **الصف:** {student_info['grade_class']} | **الرقم الأكاديمي:** {student_info['id']}")
        
        # عرض الدرجات
        st.divider()
        st.subheader("📊 النتائج الدراسية")
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0]['p1'])
            c2.metric("الفترة 2", g_data.iloc[0]['p2'])
            c3.metric("المشاركة والمهام", g_data.iloc[0]['perf'])
        else:
            st.info("لم يتم رصد درجاتك بعد.")
            
        # عرض السلوك
        st.divider()
        st.subheader("📅 سجل السلوك والملاحظات")
        b_data = pd.read_sql_query("SELECT date AS التاريخ, day AS اليوم, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty:
            st.table(b_data)
        else:
            st.info("سجل السلوك نظيف ولا توجد ملاحظات.")
