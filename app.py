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
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
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
# 🛠️ واجهة المعلم (كاملة الحقول والهوية)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة ملفات الطلاب الشاملة")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        with st.form("add_full_st"):
            st.subheader("➕ إضافة طالب (بيانات كاملة)")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("الرقم الأكاديمي")
            name_n = c2.text_input("الاسم الثلاثي")
            class_n = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            
            c4, c5, c6 = st.columns(3)
            year_n = c4.text_input("العام الدراسي", value="1447هـ")
            stage_n = c5.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            sub_n = c6.text_input("المادة", value="English")
            
            if st.form_submit_button("حفظ الطالب في قاعدة البيانات"):
                # الأعمدة: ID, Name, Class, Year, Term, Subject, Stage, Email, Phone, Points
                sh.worksheet("students").append_row([id_n, name_n, class_n, year_n, "1", sub_n, stage_n, "", "", 0])
                st.success("✅ تم الحفظ بنجاح"); st.rerun()
        
        st.subheader("🗑️ منطقة الحذف")
        target = st.selectbox("اختر الطالب المراد حذفه", [""] + df_st.iloc[:, 1].tolist())
        if st.button("❌ حذف الطالب نهائياً") and target:
            ws = sh.worksheet("students"); cell = ws.find(target)
            ws.delete_rows(cell.row); st.warning("تم الحذف"); st.rerun()

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والنقاط")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["⭐ تميز (+10)", "✅ مشاركة (+5)", "⚠️ تنبيه (-5)", "❌ غياب (-10)"])
                b_note = st.text_area("الملاحظة السلوكية")
                if st.form_submit_button("حفظ ورصد"):
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                    # تحديث النقاط تلقائياً
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5
                    ws_s = sh.worksheet("students"); cell = ws_s.find(sel_b)
                    current_pts = int(ws_s.cell(cell.row, 10).value or 0)
                    ws_s.update_cell(cell.row, 10, current_pts + pts)
                    st.success("✅ تم الرصد وتحديث النقاط"); st.rerun()
        
        st.subheader("📋 السجل العام للسلوك")
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("ex_form"):
            c1, c2, c3 = st.columns(3)
            ex_sub = c1.text_input("المادة")
            ex_dt = c2.date_input("التاريخ")
            ex_time = c3.text_input("الحصة/الوقت")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_dt), ex_sub, ex_time])
                st.success("✅ تم النشر"); st.rerun()
        
        st.subheader("📋 الإعلانات الحالية (إدارة)")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                c1, c2 = st.columns([5, 1])
                c1.info(f"📖 {row.iloc[1]} | 📅 {row.iloc[0]} | ⏰ {row.iloc[2] if len(row)>2 else ''}")
                if c2.button("🗑️ حذف", key=f"ex_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الأوسمة + التميز + التحديث)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_idx = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].index[0]
    s_row = df_st.loc[s_idx]
    pts = int(s_row.iloc[9] if len(s_row)>9 else 0)

    # --- هوية الطالب والأوسمة ---
    st.markdown(f"<h2 style='text-align: center;'>👋 مرحباً بالبطل: {s_row.iloc[1]}</h2>", unsafe_allow_html=True)
    
    col_p, col_badge = st.columns(2)
    with col_p:
        st.metric("🏆 رصيد نقاطك", f"{pts} نقطة")
    with col_badge:
        if pts >= 50: st.markdown("### 🎖️ وسام: **الطالب الماسي** 💎")
        elif pts >= 30: st.markdown("### 🎖️ وسام: **الطالب الذهبي** ⭐")
        else: st.markdown("### 🎖️ وسام: **طالب طموح** 🌱")

    with st.expander("⚙️ تحديث بيانات التواصل (الإيميل والجوال)"):
        with st.form("st_update"):
            u_email = st.text_input("بريد ولي الأمر", value=s_row.iloc[7] if len(s_row)>7 else "")
            u_phone = st.text_input("رقم الجوال", value=s_row.iloc[8] if len(s_row)>8 else "")
            if st.form_submit_button("تحديث بياناتي"):
                ws = sh.worksheet("students")
                ws.update_cell(s_idx + 2, 8, u_email)
                ws.update_cell(s_idx + 2, 9, u_phone)
                st.success("✅ تم التحديث"); st.rerun()

    t1, t2, t3 = st.tabs(["📊 نتائج الاختبارات", "📅 جدول الاختبارات", "🎭 سجل التميز والسلوك"])
    with t1: st.table(fetch_safe("grades").query(f"student_id=='{s_row.iloc[1]}'"))
    with t2: st.table(fetch_safe("exams"))
    with t3: st.table(fetch_safe("behavior").query(f"name=='{s_row.iloc[1]}'"))
