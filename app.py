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

# التصميم المطور لإخفاء الرسائل المزعجة وتوضيح الخط
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px;
        border-radius: 0 0 40px 40px;
        color: white;
        text-align: center;
        margin: -80px -20px 30px -20px;
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 70px; height: 70px; border-radius: 18px;
        margin: 0 auto 10px; display: flex; 
        justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 10px !important;
    }
    /* إخفاء رسالة Press Enter to submit */
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:35px; color:white;"></i></div>
        <h1 style="font-size:24px; margin:0;">منصة الأستاذ زياد</h1>
        <p style="opacity:0.8; font-size:14px;">نظام الإدارة المدرسية المتكامل</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    h = datetime.datetime.now().hour
    msg = "صباح التميز ☀️" if 5 <= h < 12 else "مساء النجاح ✨"
    st.markdown(f"<h3 style='text-align:center;'>{msg}</h3>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎓 الطلاب", "🔐 الإدارة"])
    
    with tab1:
        with st.form("st_form"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقمك هنا")
            if st.form_submit_button("دخول الطلاب"):
                df = fetch_safe("students")
                if not df.empty and sid:
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    if sid.strip() in df.iloc[:, 0].values:
                        st.session_state.role = "student"; st.session_state.sid = sid.strip()
                        st.balloons(); time.sleep(1); st.rerun()
                    else: st.error("عذراً، الرقم غير مسجل")

    with tab2:
        with st.form("te_form"):
            u = st.text_input("👤 المستخدم")
            p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u.strip()]
                    if not row.empty:
                        hashed = hashlib.sha256(str.encode(p)).hexdigest()
                        if hashed == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"; st.rerun()
                        else: st.error("خطأ في كلمة المرور")
                    else: st.error("المستخدم غير موجود")
    st.stop()

if st.session_state.role:
    st.success("أهلاً بك في المنصة!")
    if st.button("خروج"):
        st.session_state.role = None; st.rerun()
