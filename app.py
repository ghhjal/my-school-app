import streamlit as st
import gspread
import pandas as pd
import hashlib
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة والتصميم
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-box { background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); padding: 30px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -60px -20px 20px -20px; }
    .stTextInput input { border-radius: 10px !important; }
    .stButton>button { width: 100%; border-radius: 10px !important; background-color: #2563eb !important; color: white !important; font-weight: bold; height: 3em; }
    </style>
    <div class="header-box">
        <h1>منصة الأستاذ زياد</h1>
        <p>نظام تعليمي آمن ومشفر</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الربط والتشفير
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

client = get_client()

# 3. إدارة الجلسة
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        # نص التلميح الذي طلبته
        s_id = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية")
        if st.button("تسجيل دخول الطالب"):
            if client:
                try:
                    # جلب ورقة students وتنظيفها
                    ws = client.worksheet("students")
                    df = pd.DataFrame(ws.get_all_records())
                    # تحويل ID لنص وحذف الصفوف الفارغة تماماً
                    df = df[df['id'].astype(str).str.strip() != ""]
                    
                    search_id = str(s_id).strip()
                    user = df[df['id'].astype(str) == search_id]
                    
                    if not user.empty:
                        st.session_state.role = "student"
                        st.session_state.data = user.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except: st.error("⚠️ خطأ في قراءة بيانات الطلاب")

    with tab2:
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if client:
                try:
                    # جلب ورقة users كما في صورتك
                    ws_u = client.worksheet("users")
                    users_df = pd.DataFrame(ws_u.get_all_records())
                    row = users_df[users_df['username'] == u_name.strip()]
                    
                    if not row.empty:
                        # التشفير SHA256 كما في جدولك
                        input_hash = hashlib.sha256(str.encode(u_pass)).hexdigest()
                        if input_hash == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"
                            st.rerun()
                        else: st.error("❌ كلمة المرور غير صحيحة")
                    else: st.error("❌ اسم المستخدم غير موجود")
                except: st.error("⚠️ فشل الاتصال بصلاحيات المعلم")
    st.stop()

# 4. لوحات التحكم
if st.session_state.role == "student":
    st.success(f"أهلاً بك: {st.session_state.data['name']}")
    st.write(f"نقاطك: {st.session_state.data.get('النقاط', 0)}")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.role == "teacher":
    st.success("مرحباً بك أستاذ زياد في لوحة التحكم")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()
