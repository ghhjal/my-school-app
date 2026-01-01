import streamlit as st
import gspread
import pandas as pd
import hashlib, html, uuid, time, urllib.parse
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات
# =========================
st.set_page_config(page_title="منصة تعليمية آمنة", layout="wide")

# =========================
# 🔒 اتصال Google Sheets
# =========================
@st.cache_resource
def get_db():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(creds).open_by_key(st.secrets["https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/edit?usp=sharing"])

sh = get_db()

def fetch(sheet):
    try:
        ws = sh.worksheet(sheet)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# =========================
# 🛡️ أدوات الأمان
# =========================
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()
def clean(x): return html.escape(str(x).strip())

def rate_limit(sec=4):
    now = time.time()
    last = st.session_state.get("last", 0)
    if now - last < sec:
        st.warning("⏳ انتظر قليلاً")
        st.stop()
    st.session_state.last = now

def require(role):
    if not st.session_state.get("auth"):
        st.stop()
    if st.session_state.role != role:
        st.error("🚫 غير مصرح")
        st.stop()

def log(action):
    try:
        sh.worksheet("logs").append_row([
            st.session_state.get("user"),
            action,
            datetime.now().isoformat()
        ])
    except:
        pass

# =========================
# 🧠 Session
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 تسجيل الدخول
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")

    u = clean(st.text_input("اسم المستخدم"))
    p = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
        rate_limit()
        df = fetch("users")
        h = hash_pwd(p)
        user = df[(df.username == u) & (df.password_hash == h)]
        if not user.empty:
            st.session_state.auth = True
            st.session_state.role = user.iloc[0].role
            st.session_state.user = u
            log("login")
            st.rerun()
        else:
            st.error("بيانات خاطئة")
    st.stop()

# =========================
# 👨‍🏫 المعلم
# =========================
if st.session_state.role == "teacher":
    require("teacher")

    st.sidebar.title("👨‍🏫 المعلم")
    if st.sidebar.button("🚪 خروج"):
        log("logout")
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.selectbox("القائمة", [
        "👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"
    ])

    # 👥 الطلاب
    if menu == "👥 الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(fetch("students"), use_container_width=True)

        with st.form("add_student"):
            sid = clean(st.text_input("الرقم الأكاديمي"))
            name = clean(st.text_input("الاسم"))
            if st.form_submit_button("➕ إضافة"):
                rate_limit()
                sh.worksheet("students").append_row([
                    str(uuid.uuid4()), sid, name, "نشط", "0"
                ])
                log(f"add_student:{sid}")
                st.success("تمت الإضافة")
                st.rerun()

    # 📝 الدرجات
    elif menu == "📝 الدرجات":
        st.header("📝 رصد الدرجات")
        df = fetch("grades")
        st.dataframe(df, use_container_width=True)

    # 🎭 السلوك
    elif menu == "🎭 السلوك":
        st.header("🎭 رصد السلوك")
        df = fetch("behavior")
        st.dataframe(df, use_container_width=True)

    # 📢 الاختبارات
    elif menu == "📢 الاختبارات":
        st.header("📢 الاختبارات")
        df = fetch("exams")
        st.dataframe(df, use_container_width=True)

# =========================
# 👨‍🎓 الطالب
# =========================
elif st.session_state.role == "student":
    require("student")

    st.title("👨‍🎓 لوحة الطالب")
    if st.button("🚪 خروج"):
        log("logout")
        st.session_state.clear()
        st.rerun()

    df = fetch("students")
    me = df[df.iloc[:,1] == st.session_state.user]

    if not me.empty:
        st.success(f"مرحبًا {me.iloc[0,2]}")

        t1, t2, t3 = st.tabs(["📢 التنبيهات", "📊 الدرجات", "🎭 السلوك"])

        with t1:
            st.dataframe(fetch("exams"), use_container_width=True)

        with t2:
            st.dataframe(fetch("grades"), use_container_width=True)

        with t3:
            st.dataframe(fetch("behavior"), use_container_width=True)

# =========================
# 🛑 حماية أخيرة
# =========================
else:
    st.stop()
