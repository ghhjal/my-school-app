import streamlit as st
import gspread
import pandas as pd
import hashlib
import datetime
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2. الدوال الأساسية (ضمان استقرار النظام)
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

# 3. اللمسات الاحترافية (CSS المطور)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* تنسيق الخط والاتجاه */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
        background-color: #f0f2f6;
    }
    
    /* الهيدر الاحترافي */
    .hero-section {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 60px 20px;
        border-radius: 0 0 50px 50px;
        color: white;
        text-align: center;
        margin: -80px -20px 40px -20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* تصميم الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 12px !important;
        height: 3.5em !important;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* بطاقة الدخول */
    div[data-testid="stForm"] {
        background: white !important;
        padding: 30px !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.05) !important;
    }
    
    /* إخفاء السايدبار */
    [data-testid="stSidebar"] {display: none !important;}
    </style>
    
    <div class="hero-section">
        <h1 style="font-weight: 700; margin-bottom: 10px;">🏛️ منصة زياد الذكية</h1>
        <p style="font-size: 1.1em; opacity: 0.9;">مستقبلك يبدأ هنا.. دخول آمن وذكي</p>
    </div>
""", unsafe_allow_html=True)

# 4. منطق الدخول والترحيب
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    # رسالة ترحيب ذكية
    hour = datetime.datetime.now().hour
    msg = "صباح الخير والتميز ☀️" if 5 <= hour < 12 else "مساء النور والإبداع ✨"
    st.markdown(f"<h3 style='text-align:center; color:#1e3a8a;'>{msg}</h3>", unsafe_allow_html=True)
    
    # محاذاة في المنتصف
    _, col_main, _ = st.columns([0.1, 0.8, 0.1])
    
    with col_main:
        t1, t2 = st.tabs(["🎓 بوابة الطلاب", "🔒 إدارة المنصة"])
        
        with t1:
            with st.form("st_login"):
                st.write("تسجيل دخول الطالب")
                sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية")
                if st.form_submit_button("دخول للمنصة 🚀"):
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
                            else: st.error("عذراً.. الرقم غير مسجل")

        with t2:
            with st.form("te_login"):
                st.write("منطقة المعلمين والإدارة")
                user = st.text_input("👤 اسم المستخدم")
                pwd = st.text_input("🔑 كلمة المرور", type="password")
                if st.form_submit_button("تسجيل الدخول الآمن 🔐"):
                    df = fetch_safe("users")
                    if not df.empty:
                        row = df[df['username'] == user.strip()]
                        if not row.empty:
                            hashed = hashlib.sha256(str.encode(pwd)).hexdigest()
                            if hashed == row.iloc[0]['password_hash']:
                                st.session_state.role = "teacher"
                                st.rerun()
                            else: st.error("كلمة المرور غير صحيحة")
                        else: st.error("المستخدم غير موجود")

    st.markdown("<br><p style='text-align:center; opacity:0.5;'>منصة زياد الذكية © 2026</p>", unsafe_allow_html=True)
    st.stop()

# 5. الواجهة بعد الدخول (مثال)
if st.session_state.role:
    st.success(f"مرحباً بك مجدداً!")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
