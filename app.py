import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
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
            else: st.error("عذراً، الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()

    # --- 1. إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_st"):
            st.markdown("### ➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("✅ إضافة"):
                sh.worksheet("students").append_row([nid, nname, nclass, "1447هـ", "نشط", "English", "ابتدائي", "", "", "0"])
                st.success("تمت الإضافة"); st.rerun()

    # --- 2. شاشة الدرجات ---
    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة 1", 0, 100)
                p2 = c2.number_input("الفترة 2", 0, 100)
                part = c3.number_input("مشاركة", 0, 100)
                if st.form_submit_button("💾 حفظ"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target); ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ")
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    # --- 3. رصد السلوك (مع واتساب وإيميل) ---
    elif menu == "🎭 رصد السلوك":
        st.markdown('<div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>🎭 رصد السلوك والتواصل الفوري</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        search_term = st.text_input("🔍 ابحث عن الطالب")
        filtered_names = [n for n in df_st.iloc[:, 1].tolist() if search_term in n] if search_term else df_st.iloc[:, 1].tolist()
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + filtered_names)
        
        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6]; s_phone = str(student_info[7]).split('.')[0]
            with st.form("beh_form"):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 نص الملاحظة")
                col1, col2, col3 = st.columns(3)
                btn_save = col1.form_submit_button("💾 حفظ")
                btn_mail = col2.form_submit_button("📧 + إيميل")
                btn_wa = col3.form_submit_button("💬 + واتساب")

                if btn_save or btn_mail or btn_wa:
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    msg = f"تقرير سلوك: {b_name}\nالنوع: {b_type}\nالملاحظة: {b_note}\nالتاريخ: {b_date}"
                    if btn_mail and s_email:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url=mailto:{s_email}?subject=تقرير&body={urllib.parse.quote(msg)}">', unsafe_allow_html=True)
                    if btn_wa and s_phone:
                        wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(msg)}"
                        st.markdown(f'<a href="{wa_url}" target="_blank">📲 إرسال واتساب</a>', unsafe_allow_html=True)
                    st.success("تم الرصد")

    # --- 4. شاشة الاختبارات (مع زر واتساب العام) ---
    elif menu == "📢 شاشة الاختبارات":
        st.markdown('<div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>📢 مركز التنبيهات</h1></div>', unsafe_allow_html=True)
        with st.form("ex_post"):
            c1, c2, c3 = st.columns([1, 2, 1])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = c2.text_input("📝 العنوان")
            a_date = c3.date_input("📅 الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([a_class, a_title, str(a_date)]); st.rerun()
        
        df_ann = fetch_safe("exams")
        if not df_ann.empty:
            for i, row in df_ann.iloc[::-1].iterrows():
                with st.expander(f"📢 {row[1]} - ({row[0]})"):
                    st.write(f"📅 التاريخ: {row[2]}")
                    wa_msg = f"📢 تنبيه جديد\nالموضوع: {row[1]}\nالصف: {row[0]}\nالموعد: {row[2]}"
                    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-decoration:none;">💬 إرسال التنبيه للمجموعات</a>', unsafe_allow_html=True)

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    st.markdown(f'<div style="background:#10b981; padding:20px; border-radius:15px; color:white; text-align:center;"><h1>مرحباً {s_row[1]}</h1><h3>رصيد نقاطك: {s_row[8]} نقطة</h3></div>', unsafe_allow_html=True)
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_row[2]) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.info(f"📍 {r[1]} | 📅 {r[2]}")
