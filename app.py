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
            df = pd.DataFrame(data[1:], columns=data[0])
            # تنظيف البيانات من أي مسافات خفية في الجدول نفسه
            return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# =========================
# 🛡️ أدوات الأمان
# =========================
def hash_pwd(password):
    """تشفير كلمة المرور باستخدام SHA-256"""
    return hashlib.sha256(password.encode().strip()).hexdigest()

def clean(x): 
    return html.escape(str(x).strip())

def rate_limit(sec=2):
    now = time.time()
    if "last_attempt" in st.session_state:
        if now - st.session_state.last_attempt < sec:
            st.warning(f"⏳ فضلاً انتظر ثانية...")
            st.stop()
    st.session_state.last_attempt = now

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
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 نظام تسجيل الدخول (معدل)
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول للمنصة")
    
    with st.form("login_form"):
        u_input = st.text_input("اسم المستخدم (Username)")
        p_input = st.text_input("كلمة المرور", type="password")
        submit = st.form_submit_button("دخول", use_container_width=True)

    if submit:
        rate_limit()
        u = clean(u_input).lower() # تحويل لسمول لضمان المطابقة
        h = hash_pwd(p_input)
        
        df_users = fetch("users")
        
        if not df_users.empty:
            # البحث مع تجاهل حالة الأحرف في اسم المستخدم وتنظيف المسافات
            user_match = df_users[
                (df_users['username'].str.lower() == u) & 
                (df_users['password_hash'] == h)
            ]
            
            if not user_match.empty:
                st.session_state.auth = True
                st.session_state.role = user_match.iloc[0]['role'].strip().lower()
                st.session_state.user = user_match.iloc[0]['username']
                log("login")
                st.success("✅ تم التحقق.. جاري التحويل")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة. تأكد من كلمة المرور واسم المستخدم.")
                # لمساعدتك في التصحيح، سأظهر الـ Hash الناتج (يمكنك حذفه لاحقاً)
                st.info(f"الـ Hash لـ '{p_input}' هو: {h}")
        else:
            st.error("⚠️ فشل الوصول إلى ورقة 'users' في الجدول.")
    st.stop()

# =========================
# 👨‍🏫 لوحة تحكم المعلم
# =========================
if st.session_state.role == "teacher":
    st.sidebar.title(f"👨‍🏫 أ/ {st.session_state.user}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.selectbox("القائمة", ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك"])

    if menu == "👥 الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(fetch("students"), use_container_width=True)
        
        with st.form("add_student"):
            sid = clean(st.text_input("الرقم الأكاديمي"))
            name = clean(st.text_input("اسم الطالب"))
            if st.form_submit_button("➕ إضافة"):
                sh.worksheet("students").append_row([str(uuid.uuid4()), sid, name, "نشط", "0"])
                st.success("تمت الإضافة")
                st.rerun()

    elif menu == "📝 الدرجات":
        st.header("📝 الدرجات")
        st.dataframe(fetch("grades"), use_container_width=True)

# =========================
# 👨‍🎓 لوحة الطالب
# =========================
elif st.session_state.role == "student":
    st.sidebar.title(f"👨‍🎓 الطالب: {st.session_state.user}")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    st.title("📊 لوحة بياناتي")
    df_students = fetch("students")
    # البحث عن بيانات الطالب بناءً على اسم المستخدم (الذي يفترض أن يكون هو الرقم الأكاديمي)
    me = df_students[df_students.iloc[:, 1] == st.session_state.user]

    if not me.empty:
        st.info(f"مرحباً بك: **{me.iloc[0, 2]}**")
        t1, t2 = st.tabs(["📊 الدرجات", "🎭 السلوك"])
        with t1: st.dataframe(fetch("grades"), use_container_width=True)
        with t2: st.dataframe(fetch("behavior"), use_container_width=True)
    else:
        st.warning("تم تسجيل دخولك بنجاح كحساب، لكن لم نجد اسمك في ورقة 'students'.")

else:
    st.warning("دور المستخدم غير معرّف بشكل صحيح في الجدول.")
    if st.button("العودة"):
        st.session_state.clear()
        st.rerun()
