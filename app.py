import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide", initial_sidebar_state="expanded")

# تطبيق ثيم ملكي (ألوان ذهبية وفخمة)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #d4af37; color: white; border-radius: 20px;
        border: none; padding: 10px 25px; font-weight: bold; width: 100%;
    }
    .stTextInput>div>div>input { border-radius: 10px; border: 1px solid #d4af37; }
    .sidebar .sidebar-content { background-image: linear-gradient(#1a1a1a, #4b4b4b); color: white; }
    h1 { color: #1a1a1a; font-family: 'Amiri', serif; text-align: center; border-bottom: 2px solid #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 3. القائمة الجانبية (Navigation)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=100)
    st.title("القائمة الرئيسية")
    page = st.radio("انتقل إلى:", ["🏠 الشاشة الرئيسية", "👥 إدارة الطلاب", "📊 رصد الدرجات", "⚙️ الإعدادات"])
    st.divider()
    st.info("نظام الإدارة الذكي v2.0")

# الاتصال بالملف
try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    
    # الشاشة الرئيسية
    if page == "🏠 الشاشة الرئيسية":
        st.markdown("<h1>👑 لوحة التحكم الملكية - الأستاذ زياد</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("إجمالي الطلاب", len(sh.worksheet("students").get_all_values()) - 1)
        with col2:
            st.metric("الدرجات المرصودة", "100%")
        with col3:
            st.metric("حالة النظام", "متصل آمن")
        
        st.image("https://img.freepik.com/free-vector/education-background-concept_52683-33318.jpg", use_container_width=True)

    # شاشة إدارة الطلاب
    elif page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 تسجيل وإدارة الطلاب</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["➕ إضافة طالب جديد", "📋 عرض القائمة"])
        
        with tab1:
            with st.form("add_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                with c2:
                    sclass = st.selectbox("الصف", ["خامس أ", "خامس ب", "سادس أ", "سادس ب"])
                    syear = st.text_input("العام الدراسي", value="1447هـ")
                
                if st.form_submit_button("حفظ الطالب في السحابة"):
                    if sname:
                        sh.worksheet("students").append_row([sid, sname, sclass, syear, "الأول"])
                        st.success(f"تم تسجيل {sname} بنجاح")
                        st.balloons()
        
        with tab2:
            df = pd.DataFrame(sh.worksheet("students").get_all_records())
            st.dataframe(df, use_container_width=True)

    # شاشة رصد الدرجات
    elif page == "📊 رصد الدرجات":
        st.markdown("<h1>📊 وحدة رصد الدرجات</h1>", unsafe_allow_html=True)
        st.warning("هذه الوحدة قيد التجهيز لربطها بورقة الدرجات (grades)")

except Exception as e:
    st.error(f"خطأ في الوصول للبيانات: {e}")
