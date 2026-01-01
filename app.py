import streamlit as st
import gspread
import pandas as pd
import hashlib
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة والتصميم الاحترافي
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-box { background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); padding: 35px; border-radius: 0 0 35px 35px; color: white; text-align: center; margin: -60px -20px 25px -20px; }
    .stTextInput input { border-radius: 12px !important; }
    .stButton>button { width: 100%; border-radius: 12px !important; background-color: #2563eb !important; color: white !important; font-weight: bold; height: 3.2em; border: none; }
    </style>
    <div class="header-box">
        <h1>منصة الأستاذ زياد</h1>
        <p>بوابتك نحو التميز والنجاح الآمن</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الربط والأمان
@st.cache_resource
def get_google_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

client = get_google_client()

# 3. إدارة الجلسات
if "role" not in st.session_state:
    st.session_state.role = None

# --- واجهة تسجيل الدخول ---
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        # نص التلميح الذي طلبته (ادخل رقم الهوية)
        s_input = st.text_input("الرقم الأكاديمي الموحد", placeholder="ادخل رقم الهوية", key="std_login")
        if st.button("تسجيل دخول الطالب 🚀"):
            if client:
                try:
                    # جلب البيانات وتصفية الصفوف الفارغة فوراً لمنع الرسالة الحمراء
                    df_std = pd.DataFrame(client.worksheet("students").get_all_records())
                    # تنظيف البيانات: حذف الصفوف الفارغة تماماً وتحويل ID لنص
                    df_std = df_std[df_std['id'].astype(str).str.strip() != ""]
                    
                    search_id = str(s_input).strip()
                    match = df_std[df_std['id'].astype(str) == search_id]
                    
                    if not match.empty:
                        st.session_state.role = "student"
                        st.session_state.data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        # الرسالة المحددة التي طلبتها عند الخطأ
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except Exception:
                    st.error("⚠️ فشل في معالجة بيانات الطلاب، يرجى التحقق من الجدول.")
            else: st.error("⚠️ مشكلة في الاتصال بالخادم.")

    with tab2:
        u_name = st.text_input("اسم المستخدم", key="teach_user")
        u_pass = st.text_input("كلمة المرور", type="password", key="teach_pass")
        if st.button("دخول المعلم الآمن 🔐"):
            if client:
                try:
                    # جلب ورقة users المشفرة
                    df_users = pd.DataFrame(client.worksheet("users").get_all_records())
                    user_match = df_users[df_users['username'] == u_name.strip()]
                    
                    if not user_match.empty:
                        # تدقيق الهاش SHA-256 كما في عمود password_hash بجدولك
                        input_hash = hashlib.sha256(str.encode(u_pass)).hexdigest()
                        if input_hash == user_match.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"
                            st.rerun()
                        else: st.error("❌ كلمة المرور غير صحيحة")
                    else: st.error("❌ اسم المستخدم غير مسجل")
                except Exception:
                    st.error("⚠️ فشل في التحقق من صلاحيات المعلم.")
    st.stop()

# --- لوحات التحكم بعد النجاح ---
if st.session_state.role == "student":
    u = st.session_state.data
    st.success(f"مرحباً بك يا {u['name']}")
    st.info(f"نقاطك الحالية: {u.get('النقاط', 0)}")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.role == "teacher":
    st.success("أهلاً بك يا أستاذ زياد في بوابة الإدارة")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()
