import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        # تأكد من أن ملف secrets في streamlit يحتوي على بيانات gcp_service_account
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            headers = [h if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            df = pd.DataFrame(data[1:], columns=headers)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المستقلة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("كلمة المرور خاطئة")
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(sid_in)
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (تقسيم الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إ
