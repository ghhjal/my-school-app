import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# ==========================================
# 1. تهيئة الجلسة (حل مشكلة AttributeError)
# ==========================================
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# ==========================================
# 2. دالة الاتصال المحسنة
# ==========================================
def fetch_safe(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # الرابط الخاص بملفك
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit") 
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            # تحويل أول عمود لنص لضمان مطابقة الكود
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df, sh, worksheet
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بورقة {sheet_name}: {e}")
        return pd.DataFrame(), None, None

# جلب البيانات الأساسية عند التشغيل
df_st, sh_file, ws_students = fetch_safe("students")

# ==========================================
# 🏠 3. واجهة تسجيل الدخول
# ==========================================
if st.session_state.role is None:
    st.title("🌟 منصة الأستاذ زياد العمري")
    
    with st.form("login_form"):
        login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك").strip()
        submit = st.form_submit_button("دخول")
        
        if submit:
            if login_type == "معلم" and user_id == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            elif login_type == "طالب":
                if not df_st.empty and user_id in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"
                    st.session_state.sid = user_id
                    st.rerun()
                else:
                    st.error("❌ الكود غير صحيح أو غير مسجل")

# ==========================================
# 👨‍🏫 4. واجهة المعلم (تم إصلاح خطأ الإضافة)
# ==========================================
elif st.session_state.role == "teacher":
    st.sidebar.title("لوحة تحكم المعلم")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    menu = st.sidebar.selectbox("القائمة", ["إدارة الطلاب", "رصد الدرجات"])

    if menu == "إدارة الطلاب":
        st.header("👥 إضافة طالب جديد")
        with st.form("add_student_form"):
            new_id = st.text_input("الكود (ID)")
            new_name = st.text_input("اسم الطالب")
            new_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("حفظ الطالب"):
                if ws_students:
                    # إضافة الصف مع التأكد من مطابقة عدد الأعمدة في جدولك
                    ws_students.append_row([new_id, new_name, new_class, "1447", "نشط", "English", "Primary", "0", "0", "0"])
                    st.success("✅ تم إضافة الطالب بنجاح")
                    time.sleep(1)
                    st.rerun()

    elif menu == "رصد الدرجات":
        st.header("📝 رصد الدرجات")
        df_grades, _, ws_grades = fetch_safe("grades")
        st.dataframe(df_grades)

# ==========================================
# 👨‍🎓 5. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    # عرض البيانات الشخصية للطالب
    student_info = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
    
    st.markdown(f"### 🎓 مرحباً: {student_info.iloc[1]}")
    st.info(f"الصف: {student_info.iloc[2]}")
    
    if st.button("خروج"):
        st.session_state.role = None
        st.rerun()
