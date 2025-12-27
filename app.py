import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide", initial_sidebar_state="expanded")

# تطبيق ثيم ملكي فخم وألوان متناسقة
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #d4af37; color: white; border-radius: 12px;
        border: none; padding: 10px; font-weight: bold; width: 100%;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 10px 10px 0 0; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #d4af37; color: white; }
    h1 { color: #2c3e50; font-family: 'Amiri', serif; text-align: center; border-bottom: 3px solid #d4af37; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي (أداء سريع)
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 3. القائمة الجانبية (Sidebar) بتصميم جديد
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=80)
    st.title("القائمة الرئيسية")
    page = st.radio("انتقل إلى:", ["🏠 الشاشة الرئيسية", "👥 إدارة الطلاب", "📊 رصد الدرجات"])
    st.divider()
    st.markdown(f"<div style='text-align: center; color: #d4af37;'>v2.5 نظام الأستاذ زياد</div>", unsafe_allow_html=True)

# 4. تشغيل النظام والمعالجة
try:
    client = get_gspread_client()
    # فتح الملف باستخدام المعرف الخاص بك
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws = sh.worksheet("students")

    # --- الشاشة الرئيسية ---
    if page == "🏠 الشاشة الرئيسية":
        st.markdown("<h1>👑 لوحة التحكم الملكية</h1>", unsafe_allow_html=True)
        all_data = ws.get_all_records()
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("إجمالي الطلاب", len(all_data))
        with col2: st.metric("حالة الربط", "آمن ✅")
        with col3: st.metric("العام الدراسي", "1447هـ")
        st.image("https://img.freepik.com/free-vector/education-background-concept_52683-33318.jpg", use_container_width=True)

    # --- شاشة إدارة الطلاب ---
    elif page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["➕ إضافة طالب", "✏️ تعديل بيانات", "🗑️ حذف طالب"])

        # جلب البيانات وتحويلها لتنسيق مناسب لمنع خطأ int64
        all_data = ws.get_all_records()
        df = pd.DataFrame(all_data)

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sclass = st.selectbox("الصف", ["خامس أ", "خامس ب", "سادس أ", "سادس ب"])
                    syear = "1447هـ"
                if st.form_submit_button("حفظ الطالب"):
                    if sname:
                        ws.append_row([int(sid), sname, sclass, syear, "الأول"])
                        st.success("✅ تم الحفظ بنجاح")
                        st.rerun()

        with tab2:
            if not df.empty:
                target_name = st.selectbox("اختر الطالب للتعديل", df['name'].tolist())
                student_row = df[df['name'] == target_name].iloc[0]
                # تحديد رقم السطر في جوجل شيت
                real_row_idx = int(df[df['name'] == target_name].index[0]) + 2
                
                with st.expander(f"تعديل بيانات: {target_name}"):
                    new_n = st.text_input("الاسم", value=str(student_row['name']))
                    new_c = st.text_input("الصف", value=str(student_row['class']))
                    if st.button("تحديث الآن"):
                        ws.update_cell(real_row_idx, 2, new_n)
                        ws.update_cell(real_row_idx, 3, new_c)
                        st.success("تم التعديل!")
                        st.rerun()
                st.dataframe(df, use_container_width=True)

        with tab3:
            if not df.empty:
                st.write("### ⚠️ منطقة الحذف النهائي")
                del_name = st.selectbox("اختر الطالب المراد حذفه", df['name'].tolist(), key="del_select")
                confirm = st.checkbox(f"أوافق على حذف {del_name} نهائياً")
                
                if st.button("حذف نهائي"):
                    if confirm:
                        # تحويل الـ index إلى رقم صحيح عادي لتجنب خطأ int64
                        idx = int(df[df['name'] == del_name].index[0])
                        ws.delete_rows(idx + 2)
                        st.warning(f"تم حذف {del_name} بنجاح.")
                        st.rerun()
                    else:
                        st.error("يرجى التأكيد أولاً عبر علامة الصح.")

    # --- شاشة رصد الدرجات ---
    elif page == "📊 رصد الدرجات":
        st.markdown("<h1>📊 رصد الدرجات</h1>", unsafe_allow_html=True)
        st.info("سيتم ربط هذا القسم بورقة الدرجات (grades) قريباً...")

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
    st.info("نصيحة: تأكد من مشاركة الملف مع إيميل الخدمة بشكل Editor.")
