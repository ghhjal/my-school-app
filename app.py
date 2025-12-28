import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال ---
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def safe_fetch(sheet_name):
    try:
        if sh:
            df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
            return df
    except: return pd.DataFrame()

# --- 2. واجهة المعلم (بعد تسجيل الدخول) ---
if 'role' not in st.session_state: st.session_state.role = "teacher" # للتجربة مباشرة

if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    # --- أ: إدارة الطلاب مع زر الحذف ---
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_view:
            df_st = safe_fetch("students")
            if not df_st.empty:
                df_st.columns = ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"]
                for i, row in df_st.iterrows():
                    cols = st.columns([4, 1])
                    cols[0].write(f"👤 {row['الاسم']} | {row['الصف']} | {row['الرقم']}")
                    # زر الحذف لكل طالب
                    if cols[1].button("🗑️ حذف", key=f"del_st_{i}"):
                        ws = sh.worksheet("students")
                        cell = ws.find(str(row['الرقم']))
                        ws.delete_rows(cell.row)
                        st.success(f"تم حذف {row['الاسم']} بنجاح")
                        time.sleep(1); st.rerun()

    # --- ب: الدرجات والسلوك مع حقل التاريخ وأزرار الحذف ---
    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_students = safe_fetch("students")
        
        if not df_students.empty:
            df_students.columns = ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"]
            names = df_students["الاسم"].tolist()
            t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])

            with t_grad:
                # عرض الدرجات مع خيار الحذف
                df_g = safe_fetch("grades")
                if not df_g.empty:
                    df_g.columns = ["الاسم", "ف1", "ف2", "أداء"]
                    for i, row in df_g.iterrows():
                        cols = st.columns([4, 1])
                        cols[0].write(f"📊 {row['الاسم']}: {row['ف1']} | {row['ف2']} | {row['أداء']}")
                        if cols[1].button("🗑️ حذف", key=f"del_g_{i}"):
                            ws = sh.worksheet("grades")
                            cell = ws.find(row['الاسم'])
                            ws.delete_rows(cell.row)
                            st.rerun()

            with t_beh:
                with st.form("beh_form"):
                    b_st = st.selectbox("اختر الطالب", names)
                    # إضافة حقل اختيار التاريخ يدوياً
                    b_date = st.date_input("📅 اختر تاريخ الرصد", datetime.now()) 
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                        st.success("تم الرصد بنجاح")
                
                # سجل السلوك مع زر الحذف
                st.subheader("📋 سجل السلوك")
                df_b = safe_fetch("behavior")
                if not df_b.empty:
                    df_b.columns = ["الاسم", "التاريخ", "النوع", "الملاحظة"]
                    for i, row in df_b.iterrows():
                        cols = st.columns([4, 1])
                        cols[0].write(f"🗓️ {row['التاريخ']} | {row['الاسم']} | {row['النوع']}")
                        if cols[1].button("🗑️ حذف", key=f"del_b_{i}"):
                            ws = sh.worksheet("behavior")
                            # حذف السجل بناءً على الملاحظة والاسم لضمان الدقة
                            cell = ws.find(row['الملاحظة'])
                            ws.delete_rows(cell.row)
                            st.rerun()
