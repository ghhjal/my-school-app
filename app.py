import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# التصميم مع الشعار والاسم (RTL)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin: -60px -20px 20px -20px;
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.2);
        width: 60px; height: 60px; border-radius: 15px;
        margin: 0 auto 10px auto; display: flex; justify-content: center; align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .logo-container i { font-size: 30px; color: white; }
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; text-align: right !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 12px !important; width: 100%; height: 50px; font-weight: bold; }
    </style>

    <div class="header-box">
        <div class="logo-container"><i class="bi bi-graph-up-arrow"></i></div>
        <h2 style="margin:0;">منصة الأستاذ زياد</h2>
        <p style="opacity: 0.8; font-size: 14px;">نحو مستقبل تعليمي مشرق</p>
    </div>
    """, unsafe_allow_html=True)

# دالة الاتصال بالبيانات
@st.cache_resource
def get_sheet_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

# نظام الدخول
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 المعلم"])
    
    with tab1:
        st.write("")
        user_input = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="std_id")
        
        if st.button("تسجيل الدخول"):
            if not user_input:
                st.warning("⚠️ يرجى إدخال رقم الهوية أولاً.")
            else:
                client = get_sheet_client()
                if client:
                    try:
                        sheet = client.worksheet("students")
                        # جلب البيانات وتحويلها لجدول
                        df = pd.DataFrame(sheet.get_all_records())
                        
                        # تنظيف البيانات للمقارنة
                        df['id'] = df['id'].astype(str).str.strip()
                        search_id = str(user_input).strip()
                        
                        # البحث عن الرقم
                        match = df[df['id'] == search_id]
                        
                        if not match.empty:
                            st.session_state.auth = True
                            st.session_state.data = match.iloc[0].to_dict()
                            st.success("✅ مرحباً بك! جاري التحميل...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # الرسالة المطلوبة عند إدخال رقم خطأ
                            st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                            
                    except Exception as e:
                        st.error("⚠️ عذراً، حدث خطأ في قراءة بيانات الطلاب.")
                else:
                    st.error("⚠️ فشل الاتصال بقاعدة البيانات.")
    st.stop()

# لوحة الطالب بعد النجاح
if st.session_state.auth:
    std = st.session_state.data
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; border-right: 10px solid #2563eb; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h3 style="margin:0;">مرحباً بك: {std['name']}</h3>
            <p style="color:#64748b;">رقم الهوية: {std['id']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()
