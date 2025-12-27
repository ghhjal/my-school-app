import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المطور", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام قاعدة بيانات جديدة لضمان سلامة الهيكلية
    return sqlite3.connect('school_final_v11.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية مع التأكد من وجود كافة الأعمدة
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS behavior 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)''')
conn.commit()

# --- 2. وظائف التحكم (تفريغ الحقول) ---
def clear_student_form():
    st.session_state["id_key"] = 1
    st.session_state["name_key"] = ""
    st.session_state["level_key"] = "ابتدائي"
    st.session_state["class_key"] = ""

# --- 3. بوابة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 الدخول إلى النظام")
    t1, t2 = st.tabs(["إدارة المدرسة", "بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المسؤول"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض التقرير"):
            res = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not res.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل.")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- واجهة مدير النظام ---
    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # القسم 1: إدارة الطلاب (إضافة وتفريغ)
        if menu == "👥 إدارة الطلاب":
            st.header("👤 تسجيل وتعديل بيانات الطلاب")
            
            # زر إضافة طالب جديد (تفريغ)
            st.button("➕ إضافة طالب جديد (تفريغ الحقول)", on_click=clear_student_form)
            
            with st.form("student_form"):
                col1, col2 = st.columns(2)
                fid = col1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = col2.text_input("اسم الطالب الكامل", key="name_key")
                flevel = col1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                fclass = col2.text_input("الصف (مثلاً: 1/أ)", key="class_key")
                
                if st.form_submit_button("حفظ البيانات"):
                    if fname.strip() == "": st.error("الاسم مطلوب!")
                    else:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                        conn.commit()
                        st.success(f"تم حفظ بيانات: {fname}")
                        st.rerun()

            st.divider()
            st.subheader("📋 قائمة الطلاب المسجلين")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"👤 **{r['name']}** | الرقم: {r['id']}")
                    c2.write(f"🏫 **{r['level']}** | الصف: {r['grade_class']}") # عرض المرحلة والصف
                    if c3.button("🗑️ حذف الطالب", key=f"del_st_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # القسم 2: رصد الدرجات (تعديل وحذف الدرجات)
        elif menu == "📝 رصد الدرجات":
            st.header("📝 إدارة ورصد الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب لتعديل درجاته", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                # جلب الدرجات الحالية للتعديل
                cur_g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur_g.empty else (cur_g.iloc[0]['p1'], cur_g.iloc[0]['p2'], cur_g.iloc[0]['perf'])

                with st.form("grades_form"):
                    st.write(f"🖊️ تعديل درجات الطالب: **{target_name}**")
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("✅ حفظ التعديلات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم تحديث الدرجات بنجاح")
                        st.rerun()
                
                if not cur_g.empty:
                    st.divider()
                    if st.button(f"🗑️ حذف درجات {target_name} نهائياً"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.success("تم مسح الدرجات")
                        st.rerun()
            else: st.warning("يجب إضافة طلاب أولاً")

        # القسم 3: سجل السلوك (إصلاح خطأ NameError)
        elif menu == "📅 سجل السلوك":
            st.header("📅 إدارة سجل السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                with st.form("behavior_form"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة الموقف"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, dt.isoformat(), day_ar, tp, nt))
                        conn.commit()
                        st.rerun()

                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        ca, cb = st.columns([5, 1])
                        ca.write(f"📅 **{ln['date']} ({ln['day']})** | {ln['type']}: {ln['note']}")
                        if cb.button("🗑️ حذف", key=f"del_beh_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()
            else: st.warning("أضف طلاباً أولاً")

    # --- واجهة الطالب (إصلاح ظهور الأكواد) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        student_info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 تقرير الطالب: {student_info['name']}")
        st.subheader(f"المرحلة: {student_info['level']} | الصف: {student_info['grade_class']}")
        
        # عرض الدرجات
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            st.divider()
            st.write("### 📊 النتائج الدراسية")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0]['p1'])
            c2.metric("الفترة 2", g_data.iloc[0]['p2'])
            c3.metric("المشاركة والمهام", g_data.iloc[0]['perf'])
            
        # عرض السلوك (جدول نظيف)
        st.divider()
        st.write("### 📅 سجل السلوك والملاحظات")
        b_data = pd.read_sql_query("SELECT date AS التاريخ, day AS اليوم, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty:
            st.table(b_data)
        else:
            st.info("سجل السلوك نظيف ولا توجد ملاحظات.")
