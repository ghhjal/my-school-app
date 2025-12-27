import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    return sqlite3.connect('school_final_v9.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. وظائف تفريغ الحقول ---
def clear_form_action():
    st.session_state["id_key"] = 1
    st.session_state["name_key"] = ""
    st.session_state["class_key"] = ""
    st.session_state["level_key"] = "ابتدائي"

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["الإدارة", "الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض التقرير"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # القسم الأول: إدارة الطلاب
        if menu == "👥 إدارة الطلاب":
            st.header("👤 إدارة بيانات الطلاب")
            st.button("➕ إضافة طالب جديد (تفريغ الحقول)", on_click=clear_form_action)
            with st.form("st_form"):
                col1, col2 = st.columns(2)
                fid = col1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = col2.text_input("اسم الطالب", key="name_key")
                flevel = col1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                fclass = col2.text_input("الصف", key="class_key")
                if st.form_submit_button("حفظ"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                    conn.commit()
                    st.success("تم الحفظ")
                    st.rerun()

            st.subheader("📋 قائمة الطلاب")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"👤 **{r['name']}** | الرقم: {r['id']}")
                    c2.write(f"🏫 **{r['level']}** | الصف: {r['grade_class']}")
                    if c3.button("🗑️ حذف", key=f"ds_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # القسم الثاني: رصد الدرجات (تعديل وحذف)
        elif menu == "📝 رصد الدرجات":
            st.header("📝 إدارة درجات الطلاب")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                # جلب الدرجات الحالية للتعديل
                cur = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur.empty else (cur.iloc[0]['p1'], cur.iloc[0]['p2'], cur.iloc[0]['perf'])

                with st.form("gr_form"):
                    st.write(f"🖊️ **تعديل درجات الطالب: {target_name}**")
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("✅ حفظ التعديلات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم تحديث الدرجات")
                        st.rerun()
                
                # خيار حذف الدرجات
                if not cur.empty:
                    st.divider()
                    st.warning("⚠️ منطقة الحذف")
                    if st.button(f"🗑️ حذف كافة درجات الطالب {target_name} نهائياً"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.success("تم مسح الدرجات بنجاح")
                        st.rerun()
                    
                    st.subheader("📊 العرض الحالي")
                    st.table(cur.rename(columns={'p1':'الفترة 1','p2':'الفترة 2','perf':'المشاركة'}))
            else: st.warning("أضف طلاباً أولاً")

        # القسم الثالث: سجل السلوك
        elif menu == "📅 سجل السلوك":
            st.header("📅 سجل السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                with st.form("b_form"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, dt.isoformat(), day_ar, tp, nt))
                        conn.commit()
                        st.rerun()

                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        ca, cb = st.columns([5, 1])
                        ca.write(f"📅 **{ln['date']}** | {ln['type']}: {ln['note']}")
                        if cb.button("🗑️", key=f"db_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()

    # واجهة الطالب
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"🎓 تقرير: {info['name']}")
        st.write(f"المرحلة: {info['level']} | الصف: {info['grade_class']}")
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0]['p1'])
            c2.metric("الفترة 2", g_data.iloc[0]['p2'])
            c3.metric("المشاركة", g_data.iloc[0]['perf'])
        st.divider()
        b_data = pd.read_sql_query("SELECT date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        st.table(b_data) if not b_data.empty else st.info("السجل نظيف")
