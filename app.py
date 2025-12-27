import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. إعدادات الصفحة وقاعدة البيانات ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide", page_icon="🎓")

def get_connection():
    # استخدام اسم قاعدة بيانات جديد لضمان تحديث الجداول بشكل سليم
    return sqlite3.connect('school_management_v5.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول الأساسية مع التأكد من وجود كافة الأعمدة
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, level TEXT, grade_class TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS grades (student_id INTEGER PRIMARY KEY, p1 REAL, p2 REAL, perf REAL)')
c.execute('CREATE TABLE IF NOT EXISTS behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, day TEXT, type TEXT, note TEXT)')
conn.commit()

# --- 2. إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

# --- 3. بوابة الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول للنظام")
    t1, t2 = st.tabs(["بوابة الإدارة", "بوابة الطالب"])
    with t1:
        pwd = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول المدير"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي للطالب", min_value=1, step=1)
        if st.button("عرض تقريري"):
            check = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(int(sid_in),))
            if not check.empty:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم الأكاديمي غير مسجل.")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- واجهة المدير ---
    if st.session_state.role == 'admin':
        choice = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "📅 سجل السلوك"])

        # --- قسم إدارة الطلاب (تم إصلاح العرض لظهور المرحلة والصف) ---
        if choice == "👥 إدارة الطلاب":
            st.header("👤 تسجيل وتعديل بيانات الطلاب")
            with st.form("st_form"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب الكامل")
                flevel = c1.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                fclass = c2.text_input("الصف (مثلاً: أول/أ)")
                if st.form_submit_button("حفظ بيانات الطالب"):
                    c.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?)", (int(fid), fname, flevel, fclass))
                    conn.commit()
                    st.success(f"تم حفظ بيانات الطالب: {fname}")
                    st.rerun()

            st.divider()
            st.subheader("📋 قائمة الطلاب المسجلين حالياً")
            df_s = pd.read_sql_query("SELECT * FROM students", conn)
            
            if df_s.empty:
                st.info("لا يوجد طلاب مسجلين حالياً.")
            else:
                for _, r in df_s.iterrows():
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 2, 1])
                        # عرض كافة البيانات: الاسم، الرقم، المرحلة، والصف
                        col1.write(f"👤 **الاسم:** {r['name']} | **الرقم:** {r['id']}")
                        col2.write(f"🏫 **المرحلة:** {r['level']} | **الصف:** {r['grade_class']}")
                        
                        # أزرار الحذف والتعديل
                        sub_c1, sub_c2 = col3.columns(2)
                        if sub_c1.button("📝", key=f"ed_{r['id']}", help="تعديل: قم بتغيير البيانات في الأعلى واضغط حفظ"):
                            st.info("قم بتعديل البيانات في النموذج العلوي مع بقاء نفس الرقم الأكاديمي.")
                        if sub_c2.button("🗑️", key=f"del_{r['id']}", help="حذف الطالب نهائياً"):
                            c.execute("DELETE FROM students WHERE id=?", (r['id'],))
                            c.execute("DELETE FROM grades WHERE student_id=?", (r['id'],))
                            c.execute("DELETE FROM behavior WHERE student_id=?", (r['id'],))
                            conn.commit()
                            st.rerun()

        # --- قسم الدرجات (مع إمكانية التعديل والحذف) ---
        elif choice == "📝 رصد الدرجات":
            st.header("📝 رصد وتعديل الدرجات")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                # جلب البيانات الحالية لتسهيل التعديل
                cur_g = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(tid,))
                v1, v2, v3 = (0.0, 0.0, 0.0) if cur_g.empty else (cur_g.iloc[0]['p1'], cur_g.iloc[0]['p2'], cur_g.iloc[0]['perf'])

                with st.form("grade_form"):
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("الفترة الأولى", 0.0, 20.0, value=v1)
                    p2 = c2.number_input("الفترة الثانية", 0.0, 20.0, value=v2)
                    pf = c3.number_input("المهام والمشاركة", 0.0, 40.0, value=v3)
                    if st.form_submit_button("تحديث الدرجات"):
                        c.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?)", (tid, p1, p2, pf))
                        conn.commit()
                        st.success(f"تم تحديث درجات الطالب: {target_name}")
                        st.rerun()
                
                if not cur_g.empty:
                    st.divider()
                    st.write(f"📊 **الدرجات الحالية لـ {target_name}:**")
                    st.table(cur_g.rename(columns={'p1':'الفترة 1','p2':'الفترة 2','perf':'المهام'}))
                    if st.button("🗑️ حذف هذه الدرجات"):
                        c.execute("DELETE FROM grades WHERE student_id=?", (tid,))
                        conn.commit()
                        st.rerun()
            else: st.warning("يجب إضافة طلاب أولاً.")

        # --- قسم السلوك (حذف المواقف الفردية) ---
        elif choice == "📅 سجل السلوك":
            st.header("📅 إدارة سجل المواقف السلوكية")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                target_name = st.selectbox("اختر الطالب", st_df['name'])
                tid = int(st_df[st_df['name'] == target_name]['id'].values[0])
                
                with st.form("beh_form"):
                    dt = st.date_input("تاريخ الموقف")
                    tp = st.selectbox("نوع السلوك", ["إيجابي ✅", "سلبي ⚠️"])
                    nt = st.text_area("الملاحظات")
                    if st.form_submit_button("إضافة الموقف للسجل"):
                        day_ar = {"Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة","Saturday":"السبت","Sunday":"الأحد"}[dt.strftime('%A')]
                        c.execute("INSERT INTO behavior (student_id, date, day, type, note) VALUES (?,?,?,?,?)", (tid, dt.isoformat(), day_ar, tp, nt))
                        conn.commit()
                        st.rerun()

                st.divider()
                st.subheader(f"📋 السجل السلوكي لـ {target_name}")
                logs = pd.read_sql_query("SELECT id, date, day, type, note FROM behavior WHERE student_id=?", conn, params=(tid,))
                for _, ln in logs.iterrows():
                    with st.container(border=True):
                        col_a, col_b = st.columns([5, 1])
                        col_a.write(f"📅 **{ln['date']} ({ln['day']})** | **{ln['type']}**: {ln['note']}")
                        if col_b.button("🗑️", key=f"del_b_{ln['id']}"):
                            c.execute("DELETE FROM behavior WHERE id=?", (ln['id'],))
                            conn.commit()
                            st.rerun()
            else: st.warning("يجب إضافة طلاب أولاً.")

    # --- واجهة الطالب (تم إصلاح مشكلة ظهور الكود البرمجي) ---
    elif st.session_state.role == 'student':
        sid = st.session_state.user_id
        info_q = pd.read_sql_query("SELECT * FROM students WHERE id=?", conn, params=(sid,))
        if not info_q.empty:
            info = info_q.iloc[0]
            st.title(f"🎓 التقرير الدراسي لـ: {info['name']}")
            st.subheader(f"المرحلة: {info['level']} | الصف: {info['grade_class']}")
            
            # عرض الدرجات بمربعات ملونة
            g_q = pd.read_sql_query("SELECT * FROM grades WHERE student_id=?", conn, params=(sid,))
            if not g_q.empty:
                st.divider()
                st.write("### 📊 النتائج الدراسية")
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة الأولى", g_q.iloc[0]['p1'])
                c2.metric("الفترة الثانية", g_q.iloc[0]['p2'])
                c3.metric("المهام والمشاركة", g_q.iloc[0]['perf'])
            
            # عرض السلوك (تم إصلاح المشكلة الظاهرة في الصورة 8)
            st.divider()
            st.write("### 📅 السجل السلوكي والملاحظات")
            b_q = pd.read_sql_query("SELECT date AS التاريخ, day AS اليوم, type AS النوع, note AS الملاحظة FROM behavior WHERE student_id=?", conn, params=(sid,))
            
            if not b_q.empty:
                st.table(b_q) # عرض الجدول مباشرة دون كود برمجي إضافي
            else:
                st.info("لا توجد ملاحظات سلوكية مسجلة حالياً.")
