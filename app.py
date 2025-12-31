import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# إعدادات الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# وظيفة الاتصال بملف جوجل شيت
def connect_and_fetch(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # تأكد أن هذا الرابط هو رابط ملفك الصحيح
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit")
        worksheet = sh.worksheet(sheet_name)
        df = pd.DataFrame(worksheet.get_all_records())
        return df, worksheet
    except Exception as e:
        st.error(f"❌ خطأ في الوصول لورقة {sheet_name}: {e}")
        return pd.DataFrame(), None

# --- واجهة تسجيل الدخول ---
if st.session_state.role is None:
    st.title("🌟 منصة الأستاذ زياد العمري")
    login_type = st.radio("الدخول كـ:", ["طالب", "معلم"], horizontal=True)
    user_id = st.text_input("أدخل الكود الخاص بك").strip()
    
    if st.button("دخول", use_container_width=True):
        if login_type == "معلم" and user_id == "1234":
            st.session_state.role = "teacher"
            st.rerun()
        else:
            df_st, _ = connect_and_fetch("students")
            # تحويل العمود الأول لنصوص للمطابقة الصحيحة
            if not df_st.empty:
                codes = df_st.iloc[:, 0].astype(str).values
                if user_id in codes:
                    st.session_state.role = "student"
                    st.session_state.sid = user_id
                    st.rerun()
                else:
                    st.error(f"❌ الكود {user_id} غير موجود في عمود الأكواد بالجدول")

# --- واجهة الطالب (بعد الدخول) ---
elif st.session_state.role == "student":
    df_st, _ = connect_and_fetch("students")
    # البحث عن بيانات الطالب
    student_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"<h2 style='text-align:center;'>🎓 أهلاً بك: {student_data.iloc[1]}</h2>", unsafe_allow_html=True)
    st.info(f"الصف: {student_data.iloc[2]}")
    
    # عرض النقاط (العمود رقم 9 في جدولك)
    points = student_data.iloc[8] if len(student_data) > 8 else 0
    st.metric("رصيد نقاطك الحالي", points)

    if st.button("خروج"):
        st.session_state.role = None
        st.rerun()

# --- واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.title("👨‍🏫 لوحة التحكم")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    # هنا يمكنك إضافة أزرار الإضافة والرصد
