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
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 4px solid #1e3a8a; }
    footer {visibility: hidden;}
    .title-text { color: #1e3a8a; font-family: 'Arial'; text-align: center; }
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
    st.markdown("<h1 class='title-text'>🏛️ منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("تسجيل الدخول كمعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب", key="login_sid")
        if st.button("تسجيل الدخول كطالب"):
            if sid_in:
                df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
                match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
                if not match.empty:
                    st.session_state.role = "student"; st.session_state.student_id = str(sid_in)
                    st.session_state.student_name = match.iloc[0]["الاسم"]; st.rerun()
                else: st.error("الرقم الأكاديمي غير مسجل.")
    st.stop()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown("## 🏛️ منصة أ. زياد المعمري")
    if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()
    st.divider()
    st.markdown("### ✍️ إشراف وإدارة:")
    st.info("**الأستاذ زياد المعمري**")

# --- 3. واجهة المعلم (تحديث رصد السلوك) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        # (بقية كود إدارة الطلاب كما هو بدون تغيير)
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with t_beh:
            with st.form("beh_form"):
                b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                b_date = st.date_input("التاريخ", datetime.now())
                # التعديل الجديد: إضافة الخيارات الأربعة
                b_type = st.radio("نوع السلوك", ["✅ إيجابي", "⭐ متميز", "⚠️ تنبيه", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد"):
                    sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                    st.success("✅ تم الرصد بنجاح"); time.sleep(1); st.rerun()

# --- 4. واجهة الطالب (تحديث عرض السلوك الملون) ---
elif st.session_state.role == "student":
    st.markdown(f"<h2 style='text-align:right;'>🎓 بيانات الطالب | أهلاً بك: {st.session_state.student_name}</h2>", unsafe_allow_html=True)
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    # عرض البيانات الأساسية والدرجات
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    st.metric("المادة المسجلة", my_info["المادة"])
    st.divider()
    
    st.subheader("🎭 السجل السلوكي الشامل")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            # السطر 139 المطور بالألوان الأربعة
            if "إيجابي" in row["النوع"]:
                st.success(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "متميز" in row["النوع"]:
                st.info(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "تنبيه" in row["النوع"]:
                st.warning(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "سلبي" in row["النوع"]:
                st.error(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
    else: st.success("سجلك السلوكي متميز!")
