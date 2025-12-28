import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والربط ---
st.set_page_config(page_title="نظام الإدارة المدرسية المتكامل", layout="wide")

def get_db():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = gspread.authorize(creds)
        # استبدل المعرف أدناه بمعرف ملفك الحقيقي
        return client.open_by_key("YOUR_SHEET_ID_HERE")
    except:
        return None

sh = get_db()

# --- 2. نظام تسجيل الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول الموحدة")
    tab_l1, tab_l2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    
    with tab_l1:
        pwd = st.text_input("كلمة المرور", type="password", key="pwd_teacher")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
            
    with tab_l2:
        sid_login = st.text_input("أدخل الرقم الأكاديمي", key="sid_student")
        if st.button("عرض ملفي"):
            if sid_login:
                st.session_state.role = "student"
                st.session_state.user_id = sid_login
                st.rerun()
            else: st.warning("يرجى إدخال الرقم")
    st.stop()

# --- زر الخروج في الشريط الجانبي ---
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    page = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    # --- شاشة إدارة الطلاب ---
    if page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with t1:
            with st.form("add_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ"):
                    try:
                        ws_students = sh.worksheet("students")
                        ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                        # تحديث ورقة sheet1 أيضاً لضمان دخول الطالب لاحقاً
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success(f"تم حفظ الطالب {sname}")
                        st.rerun()
                    except: st.error("حدث خطأ في الحفظ")

        with t2:
            try:
                ws_students = sh.worksheet("students")
                data = ws_students.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    for i, r in df.iterrows():
                        st.markdown(f"**{r.get('name', r.get('اسم الطالب', '؟'))}** (ID: {r.get('id', r.get('الرقم الأكاديمي', i))})")
                        if st.button("🗑️ حذف", key=f"del_{i}"):
                            ws_students.delete_rows(i + 2)
                            st.rerun()
            except: st.info("لا توجد بيانات طلاب")

    # --- شاشة الدرجات والسلوك ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        try:
            ws_students = sh.worksheet("students")
            all_st = ws_students.get_all_records()
            names_list = [r.get('اسم الطالب', r.get('name', 'بدون اسم')) for r in all_st]
            
            if not names_list:
                st.warning("⚠️ لا يوجد طلاب مسجلون.")
            else:
                t_gr, t_bh = st.tabs(["📝 إدارة الدرجات", "🎭 السلوك والمواظبة"])
                
                with t_gr:
                    with st.form("grades_form", clear_on_submit=True):
                        sel_st = st.selectbox("اختر الطالب", names_list)
                        c1, c2, c3 = st.columns(3)
                        with c1: p1 = st.number_input("P1", min_value=0.0)
                        with c2: p2 = st.number_input("P2", min_value=0.0)
                        with c3: pf = st.number_input("Perf", min_value=0.0)
                        if st.form_submit_button("حفظ الدرجات"):
                            sh.worksheet("grades").append_row([sel_st, p1, p2, pf])
                            st.success(f"تم التحديث لـ {sel_st}")

                with t_bh:
                    with st.form("behavior_form", clear_on_submit=True):
                        sel_b = st.selectbox("اسم الطالب", names_list, key="bh_sel")
                        b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                        b_desc = st.selectbox("الوصف", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
                        if st.form_submit_button("رصد السلوك"):
                            sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_desc])
                            st.success("تم الرصد")
        except: st.error("تأكد من إعداد أوراق العمل بشكل صحيح")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 ملف نتائج الطالب")
    try:
        ws_gr = sh.worksheet("sheet1")
        data = ws_gr.get_all_values()
        # البحث عن رقم الطالب في العمود A
        student_row = next((r for r in data if r[0] == st.session_state.user_id), None)
        
        if student_row:
            st.success(f"أهلاً بك يا {student_row[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", student_row[2])
            c2.metric("الفترة 2", student_row[3])
            c3.metric("الأداء", student_row[4])
        else:
            st.error("الرقم الأكاديمي غير مسجل")
    except: st.info("🔄 جاري تحميل البيانات...")
