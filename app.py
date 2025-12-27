import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة الفخمة
st.set_page_config(page_title="نظام الأستاذ زياد - الإدارة الذكية", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; transition: 0.3s; }
    .stTabs [data-baseweb="tab-list"] { background-color: #f8f9fa; padding: 10px; border-radius: 15px; }
    .student-card { 
        background-color: white; padding: 20px; border-radius: 15px; 
        border-right: 8px solid #d4af37; margin-bottom: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }
    h1 { color: #1a1a1a; font-family: 'Amiri', serif; text-align: center; border-bottom: 3px solid #d4af37; padding-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws = sh.worksheet("students")

    # القائمة الجانبية
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=80)
        st.title("بوابة الأستاذ زياد")
        page = st.radio("القوائم المتاحة:", ["🏠 الرئيسية", "👥 إدارة الطلاب والتحكم", "📊 الدرجات والسلوك"])

    # --- شاشة إدارة الطلاب ---
    if page == "👥 إدارة الطلاب والتحكم":
        st.markdown("<h1>👥 إدارة شؤون الطلاب (إصدار ملكي)</h1>", unsafe_allow_True=True)
        tab1, tab2 = st.tabs(["✨ إضافة طالب جديد", "🛠️ التحكم في البيانات"])

        with tab1:
            with st.form("new_student"):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب بالكامل")
                    sphase = st.selectbox("المرحلة الدراسية", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("🚀 حفظ البيانات للسحابة"):
                    # إرسال البيانات بترتيب الأعمدة: ID, Name, Phase, Class, Year, Subject
                    ws.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()

        with tab2:
            all_data = ws.get_all_records()
            if all_data:
                df = pd.DataFrame(all_data)
                for index, row in df.iterrows():
                    # معالجة مشكلة phase: إذا لم يوجد العمود، نضع قيمة افتراضية
                    p_val = row.get('phase', row.get('المرحلة الدراسية', 'غير محدد'))
                    
                    st.markdown(f"""
                    <div class="student-card">
                        <span style="font-size: 1.2em; font-weight: bold; color: #d4af37;">🆔 {row.get('id', '??')} | 👤 {row.get('name', 'بدون اسم')}</span><br>
                        <span style="color: #666;">المرحلة: {p_val} | الصف: {row.get('class', '-')} | المادة: {row.get('subject', 'اللغة الإنجليزية')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_edit, c_del, c_empty = st.columns([1, 1, 3])
                    with c_edit:
                        if st.button("✏️ تعديل", key=f"e_{index}"):
                            st.toast("سيتم فتح نافذة التعديل قريباً")
                    with c_del:
                        if st.button("🗑️ حذف", key=f"d_{index}"):
                            ws.delete_rows(int(index) + 2)
                            st.warning("تم الحذف.")
                            st.rerun()
            else:
                st.info("لا توجد بيانات مسجلة حالياً.")

    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 رصد الدرجات والسلوك</h1>", unsafe_allow_html=True)
        st.info("هذه الشاشة ستعتمد على الأسماء التي تسجلها في شاشة الإدارة.")

except Exception as e:
    st.error(f"خطأ في الوصول للبيانات: {e}")
