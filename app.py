import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات المظهر العام (CSS Custom Styling) ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1e3a8a; color: white; border: none; }
    .stButton>button:hover { background-color: #2563eb; color: white; }
    .report-card { background-color: white; padding: 20px; border-radius: 15px; border-right: 5px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .header-text { color: #1e3a8a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; }
    .sidebar-header { text-align: center; padding: 10px; background-color: #e0e7ff; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات قاعدة البيانات ---
def get_connection():
    return sqlite3.connect('english_pro_system.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, academic_year TEXT, semester TEXT, subject TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 3. وظيفة تفريغ الحقول ---
def clear_form():
    st.session_state["id_key"] = 1
    st.session_state["name_key"] = ""
    st.session_state["level_key"] = "ابتدائي"
    st.session_state["class_key"] = ""
    st.session_state["year_key"] = "1447هـ"
    st.session_state["sem_key"] = "الفصل الأول"

# --- 4. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown("<h1 class='header-text'>🇬🇧 English Grading System</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>بإشراف الأستاذ زياد المعمري</h3>", unsafe_allow_html=True)
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        t1, t2 = st.tabs(["🔐 دخول المعلم", "🎓 دخول الطالب"])
        with t1:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("تسجيل الدخول"):
                if pwd == "admin123":
                    st.session_state.update({'logged_in': True, 'role': 'admin'})
                    st.rerun()
        with t2:
            sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            if st.button("استعلام"):
                res = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
                if not res.empty:
                    st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                    st.rerun()

# --- 5. واجهات النظام ---
else:
    # القائمة الجانبية (شعار الأستاذ)
    with st.sidebar:
        st.markdown("<div class='sidebar-header'><h4>زياد المعمري</h4><p>English Teacher</p></div>", unsafe_allow_html=True)
        menu = st.radio("📑 التنقل", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📝 سجل السلوك"])
        st.divider()
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # --- واجهة المدير ---
    if st.session_state.role == 'admin':
        if menu == "👥 إدارة الطلاب":
            st.markdown("<h2 class='header-text'>👥 تسجيل بيانات الطلاب</h2>", unsafe_allow_html=True)
            st.button("➕ طالب جديد", on_click=clear_form)
            
            with st.container():
                with st.form("st_form"):
                    c1, c2 = st.columns(2)
                    fid = c1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                    fname = c2.text_input("اسم الطالب", key="name_key")
                    c3, c4 = st.columns(2)
                    flevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                    fclass = c4.text_input("الصف", key="class_key")
                    c5, c6 = st.columns(2)
                    fyear = c5.selectbox("العام", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"], key="year_key")
                    fsem = c6.selectbox("الفصل", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"], key="sem_key")
                    
                    if st.form_submit_button("💾 حفظ البيانات"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)", 
                                  (int(fid), fname, flevel, fclass, fyear, fsem, "اللغة الإنجليزية"))
                        conn.commit()
                        st.success("✅ تم الحفظ")
                        st.rerun()

            st.divider()
            st.subheader("📋 القائمة الحالية")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.markdown(f"<div class='report-card'><b>{r['name']}</b> | {r['level']} - {r['grade_class']}</div>", unsafe_allow_html=True):
                    if st.button(f"🗑️ حذف {r['id']}", key=f"del_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        elif menu == "📊 رصد الدرجات":
            st.markdown("<h2 class='header-text'>📊 رصد درجات اللغة الإنجليزية</h2>", unsafe_allow_html=True)
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                target = st.selectbox("اختر الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == target]['id'].values[0])
                
                cur_g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur_g.empty else (cur_g.iloc[0]['p1'], cur_g.iloc[0]['p2'], cur_g.iloc[0]['perf'])

                with st.form("gr_form"):
                    st.write(f"🖊️ الدرجات لـ: **{target}**")
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

        elif menu == "📝 سجل السلوك":
            st.header("📝 السجل السلوكي")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                target = st.selectbox("الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == target]['id'].values[0])
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

    # --- واجهة الطالب (تصميم احترافي) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.markdown(f"<h1 class='header-text'>🎓 Student Academic Report</h1>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>بإشراف الأستاذ زياد المعمري</h4>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown(f"""
            <div class='report-card'>
                <h4>👤 {info['name']}</h4>
                <p>📚 المادة: {info['subject']} | 🗓️ العام: {info['academic_year']}</p>
                <p>🏫 {info['level']} - {info['grade_class']} | {info['semester']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("### 📊 الدرجات الدراسية")
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة الأولى", f"{g_data.iloc[0]['p1']} / 20")
            c2.metric("الفترة الثانية", f"{g_data.iloc[0]['p2']} / 20")
            c3.metric("المشاركة والمهام", f"{g_data.iloc[0]['perf']} / 40")
        
        st.divider()
        st.write("### 📅 ملاحظات المعلم")
        b_data = pd.read_sql_query("SELECT date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty: st.table(b_data)
        else: st.info("السجل نظيف")
