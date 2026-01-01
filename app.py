import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# 2. التصميم الاحترافي (Header & Logo)
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
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
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
        <p style="opacity: 0.8; font-size: 14px;">بوابتك نحو التميز والنجاح</p>
    </div>
    """, unsafe_allow_html=True)

# 3. الاتصال ببيانات جوجل
@st.cache_resource
def get_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

client = get_db()

# 4. نظام الجلسات
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.user_data = None

# --- شاشة تسجيل الدخول ---
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        st.write("")
        std_id = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="std_input")
        
        if st.button("دخول الطالب"):
            if not std_id:
                st.warning("⚠️ يرجى كتابة رقم الهوية")
            elif client is None:
                st.error("⚠️ فشل الاتصال بالخادم، تأكد من إعدادات Secrets")
            else:
                try:
                    # جلب ورقة الطلاب
                    sheet = client.worksheet("students")
                    df = pd.DataFrame(sheet.get_all_records())
                    
                    # تنظيف البيانات للمقارنة
                    df['id'] = df['id'].astype(str).str.strip()
                    search_val = str(std_id).strip()
                    
                    # البحث
                    match = df[df['id'] == search_val]
                    
                    if not match.empty:
                        st.session_state.role = "student"
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        # هذه الرسالة التي طلبتها تحديداً
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except:
                    st.error("⚠️ خطأ في قراءة بيانات الجدول.")

    with tab2:
        st.write("")
        admin_user = st.text_input("اسم المستخدم (المعلم)", placeholder="ادخل اسم المستخدم")
        admin_pass = st.text_input("كلمة المرور", type="password", placeholder="ادخل كلمة المرور")
        
        if st.button("دخول المعلم"):
            # يمكنك تغيير admin و 1234 بما يناسبك
            if admin_user == "admin" and admin_pass == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("❌ بيانات دخول المعلم غير صحيحة")
    st.stop()

# --- واجهة الطالب ---
if st.session_state.role == "student":
    u = st.session_state.user_data
    st.success(f"مرحباً بك يا {u['name']}")
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 15px; border-right: 8px solid #2563eb; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3>بياناتك التعليمية</h3>
            <p><b>رقم الهوية:</b> {u['id']}</p>
            <p><b>النقاط:</b> {u.get('النقاط', 0)}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

# --- واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.header("👨‍🏫 لوحة تحكم المعلم")
    if client:
        try:
            sheet = client.worksheet("students")
            df = pd.DataFrame(sheet.get_all_records())
            st.write("قائمة الطلاب الحالية:")
            st.dataframe(df)
        except:
            st.error("تعذر جلب البيانات")
            
    if st.button("خروج"):
        st.session_state.role = None
        st.rerun()
