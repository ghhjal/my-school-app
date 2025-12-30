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

# --- 3. دالة جلب البيانات الذكية (تتجاوز الصفوف الفارغة وتوحد الأعمدة) ---
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            # حذف الصفوف التي يكون فيها المفتاح الأساسي فارغاً
            df = df[df.iloc[:, 0].str.strip() != ""]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# إدارة حالة الدخول
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
# 🛠️ واجهة المعلم (إدارة شاملة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])
    
    # --- 1. شاشة إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("➕ إضافة طالب")
            with st.form("add_student"):
                nid = st.text_input("الرقم الأكاديمي")
                nname = st.text_input("الاسم")
                ncls = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                nstg = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ"):
                    sh.worksheet("students").append_row([nid, nname, ncls, "1447هـ", "الأول", "إنجليزي", nstg, "", "", 0])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        with c2:
            st.subheader("🗑️ حذف طالب")
            if not df_st.empty:
                target = st.selectbox("اختر للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("تأكيد الحذف"):
                    ws = sh.worksheet("students"); cell = ws.find(target)
                    ws.delete_rows(cell.row); st.warning("تم الحذف"); time.sleep(1); st.rerun()

    # --- 2. شاشة رصد الدرجات ---
    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_name:
                with st.form("g_form"):
                    p1 = st.number_input("فترة 1", 0, 100)
                    p2 = st.number_input("فترة 2", 0, 100)
                    pf = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("حفظ الدرجة"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_name)
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except:
                            ws_g.append_row([sel_name, p1, p2, pf])
                        st.success("تم الرصد"); time.sleep(1); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- 3. شاشة إعلان الاختبارات (الجديدة) ---
    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 جدول الاختبارات القادمة")
        
        with st.form("exam_form", clear_on_submit=True):
            ex_subject = st.text_input("المادة", value="اللغة الإنجليزية")
            ex_date = st.date_input("تاريخ الاختبار")
            ex_day = st.selectbox("اليوم", ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            ex_period = st.selectbox("الحصة", ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"])
            if st.form_submit_button("📢 نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_date), ex_day, ex_subject, ex_period])
                st.success("تم نشر إعلان الاختبار بنجاح")
                time.sleep(1); st.rerun()
        
        st.divider()
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            st.subheader("📋 الاختبارات المعلنة")
            st.dataframe(df_ex, use_container_width=True)
            if st.button("🗑️ مسح جميع الإعلانات القديمة"):
                ws_ex = sh.worksheet("exams")
                rows = len(ws_ex.get_all_values())
                if rows > 1:
                    ws_ex.delete_rows(2, rows)
                    st.success("تم تنظيف الجدول"); time.sleep(1); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"👋 أهلاً بك يا بطل: {s_data.iloc[1]}")
    
    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "📢 الاختبارات", "🎭 سلوكي"])
    
    with tab1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_data.iloc[1]]
        st.table(my_g) if not my_g.empty else st.info("لم ترصد درجاتك بعد")
        
    with tab2:
        df_ex = fetch_safe("exams")
        st.table(df_ex) if not df_ex.empty else st.info("لا توجد اختبارات معلنة حالياً")
        
    with tab3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_data.iloc[1]]
        st.table(my_b) if not my_b.empty else st.info("سجلك السلوكي نظيف، استمر!")
