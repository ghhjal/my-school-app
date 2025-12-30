import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- 2. الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=2)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# --- 3. دالة جلب البيانات الذكية ---
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 4. إدارة حالة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المزدوجة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    col_t, col_s = st.columns(2)
    
    with col_t:
        st.markdown("### 🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
            
    with col_s:
        st.markdown("### 👨‍🎓 منطقة الطالب")
        s_id = st.text_input("أدخل الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id)
                st.rerun()
            else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])
    
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.form("add_st"):
                st.subheader("➕ إضافة طالب")
                nid = st.text_input("الرقم الأكاديمي")
                nname = st.text_input("الاسم")
                nstg = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ"):
                    sh.worksheet("students").append_row([nid, nname, "الأول", "1447هـ", "1", "إنجليزي", nstg, "", "", 0])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        with c2:
            st.subheader("🗑️ حذف طالب")
            if not df_st.empty:
                target = st.selectbox("اختر للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("حذف") and target:
                    ws = sh.worksheet("students"); cell = ws.find(target)
                    ws.delete_rows(cell.row); st.rerun()

    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_name:
                with st.form("g_form"):
                    p1 = st.number_input("فترة 1", 0, 100)
                    p2 = st.number_input("فترة 2", 0, 100)
                    if st.form_submit_button("حفظ الدرجة"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_name)
                            ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                        except:
                            ws_g.append_row([sel_name, p1, p2, 0])
                        st.success("تم الحفظ"); time.sleep(1); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 إعلان اختبار جديد")
        with st.form("ex_form"):
            sub = st.text_input("المادة")
            dt = st.date_input("التاريخ")
            day = st.selectbox("اليوم", ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(dt), day, sub])
                st.success("تم النشر"); time.sleep(1); st.rerun()
        st.dataframe(fetch_safe("exams"), use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"👋 أهلاً بك: {s_data.iloc[1]}")
    
    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سلوكي"])
    with tab1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_data.iloc[1]]
        if not my_g.empty: st.table(my_g)
        else: st.info("لا توجد درجات حالياً")
    with tab2:
        df_ex = fetch_safe("exams")
        if not df_ex.empty: st.table(df_ex)
        else: st.info("لا توجد اختبارات معلنة")
    with tab3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_data.iloc[1]]
        if not my_b.empty: st.table(my_b)
        else: st.info("سجلك نظيف")
