import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال الذكي ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=300) # تخزين مؤقت لمدة 5 دقائق لتقليل الضغط
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# --- 2. إدارة الجلسة وزر الخروج الجانبي ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

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
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                st.subheader("📝 بيانات الطالب الجديدة")
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب بالكامل")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    # استعادة الحقول المفقودة
                    sclass = st.selectbox("الصف الدراسي", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ بيانات الطالب"):
                    if sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم حفظ بيانات الطالب بنجاح")
                        time.sleep(1); st.rerun()

        with tab_view:
            st.subheader("🔍 البحث والإدارة")
            search_query = st.text_input("ابحث بالاسم أو الرقم الأكاديمي", placeholder="اكتب للبحث...")
            try:
                ws_st = sh.worksheet("students")
                df = pd.DataFrame(ws_st.get_all_records())
                if not df.empty:
                    df.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                    filtered = df[df.apply(lambda r: search_query in str(r["اسم الطالب"]) or search_query in str(r["الرقم الأكاديمي"]), axis=1)]
                    st.dataframe(filtered, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    for idx, row in filtered.iterrows():
                        c_name, c_btn = st.columns([4, 1])
                        c_name.write(f"👤 **{row['اسم الطالب']}** | {row['الصف']} | {row['السنة']}")
                        if c_btn.button("حذف", key=f"del_{row['الرقم الأكاديمي']}"):
                            with st.spinner("جاري حذف السجلات..."):
                                for sn in ["behavior", "grades", "sheet1"]:
                                    try:
                                        target = sh.worksheet(sn)
                                        term = str(row['اسم الطالب']) if sn != "sheet1" else str(row['الرقم الأكاديمي'])
                                        for cell in reversed(target.findall(term)): target.delete_rows(cell.row)
                                    except: continue
                                # الحذف من القائمة الرئيسية
                                ws_st.delete_rows(idx + 2)
                                st.success("✅ تم حذف الطالب بنجاح")
                                time.sleep(1); st.cache_resource.clear(); st.rerun()
            except: 
                st.warning("🔄 النظام يقوم بتحديث البيانات، يرجى الانتظار ثواني...")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        # نفس منطق الرصد مع تعريب كامل للمسميات
        try:
            all_st = sh.worksheet("students").get_all_values()
            if len(all_st) > 1:
                names = [r[1] for r in all_st[1:]]
                t_grad, t_beh = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
                with t_grad:
                    with st.form("grade_form"):
                        sel_st = st.selectbox("اختر الطالب", names)
                        c1, c2, c3 = st.columns(3)
                        p1 = c1.number_input("درجة الفترة الأولى", 0.0)
                        p2 = c2.number_input("درجة الفترة الثانية", 0.0)
                        pf = c3.number_input("درجة الأداء", 0.0)
                        if st.form_submit_button("تحديث الدرجات"):
                            # دالة تحديث مختصرة لتقليل Quota
                            ws_g = sh.worksheet("grades")
                            try:
                                cell = ws_g.find(sel_st)
                                ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                            except: ws_g.append_row([sel_st, p1, p2, pf])
                            st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
        except: st.error("⚠️ مشكلة في الاتصال (Quota)، يرجى الانتظار دقيقة")
