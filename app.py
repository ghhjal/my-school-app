import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            data = sh.worksheet(sheet_name).get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except Exception: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام تسجيل الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_log = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            if sid_log: st.session_state.role = "student"; st.session_state.student_id = sid_log; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف الشامل"])
        
        with tab_view:
            search_q = st.text_input("🔍 ابحث بالاسم أو الرقم")
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            if not df_st.empty:
                filt = df_st[df_st.apply(lambda r: search_q in str(r["الاسم"]) or search_q in str(r["الرقم"]), axis=1)]
                st.dataframe(filt, use_container_width=True, hide_index=True)
                
                # --- تحديث الحذف الشامل (الحل البرمجي الأضمن) ---
                st.divider()
                st.subheader("🗑️ حذف طالب (شامل نهائي)")
                del_name = st.selectbox("اختر الطالب للحذف النهائي", [""] + filt["الاسم"].tolist())
                if st.button("تأكيد الحذف الشامل"):
                    if del_name:
                        with st.spinner("جاري تنظيف كافة الجداول..."):
                            # 1. حذف من السلوك (عن طريق إعادة بناء الجدول بدون اسم الطالب)
                            ws_bh = sh.worksheet("behavior")
                            records_bh = ws_bh.get_all_records()
                            if records_bh:
                                # فلترة السجلات وإزالة الطالب المختار
                                clean_bh = [r for r in records_bh if str(list(r.values())[0]).strip() != del_name.strip()]
                                ws_bh.clear()
                                if clean_bh:
                                    ws_bh.append_row(list(records_bh[0].keys())) # استرجاع الهيدر
                                    ws_bh.append_rows([list(r.values()) for r in clean_bh])

                            # 2. حذف من الدرجات (grades)
                            try:
                                ws_gr = sh.worksheet("grades")
                                c_gr = ws_gr.find(del_name.strip())
                                ws_gr.delete_rows(c_gr.row)
                            except: pass

                            # 3. حذف من الطلاب (students)
                            ws_st = sh.worksheet("students")
                            c_st = ws_st.find(del_name.strip())
                            ws_st.delete_rows(c_st.row)

                            st.success(f"✅ تم حذف {del_name} وكافة بياناته من جميع الجداول")
                            time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        if not df_all.empty:
            names = df_all["الاسم"].tolist()
            t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])

            with t_grad:
                with st.form("g_up"):
                    sel_st = st.selectbox("اختر الطالب", names)
                    c1, c2, c3 = st.columns(3)
                    p1, p2, pf = c1.number_input("الفترة 1"), c2.number_input("الفترة 2"), c3.number_input("الأداء")
                    if st.form_submit_button("تحديث"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_st); ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except: ws_g.append_row([sel_st, p1, p2, pf])
                        st.success("✅ تم تحديث الدرجات")
                
                df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "أداء"])
                st.dataframe(df_g, use_container_width=True, hide_index=True)

            with t_beh:
                with st.form("b_add"):
                    b_st = st.selectbox("اسم الطالب", names)
                    b_date = st.date_input("📅 التاريخ", datetime.now())
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد"):
                        sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                        st.success("✅ تم الرصد")
                
                # --- حل مشكلة حذف السلوك المنفرد ---
                st.subheader("🗑️ حذف سجل سلوك")
                df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
                if not df_b.empty:
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
                    del_b_note = st.selectbox("اختر الملاحظة لحذفها", [""] + df_b["الملاحظة"].tolist())
                    if st.button("حذف الملاحظة"):
                        if del_b_note:
                            ws_bh = sh.worksheet("behavior")
                            cell = ws_bh.find(del_b_note)
                            ws_bh.delete_rows(cell.row)
                            st.success("✅ تم الحذف"); time.sleep(1); st.rerun()
