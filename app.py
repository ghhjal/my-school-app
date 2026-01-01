import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة والهوية (تأكد من وضع هذا في أول السطر)
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# 2. تصميم الواجهة الاحترافي (CSS) - لضمان ظهور اللوجو والاسم والهيدر
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }

    /* الهيدر الملكي */
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px;
        border-radius: 0 0 35px 35px;
        color: white;
        text-align: center;
        margin: -65px -20px 30px -20px;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }

    /* صندوق اللوجو (أيقونة السهم) */
    .logo-container {
        background: rgba(255, 255, 255, 0.2);
        width: 60px;
        height: 60px;
        border-radius: 15px;
        margin: 0 auto 10px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .logo-container i {
        font-size: 30px;
        color: white;
    }
    
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; width: 100%; border-radius: 12px !important; height: 50px !important; font-weight: bold !important; }
    </style>

    <div class="header-container">
        <div class="logo-container">
            <i class="bi bi-graph-up-arrow"></i>
        </div>
        <h2 style="margin:0;">منصة الأستاذ زياد</h2>
        <p style="opacity: 0.8; font-size: 14px;">نحو مستقبل تعليمي مشرق</p>
    </div>
    """, unsafe_allow_html=True)

# 3. وظيفة الاتصال ببيانات جوجل شيت
@st.cache_resource
def connect_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات - تأكد من الإعدادات")
        return None

sh = connect_db()

# 4. شاشة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "🔒 بوابة المعلم"])
    
    with tab1:
        st.write("")
        # التعديل المطلوب: نص التلميح (ادخل رقم الهوية)
        student_id = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="std_login")
        
        if st.button("تسجيل الدخول للمنصة"):
            if sh:
                try:
                    df = pd.DataFrame(sh.worksheet("students").get_all_records())
                    # تنظيف البيانات (حذف المسافات)
                    df = df.astype(str).apply(lambda x: x.str.strip())
                    
                    # البحث في العمود الأول (الذي عنوانه id كما في صورتك)
                    user_match = df[df['id'] == student_id.strip()]
                    
                    if not user_match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_match.iloc[0].to_dict()
                        st.success("تم تسجيل دخولك بنجاح")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ عذراً، رقم الهوية غير مسجل.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء قراءة البيانات: {e}")

    with tab2:
        st.write("بوابة المعلم قيد التحديث...")
    st.stop()

# 5. لوحة الطالب بعد الدخول
if st.session_state.logged_in:
    data = st.session_state.user_data
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; border-right: 10px solid #2563eb; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin:0; color:#0f172a;">مرحباً بك: {data['name']}</h3>
            <p style="color:#64748b; margin-top:5px;">رقمك الأكاديمي الموثق: {data['id']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()
