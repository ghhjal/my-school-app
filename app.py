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
# 🛠️ واجهة المعلم (تصميمك الأصلي مع معالجة قائمة menu)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        with st.container(border=True):
            st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_student_pro", clear_on_submit=True):
            st.markdown("### ➕ تأسيس طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nyear = c5.text_input("🗓️ العام", value="1447هـ")
            nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
            if st.form_submit_button("✅ اعتماد التأسيس"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"])
                    st.success("تم التأسيس بنجاح"); st.rerun()

    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("grade_pro_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("📉 الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                if st.form_submit_button("💾 حفظ"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target); ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except:
                        ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    elif menu == "🎭 رصد السلوك":
        st.markdown('<div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>🎭 رصد السلوك والتواصل</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        search_term = st.text_input("🔍 ابحث عن اسم الطالب")
        filtered_names = [n for n in df_st.iloc[:, 1].tolist() if search_term in n] if search_term else df_st.iloc[:, 1].tolist()
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + filtered_names)
        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6]; s_phone = str(student_info[7]).split('.')[0]
            with st.form("behavior_form"):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 الملاحظة")
                if st.form_submit_button("💾 حفظ ورصد"):
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    # تحديث النقاط تلقائياً
                    try:
                        ws_st = sh.worksheet("students"); cell = ws_st.find(b_name)
                        p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                        curr_p = int(ws_st.cell(cell.row, 9).value or 0)
                        ws_st.update_cell(cell.row, 9, str(curr_p + p_map.get(b_type, 0)))
                    except: pass
                    st.success("تم الرصد"); st.rerun()

    elif menu == "📢 شاشة الاختبارات":
        st.markdown('<div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>📢 مركز التنبيهات</h1></div>', unsafe_allow_html=True)
        with st.form("exam_post"):
            c1, c2, c3 = st.columns([1, 2, 1])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = c2.text_input("📝 العنوان")
            a_date = c3.date_input("📅 الموعد")
            if st.form_submit_button("🚀 نشر الآن"):
                sh.worksheet("exams").append_row([a_class, a_title, str(a_date)])
                st.rerun()
        df_ann = fetch_safe("exams")
        if not df_ann.empty:
            for i, row in df_ann.iloc[::-1].iterrows():
                st.info(f"[{row[0]}] {row[1]} - 📅 {row[2]}")

# ==========================================
# 👨‍🎓 واجهة الطالب (تم فصلها لتجنب خطأ NameError)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.markdown("### 👨‍🎓 قائمة الطالب")
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()

    st.markdown("""
        <div style="background: linear-gradient(90deg, #059669 0%, #10B981 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
            <h1 style="margin:0;">👨‍🎓 بوابة الطالب المتميز</h1>
            <p style="margin:5px 0 0 0; opacity: 0.9;">تابع نقاطك واخر التنبيهات</p>
        </div>
    """, unsafe_allow_html=True)

    df_st = fetch_safe("students")
    # جلب بيانات الطالب بناءً على الرقم الأكاديمي المستخدم في الدخول
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row[1]
    s_class = s_row[2]
    s_points = s_row[8] if s_row[8] else 0

    st.subheader(f"مرحباً بك يا {s_name} 👋")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='background:#ecfdf5; padding:20px; border-radius:15px; border:1px solid #10b981; text-align:center;'><small>🌟 رصيد نقاطك</small><br><b style='font-size:24px; color:#059669;'>{s_points} نقطة</b></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background:#f0f9ff; padding:20px; border-radius:15px; border:1px solid #0ea5e9; text-align:center;'><small>🏫 الصف</small><br><b style='font-size:24px; color:#0ea5e9;'>{s_class}</b></div>", unsafe_allow_html=True)

    with st.expander("⚙️ تحديث بيانات التواصل"):
        with st.form("update_info"):
            new_mail = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            new_phone = st.text_input("📱 رقم الجوال", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ التعديلات"):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail)
                ws.update_cell(cell.row, 8, new_phone)
                st.success("تم التحديث!"); time.sleep(1); st.rerun()

    st.markdown("### 📢 آخر التنبيهات الخاصة بك")
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.success(f"📍 **{r[1]}** \n\n 📅 التاريخ: {r[2]}")
