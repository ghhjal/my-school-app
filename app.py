import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال (مؤمنة ضد Quota Error) ---
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
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="t_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي", key="s_sid")
        if st.button("دخول الطالب"):
            if sid_in: st.session_state.role = "student"; st.session_state.student_id = sid_in; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف الشامل"])
        
        with tab_reg:
            # تم تثبيت كافة الحقول هنا لمنع اختفائها مستقبلاً
            with st.form("main_reg_form", clear_on_submit=True):
                st.subheader("إضافة طالب جديد")
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ البيانات"):
                    if sname:
                        with st.spinner("جاري الحفظ الآمن..."):
                            try:
                                # حفظ متتابع لضمان عدم فقدان البيانات
                                sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                                try: sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                                except: pass
                                st.success(f"✅ تم تسجيل الطالب {sname} بنجاح")
                                time.sleep(1); st.rerun()
                            except: st.error("⚠️ ضغط عالي على الشبكة، يرجى المحاولة مرة أخرى")

        with tab_view:
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
                st.divider()
                st.subheader("🗑️ الحذف الشامل (نهائي)")
                del_target = st.selectbox("اختر الطالب للحذف من كل السجلات", [""] + df_st["الاسم"].tolist())
                if st.button("تأكيد الحذف"):
                    if del_target:
                        with st.spinner("جاري المسح الشامل..."):
                            # حذف الطالب من جميع الأماكن دفعة واحدة
                            for sn in ["students", "behavior", "grades", "sheet1"]:
                                try:
                                    ws = sh.worksheet(sn); cell = ws.find(del_target.strip())
                                    ws.delete_rows(cell.row)
                                except: pass
                            st.success(f"🗑️ تم حذف {del_target} بالكامل"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        if not df_all.empty:
            t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            with t_grad:
                with st.form("g_update"):
                    sel_st = st.selectbox("الطالب", df_all["الاسم"].tolist())
                    c1, c2 = st.columns(2)
                    p1, p2 = c1.number_input("الفترة 1"), c2.number_input("الفترة 2")
                    if st.form_submit_button("تحديث"):
                        try:
                            ws = sh.worksheet("grades"); cell = ws.find(sel_st)
                            ws.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                            st.success("✅ تم تحديث الدرجات"); time.sleep(1); st.rerun()
                        except:
                            sh.worksheet("grades").append_row([sel_st, p1, p2])
                            st.success("✅ تم الرصد"); time.sleep(1); st.rerun()

            with t_beh:
                with st.form("b_add"):
                    b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد"):
                        try:
                            sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                            st.success("✅ تم رصد السلوك"); time.sleep(1); st.rerun()
                        except: st.error("فشل الاتصال، يرجى الانتظار قليلاً")
                
                df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
                st.dataframe(df_b, use_container_width=True, hide_index=True)
