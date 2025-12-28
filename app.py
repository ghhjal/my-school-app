import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال الذكي بالذاكرة المؤقتة ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

# دالة لجلب البيانات دفعة واحدة لتقليل الضغط ومنع اختفاء الجداول
def get_all_data(sheet_name):
    try:
        return pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
    except: return pd.DataFrame()

# --- 2. واجهة المعلم الرئيسية ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role == "teacher":
    # إضافة زر تسجيل الخروج في الشريط الجانبي
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    # استعادة الحقول المفقودة في شاشة الإضافة
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                    sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                    st.success("✅ تم التسجيل بنجاح"); time.sleep(1); st.rerun()

        with tab_view:
            st.subheader("🔍 البحث والإدارة")
            search_q = st.text_input("ابحث بالاسم أو الرقم الأكاديمي")
            df_st = get_all_data("students")
            if not df_st.empty:
                df_st.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                filtered = df_st[df_st.apply(lambda r: search_q in str(r["اسم الطالب"]) or search_q in str(r["الرقم الأكاديمي"]), axis=1)]
                st.dataframe(filtered, use_container_width=True, hide_index=True)
                
                # منطقة الحذف المحسنة لمنع الرسائل الحمراء
                for idx, row in filtered.iterrows():
                    c_n, c_b = st.columns([4, 1])
                    c_n.write(f"👤 **{row['اسم الطالب']}**")
                    if c_b.button("حذف", key=f"del_{row['الرقم الأكاديمي']}"):
                        with st.spinner("جاري المسح..."):
                            for sn in ["behavior", "grades", "sheet1"]:
                                try:
                                    ws = sh.worksheet(sn)
                                    term = str(row['اسم الطالب']) if sn != "sheet1" else str(row['الرقم الأكاديمي'])
                                    for cell in reversed(ws.findall(term)): ws.delete_rows(cell.row)
                                except: continue
                            sh.worksheet("students").delete_rows(idx + 2)
                            st.success("✅ تم الحذف بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = get_all_data("students")
        if not df_all.empty:
            names = df_all["اسم الطالب"].tolist() if "اسم الطالب" in df_all.columns else [r[1] for r in sh.worksheet("students").get_all_values()[1:]]
            t_grad, t_beh = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
            
            with t_grad:
                with st.form("g_form"):
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
                        st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
                
                # استعادة جدول الدرجات السفلي
                st.subheader("📋 سجل الدرجات العام")
                df_g = get_all_data("grades")
                if not df_g.empty:
                    df_g.columns = ["اسم الطالب", "الفترة 1", "الفترة 2", "الأداء"]
                    st.dataframe(df_g, use_container_width=True, hide_index=True)

            with t_beh:
                with st.form("b_form"):
                    b_st = st.selectbox("اسم الطالب", names, key="b_s_key")
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                        st.success("✅ تم رصد السلوك"); time.sleep(1); st.rerun()
                
                # استعادة جدول السلوك السفلي
                st.subheader("📋 سجل السلوك العام")
                df_b = get_all_data("behavior")
                if not df_b.empty:
                    df_b.columns = ["اسم الطالب", "التاريخ", "النوع", "الملاحظة"]
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
        else: st.warning("⚠️ يرجى إضافة طلاب أولاً لعرض الجداول.")
