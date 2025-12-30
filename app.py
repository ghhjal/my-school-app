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
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إدارة شاملة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nstage = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            c4, c5 = st.columns(2)
            nclass = c4.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            nyear = c5.text_input("العام الدراسي", value="1447هـ")
            if st.form_submit_button("حفظ الطالب"):
                sh.worksheet("students").append_row([nid, nname, nclass, nyear, "1", "إنجليزي", nstage, "", "", 0])
                st.success("تم الحفظ"); st.rerun()

    elif menu == "📝 رصد الدرجات":
        st.header("📝 تحديث الدرجات")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            with st.form("g_up"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("فترة 1", 0, 100, value=v1)
                p2 = c2.number_input("فترة 2", 0, 100, value=v2)
                if st.form_submit_button("تعديل الدرجة"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_name)
                        ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                    except: ws_g.append_row([sel_name, p1, p2])
                    st.success("✅ تم التحديث"); st.rerun()

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("النوع", ["تميز (+10)", "تنبيه (-5)"])
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("رصد"):
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note, "⏳ لم تقرأ"])
                    st.success("تم الرصد"); st.rerun()
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (إصلاح سجل السلوك + زر الشكر)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    # بطاقة معلومات الطالب (الهوية المستعادة)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("🏆 نقاط التميز", s_row.iloc[9])
        c2.write(f"**المرحلة:** {s_row.iloc[6]}")
        c3.write(f"**العام الدراسي:** {s_row.iloc[3]}")

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 ملاحظاتي السلوكية", "📅 الاختبارات"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات حالياً")

    with t2:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            # فلترة ملاحظات هذا الطالب فقط
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    with st.expander(f"📅 {row.iloc[1]} - {row.iloc[2]}"):
                        st.write(f"💬 {row.iloc[3]}")
                        st.write(f"الحالة: {row.iloc[4]}")
                        # زر شكراً أستاذ زياد (مرتبط بالملاحظة)
                        if st.button("❤️ شكراً أستاذ (تمت القراءة)", key=f"thnx_{i}"):
                            ws_b = sh.worksheet("behavior")
                            # تحديث حالة القراءة في جوجل شيت
                            try:
                                cell = ws_b.find(row.iloc[3]) # البحث بالملاحظة لضمان الدقة
                                ws_b.update_cell(cell.row, 5, "✅ تمت القراءة")
                                st.success("تم تأكيد الاطلاع، شكراً لك!"); time.sleep(1); st.rerun()
                            except: st.error("فشل التحديث")
            else: st.success("🌟 سجلك نظيف ومميز!")
    
    with t3:
        st.table(fetch_safe("exams"))
