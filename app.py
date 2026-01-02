import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# =============================
# إعدادات الصفحة
# =============================
st.set_page_config(page_title="منصة الأستاذ زياد التعليمية", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    font-family: 'Cairo', sans-serif;
    direction: RTL;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# =============================
# الاتصال بـ Google Sheets
# =============================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])

sh = get_client()

def fetch_safe(name):
    try:
        ws = sh.worksheet(name)
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df = df.loc[:, df.columns != ""]
        return df
    except:
        return pd.DataFrame()

# =============================
# الجلسة
# =============================
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.sid = None

# =============================
# شاشة الدخول
# =============================
if st.session_state.role is None:
    t1, t2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])

    with t1:
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df = fetch_safe("students")
            if not df.empty and sid in df.iloc[:,0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = sid
                st.rerun()
            else:
                st.error("❌ الرقم غير صحيح")

    with t2:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            df = fetch_safe("users")
            h = hashlib.sha256(p.encode()).hexdigest()
            user = df[(df["username"] == u) & (df["password_hash"] == h)]
            if not user.empty:
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("❌ بيانات الدخول خاطئة")

    st.stop()

# =============================
# واجهة المعلم
# =============================
if st.session_state.role == "teacher":

    t_manage, t_grades, t_behavior, t_exams, t_logout = st.tabs([
        "👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 التنبيهات", "🚗 خروج"
    ])

    # ---------------- الطلاب ----------------
    with t_manage:
        df = fetch_safe("students")
        st.dataframe(df, use_container_width=True)

    # ---------------- الدرجات ----------------
    with t_grades:
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # ---------------- السلوك ----------------
    with t_behavior:
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    # ---------------- التنبيهات ----------------
    with t_exams:
        df = fetch_safe("exams")
        if not df.empty:
            for i, r in df.iloc[::-1].iterrows():
                st.markdown(f"**{r[1]}** — {r[2]}")

    # ---------------- خروج ----------------
    with t_logout:
        if st.button("🚨 تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()

# =============================
# واجهة الطالب
# =============================
elif st.session_state.role == "student":
    st.success("🎓 تم تسجيل دخول الطالب بنجاح")
