import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. إعداد الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            headers = [h if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            df = pd.DataFrame(data[1:], columns=headers)
            df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"])

    # 1. إدارة الطلاب (العام الدراسي + الحذف)
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("الرقم الأكاديمي")
            name_n = c2.text_input("الاسم")
            year_n = c3.text_input("العام الدراسي", value="1447هـ")
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([id_n, name_n, "الأول", year_n, "1", "إنجليزي", "ابتدائي", "", "", 0])
                st.success("تم الحفظ"); st.rerun()
        
        st.subheader("🗑️ حذف طالب")
        target = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
        if st.button("تأكيد الحذف") and target:
            ws = sh.worksheet("students"); cell = ws.find(target)
            ws.delete_rows(cell.row); st.rerun()

    # 2. السلوك (الجدول السفلي متوفر الآن)
    elif menu == "🎭 السلوك":
        st.header("🎭 رصد السلوك")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["تميز", "تنبيه", "غياب"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد"):
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الرصد"); st.rerun()
        
        st.subheader("📋 جدول السلوك المرصود")
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    # 3. الاختبارات (حذف الإعلانات)
    elif menu == "📢 الاختبارات":
        st.header("📢 إعلان الاختبارات")
        with st.form("ex_form"):
            ex_sub = st.text_input("المادة")
            ex_dt = st.date_input("التاريخ")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(ex_dt), ex_sub])
                st.rerun()
        
        st.subheader("📋 الإعلانات الحالية")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.info(f"{row.iloc[1]} | {row.iloc[0]}")
                if c2.button("🗑️ حذف", key=f"ex_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (تحديث الإيميل والجوال)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_idx = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].index[0]
    s_row = df_st.loc[s_idx]
    
    st.title(f"👋 أهلاً {s_row.iloc[1]}")

    with st.expander("⚙️ تحديث بياناتي الشخصية (الإيميل والجوال)"):
        with st.form("st_update"):
            u_email = st.text_input("البريد الإلكتروني", value=s_row.iloc[7] if len(s_row)>7 else "")
            u_phone = st.text_input("رقم الجوال", value=s_row.iloc[8] if len(s_row)>8 else "")
            if st.form_submit_button("تحديث"):
                ws = sh.worksheet("students")
                ws.update_cell(s_idx + 2, 8, u_email)
                ws.update_cell(s_idx + 2, 9, u_phone)
                st.success("تم التحديث"); st.rerun()

    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سلوكي"])
    with t1: st.table(fetch_safe("grades").query(f"student_id=='{s_row.iloc[1]}'"))
    with t2: st.table(fetch_safe("exams"))
    with t3: st.table(fetch_safe("behavior").query(f"name=='{s_row.iloc[1]}'"))
