import streamlit as st
import pandas as pd
import sqlite3

# --- 1. الإعدادات الجمالية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; background-color: #1e3a8a; color: white; border: none; height: 3em; }
    .stButton>button:hover { background-color: #2563eb; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 6px solid #1e3a8a; }
    .grade-display { background: #f1f5f9; padding: 10px; border-radius: 8px; margin-top: 5px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات (مع التحديث التلقائي لمنع اختفاء البيانات) ---
def init_db():
    conn = sqlite3.connect('english_pro_v6.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, 
                  academic_year TEXT, semester TEXT, subject TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
    
    # إصلاح الأخطاء البرمجية عبر إضافة الأعمدة الناقصة تلقائياً
    cols = [col[1] for col in c.execute("PRAGMA table_info(students)").fetchall()]
    for col in [('academic_year', '1447هـ'), ('semester', 'الفصل الأول'), ('subject', 'اللغة الإنجليزية')]:
        if col[0] not in cols:
            c.execute(f"ALTER TABLE students ADD COLUMN {col[0]} TEXT DEFAULT '{col[1]}'")
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. وظائف النظام ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

def clear_form():
    st.session_state.update({"id_key": 1, "name_key": "", "class_key": ""})

# --- 4. تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🇬🇧 نظام إدارة درجات اللغة الإنجليزية")
    st.subheader("إشراف الأستاذ: زياد المعمري")
    t1, t2 = st.tabs(["🔐 بوابة المعلم", "🎓 بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
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

# --- 5. واجهات المعلم ---
else:
    with st.sidebar:
        st.markdown(f"<div style='background:#e0e7ff; padding:10px; border-radius:10px; text-align:center;'><b>أ/ زياد المعمري</b><br>English Teacher</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])
        if st.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

    if st.session_state.role == 'admin':
        if menu == "👥 إدارة الطلاب":
            st.header("إدارة بيانات الطلاب")
            st.button("➕ إضافة طالب جديد", on_click=clear_form)
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1, key="id_key")
                fname = c2.text_input("اسم الطالب", key="name_key")
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c4.text_input("الصف", key="class_key")
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                fsem = c6.selectbox("الفصل", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"])
                if st.form_submit_button("حفظ الطالب"):
                    if fname:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)", 
                                  (int(fid), fname, flevel, fclass, fyear, fsem, "اللغة الإنجليزية"))
                        conn.commit()
                        st.success("تم الحفظ")
                        st.rerun()

            st.divider()
            st.subheader("📋 القائمة الحالية (مع الدرجات)")
            all_st = pd.read_sql_query("""
                SELECT s.id, s.name, s.level, s.grade_class, g.p1, g.p2, g.perf 
                FROM students s LEFT JOIN grades g ON s.id = g.student_id
            """, conn)
            
            for _, r in all_st.iterrows():
                with st.container():
                    col_info, col_act = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"""
                        <div class="card">
                            <b>👤 {r['name']}</b> (ID: {r['id']}) - {r['level']} | {r['grade_class']}
                            <div class="grade-display">
                                الفترة 1: {r['p1'] if r['p1'] is not None else '-'} | 
                                الفترة 2: {r['p2'] if r['p2'] is not None else '-'} | 
                                المشاركة: {r['perf'] if r['perf'] is not None else '-'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    if col_act.button("🗑️ حذف", key=f"del_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        elif menu == "📊 رصد الدرجات":
            st.header("رصد درجات الإنجليزي")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                cur = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur.empty else (cur.iloc[0]['p1'], cur.iloc[0]['p2'], cur.iloc[0]['perf'])
                with st.form("grades"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("تحديث الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()
            else: st.info("لا يوجد طلاب")

        elif menu == "📅 سجل السلوك":
            st.header("إدارة السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                t_name = st.selectbox("الطالب", st_df['name'])
                t_id = int(st_df[st_df['name'] == t_name]['id'].values[0]) # تم إصلاح خطأ NameError هنا
                with st.form("beh"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (t_id, dt.isoformat(), day_ar, tp, nt))
                        conn.commit()
                        st.rerun()
                logs = pd.read_sql_query("SELECT * FROM behavior WHERE student_id=?", conn, params=(t_id,))
                for _, ln in logs.iterrows():
                    st.warning(f"📅 {ln['date']} | {ln['type']}: {ln['note']}")

    # --- واجهة الطالب ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"تقرير الطالب: {info['name']}")
        st.markdown(f"**بإشراف الأستاذ زياد المعمري**")
        st.divider()
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g.iloc[0]['p1'])
            c2.metric("الفترة 2", g.iloc[0]['p2'])
            c3.metric("المشاركة", g.iloc[0]['perf'])
        else: st.info("لم يتم رصد درجات بعد")
