import streamlit as st
import gspread
import pandas as pd
import html, uuid, time
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
            # تنظيف البيانات من المسافات الزائدة
            return df.astype(str).apply(lambda x: x.str.strip())
        return pd.DataFrame()
    except: return pd.DataFrame()

# =========================
# 🛡️ أدوات الأمان
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
# 🔐 نظام تسجيل الدخول (مطابق لجدولك)
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطلاب (بالرقم الأكاديمي)", "👨‍🏫 دخول المعلمين"])
    
    with tab1:
        # لاحظ هنا: سيبحث الكود في العمود الأول A بناءً على صورتك
        student_id = st.text_input("أدخل رقمك الأكاديمي (id)", key="s_id")
        if st.button("دخول الطالب"):
            df_std = fetch("students") 
            if not df_std.empty:
                # المقارنة مع العمود الأول (index 0) وهو عمود الـ id في صورتك
                match = df_std[df_std.iloc[:, 0] == clean(student_id)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.role = "student"
                    st.session_state.user = clean(student_id)
                    st.success(f"مرحباً بك الطالب: {match.iloc[0, 1]}") # العمود الثاني هو الاسم
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"الرقم ({student_id}) غير مسجل في عمود الـ id.")
            else:
                st.error("فشل الوصول لبيانات جدول الطلاب.")

    with tab2:
        u_teacher = st.text_input("اسم المستخدم", key="t_u")
        p_teacher = st.text_input("كلمة المرور", type="password", key="t_p")
        if st.button("دخول المعلم"):
            df_users = fetch("users")
            # التحقق من حساب المعلم
            match = df_users[(df_users['username'] == u_teacher) & (df_users['role'] == 'teacher')]
            if not match.empty and p_teacher == "1234": 
                st.session_state.auth = True
                st.session_state.role = "teacher"
                st.session_state.user = u_teacher
                st.rerun()
            else:
                st.error("بيانات المعلم خاطئة")
    st.stop()

# =========================
# 👨‍🏫 لوحة المعلم
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
        new_id = st.text_input("الرقم الأكاديمي (id)")
        new_name = st.text_input("اسم الطالب")
        if st.form_submit_button("إضافة طالب"):
            # الإضافة بنفس ترتيب صورتك: id ثم name ثم البقية
            sh.worksheet("students").append_row([new_id, new_name, "الثالث", "1447هـ", "اللغة الإنجليزية", "ابتدائي"])
            st.success("تمت إضافة الطالب")
            st.rerun()

# =========================
# 👨‍🎓 لوحة الطالب
# =========================
elif st.session_state.role == "student":
    st.sidebar.info(f"رقم الطالب: {st.session_state.user}")
    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()

    df_students = fetch("students")
    # البحث في العمود الأول A
    me = df_students[df_students.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        st.title(f"👋 أهلاً بك {me.iloc[0, 1]}")
        st.write(f"الصف: {me.iloc[0, 2]} | السنة: {me.iloc[0, 3]}")
        
        st.subheader("📊 تفاصيل نقاطك")
        # عرض البيانات من الجدول مباشرة للطالب
        st.table(me[['id', 'name', 'النقاط']]) 
    else:
        st.error("لم يتم العثور على بياناتك")
