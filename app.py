import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. إعداد الصفحة والاتصال الآمن ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة جلب البيانات مع تجنب أخطاء العناوين المكررة التي ظهرت في الصور
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            # نستخدم العناوين من الصف الأول وننظف البيانات
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. إدارة حالة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# شاشة الدخول
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("خطأ في كلمة المرور")
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        s_id_input = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(s_id_input) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id_input)
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (تم دمج شاشة الاختبارات هنا)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"])
    
    # 1. إدارة الطلاب
    if menu == "👥 الطلاب":
        st.header("إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب جديد")
            id_n = st.text_input("الرقم الأكاديمي")
            name_n = st.text_input("الاسم الثلاثي")
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([id_n, name_n, "الأول", "1447هـ", "1", "إنجليزي", "ابتدائي", "", "", 0])
                st.success("تم الحفظ"); time.sleep(1); st.rerun()

    # 2. رصد الدرجات
    elif menu == "📝 الدرجات":
        st.header("رصد درجات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_name:
                with st.form("g_form"):
                    p1 = st.number_input("فترة 1", 0, 100)
                    p2 = st.number_input("فترة 2", 0, 100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_name)
                            ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                        except:
                            ws_g.append_row([sel_name, p1, p2, 0])
                        st.success("تم الرصد"); time.sleep(0.5); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. إعلان الاختبارات (المطلوبة)
    elif menu == "📢 الاختبارات":
        st.header("📢 إعلان جدول الاختبارات")
        with st.form("exam_form"):
            ex_sub = st.text_input("المادة")
            ex_day = st.selectbox("اليوم", ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            ex_date = st.date_input("التاريخ")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_date), ex_day, ex_sub])
                st.success("تم النشر بنجاح"); st.rerun()
        st.subheader("الجدول الحالي")
        st.table(fetch_safe("exams"))

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.title(f"👋 أهلاً بك يا بطل: {s_name}")
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📢 الاختبارات", "🎭 سلوكي"])
    
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        st.table(my_g) if not my_g.empty else st.info("لا توجد درجات حالياً")
    with t2:
        st.table(fetch_safe("exams"))
    with t3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_name]
        st.table(my_b) if not my_b.empty else st.success("سجلك نظيف!")
