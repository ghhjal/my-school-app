import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- 1. الإعدادات الجمالية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .st-emotion-cache-1kyxreq { justify-content: center; }
    .student-card { background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('english_system_v9.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT, 
                  academic_year TEXT, semester TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, type TEXT, note TEXT)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. إدارة الجلسة والدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🇬🇧 نظام الأستاذ زياد المعمري")
    t1, t2 = st.tabs(["🔐 بوابة المعلم", "🎓 بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
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
            else: st.error("الرقم غير مسجل")

# --- 4. واجهة المعلم ---
else:
    if st.session_state.role == 'admin':
        with st.sidebar:
            st.markdown("<div style='text-align:center;'><h3>زياد المعمري</h3><p>English Teacher</p></div>", unsafe_allow_html=True)
            menu = st.radio("التنقل", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])
            if st.button("🚪 خروج"):
                st.session_state.clear()
                st.rerun()

        # --- شاشة إدارة الطلاب ---
        if menu == "👥 إدارة الطلاب":
            st.header("👥 تسجيل وتعديل بيانات الطلاب")
            
            # أزرار التحكم العلوية
            col_btn1, col_btn2 = st.columns([1, 5])
            if col_btn1.button("➕ طالب جديد"):
                st.rerun() # هذا الزر يقوم بتفريغ الحقول عبر إعادة تحميل الصفحة

            with st.form("student_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب الكامل")
                
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c4.text_input("الصف")
                
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام", ["1447هـ", "1448هـ"])
                fsem = c6.selectbox("الفصل", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"])
                
                if st.form_submit_button("💾 حفظ بيانات الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?)", (int(fid), fname, flevel, fclass, fyear, fsem))
                    conn.commit()
                    st.success("تم الحفظ بنجاح")
                    st.rerun()

            st.divider()
            st.subheader("📋 القائمة الحالية")
            all_st = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in all_st.iterrows():
                col_txt, col_del = st.columns([4, 1])
                col_txt.markdown(f"<div class='student-card'>{r['id']} - {r['name']} ({r['grade_class']})</div>", unsafe_allow_html=True)
                if col_del.button("🗑️ حذف", key=f"del_{r['id']}"):
                    c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

        # --- شاشة رصد الدرجات ---
        elif menu == "📊 رصد الدرجات":
            st.header("📊 رصد درجات الإنجليزي")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                # جلب الدرجات الحالية إن وجدت
                curr = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                
                with st.form("grade_form"):
                    g1, g2, g3 = st.columns(3)
                    v1 = curr.iloc[0]['p1'] if not curr.empty else 0.0
                    v2 = curr.iloc[0]['p2'] if not curr.empty else 0.0
                    v3 = curr.iloc[0]['perf'] if not curr.empty else 0.0
                    
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    
                    if st.form_submit_button("📝 تحديث/إضافة الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم تحديث الدرجات")
            
            st.divider()
            st.subheader("📑 سجل الدرجات العام")
            full_grades = pd.read_sql_query("""
                SELECT s.id, s.name, g.p1, g.p2, g.perf 
                FROM students s LEFT JOIN grades g ON s.id = g.student_id
            """, conn)
            st.dataframe(full_grades, use_container_width=True)

        # --- شاشة سجل السلوك ---
        elif menu == "📅 سجل السلوك":
            st.header("📅 إدارة سلوك الطالب")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                sel_st = st.selectbox("الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == sel_st]['id'].values[0])
                
                with st.form("beh_form"):
                    d1, d2 = st.columns(2)
                    bdate = d1.date_input("التاريخ", date.today())
                    btype = d2.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    bnote = st.text_area("الملاحظة")
                    if st.form_submit_button("➕ إضافة للسجل"):
                        c.execute("INSERT INTO behavior (student_id, date, type, note) VALUES (?,?,?,?)", (sid, str(bdate), btype, bnote))
                        conn.commit()
                        st.rerun()

                st.divider()
                st.subheader(f"📜 سجل ملاحظات: {sel_st}")
                beh_list = pd.read_sql_query("SELECT id, date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
                if not beh_list.empty:
                    for _, b in beh_list.iterrows():
                        bc1, bc2 = st.columns([5, 1])
                        bc1.warning(f"{b['date']} | {b['type']} : {b['note']}")
                        if bc2.button("🗑️", key=f"bdel_{b['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (b['id'],))
                            conn.commit()
                            st.rerun()
                else: st.info("لا توجد ملاحظات مسجلة.")

    # --- 5. واجهة الطالب (إخفاء الشريط الجانبي) ---
    elif st.session_state.role == 'student':
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        sid = st.session_state.user_id
        
        # جلب البيانات
        s_info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        s_grades = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        s_beh = pd.read_sql_query("SELECT date, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        
        col_name, col_exit = st.columns([5, 1])
        col_name.title(f"🎓 تقرير الطالب: {s_info['name']}")
        if col_exit.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()
            
        st.write(f"الصف: {s_info['grade_class']} | {s_info['academic_year']} | {s_info['semester']}")
        
        # عرض الدرجات
        st.divider()
        c1, c2, c3 = st.columns(3)
        if not s_grades.empty:
            c1.metric("الفترة 1", s_grades.iloc[0]['p1'])
            c2.metric("الفترة 2", s_grades.iloc[0]['p2'])
            c3.metric("المشاركة", s_grades.iloc[0]['perf'])
        
        # عرض السلوك (جدول نظيف)
        st.divider()
        st.subheader("📅 سجل السلوك والملاحظات")
        if not s_beh.empty:
            st.table(s_beh)
        else:
            st.info("السجل نظيف")
