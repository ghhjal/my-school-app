import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ إعدادات الهوية والواجهة (منصة الأستاذ زياد)
# ==========================================
st.set_page_config(
    page_title="منصة الأستاذ زياد",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تضمين مكتبة الأيقونات وتنسيق الواجهة RTL
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
        background-color: #f8fafc;
    }

    /* هيدر المنصة الاحترافي */
    .custom-header {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px;
        border-radius: 0 0 35px 35px;
        color: white;
        text-align: center;
        margin: -65px -20px 30px -20px;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }

    .logo-box {
        background: rgba(255, 255, 255, 0.2);
        width: 70px;
        height: 70px;
        border-radius: 20px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .logo-box i {
        font-size: 35px;
        color: white;
    }

    .platform-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }

    /* تحسين مدخلات الجوال */
    .stTextInput input {
        border-radius: 12px !important;
        padding: 12px !important;
        border: 1.5px solid #e2e8f0 !important;
    }

    .stButton>button {
        background-color: #2563eb !important;
        border-radius: 12px !important;
        height: 50px !important;
        width: 100%;
        font-weight: bold !important;
    }
    </style>

    <div class="custom-header">
        <div class="logo-box">
            <i class="bi bi-graph-up-arrow"></i>
        </div>
        <h1 class="platform-title">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.9; font-size: 14px; margin-top: 5px;">بوابتك نحو التفوق الدراسي</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# 🔒 الاتصال ببيانات الطلاب
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
# 🔐 شاشة تسجيل الدخول
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "🔒 بوابة المعلم"])
    
    with tab1:
        st.write("")
        # تم تعديل التلميح هنا بناءً على طلبك
        sid = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="sid_input")
        if st.button("تسجيل الدخول"):
            df_std = fetch_data("students")
            # التأكد من عمود رقم الطالب (العمود الأول A)
            if not df_std.empty and sid.strip() in df_std.iloc[:, 0].values:
                st.session_state.auth = True
                st.session_state.user = sid.strip()
                st.success("تم الدخول بنجاح!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ الرقم الأكاديمي غير مسجل")

    with tab2:
        st.write("خاص بهيئة التدريس فقط")
    st.stop()

# =========================
# 👨‍🎓 لوحة بيانات الطالب
# =========================
df_all = fetch_data("students")
me = df_all[df_all.iloc[:, 0] == st.session_state.user]

if not me.empty:
    student_name = me.iloc[0, 1] # العمود الثاني هو الاسم
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; border-right: 8px solid #2563eb; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="color: #64748b; margin-bottom: 0;">أهلاً بك يا بطل 🌟</p>
            <h2 style="margin-top: 5px; color: #1e293b;">{student_name}</h2>
            <p><b>رقمك الأكاديمي:</b> {st.session_state.user}</p>
        </div>
    """, unsafe_allow_html=True)

if st.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()
