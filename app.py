import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال والذاكرة المؤقتة ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة جلب البيانات مع معالجة ذكية للأعمدة لتجنب KeyError
def safe_fetch(sheet_name):
    try:
        if sh:
            df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
            return df
    except:
        pass
    return pd.DataFrame()

# --- 2. إدارة الجلسة ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف"])
        
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    # استعادة الحقول المفقودة
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

        with tab_view:
            search_q = st.text_input("🔍 بحث بالاسم أو الرقم")
            df_st = safe_fetch("students")
            if not df_st.empty:
                # التأكد من أسماء الأعمدة لتجنب الأخطاء
                df_st.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                filtered = df_st[df_st.apply(lambda r: search_q in str(r["اسم الطالب"]) or search_q in str(r["الرقم الأكاديمي"]), axis=1)]
                st.dataframe(filtered, use_container_width=True, hide_index=True)

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_students = safe_fetch("students")
        
        # حل مشكلة KeyError عبر التحقق من وجود البيانات
        if not df_students.empty:
            df_students.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
            names = df_students["اسم الطالب"].tolist()
            
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
                            cell = ws_g.find(sel_st)
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except: ws_g.append_row([sel_st, p1, p2, pf])
                        st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
                
                # استعادة الجدول السفلي للدرجات
                st.subheader("📋 سجل الدرجات")
                df_g = safe_fetch("grades")
                if not df_g.empty:
                    df_g.columns = ["اسم الطالب", "الفترة 1", "الفترة 2", "الأداء"]
                    st.dataframe(df_g, use_container_width=True, hide_index=True)

            with t_beh:
                with st.form("beh_form"):
                    b_st = st.selectbox("اسم الطالب", names, key="bsel")
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                        st.success("✅ تم الرصد"); time.sleep(1); st.rerun()
                
                # استعادة سجل السلوك
                st.subheader("📋 سجل السلوك")
                df_b = safe_fetch("behavior")
                if not df_b.empty:
                    df_b.columns = ["اسم الطالب", "التاريخ", "النوع", "الملاحظة"]
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ لا توجد بيانات طلاب حالياً، يرجى إضافة طلاب من شاشة الإدارة.")
