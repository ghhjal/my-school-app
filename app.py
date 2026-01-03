import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2. تعريف الدوال (لضمان عدم ظهور NameError)
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

# 3. دمج التصميم بالكامل في بلوك واحد (لإخفاء الرسائل العلوية)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }

    /* هيدر متكيف وواضح جداً */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px;
        border-radius: 0 0 40px 40px;
        color: white !important;
        text-align: center;
        margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }

    /* اللوجو العصري */
    .modern-logo {
        background: rgba(255, 255, 255, 0.1);
        width: 70px;
        height: 70px;
        border-radius: 20px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .modern-logo i { font-size: 35px; color: #60a5fa; }

    /* تحسين البطاقة للوضع الداكن */
    div[data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 25px !important;
    }
    
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border-radius: 12px !important;
    }

    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }

    /* إخفاء القائمة الجانبية تماماً */
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    
    <div class="hero-container">
        <div class="modern-logo"><i class="bi bi-rocket-takeoff-fill"></i></div>
        <h1 style="font-weight: 700; color: white !important; margin:0;">منصة زياد الذكية</h1>
        <p style="opacity: 0.8; color: white !important;">بوابتك الرقمية للتميز التعليمي</p>
    </div>
""", unsafe_allow_html=True)

# 4. منطق تسجيل الدخول
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    # رسالة ترحيب حسب الوقت
    hour = datetime.datetime.now().hour
    greeting = "صباح التميز ☀️" if 5 <= hour < 12 else "مساء الإبداع ✨"
    st.markdown(f"<h3 style='text-align:center;'>{greeting}</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([0.05, 0.9, 0.05])
    
    with col:
        tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "🔐 بوابة الإدارة"])
        
        with tab1:
            with st.form("st_login"):
                sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقمك هنا")
                if st.form_submit_button("دخول المنصة 🚀"):
                    df = fetch_safe("students")
                    if not df.empty and sid:
                        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                        if sid.strip() in df.iloc[:, 0].values:
                            st.session_state.role = "student"
                            st.session_state.sid = sid.strip()
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else: st.error("عذراً، الرقم غير مسجل")

        with tab2:
            with st.form("te_login"):
                user = st.text_input("👤 اسم المستخدم")
                pwd = st.text_input("🔑 كلمة المرور", type="password")
                if st.form_submit_button("تسجيل الدخول 🔐"):
                    u_df = fetch_safe("users")
                    if not u_df.empty:
                        row = u_df[u_df['username'] == user.strip()]
                        if not row.empty:
                            hashed = hashlib.sha256(str.encode(pwd)).hexdigest()
                            # التحقق من الهاش
                            if hashed == row.iloc[0]['password_hash']:
                                st.session_state.role = "teacher"
                                st.rerun()
                            else: st.error("كلمة المرور غير صحيحة")
                        else: st.error("المستخدم غير موجود")

    st.markdown("<p style='text-align:center; opacity:0.5; font-size:12px; margin-top:30px;'>منصة زياد الذكية © 2026</p>", unsafe_allow_html=True)
    st.stop()

# 5. الواجهة بعد الدخول
st.success("تم تسجيل الدخول بنجاح!")
if st.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
