import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

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
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد العمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        if st.text_input("كلمة المرور", type="password") == "1234":
            if st.button("دخول المعلم"): st.session_state.role = "teacher"; st.rerun()
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
# 🛠️ واجهة المعلم (إدارة الطلاب + رصد السلوك)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "🎭 رصد السلوك", "📝 الدرجات", "📢 الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("الرقم الأكاديمي")
            name_n = c2.text_input("الاسم")
            stage_n = c3.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
            c4, c5 = st.columns(2)
            class_n = c4.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            year_n = c5.text_input("العام الدراسي", value="1447هـ")
            if st.form_submit_button("حفظ الطالب"):
                sh.worksheet("students").append_row([id_n, name_n, class_n, year_n, "1", "English", stage_n, "", "", 0])
                st.success("✅ تم الحفظ"); st.rerun()

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 سجل الملاحظات السلوكية")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["تميز (+10)", "تنبيه (-5)", "مشاركة (+5)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد الملاحظة"):
                    # الأعمدة: الاسم، التاريخ، النوع، الملاحظة، الحالة (قيد الانتظار)
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note, "⏳ لم يتم الاطلاع"])
                    st.success("✅ تم الرصد"); st.rerun()
        st.subheader("📋 الملاحظات المرصودة")
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (الخصوصية + زر شكراً أستاذ)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سجل ملاحظاتي"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات حالياً")
            
    with t2:
        st.table(fetch_safe("exams"))
        
    with t3:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            # فلترة صارمة: الطالب يرى ملاحظاته هو فقط!
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    with st.expander(f"📅 ملاحظة بتاريخ {row.iloc[1]} - {row.iloc[2]}"):
                        st.write(f"💬 {row.iloc[3]}")
                        st.write(f"الحالة: {row.iloc[4]}")
                        # زر شكراً أستاذ لتأكيد القراءة
                        if st.button("❤️ شكراً أستاذ (تمت القراءة)", key=f"thanks_{i}"):
                            ws_b = sh.worksheet("behavior")
                            # البحث عن الصف الصحيح في الشيت لتحديثه
                            all_rows = ws_b.get_all_values()
                            for idx, r in enumerate(all_rows):
                                if r[0] == s_name and r[1] == row.iloc[1] and r[3] == row.iloc[3]:
                                    ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                    st.success("تم إرسال شكرك للأستاذ!")
                                    st.rerun()
            else: st.success("🌟 سجلك نظيف تماماً!")
