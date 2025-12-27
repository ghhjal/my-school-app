import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات المظهر الاحترافي ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { border-radius: 8px; background-color: #1e3a8a; color: white; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #3b82f6; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .student-card { background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .header-style { color: #1e3a8a; text-align: center; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات مع التحديث التلقائي ---
def init_db():
    conn = sqlite3.connect('english_pro_v5.db', check_same_thread=False)
    c = conn.cursor()
    # إنشاء الجدول الأساسي
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, 
                  academic_year TEXT, semester TEXT, subject TEXT)''')
    
    # التأكد من وجود كافة الأعمدة (لتجنب اختفاء البيانات)
    cols = [col[1] for col in c.execute("PRAGMA table_info(students)").fetchall()]
    needed_cols = [
        ('academic_year', 'TEXT'),
        ('semester', 'TEXT'),
        ('subject', 'TEXT')
    ]
    for col_name, col_type in needed_cols:
        if col_name not in cols:
            c.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")
    
    c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. وظائف التحكم ---
def clear_form():
    st.session_state.update({"id_key": 1, "name_key": "", "level_key": "ابتدائي", "class_key": "", "year_key": "1447هـ", "sem_key": "الفصل الأول"})

# --- 4. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown("<h1 class='header-style'>🇬🇧 نظام رصد درجات اللغة الإنجليزية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>بإشراف الأستاذ زياد المعمري</h3>", unsafe_allow_html=True)
    
    col_l, _ = st.columns([1, 1])
    with col_l:
        tab1, tab2 = st.tabs(["🔐 المعلم", "🎓 الطالب"])
        with tab1:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول النظام"):
                if pwd == "admin123":
                    st.session_state.update({'logged_in': True, 'role': 'admin'})
                    st.rerun()
        with tab2:
            sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            if st.button("استعلام عن التقرير"):
                res = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
                if not res.empty:
                    st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                    st.rerun()
                else: st.error("الرقم غير مسجل")

# --- 5. واجهات النظام ---
else:
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; padding:10px; background:#eef2ff; border-radius:10px;'><b>أ/ زياد المعمري</b><br><small>English Teacher</small></div>", unsafe_allow_html=True)
        menu = st.radio("القائمة", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📝 سجل السلوك"])
        if st.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

    # --- واجهة المعلم ---
    if st.session_state.role == 'admin':
        if menu == "👥 إدارة الطلاب":
            st.markdown("<h2 class='header-style'>إدارة بيانات الطلاب</h2>", unsafe_allow_html=True)
            st.button("➕ إضافة طالب جديد (تفريغ)", on_click=clear_form)
            
            with st.form("main_form"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = c2.text_input("اسم الطالب", key="name_key")
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"], key="level_key")
                fclass = c4.text_input("الصف", key="class_key")
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"], key="year_key")
                fsem = c6.selectbox("الفصل", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"], key="sem_key")
                
                if st.form_submit_button("💾 حفظ البيانات"):
                    if not fname: st.warning("يرجى كتابة الاسم")
                    else:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)", 
                                  (int(fid), fname, flevel, fclass, fyear, fsem, "اللغة الإنجليزية"))
                        conn.commit()
                        st.success("تم الحفظ بنجاح")
                        st.rerun()

            st.markdown("### 📋 الطلاب المسجلون حالياً")
            df_display = pd.read_sql_query("SELECT * FROM students", conn)
            if df_display.empty:
                st.info("لا يوجد طلاب مسجلون بعد.")
            else:
                for _, r in df_display.iterrows():
                    with st.container():
                        col_text, col_btn = st.columns([5, 1])
                        # إصلاح اختفاء البيانات عبر عرض القيم حتى لو كانت فارغة
                        y = r.get('academic_year', 'غير محدد')
                        s = r.get('semester', 'غير محدد')
                        col_text.markdown(f"""
                        <div class='student-card'>
                            <b>👤 {r['name']}</b> (ID: {r['id']})<br>
                            <small>🏫 {r['level']} - {r['grade_class']} | 🗓️ {y} - {s}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        if col_btn.button("🗑️ حذف", key=f"del_{r['id']}"):
                            c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                            c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                            conn.commit()
                            st.rerun()

        elif menu == "📊 رصد الدرجات":
            st.markdown("<h2 class='header-style'>📊 رصد درجات الإنجليزي</h2>", unsafe_allow_html=True)
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                target = st.selectbox("اختر الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == target]['id'].values[0])
                
                cur_g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur_g.empty else (cur_g.iloc[0]['p1'], cur_g.iloc[0]['p2'], cur_g.iloc[0]['perf'])

                with st.form("g_form"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("✅ تحديث الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.rerun()
            else: st.warning("أضف طلاباً من قائمة إدارة الطلاب أولاً")

        elif menu == "📝 سجل السلوك":
            st.markdown("<h2 class='header-style'>📝 ملاحظات السلوك</h2>", unsafe_allow_html=True)
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

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.markdown(f"<h1 class='header-style'>🎓 تقرير مادة {info['subject']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>بإشراف الأستاذ زياد المعمري</p>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='student-card'>
            <h4>👤 الطالب: {info['name']}</h4>
            <p>🏫 {info['level']} - {info['grade_class']} | 🗓️ {info['academic_year']} - {info['semester']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0]['p1'])
            c2.metric("الفترة 2", g_data.iloc[0]['p2'])
            c3.metric("المشاركة", g_data.iloc[0]['perf'])
        
        st.divider()
        st.write("### 📅 سجل السلوك")
        b_data = pd.read_sql_query("SELECT date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty: st.table(b_data)
        else: st.info("السجل نظيف")
