import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stMetricLabel"] { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    .stMetric { background-color: white !important; padding: 15px !important; border-radius: 12px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
    .main { background-color: #f8f9fa; direction: rtl; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .exam-alert { background-color: #fee2e2; border-right: 10px solid #dc2626; padding: 15px; border-radius: 10px; color: #991b1b; font-weight: bold; margin-bottom: 20px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

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

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل"])
            match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
            if not match.empty:
                st.session_state.role = "student"
                st.session_state.student_id = str(sid_in)
                st.session_state.student_name = match.iloc[0]["الاسم"]
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 الاختبارات"])
    
    if menu == "📢 الاختبارات":
        st.header("📢 إعلان اختبار جديد")
        with st.form("ex_f"):
            e_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("موضوع الاختبار")
            e_date = st.date_input("التاريخ")
            if st.form_submit_button("إرسال التنبيه"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.success("تم النشر بنجاح")
                
    elif menu == "👥 إدارة الطلاب":
        st.header("👥 قائمة الطلاب")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # ميزة الحذف الفردي
        target = st.selectbox("حذف طالب", [""] + df_st["الاسم"].tolist())
        if st.button("تأكيد الحذف"):
            if target:
                for sn in ["students", "behavior", "grades"]:
                    try:
                        ws = sh.worksheet(sn)
                        cell = ws.find(target)
                        ws.delete_rows(cell.row)
                    except: continue
                st.success("تم الحذف"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        # (نفس كود الرصد السابق مع إظهار الجداول بالأسفل)
        st.info("واجهة الدرجات والسلوك")

# --- 4. واجهة الطالب (وضوح عالي + تحديث البيانات) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    # جلب بيانات الطالب المحدثة
    ws_st = sh.worksheet("students")
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل"])
    my_row_idx = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].index[0]
    my_info = df_st.iloc[my_row_idx]

    # --- تنبيه الاختبارات المخصصة للفصل ---
    df_ex = fetch_data_safe("exams", ["الصف", "العنوان", "التاريخ"])
    my_exams = df_ex[df_ex["الصف"] == my_info["الصف"]]
    for i, row in my_exams.iterrows():
        st.markdown(f"<div class='exam-alert'>⚠️ اختبار جديد: {row['العنوان']} | 📅 {row['التاريخ']}</div>", unsafe_allow_html=True)

    # --- تحديث الإيميل ذاتياً ---
    with st.expander("📧 تحديث بريدك الإلكتروني لاستلام التنبيهات"):
        new_email = st.text_input("أدخل إيميلك هنا", value=my_info["الإيميل"])
        if st.button("حفظ الإيميل"):
            # تحديث الخلية السابعة (عمود G) في صف الطالب
            ws_st.update_cell(my_row_idx + 2, 7, new_email)
            st.success("تم تحديث بريدك بنجاح!")
            time.sleep(1); st.rerun()

    # عرض البيانات بوضوح
    c1, c2, c3 = st.columns(3)
    c1.metric("الصف", my_info["الصف"])
    c2.metric("المرحلة", my_info["المرحلة"])
    c3.metric("المادة", my_info["المادة"])
    
    st.divider()
    st.subheader("📊 تقرير الدرجات")
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    st.dataframe(my_grades, use_container_width=True, hide_index=True)
