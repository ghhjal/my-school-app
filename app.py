import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال والتحكم في الحصص (Quota) ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة تحديث الدرجات بطلب واحد لتقليل استهلاك Quota
def safe_update_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
        return "✅ تم تحديث الدرجات بنجاح"
    except:
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "✅ تم رصد درجات جديدة"

# --- 2. إدارة الجلسة وزر الخروج الجانبي ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role:
    # إضافة زر الخروج في الشريط الجانبي
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.student_id = None
        st.rerun()

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="p_teacher")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي", key="s_student")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_reg:
            with st.form("main_reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.text_input("الصف", value="الأول")
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                    sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                    st.success("✅ تم التسجيل"); time.sleep(1); st.rerun()

        with tab_view:
            st.subheader("🔍 البحث السريع")
            search_query = st.text_input("ابحث بالاسم أو الرقم الأكاديمي...", placeholder="اكتب
