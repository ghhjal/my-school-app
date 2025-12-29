import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- 1. الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

# --- 2. نظام الدخول المتين ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="teacher_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with col2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)", key="student_id")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم الكاملة ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        # --- استعادة شاشة إضافة طالب بكامل حقولها ---
        st.subheader("📝 إضافة طالب جديد")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("الرقم")
            new_name = c2.text_input("الاسم")
            
            c3, c4, c5 = st.columns(3)
            new_class = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            new_year = c4.text_input("العام", value="1446هـ")
            new_sub = c5.text_input("المادة", value="اللغة الإنجليزية")
            
            new_level = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            
            if st.form_submit_button("إضافة الطالب"):
                if new_id and new_name:
                    # الترتيب: id, name, class, year, sem, المرحلة, الإيميل, الجوال, النقاط
                    sh.worksheet("students").append_row([new_id, new_name, new_class, new_year, new_sub, new_level, "", "", 0])
                    st.success(f"تمت إضافة الطالب {new_name} بنجاح ✅")
                    st.rerun()
                else: st.error("يرجى ملء الاسم والرقم")

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with tab1: # تحديث p1, p2, perf
            df_st = fetch_data("students")
            sel_student = st.selectbox("اختر الطالب لتعديل درجته", df_st['name'].tolist())
            with st.form("grades_form"):
                col_g1, col_g2, col_g3 = st.columns(3)
                p1 = col_g1.number_input("ف1")
                p2 = col_g2.number_input("ف2")
                perf = col_g3.number_input("مشاركة")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_student)
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, perf]])
                    except: ws_g.append_row([sel_student, p1, p2, perf])
                    st.success("تم التحديث")

    elif menu == "📢 إعلانات الاختبارات": # شاشة الإعلانات
        st.header("📢 إضافة تنبيه اختبار جديد")
        with st.form("exam_form"):
            e_cls = st.selectbox("حدد الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("عنوان الاختبار")
            e_date = st.date_input("موعد الاختبار")
            if st.form_submit_button("إرسال التنبيه للطلاب 🚀"):
                sh.worksheet("exams").append_row([e_cls, e_title, str(e_date)])
                st.success("تم النشر")

# --- 4. واجهة الطالب (نفس الإعدادات المستقرة) ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    # (كود عرض النتائج وتحديث الإيميل...)
