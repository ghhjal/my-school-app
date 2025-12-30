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

    # --- 1. إدارة الطلاب ---
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
            class_n = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([id_n, name_n, class_n, year_n, "1", "English", "ابتدائي", "", "", 0])
                st.success("تم الحفظ"); st.rerun()

    # --- 2. رصد الدرجات (تم الإصلاح) ---
    elif menu == "📝 رصد الدرجات":
        st.header("📝 تحديث درجات الطلاب")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب لتحديث درجته", [""] + df_st.iloc[:, 1].tolist())
        
        if sel_name:
            df_g = fetch_safe("grades")
            # جلب الدرجات الحالية إذا وجدت
            current_g = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(current_g.iloc[0, 1]) if not current_g.empty else 0
            v2 = int(current_g.iloc[0, 2]) if not current_g.empty else 0
            
            with st.form("update_grade"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("الفترة الثانية", 0, 100, value=v2)
                if st.form_submit_button("حفظ التعديلات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_name)
                        ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                    except:
                        ws_g.append_row([sel_name, p1, p2])
                    st.success("✅ تم تحديث الدرجات"); st.rerun()
        st.subheader("📋 جدول الدرجات الحالي")
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- 3. رصد السلوك ---
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["⭐ تميز (+10)", "✅ مشاركة (+5)", "⚠️ تنبيه (-5)", "❌ غياب (-10)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("حفظ الرصد"):
                    # إضافة التاريخ والاسم والملاحظة
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                    # تحديث النقاط في شيت الطلاب
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5
                    ws_s = sh.worksheet("students"); cell = ws_s.find(sel_b)
                    old_p = int(ws_s.cell(cell.row, 10).value or 0)
                    ws_s.update_cell(cell.row, 10, old_p + pts)
                    st.success("✅ تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    # --- 4. إعلان الاختبارات ---
    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 إعلان الاختبارات")
        with st.form("ex_form"):
            ex_sub = st.text_input("المادة")
            ex_dt = st.date_input("التاريخ")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(ex_dt), ex_sub])
                st.rerun()
        
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.info(f"{row.iloc[1]} | {row.iloc[0]}")
                if c2.button("🗑️ حذف", key=f"ex_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (تم إصلاح شاشة السلوك)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_idx = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].index[0]
    s_row = df_st.loc[s_idx]
    s_name = s_row.iloc[1] # اسم الطالب
    
    st.title(f"👋 أهلاً بك: {s_name}")
    st.metric("🏆 مجموع نقاطك", f"{s_row.iloc[9] if len(s_row)>9 else 0}")

    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سجل سلوكي وتسميزي"])
    
    with tab1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            # فلترة الدرجات بناءً على اسم الطالب بدقة
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات مرصودة")
            
    with tab2:
        st.table(fetch_safe("exams"))
        
    with tab3:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            # فلترة السلوك بناءً على اسم الطالب المكتوب في العمود الأول من شيت behavior
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                st.write("📋 سجل ملاحظاتك السلوكية:")
                st.table(my_b)
            else:
                st.success("🌟 سجلك نظيف تماماً! استمر في التميز.")
