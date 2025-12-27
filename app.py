import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #d4af37; color: white; border-radius: 12px; font-weight: bold; }
    h1 { color: #2c3e50; font-family: 'Amiri', serif; text-align: center; border-bottom: 3px solid #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 3. القائمة الجانبية
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=80)
    st.title("القائمة الرئيسية")
    page = st.radio("انتقل إلى:", ["🏠 الشاشة الرئيسية", "👥 إدارة الطلاب", "📊 رصد الدرجات", "🎭 رصد السلوك"])
    st.divider()
    st.markdown("v3.0 نظام الأستاذ زياد")

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")

    # --- 🏠 الشاشة الرئيسية ---
    if page == "🏠 الشاشة الرئيسية":
        st.markdown("<h1>👑 لوحة التحكم الملكية</h1>", unsafe_allow_html=True)
        st.image("https://img.freepik.com/free-vector/education-background-concept_52683-33318.jpg", use_container_width=True)

    # --- 👥 إدارة الطلاب (إضافة المرحلة والسنة والمادة) ---
    elif page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        ws_students = sh.worksheet("students")
        tab1, tab2 = st.tabs(["➕ إضافة وتعديل", "📋 عرض القائمة"])

        with tab1:
            with st.form("student_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                with c2:
                    sphase = st.selectbox("المرحلة الدراسية", ["الابتدائية", "المتوسطة"])
                    sclass = st.selectbox("الصف", ["خامس أ", "خامس ب", "سادس أ", "سادس ب"])
                with c3:
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ الطالب"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success(f"تم حفظ الطالب {sname} بنجاح")
                    st.rerun()

        with tab2:
            df_s = pd.DataFrame(ws_students.get_all_records())
            st.dataframe(df_s, use_container_width=True)

    # --- 📊 رصد الدرجات (مرتبط بورقة grades) ---
    elif page == "📊 رصد الدرجات":
        st.markdown("<h1>📊 وحدة رصد الدرجات</h1>", unsafe_allow_html=True)
        ws_grades = sh.worksheet("grades") # تأكد من وجود ورقة بهذا الاسم
        
        # جلب قائمة الطلاب من ورقة الطلاب للاختيار منهم
        students_list = pd.DataFrame(sh.worksheet("students").get_all_records())['name'].tolist()
        
        with st.form("grades_form"):
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.selectbox("اختر الطالب", students_list)
                exam_type = st.selectbox("نوع الاختبار", ["فتري 1", "فتري 2", "نهائي"])
            with col2:
                grade = st.number_input("الدرجة المستحقة", min_value=0, max_value=100)
                note = st.text_input("ملاحظات المعلم")
            
            if st.form_submit_button("رصد الدرجة"):
                ws_grades.append_row([student_name, exam_type, grade, note])
                st.success("تم رصد الدرجة بنجاح")

    # --- 🎭 رصد السلوك (مرتبط بورقة behavior) ---
    elif page == "🎭 رصد السلوك":
        st.markdown("<h1>🎭 وحدة رصد السلوك والمواظبة</h1>", unsafe_allow_html=True)
        ws_behavior = sh.worksheet("behavior") # تأكد من وجود ورقة بهذا الاسم
        
        students_list = pd.DataFrame(sh.worksheet("students").get_all_records())['name'].tolist()
        
        with st.form("behavior_form"):
            c1, c2 = st.columns(2)
            with c1:
                b_name = st.selectbox("اسم الطالب", students_list)
                b_type = st.selectbox("نوع السلوك", ["إيجابي (+)", "ملاحظة (-)"])
            with c2:
                b_desc = st.text_area("وصف السلوك (المشاركة، الانضباط، إلخ)")
            
            if st.form_submit_button("حفظ السلوك"):
                ws_behavior.append_row([b_name, b_type, b_desc])
                st.success("تم الحفظ بنجاح")

except Exception as e:
    st.error(f"خطأ في النظام: {e}")
