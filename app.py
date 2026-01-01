import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة والتصميم (Header & Logo)
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 45px 20px; border-radius: 0 0 35px 35px; color: white; text-align: center;
        margin: -65px -20px 25px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .logo-square {
        background: rgba(255, 255, 255, 0.2); width: 65px; height: 65px; border-radius: 18px;
        margin: 0 auto 12px auto; display: flex; justify-content: center; align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.3); backdrop-filter: blur(5px);
    }
    .logo-square i { font-size: 32px; color: white; }
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; text-align: right !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 12px !important; width: 100%; height: 50px; font-weight: bold; border: none; }
    </style>

    <div class="header-box">
        <div class="logo-square"><i class="bi bi-graph-up-arrow"></i></div>
        <h1 style="margin:0; font-size: 26px;">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.8; font-size: 14px; margin-top: 5px;">نظام تعليمي آمن وذكي</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الأمان والاتصال
def verify_teacher(input_password, stored_hash):
    calc_hash = hashlib.sha256(str.encode(input_password)).hexdigest()
    return calc_hash == stored_hash

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
        st.write("")
        std_id = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية", key="std_field")
        
        if st.button("تسجيل دخول الطالب"):
            if client:
                try:
                    # محاولة جلب البيانات
                    sheet = client.worksheet("students")
                    df = pd.DataFrame(sheet.get_all_records())
                    df['id'] = df['id'].astype(str).str.strip()
                    
                    # التحقق من وجود الرقم
                    match = df[df['id'] == str(std_id).strip()]
                    
                    if not match.empty:
                        st.session_state.user_role = "student"
                        st.session_state.data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        # الرسالة المطلوبة عند إدخال رقم خطأ (فقط هذه الرسالة)
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except Exception:
                    st.error("⚠️ خطأ تقني في معالجة بيانات الطلاب.")
            else:
                st.error("⚠️ تعذر الاتصال بقاعدة البيانات (افحص الإعدادات).")

    with tab2:
        st.write("")
        t_user = st.text_input("اسم المستخدم", key="t_user")
        t_pass = st.text_input("كلمة المرور", type="password", key="t_pass")
        
        if st.button("دخول المعلم"):
            if client:
                try:
                    u_sheet = pd.DataFrame(client.worksheet("users").get_all_records())
                    # البحث عن المعلم
                    user_record = u_sheet[u_sheet['username'] == t_user.strip()]
                    
                    if not user_record.empty:
                        # التحقق من الهاش في عمود password_hash
                        if verify_teacher(t_pass, user_record.iloc[0]['password_hash']):
                            st.session_state.user_role = "teacher"
                            st.rerun()
                        else:
                            st.error("❌ كلمة المرور غير صحيحة")
                    else:
                        st.error("❌ اسم المستخدم غير موجود")
                except Exception:
                    st.error("⚠️ فشل التحقق من صلاحيات المعلم")
    st.stop()

# --- لوحات التحكم بعد الدخول ---
if st.session_state.user_role == "student":
    st.info(f"أهلاً بك يا بطل: {st.session_state.data['name']}")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.user_role == "teacher":
    st.success("أهلاً بك يا أستاذ زياد (لوحة التحكم الآمنة)")
    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()
