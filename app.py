import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال الآمن (تجنب الشاشة البيضاء) ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

def get_db_safe():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # تأكد من وجود secrets في Streamlit Cloud
        if "gcp_service_account" not in st.secrets:
            st.error("⚠️ ملف المفاتيح (Secrets) غير موجود!")
            return None
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {str(e)}")
        return None

sh = get_db_safe()

# دالة جلب البيانات مع حماية من الفشل
def load_data(sheet_name):
    if sh:
        try:
            data = sh.worksheet(sheet_name).get_all_records()
            return pd.DataFrame(data)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 2. نظام تسجيل الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    tab1, tab2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with tab1:
        pwd = st.text_input("كلمة المرور", type="password", key="t_pass")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
    with tab2:
        sid_l = st.text_input("الرقم الأكاديمي", key="s_id")
        if st.button("دخول الطالب"):
            if sid_l:
                st.session_state.role = "student"
                st.session_state.student_id = sid_l
                st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t_reg, t_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with t_reg:
            with st.form("new_student"):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    # استعادة الحقول المفقودة
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

        with t_view:
            search_q = st.text_input("🔍 بحث...")
            df_st = load_data("students")
            if not df_st.empty:
                df_st.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                filt = df_st[df_st.apply(lambda r: search_q in str(r["اسم الطالب"]) or search_q in str(r["الرقم الأكاديمي"]), axis=1)]
                st.dataframe(filt, use_container_width=True, hide_index=True)

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = load_data("students")
        if not df_all.empty:
            names = df_all["اسم الطالب"].tolist()
            t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with t_g:
                with st.form("g_up"):
                    sel_st = st.selectbox("اختر الطالب", names)
                    c1, c2, c3 = st.columns(3)
                    p1, p2, pf = c1.number_input("الفترة 1"), c2.number_input("الف
