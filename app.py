import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="centered")

# 2. تهيئة الجلسة لضمان استقرار الدخول
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# 3. دالة الاتصال (محسنة لضمان عدم الانقطاع)
def get_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # الرابط الخاص بملفك
        url = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        return client.open_by_url(url)
    except Exception as e:
        st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
        return None

# جلب البيانات الأساسية للتحقق من الدخول
sh = get_connection()

# --- واجهة تسجيل الدخول ---
if st.session_state.role is None:
    st.markdown("""
        <div style="background: #1e3a8a; padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h2>🌟 منصة الأستاذ زياد العمري</h2>
            <p>سجل دخولك للمتابعة</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.write("")
        login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", key="main_login").strip()
        
        if st.button("🚀 دخول للمنصة", use_container_width=True, type="primary"):
            if login_type == "معلم":
                # كود المعلم (تأكد من كتابته بشكل صحيح)
                if user_id == "1234":
                    st.session_state.role = "teacher"
                    st.success("مرحباً أستاذ زياد.. جاري التحميل")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ كود المعلم غير صحيح")
            
            elif login_type == "طالب":
                if sh:
                    try:
                        # جلب ورقة الطلاب للتحقق
                        ws = sh.worksheet("students")
                        df = pd.DataFrame(ws.get_all_records())
                        
                        # تنظيف البيانات لضمان المطابقة
                        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                        
                        if user_id in df.iloc[:, 0].values:
                            st.session_state.role = "student"
                            st.session_state.sid = user_id
                            st.success("✅ تم التحقق من الكود.. أهلاً بك")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ الكود ({user_id}) غير مسجل في النظام")
                    except Exception as e:
                        st.error(f"⚠️ حدث خطأ أثناء جلب البيانات: {e}")
                else:
                    st.error("❌ لا يوجد اتصال بملف البيانات")

# --- واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.sidebar.header("👨‍🏫 لوحة المعلم")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    st.title("لوحة تحكم الأستاذ زياد")
    st.info("أنت الآن في واجهة الإدارة")
    # يمكنك إضافة بقية الكود الخاص بالإدارة هنا

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.header("🎓 حساب الطالب")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.sid = None
        st.rerun()
    
    # جلب بيانات الطالب لعرضها
    ws = sh.worksheet("students")
    df = pd.DataFrame(ws.get_all_records())
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    student_info = df[df.iloc[:, 0] == st.session_state.sid].iloc[0]
    
    st.markdown(f"### 🎓 أهلاً بك: {student_info.iloc[1]}")
    st.markdown(f"**الصف:** {student_info.iloc[2]}")
    
    # عرض النقاط بتنسيق جميل للجوال
    points = student_info.iloc[8] if len(student_info) > 8 else 0
    st.metric("رصيد نقاطك", points)
