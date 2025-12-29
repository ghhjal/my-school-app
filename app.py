import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# دالة الاتصال الآمن
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# التحقق من تسجيل الدخول (لمنع الشاشة البيضاء)
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "👥 إدارة الطلاب":
        st.header("👥 شاشة إدارة الطلاب")
        df_st = fetch_safe("students")
        # عرض الجدول مع كافة الحقول
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        # نموذج إضافة طالب جديد (استعادة الحقول المفقودة)
        with st.form("add_student"):
            st.subheader("📝 إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            id_in = c1.text_input("الرقم")
            name_in = c2.text_input("الاسم")
            class_in = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
            
            c4, c5, c6 = st.columns(3)
            year_in = c4.text_input("السنة", value="1446هـ")
            sub_in = c5.text_input("المادة", value="اللغة الإنجليزية")
            sem_in = c6.text_input("المرحلة", value="ابتدائي")
            
            if st.form_submit_button("حفظ الطالب"):
                if id_in and name_in:
                    sh.worksheet("students").append_row([id_in, name_in, class_in, year_in, sub_in, sem_in, "", "", 0])
                    st.success("تمت الإضافة"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        # كود رصد السلوك مع الفلترة التلقائية
        df_st = fetch_safe("students")
        st_name = st.selectbox("اختر الطالب", df_st.iloc[:, 1].tolist())
        
        # فلترة الجدول ليعرض سجل الطالب المختار فقط
        df_b = fetch_safe("behavior")
        filtered_b = df_b[df_b.iloc[:, 0] == st_name]
        st.dataframe(filtered_b, use_container_width=True)
