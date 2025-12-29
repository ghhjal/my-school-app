import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. الاتصال الآمن ---
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

# --- 2. تنسيق الواجهة (CSS) لجمالية المنصة ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTable { border-radius: 10px; overflow: hidden; }
    .block-container { padding-top: 2rem; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; font-family: 'Arial'; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. قسم إدارة الطلاب (النسخة المنسقة) ---
if 'role' in st.session_state and st.session_state.role == "teacher":
    # استدعاء القائمة الجانبية للتنقل
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "👥 إدارة الطلاب":
        st.markdown("<h2>👥 شاشة إدارة الطلاب الشاملة</h2>", unsafe_allow_html=True)
        
        # عرض الجدول بشكل أنيق
        df_st = fetch_safe("students")
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📋 قائمة الطلاب الحالية")
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        
        # تقسيم الشاشة لنموذجين منسقين
        col_add, col_del = st.columns([2, 1])

        with col_add:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📝 إضافة طالب جديد (بيانات كاملة)")
            with st.form("add_full_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_id = c1.text_input("الرقم الأكاديمي")
                n_name = c2.text_input("الاسم الثلاثي")
                
                c3, c4 = st.columns(2)
                n_class = c3.selectbox("الصف الدراسي", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                # استعادة حقول العام الدراسي والمادة [نقص في image_435a8d.png]
                n_year = c4.text_input("العام الدراسي", value="1446هـ")
                
                c5, c6 = st.columns(2)
                n_sub = c5.text_input("المادة الدراسية", value="اللغة الإنجليزية")
                n_level = c6.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                
                if st.form_submit_button("🚀 حفظ الطالب الجديد"):
                    if n_id and n_name:
                        # ترتيب الأعمدة حسب الجدول: الرقم، الاسم، الصف، السنة، المادة، المرحلة، ايميل، جوال، نقاط
                        new_data = [n_id, n_name, n_class, n_year, n_sub, n_level, "", "", 0]
                        sh.worksheet("students").append_row(new_data)
                        st.success(f"✅ تم تسجيل {n_name} بنجاح")
                        time.sleep(1); st.rerun()
                    else: st.warning("يرجى ملء الاسم والرقم الأكاديمي")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_del:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("🗑️ حذف سريع")
            st_to_del = st.selectbox("اختر الاسم", [""] + df_st.iloc[:,1].tolist())
            if st.button("تأكيد الحذف"):
                if st_to_del:
                    # الحذف من كافة الجداول لضمان نظافة البيانات
                    for s in ["students", "behavior", "grades"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(st_to_del); ws.delete_rows(cell.row)
                        except: continue
                    st.success("🗑️ تم الحذف"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# (ملاحظة: تأكد من إبقاء بقية كود الدخول والدرجات كما هو في ملفك لضمان عمل النظام بالكامل)
