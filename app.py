import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide")

# تصميم CSS لتحسين واجهة العرض وزر الحذف
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .delete-btn>button { background-color: #ff4b4b; color: white; }
    .edit-btn>button { background-color: #d4af37; color: white; }
    h1 { color: #1a1a1a; text-align: center; border-bottom: 2px solid #d4af37; padding-bottom: 10px; }
    .student-card { background-color: #ffffff; padding: 15px; border-radius: 15px; border-right: 5px solid #d4af37; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. الربط مع جوجل شيت
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws_students = sh.worksheet("students")

    # القائمة الجانبية
    with st.sidebar:
        st.title("القائمة الرئيسية")
        page = st.radio("انتقل إلى:", ["🏠 الرئيسية", "👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    # --- شاشة إدارة الطلاب ---
    if page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب الذكية</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["➕ إضافة طالب جديد", "📋 قائمة الطلاب والتحكم"])

        with tab1:
            with st.form("add_student_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                    sphase = st.selectbox("المرحلة الدراسية", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["خامس", "سادس", "أول متوسط", "ثاني متوسط", "ثالث متوسط", "أول ثانوي", "ثاني ثانوي", "ثالث ثانوي"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("✨ حفظ بيانات الطالب"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success(f"تم تسجيل {sname} بنجاح")
                    st.rerun()

        with tab2:
            data = ws_students.get_all_records()
            if data:
                df = pd.DataFrame(data)
                for index, row in df.iterrows():
                    with st.container():
                        # عرض البيانات بشكل كروت أنيقة
                        st.markdown(f"""
                        <div class="student-card">
                            <strong>🆔 {row['id']} | 👤 {row['name']}</strong><br>
                            المرحلة: {row['phase']} | الصف: {row['class']} | السنة: {row['year']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_edit, col_del, col_space = st.columns([1, 1, 4])
                        
                        # زر التعديل
                        with col_edit:
                            if st.button(f"✏️ تعديل", key=f"edit_{index}"):
                                st.info("ميزة التعديل السريع ستفتح في نافذة منبثقة قريباً")
                        
                        # زر الحذف (عاد من جديد)
                        with col_del:
                            if st.button(f"🗑️ حذف", key=f"del_{index}"):
                                # الحذف الفعلي من جوجل شيت
                                ws_students.delete_rows(index + 2)
                                st.warning(f"تم حذف الطالب {row['name']}")
                                st.rerun()
                        st.divider()
            else:
                st.info("لا يوجد طلاب مسجلين حالياً.")

    # --- شاشة الدرجات والسلوك ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 رصد الدرجات والسلوك</h1>", unsafe_allow_html=True)
        st.write("سيتم تفعيل الرصد المباشر هنا بناءً على قائمة الطلاب أعلاه.")

except Exception as e:
    st.error(f"خطأ: {e}")
