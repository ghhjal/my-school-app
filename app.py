import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide", page_icon="🎓")

def get_connection():
    return sqlite3.connect('school_data_v3.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 3. بوابة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["الإدارة", "الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("عرض النتيجة"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        choice = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # --- قسم إدارة الطلاب (حذف وتعديل) ---
        if choice == "👥 إدارة الطلاب":
            st.header("👤 إدارة الطلاب")
            with st.form("st_add"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب")
                flevel = c1.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c2.text_input("الصف")
                if st.form_submit_button("حفظ الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                    conn.commit()
                    st.success("تم الحفظ")
                    st.rerun()

            st.subheader("الطلاب المسجلون")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{r['name']}** (ID: {r['id']})")
                    if col3.button("🗑️ حذف", key=f"del_s_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # --- قسم الدرجات (حذف وتعديل) ---
        elif choice == "📝 رصد الدرجات":
            st.header("📝 رصد الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                # جلب البيانات للتعديل
                cur = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur.empty else (cur.iloc[0]['p1'], cur.iloc[0]['p2'], cur.iloc[0]['perf'])

                with st.form("gr_form"):
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("فترة 1", 0.0, 20.0, value=v1)
                    p2 = c2.number_input("فترة 2", 0.0, 20.0, value=v2)
                    pf = c3.number_input("مشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()
                
                if not cur.empty:
                    st.subheader("الدرجات الحالية")
                    st.table(cur.rename(columns={'p1':'فترة 1','p2':'فترة 2','perf':'مشاركة'}))
                    if st.button("🗑️ حذف الدرجات لهذا الطالب"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.rerun()

        # --- قسم السلوك (حذف المواقف) ---
        elif choice == "📅 سجل السلوك":
            st.header("📅 إدارة السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                with st.form("beh_form"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        day = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, dt.isoformat(), day, tp, nt))
                        conn.commit()
                        st.rerun()

                st.subheader("السجل الحالي")
                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        col1.write(f"[{ln['date']}] {ln['type']}: {ln['note']}")
                        if col2.button("🗑️ حذف الموقف", key=f"del_b_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()

    # --- واجهة الطالب (إصلاح مشكلة العرض في الصورة 8) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"🎓 تقرير: {info['name']}")
        
        # الدرجات
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1", g.iloc[0]['p1'])
            c2.metric("فترة 2", g.iloc[0]['p2'])
            c3.metric("مشاركة", g.iloc[0]['perf'])
            
        # إصلاح كود الجدول (الصورة 8)
        st.subheader("📅 سجل السلوك")
        b = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        
        if not b.empty:
            st.table(b) # تم إصلاح السطر الذي كان يظهر ككود برمجي
        else:
            st.info("السجل نظيف")
