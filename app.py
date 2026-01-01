import streamlit as st
import gspread
import pandas as pd
import html, time
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ إعدادات الهوية والتصميم (منصة الأستاذ زياد)
# ==========================================
st.set_page_config(
    page_title="منصة الأستاذ زياد",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تصميم الـ Header والشعار باستخدام CSS
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
        background-color: #f4f7f9;
    }

    /* هيدر منصة الأستاذ زياد */
    .custom-header {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 30px 20px;
        border-radius: 0 0 40px 40px;
        color: white;
        text-align: center;
        margin: -60px -20px 30px -20px;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
    }

    .logo-container {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        width: 70px;
        height: 70px;
        line-height: 75px;
        border-radius: 20px;
        margin-bottom: 15px;
        font-size: 35px;
        border: 2px solid rgba(255, 255, 255, 0.4);
    }

    .platform-name {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* تحسين البطاقات والحقول */
    .stTextInput input { border-radius: 15px !important; padding: 15px !important; border: 1.5px solid #e2e8f0 !important; }
    .stButton>button { 
        background: #2563eb !important; 
        border-radius: 15px !important; 
        height: 55px !important; 
        font-size: 18px !important; 
    }
    
    /* بطاقة الطالب */
    .student-card {
        background: white;
        padding: 25px;
        border-radius: 25px;
        border-right: 12px solid #2563eb;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    </style>

    <div class="custom-header">
        <div class="logo-container">
            <i class="bi bi-graph-up-arrow"></i>
        </div>
        <div class="platform-name">منصة الأستاذ زياد</div>
        <div style="font-size: 14px; opacity: 0.8;">بوابتك نحو التميز والنجاح</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# 🔒 الاتصال والبيانات
# =========================
@st.cache_resource
def get_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        st.error("⚠️ فشل الاتصال بالخادم")
        st.stop()

sh = get_db()

def fetch_data(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df.astype(str).apply(lambda x: x.str.strip())
        return pd.DataFrame()
    except: return pd.DataFrame()

# =========================
# 🧠 إدارة الجلسة والدخول
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

if not st.session_state.auth:
    tab1, tab2 = st.tabs(["👋 دخول الطالب", "🔒 بوابة المعلم"])
    
    with tab1:
        st.write("")
        sid = st.text_input("أدخل الرقم الأكاديمي الموحد", placeholder="مثال: 26")
        if st.button("دخول آمن للمنصة 🚀", key="std_btn"):
            df = fetch_data("students")
            match = df[df.iloc[:, 0] == sid.strip()]
            if not match.empty:
                st.session_state.auth = True
                st.session_state.role = "student"
                st.session_state.user = sid.strip()
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("⚠️ الرقم غير مسجل في قواعد بيانات المنصة.")

    with tab2:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول الإدارة"):
            df_u = fetch_data("users")
            match = df_u[(df_u['username'] == u) & (df_u['role'] == 'teacher')]
            if not match.empty and p == "1234":
                st.session_state.auth = True
                st.session_state.role = "teacher"
                st.session_state.user = u
                st.rerun()
            else:
                st.error("❌ بيانات الوصول مرفوضة")
    st.stop()

# =========================
# 👨‍🎓 لوحة الطالب الاحترافية
# =========================
if st.session_state.role == "student":
    df_s = fetch_data("students")
    me = df_s[df_s.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        s_data = me.iloc[0]
        st.markdown(f"""
            <div class="student-card">
                <p style="color: #64748b; margin-bottom: 0;">مرحباً بك يا بطل 🌟</p>
                <h1 style="color: #0f172a; margin-top: 0;">{s_data['name']}</h1>
                <div style="display: flex; gap: 20px; margin-top: 15px;">
                    <div style="background: #f1f5f9; padding: 10px 20px; border-radius: 12px;">
                        <b>🔢 الرقم:</b> {s_data['id']}
                    </div>
                    <div style="background: #eff6ff; padding: 10px 20px; border-radius: 12px; color: #2563eb;">
                        <b>🏆 النقاط:</b> {s_data.get('النقاط', '0')}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 عرض درجاتي"):
                st.toast("جاري تحميل النتائج...")
        with col2:
            if st.button("🚪 خروج من المنصة"):
                st.session_state.clear()
                st.rerun()
