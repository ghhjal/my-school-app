import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال الآمنة ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception: return None

sh = get_db()

# دالة جلب بيانات ذكية لمنع أخطاء KeyError
def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
            if not df.empty:
                df.columns = expected_cols # فرض المسميات الصحيحة لتجنب المشاكل
                return df
    except Exception: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام تسجيل الدخول (استعادة الواجهة الأصلية) ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول الموحدة")
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="p_in")
        if st.button("دخول كمعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_log = st.text_input("الرقم الأكاديمي", key="s_in")
        if st.button("دخول كطالب"):
            if sid_log: st.session_state.role = "student"; st.session_state.student_id = sid_log; st.rerun()
    st.stop()

# --- 3. واجهة المعلم الشاملة ---
if st.session_state.role == "teacher":
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف"])
        
        with tab_reg:
            with st.form("add_student", clear_on_submit=True):
                st.subheader("📝 إدخال بيانات الطالب")
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    # ضمان بقاء الحقول المفقودة
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("إضافة الطالب"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم حفظ البيانات بنجاح"); time.sleep(1); st.rerun()

        with tab_view:
            search_query = st.text_input("🔍 ابحث بالاسم أو الرقم")
            cols_st = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
            df_st = fetch_data_safe("students", cols_st)
            
            if not df_st.empty:
                filtered = df_st[df_st.apply(lambda r: search_query in str(r["اسم الطالب"]) or search_query in str(r["الرقم الأكاديمي"]), axis=1)]
                st.dataframe(filtered, use_container_width=True, hide_index=True)
                
                # قسم حذف الطلاب المستقر
                st.divider()
                st.subheader("🗑️ حذف سجل طالب")
                st.warning("تنبيه: سيتم حذف بيانات الطالب نهائياً من القائمة.")
                del_target = st.selectbox("اختر الطالب المراد حذفه", [""] + filtered["اسم الطالب"].tolist())
                if st.button("تأكيد حذف الطالب"):
                    if del_target:
                        ws = sh.worksheet("students"); cell = ws.find(del_target); ws.delete_rows(cell.row)
                        st.success(f"تم حذف {del_target} بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        cols_st = ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"]
        df_students = fetch_data_safe("students", cols_st)
        
        if not df_students.empty:
            names = df_students["الاسم"].tolist()
            t_grad, t_beh = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])

            with t_grad:
                with st.form("grade_form"):
                    sel_st = st.selectbox("اختر الطالب", names)
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("درجة الفترة الأولى", 0.0)
                    p2 = c2.number_input("درجة الفترة الثانية", 0.0)
                    pf = c3.number_input("درجة الأداء", 0.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_st); ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except: ws_g.append_row([sel_st, p1, p2, pf])
                        st.success("✅ تم تحديث الدرجات بنجاح"); time.sleep(1); st.rerun()
                
                # عرض جدول الدرجات مع خيار الحذف المستقر
                st.subheader("📋 سجل الدرجات")
                df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "أداء"])
                if not df_g.empty:
                    st.dataframe(df_g, use_container_width=True, hide_index=True)
                    del_g = st.selectbox("حذف سجل درجات طالب", [""] + df_g["الطالب"].tolist())
                    if st.button("حذف السجل المختار"):
                        if del_g:
                            ws = sh.worksheet("grades"); cell = ws.find(del_g); ws.delete_rows(cell.row); st.rerun()

            with t_beh:
                with st.form("beh_form"):
                    b_st = st.selectbox("اسم الطالب", names)
                    b_date = st.date_input("📅 تاريخ الرصد", datetime.now()) # ميزة التاريخ المطلوبة
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة السلوكية")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                        st.success("✅ تم رصد السلوك بنجاح"); time.sleep(1); st.rerun()
                
                # عرض سجل السلوك مع خيار الحذف
                st.subheader("📋 سجل السلوك")
                df_b = fetch_data_safe("behavior", ["الطالب", "التاريخ", "النوع", "الملاحظة"])
                if not df_b.empty:
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
                    del_b = st.selectbox("حذف ملاحظة سلوكية (حسب الملاحظة)", [""] + df_b["الملاحظة"].tolist())
                    if st.button("حذف ملاحظة السلوك"):
                        if del_b:
                            ws = sh.worksheet("behavior"); cell = ws.find(del_b); ws.delete_rows(cell.row); st.rerun()
