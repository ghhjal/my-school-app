import streamlit as st
import gspread
import pandas as pd
import time
from google.oauth2.service_account import Credentials

# إعدادات الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# التصميم الاحترافي (RTL + Header)
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
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 12px !important; width: 100%; height: 50px; font-weight: bold; border: none; }
    </style>

    <div class="header-box">
        <div class="logo-container"><i class="bi bi-graph-up-arrow"></i></div>
        <h2 style="margin:0;">منصة الأستاذ زياد</h2>
        <p style="opacity: 0.8; font-size: 14px;">بوابتك نحو التميز والنجاح</p>
    </div>
    """, unsafe_allow_html=True)

# الاتصال بـ Google Sheets
@st.cache_resource
def get_google_sheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

# شاشة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 بوابة المعلم"])
    
    with tab1:
        st.write("")
        user_id = st.text_input("رقم الهوية الأكاديمي", placeholder="ادخل رقم الهوية", key="id_input")
        
        if st.button("تسجيل الدخول"):
            client = get_google_sheet()
            
            if client is None:
                st.error("⚠️ عذراً، هناك مشكلة فنية في الاتصال بقاعدة البيانات.")
            else:
                try:
                    sheet = client.worksheet("students")
                    data = pd.DataFrame(sheet.get_all_records())
                    
                    # تنظيف المدخلات والبيانات لضمان المطابقة الدقيقة
                    data['id'] = data['id'].astype(str).str.strip()
                    input_id = str(user_id).strip()
                    
                    # البحث عن المستخدم
                    user_row = data[data['id'] == input_id]
                    
                    if not user_row.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_row.iloc[0].to_dict()
                        st.success("✅ مرحباً بك! تم الدخول بنجاح.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        # الرسالة التي طلبتها عند إدخال رقم خطأ
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل في المنصة.")
                        
                except Exception as e:
                    st.error("⚠️ عذراً، تعذر الوصول إلى بيانات الطلاب حالياً.")

    with tab2:
        st.info("بوابة المعلمين متاحة عبر الصلاحيات الإدارية.")
    st.stop()

# لوحة الطالب بعد الدخول
if st.session_state.logged_in:
    u = st.session_state.user_data
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; border-right: 10px solid #2563eb; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h3 style="margin:0;">مرحباً بك: {u['name']}</h3>
            <p style="color:#64748b;">رقم الهوية: {u['id']}</p>
            <div style="display: flex; gap: 20px; margin-top: 15px;">
                <div style="background: #eff6ff; padding: 10px 20px; border-radius: 12px; color: #2563eb;">
                    <b>🏆 النقاط:</b> {u.get('النقاط', 0)}
                </div>
                <div style="background: #f8fafc; padding: 10px 20px; border-radius: 12px;">
                    <b>📚 الصف:</b> {u.get('class', '-')}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()
