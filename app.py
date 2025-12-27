import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام نسخة جديدة من قاعدة البيانات لدعم الأعمدة الجديدة
    return sqlite3.connect('school_final_v12.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول وتحديث الهيكلية لتشمل العام والفصل الدراسي
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, academic_year TEXT, semester TEXT)''')
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
    st.session_state["year_key"] = "1446هـ"
    st.session_state["sem_key"] = "الفصل الأول"

# --- 3. بوابة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول للنظام")
    t1, t2 = st.tabs(["إدارة المدرسة", "بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض تقريري"):
            res = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not res.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل.")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # القسم 1: إدارة الطلاب (مع العام والفصل الدراسي)
        if menu == "👥 إدارة الطلاب":
            st.header("👤 تسجيل وتعديل بيانات الطلاب")
            st.button("➕ إضافة طالب جديد (تفريغ الحقول)", on_click=clear_student_form)
            
            with st.form("student_form"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = c2.text_input("اسم الطالب الكامل", key="name_key")
                
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                fclass = c4.text_input("الصف (مثلاً: 1/أ)", key="class_key")
                
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام الدراسي", ["1445هـ", "1446هـ", "1447هـ"], key="year_key")
                fsem = c6.selectbox("الفصل الدراسي", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"], key="sem_key")
                
                if st.form_submit_button("حفظ بيانات الطالب"):
                    if fname.strip() == "": st.error("الاسم مطلوب!")
                    else:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?)", 
                                  (int(fid), fname, flevel, fclass, fyear, fsem))
                        conn.commit()
                        st.success(f"تم حفظ بيانات الطالب: {fname}")
                        st.rerun()

            st.divider()
            st.subheader("📋 قائمة الطلاب")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 3, 1])
                    col1.write(f"👤 **{r['name']}** (ID: {r['id']})")
                    col2.write(f"📅 **{r['academic_year']} - {r['semester']}** \n\n 🏫 {r['level']} | {r['grade_class']}")
                    if col3.button("🗑️ حذف", key=f"del_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # القسم 2: رصد الدرجات
        elif menu == "📝 رصد الدرجات":
            st.header("📝 إدارة الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                cur_g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur_g.empty else (cur_g.iloc[0]['p1'], cur_g.iloc[0]['p2'], cur_g.iloc[0]['perf'])

                with st.form("gr_form"):
                    st.write(f"🖊️ تعديل درجات: **{target_name}**")
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("✅ حفظ وتعديل"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()
                
                if not cur_g.empty:
                    if st.button("🗑️ حذف الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.rerun()
            else: st.warning("أضف طلاباً أولاً")

        # القسم 3: سجل السلوك
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
                
                logs = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    st.info(f"📅 {ln['date']} | {ln['type']}: {ln['note']}")

    # --- واجهة الطالب (عرض العام والفصل) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.title(f"🎓 تقرير: {info['name']}")
        
        # عرض البيانات الأساسية بشكل منظم
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**العام الدراسي:** {info['academic_year']}")
            st.markdown(f"**المرحلة:** {info['level']}")
        with col_b:
            st.markdown(f"**الفصل الدراسي:** {info['semester']}")
            st.markdown(f"**الصف:** {info['grade_class']}")
            
        st.divider()
        st.write("### 📊 الدرجات")
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0]['p1'])
            c2.metric("الفترة 2", g_data.iloc[0]['p2'])
            c3.metric("المشاركة", g_data.iloc[0]['perf'])
        
        st.divider()
        st.write("### 📅 السلوك")
        b_data = pd.read_sql_query("SELECT date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty: st.table(b_data)
        else: st.info("السجل نظيف")
