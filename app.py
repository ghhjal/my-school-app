import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال ---
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
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="l_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي", key="l_sid")
        if st.button("دخول الطالب"):
            if sid_in: st.session_state.role = "student"; st.session_state.student_id = sid_in; st.rerun()
    st.stop()

# زر الخروج الجانبي
with st.sidebar:
    st.write(f"👤 الحساب: {st.session_state.role}")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
    st.divider()

# --- واجهة المعلم ---
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
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("العام الدراسي", ["1446هـ", "1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ البيانات"):
                    if sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        st.success(f"✅ تم حفظ {sname}"); time.sleep(1); st.rerun()

        with t_view:
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            st.divider()
            
            # --- تحديث وظيفة الحذف الشامل ---
            del_target = st.selectbox("اختر الطالب لحذفه من جميع الجداول", [""] + df_st["الاسم"].tolist())
            if st.button("🗑️ تنفيذ الحذف النهائي لكافة البيانات"):
                if del_target:
                    target_name = del_target.strip()
                    sheets_to_clean = ["students", "behavior", "grades"]
                    
                    with st.spinner(f"جاري حذف كافة سجلات {target_name}..."):
                        for sheet_name in sheets_to_clean:
                            ws = sh.worksheet(sheet_name)
                            # حذف كافة السطور التي تحتوي على الاسم (تكرار الحذف لضمان النظافة)
                            while True:
                                try:
                                    cell = ws.find(target_name)
                                    ws.delete_rows(cell.row)
                                except: # إذا لم يجد الاسم، يخرج من الحلقة وينتقل للجدول التالي
                                    break
                    st.success(f"✅ تم مسح كافة بيانات الطالب {target_name} من جميع السجلات.")
                    time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        
        if not df_all.empty:
            t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            with t_grad:
                with st.form("grade_update_form"):
                    sel_st = st.selectbox("اختر الطالب لتحديث درجاته", df_all["الاسم"].tolist())
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("الفترة 1")
                    p2 = c2.number_input("الفترة 2")
                    work = c3.number_input("المشاركة والمهام")
                    
                    if st.form_submit_button("تحديث الدرجات"):
                        ws_g = sh.worksheet("grades")
                        search_name = sel_st.strip()
                        try:
                            cell = ws_g.find(search_name)
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, work]])
                            st.success(f"✅ تم تحديث درجات: {search_name}")
                        except:
                            ws_g.append_row([search_name, p1, p2, work])
                            st.success(f"✅ تم إضافة سجل درجات جديد لـ: {search_name}")
                        time.sleep(1); st.rerun()

            with t_beh:
                with st.form("beh_form"):
                    b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                    b_date = st.date_input("التاريخ", datetime.now())
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                        st.success("✅ تم رصد السلوك"); time.sleep(1); st.rerun()
