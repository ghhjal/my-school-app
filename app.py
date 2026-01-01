import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة الأساسي (يجب أن يكون أول سطر برمي)
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide", initial_sidebar_state="collapsed")

# 2. تعريف التصميم داخل متغير نصي واحد لضمان التنفيذ الصحيح
style_code = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
        background-color: #f8fafc;
    }

    /* الهيدر الاحترافي */
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 45px 20px;
        border-radius: 0 0 35px 35px;
        color: white;
        text-align: center;
        margin: -80px -20px 30px -20px;
    }

    .icon-box {
        background: rgba(255, 255, 255, 0.2);
        width: 60px;
        height: 60px;
        border-radius: 15px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .icon-box i { font-size: 30px; color: white; }
    
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; text-align: right !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; width: 100%; border-radius: 12px !important; height: 50px !important; font-weight: bold !important; border: none; }
</style>

<div class="header-box">
    <div class="icon-box"><i class="bi bi-graph-up-arrow"></i></div>
    <h1 style="margin:0; font-size: 24px;">منصة الأستاذ زياد</h1>
    <p style="opacity: 0.8; font-size: 14px; margin-top: 5px;">بوابتك للنجاح والنمو</p>
</div>
"""

# تنفيذ التصميم
st.markdown(style_code, unsafe_allow_html=True)

# 3. الاتصال بجوجل شيت (باستخدام البيانات من الصور)
@st.cache_resource
def connect_to_sheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

client = connect_to_sheet()

# 4. منطق تسجيل الدخول
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        st.write("")
        # تطبيق طلبك: نص التلميح "ادخل رقم الهوية"
        user_id = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية", key="login_id")
        
        if st.button("تسجيل الدخول"):
            if client:
                try:
                    # قراءة ورقة الطلاب (students)
                    sheet = client.worksheet("students")
                    df = pd.DataFrame(sheet.get_all_records())
                    
                    # البحث في عمود id (العمود الأول A)
                    match = df[df['id'].astype(str).str.strip() == user_id.strip()]
                    
                    if not match.empty:
                        st.session_state.auth_status = True
                        st.session_state.student_info = match.iloc[0].to_dict()
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ الرقم الأكاديمي غير مسجل")
                except:
                    st.error("⚠️ خطأ في الوصول للجدول")
            else:
                st.error("⚠️ فشل الاتصال بالبيانات")
    
    with tab2:
        st.info("بوابة المعلم متاحة عبر لوحة الإدارة فقط حالياً.")
    st.stop()

# 5. واجهة الطالب بعد الدخول
if st.session_state.auth_status:
    std = st.session_state.student_info
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; border-right: 10px solid #2563eb; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h3 style="margin:0; color: #1e293b;">مرحباً بك: {std['name']}</h3>
            <p style="color: #64748b; margin-bottom: 15px;">رقم الهوية: {std['id']}</p>
            <div style="display: flex; gap: 10px;">
                <div style="background: #f1f5f9; padding: 10px; border-radius: 10px; flex: 1; text-align: center;">
                    <small>النقاط</small><br><b>{std.get('النقاط', 0)}</b>
                </div>
                <div style="background: #f1f5f9; padding: 10px; border-radius: 10px; flex: 1; text-align: center;">
                    <small>الصف</small><br><b>{std.get('class', '-')}</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.auth_status = False
        st.rerun()
