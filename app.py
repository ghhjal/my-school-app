import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

# تنسيق CSS احترافي للوضوح العالي في الجوال
st.markdown("""
    <style>
    [data-testid="stMetricLabel"] { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; opacity: 1 !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
    .main { background-color: #f8f9fa; direction: rtl; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    /* تنسيق خاص لتنبيه الاختبار */
    .exam-alert { background-color: #fee2e2; border-right: 10px solid #dc2626; padding: 15px; border-radius: 10px; color: #991b1b; font-weight: bold; margin-bottom: 15px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري التعليمية</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب", key="login_sid")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
            if not match.empty:
                st.session_state.role = "student"
                st.session_state.student_id = str(sid_in)
                st.session_state.student_name = match.iloc[0]["الاسم"]
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "📢 إعلانات الاختبارات":
        st.header("📢 إضافة تنبيه اختبار جديد")
        with st.form("exam_form", clear_on_submit=True):
            e_class = st.selectbox("حدد الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("عنوان الاختبار (مثلاً: اختبار الفترة الأولى)")
            e_date = st.date_input("موعد الاختبار", datetime.now())
            if st.form_submit_button("🚀 إرسال التنبيه للطلاب"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.success(f"✅ تم إرسال التنبيه لطلاب الصف {e_class}")
        
        st.divider()
        st.subheader("📋 الاختبارات المعلنة حالياً")
        df_ex = fetch_data_safe("exams", ["الصف", "العنوان", "التاريخ"])
        st.dataframe(df_ex, use_container_width=True, hide_index=True)

    # (بقية أكواد المعلم السابقة للإدارة والدرجات تبقى كما هي)
    elif menu == "👥 إدارة الطلاب":
        st.info("واجهة إدارة الطلاب") # اختصار للكود الأصلي
    elif menu == "📊 الدرجات والسلوك":
        st.info("واجهة الدرجات والسلوك")

# --- 4. واجهة الطالب (مع إضافة التنبيه الذكي) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    # جلب بيانات الطالب والصفوف
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    my_class = my_info["الصف"]

    # --- ميزة التنبيه المحددة للفصل ---
    df_exams = fetch_data_safe("exams", ["الصف", "العنوان", "التاريخ"])
    # البحث عن اختبارات تخص صف هذا الطالب فقط
    my_class_exams = df_exams[df_exams["الصف"] == my_class]
    
    if not my_class_exams.empty:
        for i, row in my_class_exams.iterrows():
            st.markdown(f"""
                <div class='exam-alert'>
                    ⚠️ تنبيه اختبار جديد لطلاب الصف {my_class}:<br>
                    📝 {row['العنوان']} <br>
                    📅 الموعد: {row['التاريخ']}
                </div>
            """, unsafe_allow_html=True)

    # عرض بقية البيانات (الدرجات والسلوك) كما في الكود السابق
    st.metric("الصف الدراسي", my_class)
    st.metric("المادة", my_info["المادة"])
    st.divider()
    st.subheader("📊 تقرير الدرجات")
    # (تكملة عرض جداول الدرجات والسلوك...)
