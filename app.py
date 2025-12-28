import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الأمان والاتصال ---
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

# دالة جلب البيانات الآمنة لضمان عدم اختفاء الجداول
def fetch_data(sheet_name):
    try:
        if sh:
            return pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
    except:
        pass
    return pd.DataFrame()

# --- 2. نظام تسجيل الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول الموحدة")
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="main_pwd")
        if st.button("دخول كمعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
    with t2:
        sid_input = st.text_input("الرقم الأكاديمي للطالب", key="main_sid")
        if st.button("دخول كطالب"):
            if sid_input:
                st.session_state.role = "student"
                st.session_state.student_id = sid_input
                st.rerun()
    st.stop()

# --- 3. واجهة المعلم (حل مشكلة الحقول والجداول) ---
if st.session_state.role == "teacher":
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل طالب جديد", "📋 البحث والحذف"])
        
        with tab_reg:
            with st.form("student_reg_form", clear_on_submit=True):
                st.subheader("📝 إدخال بيانات الطالب")
                col1, col2 = st.columns(2)
                with col1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with col2:
                    # استعادة الحقول الأساسية
                    sclass = st.selectbox("الصف الدراسي", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة الدراسية", value="اللغة الإنجليزية")
                
                if st.form_submit_button("إضافة الطالب"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم حفظ الطالب بنجاح")
                        time.sleep(1); st.rerun()

        with tab_view:
            search_query = st.text_input("🔍 ابحث بالاسم أو الرقم")
            df_st = fetch_data("students")
            if not df_st.empty:
                df_st.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                filtered = df_st[df_st.apply(lambda r: search_query in str(r["اسم الطالب"]) or search_query in str(r["الرقم الأكاديمي"]), axis=1)]
                st.dataframe(filtered, use_container_width=True, hide_index=True)
                
                # إدارة الحذف الآمن
                for idx, row in filtered.iterrows():
                    c_n, c_b = st.columns([4, 1])
                    c_n.write(f" الطالب: **{row['اسم الطالب']}**")
                    if c_b.button("حذف السجل", key=f"del_{row['الرقم الأكاديمي']}"):
                        with st.spinner("جاري الحذف..."):
                            for sn in ["behavior", "grades", "sheet1"]:
                                try:
                                    ws = sh.worksheet(sn)
                                    term = str(row['اسم الطالب']) if sn != "sheet1" else str(row['الرقم الأكاديمي'])
                                    for cell in reversed(ws.findall(term)): ws.delete_rows(cell.row)
                                except: continue
                            sh.worksheet("students").delete_rows(idx + 2)
                            st.success("✅ تم الحذف بنجاح")
                            time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_students = fetch_data("students")
        if not df_students.empty:
            names = df_students["اسم الطالب"].tolist()
            t_grad, t_beh = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
            
            with t_grad:
                with st.form("grades_form"):
                    sel_st = st.selectbox("اختر الطالب", names)
                    c1, c2, c3 = st.columns(3)
                    # مسميات معربة بالكامل
                    p1 = c1.number_input("درجة الفترة الأولى", 0.0)
                    p2 = c2.number_input("درجة الفترة الثانية", 0.0)
                    pf = c3.number_input("درجة الأداء", 0.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_st)
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except: ws_g.append_row([sel_st, p1, p2, pf])
                        st.success("✅ تم رصد الدرجات"); time.sleep(1); st.rerun()
                
                # استعادة جدول الدرجات السفلي
                st.subheader("📋 سجل الدرجات العام")
                df_g = fetch_data("grades")
                if not df_g.empty:
                    df_g.columns = ["اسم الطالب", "الفترة 1", "الفترة 2", "الأداء"]
                    st.dataframe(df_g, use_container_width=True, hide_index=True)

            with t_beh:
                with st.form("behavior_form"):
                    b_st = st.selectbox("اسم الطالب", names, key="beh_sel")
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة السلوكية")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                        st.success("✅ تم الرصد بنجاح"); time.sleep(1); st.rerun()
                
                # استعادة جدول السلوك السفلي
                st.subheader("📋 سجل السلوك العام")
                df_b = fetch_data("behavior")
                if not df_b.empty:
                    df_b.columns = ["اسم الطالب", "التاريخ", "النوع", "الملاحظة"]
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
