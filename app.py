import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة الأساسي
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# 2. تصميم الواجهة (CSS) - حل مشكلة الأيقونة والاسم
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }

    /* هيدر المنصة */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #2563eb 100%);
        padding: 40px 20px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin: -60px -20px 20px -20px;
    }

    .logo-circle {
        background: rgba(255, 255, 255, 0.2);
        width: 65px;
        height: 65px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 10px auto;
        border: 2px solid rgba(255, 255, 255, 0.5);
    }

    .logo-circle i {
        font-size: 30px;
        color: white;
    }

    /* تنسيق الحقول */
    .stTextInput input {
        border-radius: 10px !important;
        padding: 12px !important;
        border: 1px solid #cbd5e1 !important;
    }

    .stButton button {
        width: 100%;
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        height: 3em !important;
        font-weight: bold !important;
    }
    </style>

    <div class="main-header">
        <div class="logo-circle">
            <i class="bi bi-graph-up-arrow"></i>
        </div>
        <h2 style="margin:0;">منصة الأستاذ زياد</h2>
        <p style="font-size: 14px; opacity: 0.8;">بوابتك نحو النجاح والنمو</p>
    </div>
    """, unsafe_allow_html=True)

# 3. الربط مع Google Sheets
@st.cache_resource
def init_connection():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("خطأ في الاتصال بالبيانات")
        return None

client = init_connection()

# 4. نظام تسجيل الدخول
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطلاب", "👨‍🏫 المعلم"])
    
    with tab1:
        # نص التلميح كما طلبت (ادخل رقم الهوية)
        student_id = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية")
        
        if st.button("تسجيل الدخول"):
            if client:
                try:
                    sheet = client.worksheet("students")
                    df = pd.DataFrame(sheet.get_all_records())
                    # مقارنة رقم الهوية بالعمود الأول (id)
                    found = df[df['id'].astype(str).str.strip() == student_id.strip()]
                    
                    if not found.empty:
                        st.session_state.user = found.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("رقم الهوية غير مسجل")
                except:
                    st.error("حدث خطأ في قراءة الجدول")
    st.stop()

# 5. الصفحة الشخصية بعد الدخول
if st.session_state.user:
    u = st.session_state.user
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 15px; border-right: 8px solid #2563eb; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin:0;">مرحباً بك يا {u['name']}</h3>
            <p style="color:#64748b;">رقم الهوية: {u['id']}</p>
            <p><b>🏆 نقاطك الحالية:</b> {u.get('النقاط', 0)}</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()
