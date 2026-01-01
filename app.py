import streamlit as st
import gspread
import pandas as pd
import html, uuid, time
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات الصفحة
# =========================
st.set_page_config(page_title="منصة تعليمية مبسطة", layout="wide")

# =========================
# 🔒 اتصال Google Sheets
# =========================
@st.cache_resource
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        st.stop()

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return pd.DataFrame()
    except: return pd.DataFrame()

# =========================
# 🛡️ أدوات الأمان المبسطة
# =========================
def clean(x): return html.escape(str(x).strip())

# =========================
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 نظام تسجيل الدخول المبسط
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطلاب (بالرقم الأكاديمي)", "👨‍🏫 دخول المعلمين"])
    
    with tab1:
        student_id = st.text_input("أدخل رقمك الأكاديمي", key="s_id")
        if st.button("دخول الطالب"):
            df_std = fetch("students") # البحث في ورقة الطلاب مباشرة
            # التأكد من وجود الرقم في العمود الثاني (الرقم الأكاديمي)
            match = df_std[df_std.iloc[:, 1] == clean(student_id)]
            if not match.empty:
                st.session_state.auth = True
                st.session_state.role = "student"
                st.session_state.user = clean(student_id)
                st.success("مرحباً بك")
                st.rerun()
            else:
                st.error("الرقم الأكاديمي غير مسجل")

    with tab2:
        u_teacher = st.text_input("اسم المستخدم", key="t_u")
        p_teacher = st.text_input("كلمة المرور", type="password", key="t_p")
        if st.button("دخول المعلم"):
            # المعلم يبقى بنظام التحقق من ورقة users للأمان
            df_users = fetch("users")
            # تنبيه: هنا يمكنك إبقاء الـ Hash للمعلم أو مقارنة نص عادي إذا أردت
            # سنفترض أنك وضعت كلمة مرور "1234" نصياً في الجدول لتسهيل الأمر عليك
            match = df_users[(df_users['username'] == u_teacher) & (df_users['role'] == 'teacher')]
            if not match.empty and p_teacher == "1234": # استبدل 1234 بكلمة مرورك
                st.session_state.auth = True
                st.session_state.role = "teacher"
                st.session_state.user = u_teacher
                st.rerun()
            else:
                st.error("بيانات المعلم خاطئة")
    st.stop()

# =========================
# 👨‍🏫 لوحة تحكم المعلم
# =========================
if st.session_state.role == "teacher":
    st.sidebar.success(f"المعلم: {st.session_state.user}")
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.clear()
        st.rerun()
    
    st.header("إدارة بيانات الطلاب")
    df = fetch("students")
    st.dataframe(df, use_container_width=True)
    
    with st.form("add"):
        new_id = st.text_input("الرقم الأكاديمي الجديد")
        new_name = st.text_input("اسم الطالب")
        if st.form_submit_button("إضافة"):
            sh.worksheet("students").append_row([str(uuid.uuid4()), new_id, new_name, "نشط", "0"])
            st.rerun()

# =========================
# 👨‍🎓 لوحة الطالب
# =========================
elif st.session_state.role == "student":
    st.sidebar.info(f"الطالب: {st.session_state.user}")
    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()

    df_students = fetch("students")
    me = df_students[df_students.iloc[:, 1] == st.session_state.user]
    
    if not me.empty:
        st.title(f"👋 أهلاً بك {me.iloc[0, 2]}")
        # عرض الدرجات والسلوك بناءً على رقم الطالب
        st.subheader("📊 نتائجك الدراسية")
        all_grades = fetch("grades")
        my_grades = all_grades[all_grades.iloc[:, 1] == st.session_state.user]
        st.table(my_grades)
    else:
        st.error("لم يتم العثور على بياناتك")
