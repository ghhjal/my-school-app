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
# 🚪 شاشة الدخول الموحدة
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
            else: st.error("عذراً، الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.markdown(f"### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()

    # 1. إدارة الطلاب
    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;"> <h1 style="margin:0;">👥 إدارة شؤون الطلاب</h1> </div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add_student"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف الدراسي", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("✅ اعتماد"):
                sh.worksheet("students").append_row([nid, nname, nclass, "1447هـ", "نشط", "English", "ابتدائي", "", "", "0"])
                st.success("تم التأسيس"); st.rerun()

    # 2. شاشة الدرجات
    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background: linear-gradient(90deg, #6366f1 0%, #4338ca 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;"> <h1>📝 رصد درجات الطلاب</h1> </div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("📉 الفترة الأولى", 0, 100)
                p2 = c2.number_input("📉 الفترة الثانية", 0, 100)
                part = c3.number_input("⭐ المشاركة", 0, 100)
                if st.form_submit_button("💾 حفظ"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target); ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ")

    # 3. رصد السلوك (الواتساب والإيميل)
    elif menu == "🎭 رصد السلوك":
        st.markdown('<div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;"> <h1>🎭 رصد السلوك والتواصل الفوري</h1> </div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + df_st.iloc[:, 1].tolist())
        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6]; s_phone = str(student_info[7]).split('.')[0]
            with st.form("beh_wa"):
                c1, c2 = st.columns(2)
                b_type = st.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_note = st.text_area("📝 الملاحظة")
                col1, col2, col3 = st.columns(3)
                if col1.form_submit_button("💾 حفظ فقط"):
                    sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note]); st.success("تم الحفظ")
                if col2.form_submit_button("📧 إيميل"):
                    msg = f"تقرير سلوك: {b_name}\nالنوع: {b_type}\nالملاحظة: {b_note}"
                    st.markdown(f'<meta http-equiv="refresh" content="0;url=mailto:{s_email}?subject=تقرير&body={urllib.parse.quote(msg)}">', unsafe_allow_html=True)
                if col3.form_submit_button("💬 واتساب"):
                    msg = f"تقرير سلوك: {b_name}\nالنوع: {b_type}\nالملاحظة: {b_note}"
                    wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank">📲 إرسال واتساب</a>', unsafe_allow_html=True)

    # 4. شاشة الاختبارات (زر واتساب لكل اختبار)
    elif menu == "📢 شاشة الاختبارات":
        st.markdown('<div style="background: linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;"> <h1>📢 مركز التنبيهات</h1> </div>', unsafe_allow_html=True)
        with st.form("ex_post"):
            c1, c2, c3 = st.columns([1, 2, 1])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = c2.text_input("📝 العنوان")
            a_date = c3.date_input("📅 الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([a_class, a_title, str(a_date)]); st.rerun()
        
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for _, r in df_ex.iloc[::-1].iterrows():
                with st.expander(f"📢 {r[1]} ({r[0]})"):
                    st.write(f"📅 التاريخ: {r[2]}")
                    wa_msg = f"تنبيه: {r[1]}\nالموعد: {r[2]}"
                    st.markdown(f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}" target="_blank">💬 نشر التنبيه</a>', unsafe_allow_html=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (مستقلة وتدعم الجوال)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    # هيدر أخضر مميز للطالب
    st.markdown(f'<div style="background: linear-gradient(90deg, #059669 0%, #10B981 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;"> <h1>مرحباً بك يا متميز: {s_row[1]}</h1> </div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    col1.metric("🌟 رصيد نقاطك", f"{s_row[8]} نقطة")
    col2.metric("🏫 الصف الدراسي", s_row[2])

    with st.expander("⚙️ تحديث بيانات التواصل الخاصة بك"):
        with st.form("st_update"):
            new_mail = st.text_input("📧 بريدك الإلكتروني", value=str(s_row[6]))
            new_phone = st.text_input("📱 رقم جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ التعديلات"):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail)
                ws.update_cell(cell.row, 8, new_phone)
                st.success("تم تحديث بياناتك بنجاح!"); time.sleep(1); st.rerun()

    st.markdown("### 📢 جدول التنبيهات والاختبارات")
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_row[2]) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.info(f"📍 {r[1]} | 📅 الموعد: {r[2]}")
            
    if st.sidebar.button("🚗 خروج"):
        st.session_state.role = None; st.rerun()
