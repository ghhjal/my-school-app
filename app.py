import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide", initial_sidebar_state="expanded")

# تطبيق ثيم ملكي فخم
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #d4af37; color: white; border-radius: 20px;
        border: none; padding: 10px 25px; font-weight: bold; width: 100%;
    }
    h1 { color: #1a1a1a; font-family: 'Amiri', serif; text-align: center; border-bottom: 2px solid #d4af37; }
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
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=100)
    st.title("القائمة الرئيسية")
    page = st.radio("انتقال إلى:", ["🏠 الشاشة الرئيسية", "👥 إدارة الطلاب", "📊 رصد الدرجات"])
    st.divider()
    st.info("نظام الأستاذ زياد v2.5")

# 4. تشغيل النظام
try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws = sh.worksheet("students")

    if page == "🏠 الشاشة الرئيسية":
        st.markdown("<h1>👑 لوحة التحكم الملكية</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        data = ws.get_all_records()
        with col1: st.metric("إجمالي الطلاب", len(data))
        with col2: st.metric("حالة النظام", "متصل ✅")
        with col3: st.metric("العام الدراسي", "1447هـ")
        st.image("https://img.freepik.com/free-vector/education-background-concept_52683-33318.jpg", use_container_width=True)

    elif page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["➕ إضافة طالب", "✏️ تعديل بيانات", "🗑️ حذف طالب"])

        # جلب البيانات للتبويبات
        all_data = ws.get_all_records()
        df = pd.DataFrame(all_data)

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sclass = st.selectbox("الصف", ["خامس أ", "خامس ب", "سادس أ", "سادس ب"])
                    syear = "1447هـ"
                if st.form_submit_button("حفظ الطالب"):
                    if sname:
                        ws.append_row([sid, sname, sclass, syear, "الأول"])
                        st.success("تم الحفظ!")
                        st.rerun()

        with tab2:
            if not df.empty:
                st.write("### اختر طالباً لتحديث بياناته")
                target_name = st.selectbox("بحث عن طالب", df['name'].tolist())
                student_data = df[df['name'] == target_name].iloc[0]
                row_num = df[df['name'] == target_name].index[0] + 2
                
                with st.expander(f"تعديل بيانات {target_name}"):
                    new_n = st.text_input("الاسم الجديد", value=student_data['name'])
                    new_c = st.text_input("الصف الجديد", value=student_data['class'])
                    if st.button("تحديث الآن"):
                        ws.update_cell(row_num, 2, new_n)
                        ws.update_cell(row_num, 3, new_c)
                        st.success("تم التعديل!")
                        st.rerun()
                st.dataframe(df, use_container_width=True)

        with tab3:
            if not df.empty:
                st.write("### ⚠️ منطقة الحذف النهائي")
                del_name = st.selectbox("اختر الطالب المراد حذفه", df['name'].tolist(), key="del")
                confirm = st.checkbox(f"أوافق على حذف {del_name}")
                if st.button("حذف نهائي"):
                    if confirm:
                        del_idx = df[df['name'] == del_name].index[0] + 2
                        ws.delete_rows(del_idx)
                        st.warning("تم الحذف بنجاح")
                        st.rerun()
                    else:
                        st.error("يرجى تفعيل خيار التأكيد أولاً")

    elif page == "📊 رصد الدرجات":
        st.markdown("<h1>📊 رصد الدرجات</h1>", unsafe_allow_html=True)
        st.info("سيتم ربط هذا القسم بورقة الدرجات قريباً...")

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
    st.info("تأكد من إعداد Secrets ومشاركة الملف مع إيميل الخدمة.")
