import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام رصد الدرجات والسلوك", layout="wide", page_icon="📝")

def get_connection():
    # قاعدة بيانات جديدة لدعم حقول السلوك
    return sqlite3.connect('school_behavior_system.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS grades 
             (student_id INTEGER, p1 REAL, p2 REAL, part REAL, proj REAL, total REAL, 
              pos_behavior TEXT, neg_behavior TEXT)''')
conn.commit()

# --- 2. إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["المدير", "الطالب"])
    with t1:
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("رقم الطالب الأكاديمي", min_value=1, step=1)
        if st.button("عرض نتيجتي"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 4. بعد الدخول ---
else:
    st.sidebar.button("تسجيل الخروج", on_click=logout)

    if st.session_state.role == 'admin':
        menu = ["إدارة الطلاب", "رصد الدرجات والسلوك"]
        choice = st.sidebar.selectbox("القائمة", menu)

        if choice == "إدارة الطلاب":
            st.header("👥 تسجيل طالب جديد")
            with st.form("add_std"):
                c1, c2 = st.columns(2)
                nid = c1.number_input("الرقم الأكاديمي", min_value=1)
                nname = c2.text_input("اسم الطالب")
                nlevel = st.selectbox("المستوى", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?)", (int(nid), nname, nlevel))
                    conn.commit()
                    st.success("تم الحفظ")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

        elif choice == "رصد الدرجات والسلوك":
            st.header("📝 رصد الدرجات والملاحظات السلوكية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                s_name = st.selectbox("اختر الطالب", st_df['name'])
                sid = int(st_df[st_df['name'] == s_name]['id'].values[0])
                
                with st.form("grade_behavior_form"):
                    st.subheader("أولاً: الدرجات الأكاديمية")
                    col1, col2 = st.columns(2)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0)
                    part = col1.number_input("المشاركة", 0.0, 10.0)
                    proj = col2.number_input("المشاريع", 0.0, 10.0)
                    
                    st.subheader("ثانياً: سجل السلوك والملاحظات")
                    pos_b = st.text_area("السلوك الإيجابي (نقاط القوة والتميز)", placeholder="مثال: طالب مبادر، يشارك بفعالية في الحصة...")
                    neg_b = st.text_area("الملاحظات السلوكية (تحتاج تطوير)", placeholder="مثال: يحتاج للتركيز أكثر، يتحدث جانبيًا أحياناً...")
                    
                    if st.form_submit_button("حفظ السجل الكامل"):
                        total = p1 + p2 + part + proj
                        c.execute("DELETE FROM grades WHERE student_id=?", (sid,))
                        c.execute("INSERT INTO grades VALUES (?,?,?,?,?,?,?,?)", 
                                  (sid, p1, p2, part, proj, total, pos_b, neg_b))
                        conn.commit()
                        st.success(f"تم حفظ بيانات الطالب {s_name} بنجاح!")
            else: st.warning("أضف طلاباً أولاً")

    elif st.session_state.role == 'student':
        sid = int(st.session_state.user_id)
        name = pd.read_sql_query("SELECT name FROM students WHERE id = ?", conn, params=(sid,)).iloc[0,0]
        st.title(f"🎓 التقرير الأكاديمي والسلـوكي")
        st.subheader(f"الطالب: {name} | الرقم: {sid}")

        res = pd.read_sql_query("SELECT * FROM grades WHERE student_id = ?", conn, params=(sid,))
        
        if not res.empty:
            st.write("---")
            # قسم الدرجات
            st.subheader("📊 النتائج الأكاديمية")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("الفترة 1", res.iloc[0]['p1'])
            c2.metric("الفترة 2", res.iloc[0]['p2'])
            c3.metric("المشاركة", res.iloc[0]['part'])
            c4.metric("المشاريع", res.iloc[0]['proj'])
            st.info(f"المجموع الكلي: {res.iloc[0]['total']} / 60")

            # قسم السلوك
            st.write("---")
            st.subheader("🎭 سجل الملاحظات السلوكية")
            col_pos, col_neg = st.columns(2)
            
            with col_pos:
                st.success("🌟 السلوك الإيجابي والتميز")
                st.write(res.iloc[0]['pos_behavior'] if res.iloc[0]['pos_behavior'] else "لا توجد ملاحظات مسجلة")
            
            with col_neg:
                st.error("⚠️ ملاحظات للتحسين")
                st.write(res.iloc[0]['neg_behavior'] if res.iloc[0]['neg_behavior'] else "لا توجد ملاحظات مسجلة")
        else:
            st.warning("لم يتم رصد درجاتك أو سلوكك بعد.")
