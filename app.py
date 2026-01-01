import streamlit as st
import gspread
import pandas as pd
import hashlib, html, uuid, time
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات الصفحة
# =========================
st.set_page_config(page_title="منصة تعليمية آمنة", layout="wide")

# =========================
# 🔒 اتصال Google Sheets
# =========================
@st.cache_resource
def get_db():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        st.stop()

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# =========================
# 🛡️ أدوات الأمان
# =========================
def hash_pwd(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def clean(x): 
    return html.escape(str(x).strip())

def rate_limit(sec=4):
    now = time.time()
    if "last_attempt" in st.session_state:
        if now - st.session_state.last_attempt < sec:
            st.warning(f"⏳ فضلاً انتظر {sec} ثوانٍ")
            st.stop()
    st.session_state.last_attempt = now

def require(role):
    if not st.session_state.get("auth"):
        st.stop()
    if st.session_state.role != role:
        st.error("🚫 غير مصرح لك بالدخول لهذه الصفحة")
        st.stop()

def log(action):
    try:
        sh.worksheet("logs").append_row([
            st.session_state.get("user", "unknown"),
            action,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    except:
        pass

# =========================
# 🧠 إدارة الجلسة (Session State)
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 نظام تسجيل الدخول
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول للمنصة")
    
    with st.container():
        u = clean(st.text_input("اسم المستخدم"))
        p = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول", use_container_width=True):
            rate_limit()
            df_users = fetch("users")
            
            if not df_users.empty:
                h = hash_pwd(p)
                # التأكد من مطابقة اسم المستخدم وكلمة المرور
                user_match = df_users[(df_users['username'] == u) & (df_users['password_hash'] == h)]
                
                if not user_match.empty:
                    st.session_state.auth = True
                    st.session_state.role = user_match.iloc[0]['role']
                    st.session_state.user = u
                    log("login")
                    st.success("تم تسجيل الدخول بنجاح!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة")
            else:
                st.error("⚠️ فشل الوصول إلى قائمة المستخدمين")
    st.stop()

# =========================
# 👨‍🏫 لوحة تحكم المعلم
# =========================
if st.session_state.role == "teacher":
    st.sidebar.title(f"مرحباً أ/ {st.session_state.user}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        log("logout")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    menu = st.sidebar.selectbox("القائمة الرئيسية", [
        "👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"
    ])

    if menu == "👥 الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(fetch("students"), use_container_width=True)

        with st.form("add_student", clear_on_submit=True):
            sid = clean(st.text_input("الرقم الأكاديمي (Username)"))
            name = clean(st.text_input("اسم الطالب بالكامل"))
            if st.form_submit_button("➕ إضافة طالب جديد"):
                if sid and name:
                    rate_limit()
                    sh.worksheet("students").append_row([
                        str(uuid.uuid4()), sid, name, "نشط", "0"
                    ])
                    log(f"added student: {sid}")
                    st.success("تمت إضافة الطالب بنجاح")
                    st.rerun()
                else:
                    st.warning("يرجى ملء جميع الحقول")

    elif menu == "📝 الدرجات":
        st.header("📝 رصد درجات الطلاب")
        st.dataframe(fetch("grades"), use_container_width=True)

    elif menu == "🎭 السلوك":
        st.header("🎭 سجل السلوك والمنضبط")
        st.dataframe(fetch("behavior"), use_container_width=True)

    elif menu == "📢 الاختبارات":
        st.header("📢 جدول الاختبارات")
        st.dataframe(fetch("exams"), use_container_width=True)

# =========================
# 👨‍🎓 لوحة الطالب
# =========================
elif st.session_state.role == "student":
    st.title(f"👨‍🎓 لوحة الطالب")
    if st.sidebar.button("🚪 خروج"):
        log("logout")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # جلب بيانات الطالب بناءً على اسم المستخدم الخاص به
    df_students = fetch("students")
    # البحث في العمود الثاني (index 1) الذي يمثل الرقم الأكاديمي/Username
    me = df_students[df_students.iloc[:, 1] == st.session_state.user]

    if not me.empty:
        student_name = me.iloc[0, 2]
        st.info(f"مرحباً بك الطالب: **{student_name}**")

        t1, t2, t3 = st.tabs(["📢 جدول الاختبارات", "📊 كشف الدرجات", "🎭 سجل السلوك"])

        with t1:
            st.dataframe(fetch("exams"), use_container_width=True)
        with t2:
            st.dataframe(fetch("grades"), use_container_width=True)
        with t3:
            st.dataframe(fetch("behavior"), use_container_width=True)
    else:
        st.warning("لم يتم العثور على بياناتك في سجل الطلاب. تواصل مع المعلم.")

# =========================
# 🛑 حماية إضافية
# =========================
else:
    st.error("دور المستخدم غير محدد.")
    if st.button("العودة"):
        st.session_state.clear()
        st.rerun()
