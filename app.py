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
   # شاشة إدارة الطلاب
    elif page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة الطلاب (تعديل وحذف)</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["➕ إضافة جديد", "📋 عرض وتعديل", "🗑️ حذف بيانات"])
        
        # 1. إضافة طالب جديد
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
                        st.rerun()

        # 2. عرض وتعديل البيانات
        with tab2:
            data = sh.worksheet("students").get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.write("اختر الطالب لتعديل بياناته:")
                # اختيار الطالب للتعديل بناءً على الرقم الأكاديمي أو الاسم
                student_to_edit = st.selectbox("اختر الطالب المراد تعديله", df['name'].tolist())
                
                # جلب بيانات الطالب المختار في حقول قابلة للتعديل
                student_row = df[df['name'] == student_to_edit].iloc[0]
                row_idx = df[df['name'] == student_to_edit].index[0] + 2 # +2 لأن جوجل شيت يبدأ من 1 وهناك رأس للجدول
                
                with st.expander(f"تعديل بيانات: {student_to_edit}"):
                    new_n = st.text_input("الاسم الجديد", value=student_row['name'])
                    new_c = st.text_input("الصف", value=student_row['class'])
                    
                    if st.button("تحديث البيانات الآن"):
                        sh.worksheet("students").update_cell(row_idx, 2, new_n) # تحديث الاسم (العمود 2)
                        sh.worksheet("students").update_cell(row_idx, 3, new_c) # تحديث الصف (العمود 3)
                        st.success("تم التحديث بنجاح!")
                        st.rerun()
                
                st.divider()
                st.dataframe(df, use_container_width=True)
            else:
                st.info("لا توجد بيانات لعرضها.")

        # 3. حذف البيانات
        with tab3:
            if data:
                student_to_delete = st.selectbox("اختر الطالب المراد حذفه نهائياً", df['name'].tolist(), key="del_box")
                confirm_del = st.checkbox(f"أؤكد رغبتي في حذف الطالب: {student_to_delete}")
                
                if st.button("🗑️ تنفيذ الحذف النهائي"):
                    if confirm_del:
                        del_idx = df[df['name'] == student_to_delete].index[0] + 2
                        sh.worksheet("students").delete_rows(del_idx)
                        st.warning(f"تم حذف {student_to_delete} من النظام.")
                        st.rerun()
                    else:
                        st.error("يرجى التأكيد أولاً عبر علامة الصح.")
