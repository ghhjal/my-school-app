import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام قاعدة بيانات مستقرة
    return sqlite3.connect('school_final_system.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. إدارة حالة النموذج (لتفريغ الحقول) ---
if 'st_name' not in st.session_state: st.session_state.st_name = ""
if 'st_id' not in st.session_state: st.session_state.st_id = 1
if 'st_class' not in st.session_state: st.session_state.st_class = ""

def clear_student_fields():
    st.session_state.st_name = ""
    st.session_state.st_id = 1
    st.session_state.st_class = ""

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["بوابة المدير", "بوابة الطالب"])
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
            else: st.error("الرقم غير مسجل")

# --- 4. واجهات البرنامج ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- لوحة تحكم المدير ---
    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # 1. إدارة الطلاب (إضافة / تعديل / حذف / تفريغ)
        if menu == "👥 إدارة الطلاب":
            st.header("👤 تسجيل وتعديل بيانات الطلاب")
            
            # زر تفريغ الحقول لإضافة طالب جديد
            if st.button("➕ إضافة طالب جديد (تفريغ الحقول)"):
                clear_student_fields()
                st.rerun()

            with st.form("student_form"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1, value=st.session_state.st_id)
                fname = c2.text_input("اسم الطالب الكامل", value=st.session_state.st_name)
                flevel = c1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c2.text_input("الصف (مثلاً: أول/أ)", value=st.session_state.st_class)
                
                if st.form_submit_button("حفظ البيانات"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                    conn.commit()
                    st.success(f"تم حفظ بيانات: {fname}")
                    st.rerun()

            st.divider()
            st.subheader("📋 الطلاب المسجلون بالنظام")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    # عرض المرحلة والصف بوضوح كما طلبت
                    col1.write(f"👤 **الاسم:** {r['name']} | **الرقم:** {r['id']}")
                    col2.write(f"🏫 **المرحلة:** {r['level']} | **الصف:** {r['grade_class']}")
                    
                    if col3.button("🗑️ حذف", key=f"del_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # 2. رصد الدرجات (عرض الدرجات بالأسفل)
        elif menu == "📝 رصد الدرجات":
            st.header("📝 رصد الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                # جلب الدرجات الحالية للتعديل
                cur = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur.empty else (cur.iloc[0]['p1'], cur.iloc[0]['p2'], cur.iloc[0]['perf'])

                with st.form("grade_form"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = col3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("حفظ"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم الحفظ")
                        st.rerun()
                
                st.divider()
                st.write(f"📊 **الدرجات الحالية لـ {target_name}:**")
                st.table(cur.rename(columns={'p1':'الفترة 1','p2':'الفترة 2','perf':'المشاركة'}) if not cur.empty else pd.DataFrame())
            else: st.warning("أضف طلاباً أولاً")

        # 3. سجل السلوك
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
                        col_a, col_b = st.columns([5, 1])
                        col_a.write(f"📅 **{ln['date']}** | **{ln['type']}**: {ln['note']}")
                        if col_b.button("🗑️", key=f"del_b_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()

    # --- واجهة الطالب (نظيفة بدون أخطاء) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"🎓 تقرير الطالب: {info['name']}")
        st.subheader(f"المرحلة: {info['level']} | الصف: {info['grade_class']}")
        
        # الدرجات
        g_df = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g_df.empty:
            st.divider()
            st.write("### 📊 نتائج الفترات")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_df.iloc[0]['p1'])
            c2.metric("الفترة 2", g_df.iloc[0]['p2'])
            c3.metric("المشاركة", g_df.iloc[0]['perf'])
            
        # السلوك
        st.divider()
        st.write("### 📅 سجل السلوك")
        b_df = pd.read_sql_query("SELECT date AS التاريخ, day AS اليوم, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
        if not b_df.empty:
            st.table(b_df)
        else:
            st.info("السجل نظيف")
