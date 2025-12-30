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
            # معالجة العناوين المكررة لضمان عدم حدوث ValueError
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
        st.subheader("🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 منطقة الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("الرقم الأكاديمي")
            name_n = c2.text_input("الاسم")
            year_n = c3.text_input("العام الدراسي", value="1447هـ")
            if st.form_submit_button("حفظ الطالب"):
                sh.worksheet("students").append_row([id_n, name_n, "الأول", year_n, "1", "English", "ابتدائي", "", "", 0])
                st.success("تم الحفظ"); st.rerun()

    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            with st.form("g_form"):
                p1 = st.number_input("الفترة 1", 0, 100)
                p2 = st.number_input("الفترة 2", 0, 100)
                if st.form_submit_button("حفظ الدرجة"):
                    ws = sh.worksheet("grades")
                    try: 
                        cell = ws.find(sel_name)
                        ws.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                    except: ws.append_row([sel_name, p1, p2])
                    st.success("تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    elif menu == "🎭 رصد السلوك":
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
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (تم حل مشكلة النصوص الغريبة وزر الشكر)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    # --- إضافة زر شكراً أستاذ ---
    if st.button("❤️ شكراً أستاذ زياد"):
        st.balloons()
        st.success("شكراً لك يا بطل، بارك الله فيك وفي مجهودك!")

    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سجل سلوكي"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                st.table(my_g)
            else: st.info("لا توجد درجات مرصودة حالياً")
            
    with t2:
        st.table(fetch_safe("exams"))
        
    with t3:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                st.table(my_b)
            else: st.success("سجلك نظيف ومميز! استمر يا بطل.")
