import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# 1. منع الأخطاء قبل حدوثها (تعريف الجلسة)
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# 2. تحسين مظهر الواجهة
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="centered")
st.markdown("<style>*{direction: rtl; text-align: right; font-family: 'Cairo', sans-serif;}</style>", unsafe_allow_html=True)

# 3. الاتصال الآمن بملف جوجل شيت
def connect_to_db():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # الرابط المباشر لملفك
        url = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        return client.open_by_url(url)
    except:
        return None

sh = connect_to_db()

# 4. شاشة الدخول (المعلم والطالب)
if st.session_state.role is None:
    st.title("🌟 منصة الأستاذ زياد العمري")
    login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
    user_id = st.text_input("أدخل الكود الخاص بك (ID)").strip()
    
    if st.button("🚀 دخول"):
        if login_type == "معلم" and user_id == "1234":
            st.session_state.role = "teacher"
            st.rerun()
        elif login_type == "طالب":
            if sh:
                ws = sh.worksheet("students")
                df = pd.DataFrame(ws.get_all_records())
                df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                if user_id in df.iloc[:, 0].values:
                    st.session_state.role = "student"
                    st.session_state.sid = user_id
                    st.rerun()
                else:
                    st.error("❌ الكود غير صحيح")
            else:
                st.error("❌ فشل الاتصال بقاعدة البيانات (خطأ 404)")

# 5. واجهة المعلم (إدارة الطلاب)
elif st.session_state.role == "teacher":
    st.header("👨‍🏫 لوحة المعلم")
    if st.sidebar.button("خروج"):
        st.session_state.role = None
        st.rerun()
    
    if sh:
        ws = sh.worksheet("students")
        st.write("إضافة طالب جديد:")
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الكود")
            nname = c2.text_input("الاسم")
            nclass = c3.selectbox("الصف", ["الثاني", "الثالث", "الرابع"])
            if st.form_submit_button("حفظ"):
                ws.append_row([nid, nname, nclass, "1447", "نشط", "English", "ابتدائي", "", "", "0"])
                st.success("تم الحفظ")
                st.rerun()

# 6. واجهة الطالب (عرض النقاط)
elif st.session_state.role == "student":
    st.header("🎓 حساب الطالب")
    if st.sidebar.button("خروج"):
        st.session_state.role = None
        st.rerun()
    
    ws = sh.worksheet("students")
    df = pd.DataFrame(ws.get_all_records())
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    st_data = df[df.iloc[:, 0] == st.session_state.sid].iloc[0]
    st.subheader(f"مرحباً {st_data.iloc[1]}")
    st.metric("رصيد نقاطك", st_data.iloc[8])
