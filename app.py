import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import urllib.parse

# 1. تهيئة حالة الجلسة (لحل مشكلة AttributeError)
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# 2. تحسين تصميم الجوال (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# 3. دالة الاتصال الآمنة (تعالج خطأ 404)
def connect_to_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # استبدل هذا الرابط برابط ملفك الصحيح من المتصفح
        URL = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        
        sh = client.open_by_url(URL)
        return sh
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: تأكد من رابط الملف وبريد الخدمة. (الخطأ: {e})")
        return None

# جلب الملف
sh = connect_to_sheet()

# 4. منطق تسجيل الدخول
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 25px; text-align: center; border-radius: 15px; color: white;">
            <h2 style="margin: 0;">🌟 منصة الأستاذ زياد العمري</h2>
            <p style="margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.write("")
        login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", placeholder="اكتب الكود هنا...")
        
        if st.button("🚀 دخول للمنصة", type="primary"):
            if login_type == "معلم":
                if user_id == "1234":
                    st.session_state.role = "teacher"
                    st.rerun()
                else:
                    st.error("❌ كود المعلم غير صحيح")
            else:
                if sh:
                    try:
                        df_st = pd.DataFrame(sh.worksheet("students").get_all_records())
                        # تنظيف البيانات للمطابقة
                        df_st.iloc[:, 0] = df_st.iloc[:, 0].astype(str).str.strip()
                        if str(user_id) in df_st.iloc[:, 0].values:
                            st.session_state.role = "student"
                            st.session_state.sid = str(user_id)
                            st.rerun()
                        else:
                            st.error("❌ الكود غير مسجل")
                    except:
                        st.error("❌ تأكد من وجود ورقة باسم 'students' داخل الملف")
                else:
                    st.error("❌ لا يمكن الوصول للقاعدة")

# 5. واجهة المعلم
elif st.session_state.role == "teacher":
    st.title("👨‍🏫 لوحة التحكم - الأستاذ زياد")
    menu = st.sidebar.selectbox("القائمة", ["إدارة الطلاب", "رصد الدرجات", "شاشة الاختبارات"])
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
        
    if menu == "إدارة الطلاب":
        st.subheader("👥 إضافة طالب جديد")
        with st.form("add_st"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الكود (ID)")
            nname = c2.text_input("الاسم")
            nclass = c3.selectbox("الصف", ["الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("إضافة"):
                if sh and nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, "1447", "نشط", "English", "ابتدائي", "", "", "0"])
                    st.success("تمت الإضافة")
                    st.rerun()

# 6. واجهة الطالب
elif st.session_state.role == "student":
    if sh:
        df_st = pd.DataFrame(sh.worksheet("students").get_all_records())
        df_st.iloc[:, 0] = df_st.iloc[:, 0].astype(str).str.strip()
        student_data = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
        
        st.markdown(f"""
            <div style="background: #1e3a8a; padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h3>🎓 أهلاً بك: {student_data.iloc[1]}</h3>
                <p>الصف: {student_data.iloc[2]}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.metric("رصيد نقاطك 🌟", student_data.iloc[8])
        
        if st.button("تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()
