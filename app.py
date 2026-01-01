import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# 2. دالة التشفير (لضمان أمان كلمة المرور)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# 3. التصميم الاحترافي (Header & Logo)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px; border-radius: 0 0 30px 30px; color: white; text-align: center;
        margin: -60px -20px 20px -20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.2); width: 60px; height: 60px; border-radius: 15px;
        margin: 0 auto 10px auto; display: flex; justify-content: center; align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .logo-container i { font-size: 30px; color: white; }
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; text-align: right !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 12px !important; width: 100%; height: 50px; font-weight: bold; }
    </style>

    <div class="header-box">
        <div class="logo-container"><i class="bi bi-graph-up-arrow"></i></div>
        <h2 style="margin:0;">منصة الأستاذ زياد</h2>
        <p style="opacity: 0.8; font-size: 14px;">نظام تعليمي آمن ومشفر</p>
    </div>
    """, unsafe_allow_html=True)

# 4. الاتصال ببيانات جوجل
@st.cache_resource
def get_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

client = get_db()

# 5. إدارة الجلسة
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.user_data = None

# --- شاشة تسجيل الدخول ---
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم (مشفر)"])
    
    with tab1:
        st.write("")
        std_id = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="std_input")
        if st.button("دخول الطالب"):
            if client:
                try:
                    df = pd.DataFrame(client.worksheet("students").get_all_records())
                    df['id'] = df['id'].astype(str).str.strip()
                    match = df[df['id'] == str(std_id).strip()]
                    if not match.empty:
                        st.session_state.role = "student"
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except: st.error("⚠️ خطأ في قراءة بيانات الطلاب")

    with tab2:
        st.write("")
        admin_user = st.text_input("اسم المستخدم", placeholder="Username")
        admin_pass = st.text_input("كلمة المرور", type="password", placeholder="Password")
        
        if st.button("دخول المعلم الآمن"):
            if client:
                try:
                    # جلب بيانات المستخدمين من ورقة users
                    user_sheet = pd.DataFrame(client.worksheet("users").get_all_records())
                    # البحث عن المعلم وتدقيق كلمة المرور المشفرة
                    user_row = user_sheet[user_sheet['username'] == admin_user]
                    
                    if not user_row.empty:
                        hashed_pw = user_row.iloc[0]['password']
                        if check_hashes(admin_pass, hashed_pw):
                            st.session_state.role = "teacher"
                            st.rerun()
                        else:
                            st.error("❌ كلمة المرور غير صحيحة")
                    else:
                        st.error("❌ اسم المستخدم غير موجود")
                except: st.error("⚠️ فشل الوصول لجدول الصلاحيات")
    st.stop()

# --- لوحة المعلم بعد الدخول الآمن ---
if st.session_state.role == "teacher":
    st.success("✅ تم الدخول بنظام التشفير الآمن")
    st.header("👨‍🏫 لوحة تحكم المعلم")
    # عرض البيانات...
    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
