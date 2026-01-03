import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

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

# التصميم بدون تعليقات جانبية لمنع رسائل الخطأ العلوية
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px;
        border-radius: 0 0 40px 40px;
        color: white !important;
        text-align: center;
        margin: -80px -20px 30px -20px;
    }
    .logo-box {
        background: rgba(255, 255, 255, 0.1);
        width: 75px;
        height: 75px;
        border-radius: 18px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .logo-box i { font-size: 38px; color: white; }
    div[data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px !important;
        padding: 30px !important;
    }
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        height: 3.5em !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="hero-container">
        <div class="logo-box"><i class="bi bi-graph-up-arrow"></i></div>
        <h1 style="font-weight: 700; color: white !important; margin:0;">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.9; color: white !important;">نظام الإدارة المدرسية المتكامل</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    hour = datetime.datetime.now().hour
    greet = "صباح الخير والتميز ☀️" if 5 <= hour < 12 else "مساء الطموح والنجاح ✨"
    st.markdown(f"<h3 style='text-align:center;'>{greet}</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([0.05, 0.9, 0.05])
    
    with col:
        tab1, tab2 = st.tabs(["🎓 دخول الطلاب", "🔐 بوابة الإدارة"])
        
        with tab1:
            with st.form("st_log"):
                sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم هويتك")
                if st.form_submit_button("دخول للمنصة 🚀"):
                    df = fetch_safe("students")
                    if not df.empty and sid:
                        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                        if sid.strip() in df.iloc[:, 0].values:
                            st.session_state.role = "student"; st.session_state.sid = sid.strip()
                            st.balloons(); time.sleep(1); st.rerun()
                        else: st.error("عذراً، الرقم غير مسجل")

        with tab2:
            with st.form("te_log"):
                user = st.text_input("👤 اسم المستخدم")
                pwd = st.text_input("🔑 كلمة المرور", type="password")
                if st.form_submit_button("تسجيل الدخول الآمن 🔒"):
                    u_df = fetch_safe("users")
                    if not u_df.empty:
                        row = u_df[u_df['username'] == user.strip()]
                        if not row.empty:
                            # مطابقة الهاش الموجود في جدولك
                            hashed = hashlib.sha256(str.encode(pwd)).hexdigest()
                            if hashed == row.iloc[0]['password_hash']:
                                st.session_state.role = "teacher"; st.rerun()
                            else: st.error("كلمة المرور غير صحيحة")
                        else: st.error("المستخدم غير موجود")

    st.markdown("<p style='text-align:center; opacity:0.5; font-size:12px; margin-top:30px;'>جميع الحقوق محفوظة لمنصة الأستاذ زياد © 2026</p>", unsafe_allow_html=True)
    st.stop()

if st.session_state.role:
    st.success("تم الدخول بنجاح!")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
