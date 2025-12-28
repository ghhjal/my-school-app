import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال الذكية لتقليل الضغط ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=600) # زيادة وقت التخزين لتقليل طلبات Quota
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

# دالة جلب البيانات مع معالجة الأخطاء لتجنب الصفحة البيضاء
def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except Exception as e:
        st.error(f"⚠️ تنبيه: {str(e)}")
    return pd.DataFrame(columns=expected_cols)

# --- 2. واجهة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

if menu == "👥 إدارة الطلاب":
    st.header("👥 إدارة الطلاب")
    tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف الشامل"])
    
    with tab_reg:
        with st.form("reg_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                sid = st.number_input("الرقم الأكاديمي", min_value=1)
                sname = st.text_input("اسم الطالب")
            with c2:
                sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                ssub = st.text_input("المادة", value="اللغة الإنجليزية")
            if st.form_submit_button("حفظ"):
                if sh and sname:
                    sh.worksheet("students").append_row([str(sid), sname, sclass, "1446هـ", ssub, "ابتدائي"])
                    st.success("✅ تم الحفظ بنجاح"); time.sleep(1); st.rerun()

    with tab_view:
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        if not df_st.empty:
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            st.divider()
            del_name = st.selectbox("اختر الطالب للحذف الشامل", [""] + df_st["الاسم"].tolist())
            if st.button("🗑️ تأكيد الحذف النهائي"):
                if del_name:
                    with st.spinner("جاري المسح..."):
                        # الحذف من الجداول الثلاثة الأساسية
                        for sn in ["students", "behavior", "grades"]:
                            try:
                                ws = sh.worksheet(sn); cell = ws.find(del_name); ws.delete_rows(cell.row)
                            except: pass
                        st.success(f"تم حذف {del_name} بنجاح"); time.sleep(1); st.rerun()

elif menu == "📊 الدرجات والسلوك":
    st.header("📊 رصد الدرجات والسلوك")
    df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    
    if not df_all.empty:
        t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])

        with t_grad:
            with st.form("g_form"):
                sel_st = st.selectbox("الطالب", df_all["الاسم"].tolist())
                c1, c2 = st.columns(2)
                p1 = c1.number_input("الفترة 1")
                p2 = c2.number_input("الفترة 2")
                if st.form_submit_button("تحديث"):
                    ws = sh.worksheet("grades")
                    try:
                        c = ws.find(sel_st); ws.update(f'B{c.row}:C{c.row}', [[p1, p2]])
                    except: ws.append_row([sel_st, p1, p2])
                    st.success("✅ تم التحديث"); time.sleep(1); st.rerun()

        with t_beh:
            # نموذج رصد سلوك مبسط جداً لمنع الانهيار
            with st.form("b_form", clear_on_submit=True):
                b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist(), key="beh_select")
                b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة السلوكية")
                if st.form_submit_button("رصد السلوك"):
                    if b_st:
                        try:
                            # إضافة مباشرة لتقليل الضغط على API
                            sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                            st.success(f"✅ تم رصد سلوك {b_st}")
                            time.sleep(1); st.rerun()
                        except:
                            st.warning("⚠️ مشكلة مؤقتة في الاتصال، يرجى الانتظار دقيقة")
            
            st.subheader("📋 السجل الحالي")
            df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
            st.dataframe(df_b, use_container_width=True, hide_index=True)
