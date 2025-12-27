import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 20px; font-weight: bold; }
    .student-card { 
        background-color: white; padding: 15px; border-radius: 12px; 
        border-right: 6px solid #d4af37; margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    h1 { color: #1a1a1a; text-align: center; border-bottom: 3px solid #d4af37; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 3. تشغيل النظام
try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws_students = sh.worksheet("students")

    # القائمة الجانبية
    with st.sidebar:
        st.title("بوابة الأستاذ زياد")
        page = st.radio("القوائم المتاحة:", ["🏠 الرئيسية", "👥 إدارة الطلاب والتحكم", "📊 الدرجات والسلوك"])
        st.divider()
        st.info("النسخة المستقرة v4.0")

    # --- شاشة إدارة الطلاب (التي أعجبتك) ---
    if page == "👥 إدارة الطلاب والتحكم":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["➕ تسجيل طالب جديد", "🛠️ عرض وتحكم"])
        
        with tab1:
            with st.form("new_student_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                    sphase = st.selectbox("المرحلة الدراسية", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("✨ حفظ في السحابة"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()

        with tab2:
            all_data = ws_students.get_all_records()
            if all_data:
                df = pd.DataFrame(all_data)
                for index, row in df.iterrows():
                    st.markdown(f"""<div class="student-card">
                        <strong>🆔 {row.get('id', index+1)} | 👤 {row.get('name', 'طالب')}</strong><br>
                        <small>المرحلة: {row.get('phase', 'غير محدد')} | الصف: {row.get('class', '-')} | المادة: {row.get('subject', 'الإنجليزية')}</small>
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️ حذف الطالب", key=f"del_{index}"):
                        ws_students.delete_rows(int(index) + 2)
                        st.warning("تم الحذف.")
                        st.rerun()
            else:
                st.info("لا توجد بيانات مسجلة.")

    # --- شاشة الدرجات والسلوك (المطلوبة الآن) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 رصد الدرجات والسلوك</h1>", unsafe_allow_html=True)
        
        # جلب الأسماء من ورقة الطلاب لضمان الربط
        all_students = ws_students.get_all_records()
        if not all_students:
            st.warning("⚠️ يرجى إضافة طلاب أولاً من شاشة الإدارة.")
        else:
            names_list = [r['name'] for r in all_students]
            t1, t2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
            
            with t1:
                with st.form("f1"):
                    st.write("### رصد درجة اختبار/مشاركة")
                    name = st.selectbox("اسم الطالب", names_list)
                    type_g = st.selectbox("نوع التقييم", ["فتري 1", "فتري 2", "مشاركة", "نهائي"])
                    val_g = st.number_input("الدرجة", min_value=0, max_value=100)
                    if st.form_submit_button("حفظ الدرجة"):
                        sh.worksheet("grades").append_row([name, type_g, val_g, str(datetime.now().date())])
                        st.success("تم الرصد!")
            
            with t2:
                with st.form("f2"):
                    st.write("### رصد ملاحظة سلوكية")
                    name_b = st.selectbox("اسم الطالب", names_list, key="sb")
                    type_b = st.radio("التقييم", ["🌟 إيجابي", "⚠️ تنبيه"])
                    note_b = st.text_area("الملاحظة")
                    if st.form_submit_button("حفظ السلوك"):
                        sh.worksheet("behavior").append_row([name_b, type_b, note_b, str(datetime.now().date())])
                        st.success("تم الحفظ!")

    elif page == "🏠 الرئيسية":
        st.markdown("<h1>👑 نظام الأستاذ زياد - الصفحة الرئيسية</h1>", unsafe_allow_html=True)
        st.write("أهلاً بك في نظامك المتكامل. استخدم القائمة الجانبية للتنقل.")

except Exception as e:
    st.error(f"خطأ: {e}")
