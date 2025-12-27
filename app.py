import streamlit as st
import pandas as pd
import sqlite3

# --- 1. الإعدادات الجمالية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; background-color: #1e3a8a; color: white; border: none; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 6px solid #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('english_pro_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, 
                  academic_year TEXT, semester TEXT, subject TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🇬🇧 نظام الأستاذ زياد المعمري")
    t1, t2 = st.tabs(["🔐 بوابة المعلم", "🎓 بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
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
            else: st.error("عذراً، الرقم غير مسجل.")

# --- 4. واجهات النظام ---
else:
    # زر الخروج يظهر للجميع
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # القائمة الجانبية تظهر للمعلم فقط [إصلاح المشكلة الثانية]
    if st.session_state.role == 'admin':
        st.sidebar.markdown(f"<div style='background:#e0e7ff; padding:10px; border-radius:10px; text-align:center;'><b>أ/ زياد المعمري</b><br>English Teacher</div>", unsafe_allow_html=True)
        menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])

        if menu == "👥 إدارة الطلاب":
            st.header("إدارة بيانات الطلاب")
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب")
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c4.text_input("الصف")
                if st.form_submit_button("حفظ"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)", (int(fid), fname, flevel, fclass, "1447هـ", "الفصل الأول", "اللغة الإنجليزية"))
                    conn.commit()
                    st.rerun()
            
            st.divider()
            st.subheader("📋 القائمة الحالية")
            all_st = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in all_st.iterrows():
                col_i, col_d = st.columns([5,1])
                col_i.info(f"👤 {r['name']} (ID: {r['id']}) - {r['grade_class']}")
                if col_d.button("🗑️", key=f"del_{r['id']}"):
                    c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

        elif menu == "📊 رصد الدرجات":
            st.header("رصد درجات الإنجليزي")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("gr"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0)
                    pf = g3.number_input("المشاركة", 0.0, 40.0)
                    if st.form_submit_button("تحديث"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")

        elif menu == "📅 سجل السلوك":
            st.header("إدارة السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                t_name = st.selectbox("الطالب", st_df['name'])
                t_id = int(st_df[st_df['name'] == t_name]['id'].values[0])
                with st.form("beh"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (t_id, str(dt), "", tp, nt))
                        conn.commit()
                        st.rerun()

    # --- واجهة الطالب (إصلاح المشكلة الأولى) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.markdown(f"<h2>🎓 تقرير الطالب: {info['name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p>بإشراف الأستاذ زياد المعمري | الصف: {info['grade_class']}</p>", unsafe_allow_html=True)
        
        # عرض الدرجات
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g.iloc[0]['p1'])
            c2.metric("الفترة 2", g.iloc[0]['p2'])
            c3.metric("المشاركة", g.iloc[0]['perf'])
        
        st.divider()
        st.subheader("📅 سجل السلوك والملاحظات")
        # استرجاع وعرض جدول السلوك بشكل صحيح [إصلاح المشكلة الأولى]
        b_data = pd.read_sql_query("SELECT date AS التاريخ, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        
        if not b_data.empty:
            st.table(b_data) # عرض الجدول مباشرة للطالب
        else:
            st.info("السجل نظيف، لا توجد ملاحظات سلوكية.")
