import streamlit as st
import gspread
import pandas as pd
import html, time
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ إعدادات الهوية والتنسيق (منصة الأستاذ زياد)
# ==========================================
st.set_page_config(
    page_title="منصة الأستاذ زياد",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تصميم الـ Header والشعار المطور
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

    /* هيدر احترافي مع ضبط مكان الشعار */
    .custom-header {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px;
        border-radius: 0 0 40px 40px;
        color: white;
        text-align: center;
        margin: -60px -20px 30px -20px;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
    }

    .logo-box {
        display: flex;
        justify-content: center;
        align-items: center;
        background: rgba(255, 255, 255, 0.15);
        width: 80px;
        height: 80px;
        border-radius: 22px;
        margin: 0 auto 15px auto;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(5px);
    }

    .logo-box i {
        font-size: 40px;
        color: white;
        display: block;
    }

    .platform-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
        color: white;
    }

    /* تنسيق الحقول والأزرار */
    .stTextInput input {
        border-radius: 15px !important;
        padding: 15px !important;
        text-align: right !important;
    }
    
    .stButton>button {
        background: #2563eb !important;
        border-radius: 15px !important;
        height: 55px !important;
        font-weight: bold !important;
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
        <div class="logo-box">
            <i class="bi bi-graph-up-arrow"></i>
        </div>
        <div class="platform-title">منصة الأستاذ زياد</div>
        <div style="font-size: 15px; opacity: 0.9;">نحو مستقبل تعليمي مشرق</div>
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
        st.error("⚠️ فشل الاتصال بقاعدة البيانات")
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
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

if not st.session_state.auth:
    tab1, tab2 = st.tabs(["👋 دخول الطالب", "🔒 بوابة المعلم"])
    
    with tab1:
        st.write("")
        # تم تغيير نص التلميح هنا بناءً على طلبك
        sid = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية", key="std_input")
        if st.button("دخول آمن للمنصة 🚀"):
            df = fetch_data("students")
            if not df.empty:
                # البحث في العمود الأول (id)
                match = df[df.iloc[:, 0] == sid.strip()]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.role = "student"
                    st.session_state.user = sid.strip()
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ عذراً، رقم الهوية هذا غير مسجل لدينا.")
            else:
                st.error("⚠️ لم يتم العثور على بيانات الطلاب.")

    with tab2:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل دخول المعلم"):
            df_u = fetch_data("users")
            match = df_u[(df_u['username'] == u) & (df_u['role'] == 'teacher')]
            if not match.empty and p == "1234":
                st.session_state.auth = True
                st.session_state.role = "teacher"
                st.session_state.user = u
                st.rerun()
            else:
                st.error("❌ خطأ في بيانات الدخول")
    st.stop()

# =========================
# 👨‍🎓 لوحة الطالب
# =========================
if st.session_state.role == "student":
    df_s = fetch_data("students")
    me = df_s[df_s.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        s_data = me.iloc[0]
        st.markdown(f"""
            <div class="student-card">
                <p style="color: #64748b; margin-bottom: 5px;">أهلاً بك مجدداً</p>
                <h1 style="color: #0f172a; margin-top: 0;">{s_data['name']}</h1>
                <hr style="opacity: 0.1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="display: block; font-size: 13px; color: #64748b;">رقم الهوية</span>
                        <span style="font-weight: bold; font-size: 18px;">{s_data['id']}</span>
                    </div>
                    <div style="text-align: left;">
                        <span style="display: block; font-size: 13px; color: #64748b;">رصيد النقاط</span>
                        <span style="font-weight: bold; font-size: 22px; color: #2563eb;">{s_data.get('النقاط', '0')}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("🚪 تسجيل الخروج من الحساب", use_container_width=True):
            st.session_state.clear()
            st.rerun()
