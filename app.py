import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2. الدوال الأساسية (لضمان عمل النظام بدون أخطاء NameError)
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

# 3. تحسين التصميم للوضع الداكن وإضافة الـ Logo
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }

    /* هيدر متكيف مع الوضعين الفاتح والداكن */
    .hero-section {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 50px 20px;
        border-radius: 0 0 40px 40px;
        color: white !important;
        text-align: center;
        margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    /* تصميم الـ Logo العصري */
    .logo-container {
        background: rgba(255, 255, 255, 0.15);
        width: 80px;
        height: 80px;
        border-radius: 22px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .logo-container i { font-size: 40px; color: white; }

    /* تحسين وضوح النصوص في الوضع الداكن */
    label, p, .stMarkdown {
        color: inherit !important; 
        font-weight: 500;
    }

    /* تحسين شكل بطاقة الدخول لتناسب الوضع الداكن */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 25px !important;
        padding: 30px !important;
    }

    /* أزرار عصرية بلمعة خفيفة */
    .stButton>button {
        border-radius: 15px !important;
        height: 3.8em !important;
        background: #2563eb !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
    }
    
    [data-testid="stSidebar"] {display: none !important;}
    </style>
    
    <div class="hero-section">
        <div class="logo-container">
            <i class="bi bi-rocket-takeoff-fill"></i>
        </div>
        <h1 style="font-weight: 700; color: white !important;">منصة زياد الذكية</h1>
        <p style="opacity: 0.9; color: white !important;">تعليم ذكي.. لمستقبل مشرق</p>
    </div>
""", unsafe_allow_html=True)

# 4. منطق الدخول والترحيب
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    hour = datetime.datetime.now().hour
    msg = "صباح الخير والتميز ☀️" if 5 <= hour < 12 else "مساء النور والإبداع ✨"
    st.markdown(f"<h3 style='text-align:center;'>{msg}</h3>", unsafe_allow_html=True)
    
    _, col_main, _ = st.columns([0.05, 0.9, 0.05])
    
    with col_main:
        t1, t2 = st.tabs(["👨‍🎓 دخول الطلاب", "👨‍🏫 الإدارة"])
        
        with t1:
            with st.form("st_login"):
                sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم هويتك")
                if st.form_submit_button("دخول آمن 🚀"):
                    with st.spinner("جاري التحقق..."):
                        df = fetch_safe("students")
                        if not df.empty:
                            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                            if sid.strip() in df.iloc[:, 0].values:
                                st.session_state.role = "student"
                                st.session_state.sid = sid.strip()
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else: st.error("⚠️ الرقم غير مسجل لدينا")

        with t2:
            with st.form("te_login"):
                user = st.text_input("👤 اسم المستخدم")
                pwd = st.text_input("🔑 كلمة المرور", type="password")
                if st.form_submit_button("تسجيل الدخول 🔐"):
                    df = fetch_safe("users")
                    if not df.empty:
                        row = df[df['username'] == user.strip()]
                        if not row.empty:
                            hashed = hashlib.sha256(str.encode(pwd)).hexdigest()
                            if hashed == row.iloc[0]['password_hash']:
                                st.session_state.role = "teacher"
                                st.rerun()
                            else: st.error("❌ كلمة المرور غير صحيحة")
                        else: st.error("❌ المستخدم غير موجود")

    st.markdown("<br><p style='text-align:center; opacity:0.6; font-size:12px;'>جميع الحقوق محفوظة لمنصة زياد الذكية © 2026</p>", unsafe_allow_html=True)
    st.stop()
