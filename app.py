import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# --- 1. تهيئة حالة الجلسة (أهم خطوة لمنع الأخطاء) ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# --- 2. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. دالة الاتصال بقاعدة البيانات ---
def get_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # يستخدم بيانات الاعتماد من Secrets
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # الرابط المباشر لملفك
        url = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        return client.open_by_url(url)
    except Exception as e:
        return None

sh = get_connection()

# --- 4. واجهة تسجيل الدخول ---
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 25px; border-radius: 15px; text-align: center; color: white;">
            <h2>🌟 منصة الأستاذ زياد العمري</h2>
            <p>سجل دخولك للمتابعة</p>
        </div>
    """, unsafe_allow_html=True)

    login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
    user_id = st.text_input("أدخل الكود الخاص بك (ID)").strip()
    
    if st.button("🚀 دخول للمنصة", type="primary"):
        if login_type == "معلم":
            if user_id == "1234":  # كود المعلم
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("❌ كود المعلم غير صحيح")
        
        elif login_type == "طالب":
            if sh:
                try:
                    ws = sh.worksheet("students")
                    df = pd.DataFrame(ws.get_all_records())
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    
                    if user_id in df.iloc[:, 0].values:
                        st.session_state.role = "student"
                        st.session_state.sid = user_id
                        st.rerun()
                    else:
                        st.error("❌ الكود غير مسجل")
                except:
                    st.error("❌ خطأ في الوصول لبيانات الطلاب")
            else:
                st.error("❌ لا يوجد اتصال بقاعدة البيانات")

# --- 5. واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.sidebar.success("👨‍🏫 حساب المعلم")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    st.title("لوحة تحكم المعلم")
    # هنا تضع الأكواد الخاصة بإدارة الطلاب التي تفضلها

# --- 6. واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.info("🎓 حساب الطالب")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.sid = None
        st.rerun()

    if sh:
        ws = sh.worksheet("students")
        df = pd.DataFrame(ws.get_all_records())
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        student_info = df[df.iloc[:, 0] == st.session_state.sid].iloc[0]
        
        st.header(f"أهلاً بك: {student_info.iloc[1]}")
        st.info(f"الصف: {student_info.iloc[2]}")
        
        # عرض النقاط
        points = student_info.iloc[8] if len(student_info) > 8 else 0
        st.metric("رصيد نقاطك 🌟", points)
