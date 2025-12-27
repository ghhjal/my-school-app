import streamlit as st
import pandas as pd
import sqlite3

# --- 1. الإعدادات الجمالية الاحترافية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; background-color: #1e3a8a; color: white; border: none; font-weight: bold; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 6px solid #1e3a8a; }
    .stMetric { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات (ضمان وجود كل الحقول) ---
def init_db():
    conn = sqlite3.connect('english_pro_final_v8.db', check_same_thread=False)
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

# --- 3. نظام الجلسة وتسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🇬🇧 نظام الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>نظام رصد درجات اللغة الإنجليزية</h4>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 بوابة المعلم", "🎓 بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("عرض التقرير"):
            res = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not res.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("عذراً، الرقم غير مسجل.")

# --- 4. واجهات النظام ---
else:
    # القائمة الجانبية للمعلم فقط
    if st.session_state.role == 'admin':
        with st.sidebar:
            st.markdown(f"<div style='background:#e0e7ff; padding:15px; border-radius:10px; text-align:center;'><b>أ/ زياد المعمري</b><br>English Teacher</div>", unsafe_allow_html=True)
            st.write("---")
            menu = st.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])
            st.write("---")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.clear()
                st.rerun()

        # --- واجهة إدارة الطلاب (المعلم) ---
        if menu == "👥 إدارة الطلاب":
            st.header("👤 تسجيل وتعديل بيانات الطلاب")
            with st.form("student_form_v8"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب الكامل")
                
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c4.text_input("الصف (مثلاً: سادس أ)")
                
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ"])
                fsem = c6.selectbox("الفصل الدراسي", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"])
                
                if st.form_submit_button("✅ حفظ بيانات الطالب"):
                    if fname:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)", 
                                  (int(fid), fname, flevel, fclass, fyear, fsem, "اللغة الإنجليزية"))
                        conn.commit()
                        st.success(f"تم حفظ {fname} بنجاح")
                        st.rerun()
            
            st.divider()
            st.subheader("📋 القائمة الحالية للطلاب")
            all_students = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in all_students.iterrows():
                col_i, col_d = st.columns([5, 1])
                with col_i:
                    st.markdown(f"<div class='card'><b>{r['name']}</b> | {r['grade_class']} | {r['academic_year']}</div>", unsafe_allow_html=True)
                if col_d.button("🗑️ حذف", key=f"del_{r['id']}"):
                    c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

        # --- واجهة رصد الدرجات (المعلم) ---
        elif menu == "📊 رصد الدرجات":
            st.header("📊 رصد درجات الإنجليزي")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                with st.form("grade_form"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0)
                    pf = g3.number_input("المشاركة", 0.0, 40.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث بنجاح")
            else: st.warning("لا يوجد طلاب مسجلون")

        # --- واجهة سجل السلوك (المعلم) ---
        elif menu == "📅 سجل السلوك":
            st.header("📅 إدارة سلوك الطلاب")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                t_name = st.selectbox("الطالب", st_df['name'])
                t_id = int(st_df[st_df['name'] == t_name]['id'].values[0])
                with st.form("behavior_form"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة السجل"):
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", 
                                  (t_id, str(dt), "", tp, nt))
                        conn.commit()
                        st.success("تمت الإضافة")
            else: st.warning("لا يوجد طلاب")

    # --- واجهة الطالب (نظيفة بدون قائمة جانبية) ---
    elif st.session_state.role == 'student':
        # إخفاء القائمة الجانبية تماماً للطالب
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        col_out, _ = st.columns([1, 5])
        if col_out.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

        st.markdown(f"<h2 style='text-align: center;'>🎓 تقرير الطالب: {info['name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>بإشراف الأستاذ زياد المعمري | {info['level']} - {info['grade_class']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>العام الدراسي: {info['academic_year']} | {info['semester']}</p>", unsafe_allow_html=True)
        
        st.write("---")
        # عرض الدرجات كبطاقات مترية
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        c1, c2, c3 = st.columns(3)
        if not g.empty:
            c1.metric("الفترة 1", f"{g.iloc[0]['p1']} / 20")
            c2.metric("الفترة 2", f"{g.iloc[0]['p2']} / 20")
            c3.metric("المشاركة والمهام", f"{g.iloc[0]['perf']} / 40")
        else:
            st.info("لم يتم رصد درجات لهذا الطالب بعد.")
        
        st.write("---")
        st.subheader("📅 سجل الملاحظات والسلوك")
        b_data = pd.read_sql_query("SELECT date AS التاريخ, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty:
            st.table(b_data) # عرض الجدول بشكل صحيح للطالب
        else:
            st.info("السجل نظيف، لا توجد ملاحظات سلوكية حالياً.")
