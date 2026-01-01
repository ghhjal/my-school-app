import streamlit as st
import gspread
import pandas as pd
import hashlib
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة والتنسيق (RTL)
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .stTextInput input { border-radius: 12px !important; text-align: right !important; }
    .stButton>button { width: 100%; border-radius: 12px !important; background-color: #2563eb !important; color: white !important; font-weight: bold; }
    .header-box { background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); padding: 30px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -60px -20px 20px -20px; }
    </style>
    <div class="header-box">
        <h1>منصة الأستاذ زياد</h1>
        <p>نظام تعليمي آمن وذكي</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط والتحقق
def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

@st.cache_resource
def connect_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

client = connect_db()

# 3. منطق تسجيل الدخول
if "user_role" not in st.session_state:
    st.session_state.user_role = None

if st.session_state.user_role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        std_id = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية")
        if st.button("دخول الطالب"):
            if client:
                try:
                    # جلب البيانات وتنظيفها من الصفوف الفارغة
                    df = pd.DataFrame(client.worksheet("students").get_all_records())
                    df = df.dropna(subset=['id']) # حذف الصفوف التي ليس لها ID
                    df['id'] = df['id'].astype(str).str.strip()
                    
                    user_match = df[df['id'] == str(std_id).strip()]
                    
                    if not user_match.empty:
                        st.session_state.user_role = "student"
                        st.session_state.user_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except: st.error("⚠️ حدث خطأ في معالجة البيانات، يرجى المحاولة لاحقاً.")

    with tab2:
        t_user = st.text_input("اسم المستخدم")
        t_pass = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if client:
                try:
                    u_df = pd.DataFrame(client.worksheet("users").get_all_records())
                    user_row = u_df[u_df['username'] == t_user.strip()]
                    if not user_row.empty:
                        if check_hashes(t_pass, user_row.iloc[0]['password_hash']):
                            st.session_state.user_role = "teacher"
                            st.rerun()
                        else: st.error("❌ كلمة المرور خطأ")
                    else: st.error("❌ اسم المستخدم غير موجود")
                except: st.error("⚠️ فشل الاتصال بجدول الصلاحيات")
    st.stop()

# 4. لوحة التحكم
if st.session_state.user_role == "student":
    st.success(f"أهلاً بك: {st.session_state.user_data['name']}")
    st.write(f"نقاطك الحالية: {st.session_state.user_data.get('النقاط', 0)}")
    if st.button("تسجيل خروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.user_role == "teacher":
    st.success("مرحباً بك في لوحة تحكم المعلم")
    if st.button("تسجيل خروج"):
        st.session_state.clear()
        st.rerun()
