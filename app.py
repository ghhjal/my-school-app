import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    return sqlite3.connect('school_system_v2.db', check_same_thread=False)

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

# --- 3. تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    t1, t2 = st.tabs(["الإدارة", "الطالب"])
    with t1:
        if st.text_input("كلمة المرور", type="password") == "admin123" and st.button("دخول الإدارة"):
            st.session_state.update({'logged_in': True, 'role': 'admin'})
            st.rerun()
    with t2:
        sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("دخول الطالب"):
            if not pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid),)).empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid)})
                st.rerun()
            else: st.error("غير مسجل")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        choice = st.sidebar.radio("القائمة", ["👥 الطلاب", "📝 الدرجات", "📅 السلوك"])

        # --- قسم الطلاب (إضافة / تعديل / حذف) ---
        if choice == "👥 الطلاب":
            st.header("👤 إدارة الطلاب")
            with st.expander("➕ إضافة / تحديث طالب"):
                with st.form("student_form"):
                    fid = st.number_input("الرقم الأكاديمي", min_value=1)
                    fname = st.text_input("الاسم الكامل")
                    flevel = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    fclass = st.text_input("الصف")
                    if st.form_submit_button("حفظ البيانات"):
                        c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                        conn.commit()
                        st.success("تم الحفظ")
                        st.rerun()

            st.subheader("قائمة الطلاب")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            for _, r in df_s.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    c1.write(f"**{r['name']}** (ID: {r['id']})")
                    c2.write(f"{r['level']} - {r['grade_class']}")
                    if c3.button("📝 تعديل", key=f"ed_s_{r['id']}"):
                        st.info("قم بتعبئة البيانات في النموذج العلوي مع نفس الرقم الأكاديمي للتعديل")
                    if c4.button("🗑️ حذف", key=f"del_s_{r['id']}"):
                        c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                        c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                        c.execute("DELETE FROM behavior WHERE student_id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

        # --- قسم الدرجات (رصد / تعديل / حذف) ---
        elif choice == "📝 الدرجات":
            st.header("📝 رصد وتعديل الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                # جلب الدرجات الحالية للنموذج إذا وجدت
                existing = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if existing.empty else (existing.iloc[0]['p1'], existing.iloc[0]['p2'], existing.iloc[0]['perf'])

                with st.form("g_form"):
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("الفترة 1", 0.0, 20.0, value=v1)
                    p2 = col2.number_input("الفترة 2", 0.0, 20.0, value=v2)
                    pf = col3.number_input("المشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("حفظ الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()

                st.divider()
                st.subheader(f"📊 الدرجات الحالية لـ: {target}")
                if not existing.empty:
                    st.table(existing.rename(columns={'p1':'الفترة 1','p2':'الفترة 2','perf':'المشاركة'}))
                    if st.button("🗑️ حذف الدرجات بالكامل لهذا الطالب"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.rerun()
            else: st.warning("أضف طلاباً أولاً")

        # --- قسم السلوك (إضافة / حذف المواقف) ---
        elif choice == "📅 السلوك":
            st.header("📅 إدارة سجل السلوك")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target]['id'].values[0])
                
                with st.form("b_form"):
                    dt = st.date_input("التاريخ")
                    tp = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة موقف"):
                        day = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, dt.isoformat(), day, tp, nt))
                        conn.commit()
                        st.rerun()

                st.divider()
                st.subheader(f"📋 سجل المواقف لـ: {target}")
                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        cx, cy = st.columns([4, 1])
                        cx.write(f"[{ln['date']} - {ln['day']}] **{ln['type']}**: {ln['note']}")
                        if cy.button("🗑️ حذف الموقف", key=f"del_b_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()
            else: st.warning("أضف طلاباً أولاً")

    # --- واجهة الطالب (عرض فقط) ---
    else:
        sid = st.session_state.user_id
        info = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,)).iloc[0]
        st.title(f"🎓 تقرير: {info['name']}")
        
        # عرض الدرجات
        g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
        if not g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g.iloc[0]['p1'])
            c2.metric("الفترة 2", g.iloc[0]['p2'])
            c3.metric("المشاركة", g.iloc[0]['perf'])
            
        # عرض السلوك
        st.divider()
        st.subheader("📅 سجل السلوك")
        b = pd.read_sql_query("SELECT date, day, type, note FROM behavior WHERE student_id=?", conn, params=(sid,))
        st.table(b) if not b.empty else st.info("السجل نظيف")
