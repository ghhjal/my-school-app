import streamlit as st
import gspread
import pandas as pd
import html, uuid
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات الصفحة
# =========================
st.set_page_config(page_title="منصة مدرستي البسيطة", layout="wide")

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
        st.error(f"فشل الاتصال: {e}")
        st.stop()

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            # تنظيف البيانات من المسافات لضمان دقة البحث
            return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return pd.DataFrame()
    except: return pd.DataFrame()

# =========================
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 تسجيل دخول الطالب (بالرقم الأكاديمي فقط)
# =========================
if not st.session_state.auth:
    st.title("🔐 دخول الطلاب")
    st.info("أدخل رقمك الأكاديمي المسجل في الجدول للاطلاع على بياناتك.")
    
    student_id = st.text_input("الرقم الأكاديمي", placeholder="مثلاً: 26")
    
    if st.button("دخول الطالب", use_container_width=True):
        if student_id:
            df_std = fetch("students")
            # البحث في العمود الثاني (الرقم الأكاديمي)
            match = df_std[df_std.iloc[:, 1] == student_id.strip()]
            
            if not match.empty:
                st.session_state.auth = True
                st.session_state.role = "student"
                st.session_state.user = student_id.strip()
                st.success("جاري تسجيل الدخول...")
                st.rerun()
            else:
                st.error(f"الرقم ({student_id}) غير موجود في سجلاتنا.")
        else:
            st.warning("يرجى إدخال الرقم الأكاديمي أولاً.")
    st.stop()

# =========================
# 👨‍🎓 لوحة بيانات الطالب
# =========================
if st.session_state.role == "student":
    st.sidebar.title(f"مرحباً الطالب: {st.session_state.user}")
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.clear()
        st.rerun()

    df_students = fetch("students")
    # استخراج بيانات الطالب المسجل
    me = df_students[df_students.iloc[:, 1] == st.session_state.user]
    
    if not me.empty:
        st.title(f"👋 أهلاً بك يا {me.iloc[0, 2]}")
        
        t1, t2 = st.tabs(["📊 كشف الدرجات", "🎭 سجل السلوك"])
        
        with t1:
            st.subheader("درجاتك في المواد")
            all_grades = fetch("grades")
            # فلترة الدرجات لتظهر للطالب الحالي فقط
            my_grades = all_grades[all_grades.iloc[:, 1] == st.session_state.user]
            if not my_grades.empty:
                st.table(my_grades)
            else:
                st.write("لا توجد درجات مرصودة لك حالياً.")
                
        with t2:
            st.subheader("سجل الانضباط والسلوك")
            all_behavior = fetch("behavior")
            my_behavior = all_behavior[all_behavior.iloc[:, 1] == st.session_state.user]
            if not my_behavior.empty:
                st.table(my_behavior)
            else:
                st.write("سجلك نظيف، لا توجد ملاحظات سلوكية.")
    else:
        st.error("حدث خطأ في استعادة بياناتك.")
