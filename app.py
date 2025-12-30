import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# --- 1. إعداد الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. إدارة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 المعلم")
        if st.text_input("كلمة المرور", type="password") == "1234":
            if st.button("دخول المعلم"): 
                st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and sid in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
            else: st.error("غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة", ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"])

    if menu == "👥 الطلاب":
        st.header("إدارة الطلاب")
        df = fetch_data("students")
        st.dataframe(df, use_container_width=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            id_n = c1.text_input("الرقم")
            name_n = c2.text_input("الاسم")
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([id_n, name_n, "الأول", "1447", "1", "English", "إبتدائي", "", "", 0])
                st.success("تمت الإضافة"); time.sleep(1); st.rerun()

    elif menu == "📝 الدرجات":
        st.header("رصد الدرجات")
        df_s = fetch_data("students")
        if not df_s.empty:
            name = st.selectbox("اختر الطالب", df_s.iloc[:, 1].tolist())
            with st.form("g"):
                p1, p2, pf = st.columns(3)
                v1 = p1.number_input("فترة 1", 0, 100)
                v2 = p2.number_input("فترة 2", 0, 100)
                v3 = pf.number_input("مشاركة", 0, 100)
                if st.form_submit_button("حفظ"):
                    ws = sh.worksheet("grades")
                    try: 
                        cell = ws.find(name)
                        ws.update(f"B{cell.row}:D{cell.row}", [[v1, v2, v3]])
                    except: ws.append_row([name, v1, v2, v3])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        st.dataframe(fetch_data("grades"), use_container_width=True)

    elif menu == "📢 الاختبارات":
        st.header("إعلان الاختبارات")
        with st.form("ex"):
            sub = st.text_input("المادة")
            dt = st.date_input("التاريخ")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(dt), sub])
                st.success("تم النشر"); time.sleep(1); st.rerun()
        st.table(fetch_data("exams"))

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    st.title(f"👋 أهلاً {row.iloc[1]}")
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سلوكي"])
    with t1: st.table(fetch_data("grades").query(f"`student_id`=='{row.iloc[1]}'"))
    with t2: st.table(fetch_data("exams"))
    with t3: st.table(fetch_data("behavior").query(f"`name`=='{row.iloc[1]}'"))
