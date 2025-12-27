import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعدادات الصفحة الفخمة
st.set_page_config(page_title="نظام الأستاذ زياد - الإدارة الذكية", layout="wide")

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

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws = sh.worksheet("students")

    # القائمة الجانبية
    with st.sidebar:
        st.title("بوابة الأستاذ زياد")
        page = st.radio("القوائم:", ["🏠 الرئيسية", "👥 إدارة الطلاب والتحكم", "📊 الدرجات والسلوك"])
        st.divider()
        st.info("v4.0 النسخة المستقرة")

    # --- شاشة إدارة الطلاب ---
    if page == "👥 إدارة الطلاب والتحكم":
        st.markdown("<h1>👥 إدارة الطلاب (النسخة الملكية)</h1>", unsafe_allow_html=True)
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
                    ws.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()

        with tab2:
            all_data = ws.get_all_records()
            if all_data:
                df = pd.DataFrame(all_data)
                for index, row in df.iterrows():
                    # عرض الكروت الملكية
                    st.markdown(f"""
                    <div class="student-card">
                        <strong>🆔 {row.get('id', index+1)} | 👤 {row.get('name', 'طالب جديد')}</strong><br>
                        <small>المرحلة: {row.get('phase', 'غير محدد')} | الصف: {row.get('class', '-')} | المادة: {row.get('subject', 'الإنجليزية')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار الحذف والتعديل تحت كل كرت
                    col_del, col_empty = st.columns([1, 4])
                    with col_del:
                        if st.button("🗑️ حذف", key=f"del_{index}"):
                            ws.delete_rows(int(index) + 2)
                            st.warning(f"تم حذف {row.get('name')}")
                            st.rerun()
            else:
                st.info("قائمة الطلاب فارغة حالياً.")

    elif page == "🏠 الرئيسية":
        st.markdown("<h1>👋 أهلاً بك أستاذ زياد</h1>", unsafe_allow_html=True)
        st.write("هذا النظام صمم خصيصاً لإدارة بيانات طلابك بكل سهولة واحترافية.")

    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 رصد الدرجات والسلوك</h1>", unsafe_allow_html=True)
        st.info("سيتم ربط بيانات الطلاب المسجلين هنا في التحديث القادم.")

except Exception as e:
    st.error(f"تنبيه: {e}")
