import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال وحل مشكلة Quota ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. بوابة الدخول الموحدة ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول الموحدة")
    tab1, tab2 = st.tabs(["👨‍🏫 بوابة المعلم", "🎓 بوابة الطالب"])
    with tab1:
        pwd = st.text_input("كلمة مرور المعلم", type="password", key="teacher_pwd")
        if st.button("دخول كمعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with tab2:
        sid_input = st.text_input("الرقم الأكاديمي للطالب", key="student_sid")
        if st.button("دخول كطالب"):
            if sid_input: st.session_state.role = "student"; st.session_state.student_id = sid_input; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t_reg, t_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف الشامل"])
        
        with t_reg:
            with st.form("reg_form", clear_on_submit=True):
                st.subheader("إضافة طالب جديد")
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب")
                    # استعادة حقل المرحلة
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    # استعادة حقل الأعوام الدراسية المطلوبة
                    syear = st.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ البيانات"):
                    if sh and sname:
                        try:
                            sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                            sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                            st.success(f"✅ تم تسجيل الطالب {sname} بنجاح")
                            time.sleep(1); st.rerun()
                        except: st.error("خطأ في الاتصال، حاول مرة أخرى")

        with t_view:
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
                st.divider()
                st.subheader("🗑️ الحذف الشامل (نهائي)")
                del_target = st.selectbox("اختر الطالب للحذف من كل السجلات", [""] + df_st["الاسم"].tolist())
                if st.button("تأكيد الحذف النهائي"):
                    if del_target:
                        with st.spinner("جاري تنظيف كافة الجداول..."):
                            # مسح من 4 جداول لضمان عدم بقاء أي بيانات
                            for sheet in ["students", "behavior", "grades", "sheet1"]:
                                try:
                                    ws = sh.worksheet(sheet); cell = ws.find(del_target.strip())
                                    ws.delete_rows(cell.row)
                                except: pass
                            st.success(f"🗑️ تم حذف {del_target} وكافة متعلقاته بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        if not df_all.empty:
            t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with t_g:
                with st.form("grade_form"):
                    sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                    c1, c2 = st.columns(2)
                    p1 = c1.number_input("درجة الفترة الأولى")
                    p2 = c2.number_input("درجة الفترة الثانية")
                    if st.form_submit_button("تحديث الدرجات"):
                        ws = sh.worksheet("grades")
                        try:
                            cell = ws.find(sel_st); ws.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                        except: ws.append_row([sel_st, p1, p2])
                        st.success("✅ تم التحديث"); time.sleep(1); st.rerun()

            with t_b:
                with st.form("beh_form"):
                    b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة السلوكية")
                    if st.form_submit_button("رصد السلوك"):
                        try:
                            sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                            st.success("✅ تم الرصد بنجاح"); time.sleep(1); st.rerun()
                        except: st.error("فشل الاتصال بقاعدة البيانات")
                
                df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
                st.dataframe(df_b, use_container_width=True, hide_index=True)
