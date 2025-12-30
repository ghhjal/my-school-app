import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال الآمن ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

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
            # معالجة العناوين لتجنب خطأ التكرار Duplicate Column Names
            headers = [h if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            return pd.DataFrame(data[1:], columns=headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المستقلة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات"])

    # --- 1. إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.header("👥 سجل الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("ID")
            name_n = c2.text_input("الاسم")
            stage_n = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            class_n = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([id_n, name_n, class_n, "1447هـ", "1", "English", stage_n, "", "", 0])
                st.success("✅ تم الحفظ"); st.rerun()

    # --- 2. رصد الدرجات ---
    elif menu == "📝 رصد الدرجات":
        st.header("📝 تحديث الدرجات")
        df_st = fetch_data("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            df_g = fetch_data("grades")
            curr = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            with st.form("up_g"):
                p1 = st.number_input("الفترة 1", 0, 100, value=v1)
                p2 = st.number_input("الفترة 2", 0, 100, value=v2)
                if st.form_submit_button("حفظ التعديل"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_name)
                        ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                    except: ws_g.append_row([sel_name, p1, p2])
                    st.success("✅ تم التحديث"); st.rerun()

    # --- 3. رصد السلوك ---
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        df_st = fetch_data("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("النوع", ["تميز (+10)", "تنبيه (-5)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد الملاحظة"):
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note, "🕒 لم تقرأ"])
                    st.success("✅ تم الرصد"); st.rerun()
        st.dataframe(fetch_data("behavior"), use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (الخصوصية المطلقة)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h2 style='text-align: center;'>👋 أهلاً بك: {s_name}</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سلوكي"])
    
    with tab1:
        df_g = fetch_data("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات")
            
    with tab3:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_data("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for i, row in my_b.iterrows():
                with st.container(border=True):
                    st.write(f"📅 {row.iloc[1]} | {row.iloc[2]}")
                    st.write(f"💬 {row.iloc[3]} | الحالة: {row.iloc[4]}")
                    if st.button("❤️ شكراً أستاذ زياد (تمت القراءة)", key=f"th_{i}"):
                        ws_b = sh.worksheet("behavior")
                        cells = ws_b.findall(s_name)
                        for c in cells:
                            if ws_b.cell(c.row, 4).value == row.iloc[3]:
                                ws_b.update_cell(c.row, 5, "✅ تمت القراءة")
                                st.success("تم تأكيد القراءة"); st.rerun()
