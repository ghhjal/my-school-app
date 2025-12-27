import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- 1. التصميم الملكي الاحترافي (CSS) ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    /* الخلفية العامة */
    .main { background-color: #f4f7f9; }
    
    /* الهيدر الملكي */
    .royal-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(30, 58, 138, 0.2);
        margin-bottom: 25px;
        border-bottom: 5px solid #fbbf24; /* خط ذهبي */
    }
    
    /* بطاقات الطلاب والنتائج */
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-right: 8px solid #1e3a8a;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1e3a8a;
        color: white;
        border: none;
        height: 3em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #fbbf24;
        color: #1e3a8a;
    }
    
    /* إخفاء القائمة الجانبية للطالب */
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('english_royal_v10.db', check_same_thread=False)
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

# --- 3. إدارة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown("""
        <div class="royal-header">
            <h1>🇬🇧 نظام رصد درجات اللغة الإنجليزية</h1>
            <h3 style='color: #fbbf24;'>إشراف الأستاذ: زياد المعمري</h3>
        </div>
        """, unsafe_allow_html=True)
    
    col_log, _ = st.columns([1, 1])
    with col_log:
        t1, t2 = st.tabs(["🔐 دخول المعلم", "🎓 دخول الطالب"])
        with t1:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("تسجيل دخول"):
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
                else: st.error("عذراً، الرقم غير مسجل في النظام.")

# --- 4. واجهات النظام ---
else:
    # --- القائمة الجانبية (للمعلم فقط) ---
    if st.session_state.role == 'admin':
        with st.sidebar:
            st.markdown(f"<div style='text-align:center; padding:10px; background:#1e3a8a; color:white; border-radius:10px;'><h4>أ/ زياد المعمري</h4><p>English Teacher</p></div>", unsafe_allow_html=True)
            st.write("---")
            menu = st.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])
            st.write("---")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.clear()
                st.rerun()

        # --- شاشة إدارة الطلاب ---
        if menu == "👥 إدارة الطلاب":
            st.markdown("<h2 style='color:#1e3a8a;'>👥 تسجيل وتعديل بيانات الطلاب</h2>", unsafe_allow_html=True)
            
            col_new, _ = st.columns([1, 4])
            if col_new.button("➕ إضافة/تفريغ الحقول"):
                st.rerun()

            with st.form("st_form"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب الكامل")
                
                c3, c4 = st.columns(2)
                flevel = c3.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c4.text_input("الصف (مثلاً: رابع أ)")
                
                c5, c6 = st.columns(2)
                fyear = c5.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                fsem = c6.selectbox("الفصل الدراسي", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"])
                
                if st.form_submit_button("💾 حفظ بيانات الطالب"):
                    if fname:
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?)", (int(fid), fname, flevel, fclass, fyear, fsem))
                        conn.commit()
                        st.success(f"تم حفظ الطالب {fname} بنجاح")
                        st.rerun()

            st.divider()
            st.subheader("📋 قائمة الطلاب المسجلين")
            all_st = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in all_st.iterrows():
                col_txt, col_del = st.columns([5, 1])
                col_txt.markdown(f"<div class='card'><b>{r['name']}</b> (ID: {r['id']}) - {r['grade_class']} | {r['academic_year']}</div>", unsafe_allow_html=True)
                if col_del.button("🗑️ حذف", key=f"del_{r['id']}"):
                    c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

        # --- شاشة رصد الدرجات ---
        elif menu == "📊 رصد الدرجات":
            st.markdown("<h2 style='color:#1e3a8a;'>📊 رصد درجات الإنجليزي</h2>", unsafe_allow_html=True)
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                sel_name = st.selectbox("اختر الطالب المراد رصد درجاته", st_list['name'])
                tid = int(st_list[st_list['name'] == sel_name]['id'].values[0])
                
                curr = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if curr.empty else (curr.iloc[0]['p1'], curr.iloc[0]['p2'], curr.iloc[0]['perf'])
                
                with st.form("grade_form"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = g3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("✅ تحديث الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()
                
                st.divider()
                st.subheader("📝 سجل الدرجات الحالي")
                display_grades = pd.read_sql_query("""
                    SELECT s.name AS الطالب, g.p1 AS فترة_1, g.p2 AS فترة_2, g.perf AS مشاركة 
                    FROM students s JOIN grades g ON s.id = g.student_id
                """, conn)
                st.table(display_grades)
            else: st.warning("لا يوجد طلاب مسجلون")

        # --- شاشة سجل السلوك ---
        elif menu == "📅 سجل السلوك":
            st.markdown("<h2 style='color:#1e3a8a;'>📅 إدارة السلوك والملاحظات</h2>", unsafe_allow_html=True)
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                sel_name = st.selectbox("اختر الطالب", st_list['name'])
                tid = int(st_list[st_list['name'] == sel_name]['id'].values[0])
                
                with st.form("beh_form"):
                    d1, d2 = st.columns(2)
                    b_date = d1.date_input("التاريخ", date.today())
                    b_type = d2.selectbox("نوع الملاحظة", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("تفاصيل الملاحظة")
                    if st.form_submit_button("➕ إضافة الملاحظة"):
                        c.execute("INSERT INTO behavior (student_id, date, type, note) VALUES (?,?,?,?)", (tid, str(b_date), b_type, b_note))
                        conn.commit()
                        st.rerun()
                
                st.divider()
                st.subheader(f"📜 ملاحظات الطالب: {sel_name}")
                beh_data = pd.read_sql_query("SELECT id, date, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, b in beh_data.iterrows():
                    col_b1, col_b2 = st.columns([5, 1])
                    col_b1.warning(f"📅 {b['date']} | {b['type']} : {b['note']}")
                    if col_b2.button("🗑️", key=f"bdel_{b['id']}"):
                        c.execute("DELETE FROM behavior WHERE id=?", (b['id'],))
                        conn.commit()
                        st.rerun()

    # --- واجهة الطالب (الملكية) ---
    elif st.session_state.role == 'student':
        # إخفاء القائمة الجانبية تماماً للطالب
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        
        st.markdown(f"""
            <div class="royal-header">
                <h1>🎓 تقرير الطالب: {info['name']}</h1>
                <h3 style='color: #fbbf24;'>إشراف الأستاذ: زياد المعمري</h3>
                <p>{info['level']} | {info['grade_class']} | {info['academic_year']} | {info['semester']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        col_ex, _ = st.columns([1, 5])
        if col_ex.button("🚪 خروج من التقرير"):
            st.session_state.clear()
            st.rerun()

        # عرض الدرجات
        st.write("### 📊 درجات اللغة الإنجليزية")
        g_data = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", f"{g_data.iloc[0]['p1']} / 20")
            c2.metric("الفترة 2", f"{g_data.iloc[0]['p2']} / 20")
            c3.metric("المشاركة والمهام", f"{g_data.iloc[0]['perf']} / 40")
        else: st.info("لم يتم رصد درجات بعد.")

        st.divider()
        # عرض السلوك
        st.write("### 📅 السجل السلوكي والملاحظات")
        b_data = pd.read_sql_query("SELECT date AS التاريخ, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_data.empty:
            st.table(b_data)
        else: st.success("السجل نظيف، استمر في تميزك! 🌟")
