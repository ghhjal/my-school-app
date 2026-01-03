import streamlit as st
import gspread
import pandas as pd
import hashlib
import datetime
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2. تعريف الدوال الأساسية (حل مشكلة NameError)
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame()

# 3. تصميم الواجهة (حل مشكلة النصوص المشوهة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-head { background: #1e40af; padding: 30px; color: white; text-align: center; border-radius: 15px; margin-bottom: 20px; }
    </style>
    <div class="main-head">
        <h1>🏛️ منصة زياد الذكية</h1>
        <p>مرحباً بك في نظامك التعليمي المتطور</p>
    </div>
""", unsafe_allow_html=True)

# 4. منطق الدخول
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطالب", "🔒 بوابة المعلم"])
    
    with t1:
        with st.form("student_login"):
            sid = st.text_input("الرقم الأكاديمي")
            if st.form_submit_button("دخول 🚀"):
                df = fetch_safe("students")
                if not df.empty:
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    if sid.strip() in df.iloc[:, 0].values:
                        st.session_state.role = "student"
                        st.session_state.sid = sid.strip()
                        st.rerun()
                    else: st.error("الرقم غير مسجل")

    with t2:
        with st.form("teacher_login"):
            user = st.text_input("اسم المستخدم")
            pwd = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول آمن 🔐"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == user.strip()]
                    if not row.empty:
                        hashed = hashlib.sha256(str.encode(pwd)).hexdigest()
                        # مقارنة مع الهاش الموجود في صورتك (image_31085e)
                        if hashed == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"
                            st.rerun()
                        else: st.error("كلمة المرور خطأ")
    st.stop()

# 5. الواجهة بعد الدخول (مثال للمعلم)
if st.session_state.role == "teacher":
    st.success("أهلاً بك يا أستاذ زياد في لوحة التحكم")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
