import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
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

# دالة جلب البيانات الآمنة (تعالج مشكلة تكرار العناوين)
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

# دالة إرسال الإيميل
def send_email(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # الكود المكون من 16 حرفاً
        body = f"ولي أمر الطالب/ة: {student_name}\nرصد ملاحظة سلوكية جديدة:\n📅 التاريخ: {note_date}\n🏷️ النوع: {note_type}\n📝 الملاحظة: {note_text}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"إشعار من الأستاذ زياد المعمري", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except: return False

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المزدوجة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 منطقة المعلم")
        if st.text_input("كلمة المرور", type="password") == "1234":
            if st.button("دخول المعلم"): st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 منطقة الطالب")
        s_id_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(s_id_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(s_id_in); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (كاملة الحقول)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"])

    # 1. إدارة الطلاب (إضافة وحذف بكافة الحقول)
    if menu == "👥 الطلاب":
        st.header("👥 إدارة ملفات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        col_add, col_del = st.columns(2)
        with col_add:
            with st.form("add_student"):
                st.subheader("➕ إضافة طالب جديد")
                id_n = st.text_input("الرقم الأكاديمي")
                name_n = st.text_input("الاسم الثلاثي")
                class_n = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                stage_n = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                email_n = st.text_input("إيميل ولي الأمر")
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([id_n, name_n, class_n, "1447هـ", "1", "إنجليزي", stage_n, email_n, "نشط", 0])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        with col_del:
            st.subheader("🗑️ حذف طالب")
            target = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if st.button("تأكيد الحذف") and target:
                ws = sh.worksheet("students"); cell = ws.find(target)
                ws.delete_rows(cell.row); st.rerun()

    # 2. رصد الدرجات (الفترات والمشاركة)
    elif menu == "📝 الدرجات":
        st.header("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            with st.form("g_form"):
                p1 = st.number_input("فترة 1", 0, 100)
                p2 = st.number_input("فترة 2", 0, 100)
                perf = st.number_input("المشاركة", 0, 100)
                if st.form_submit_button("حفظ"):
                    ws = sh.worksheet("grades")
                    try: 
                        cell = ws.find(sel_name)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, perf]])
                    except: ws.append_row([sel_name, p1, p2, perf])
                    st.success("تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. رصد السلوك (النقاط والإيميل)
    elif menu == "🎭 السلوك":
        st.header("🎭 رصد السلوك والنقاط")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["⭐ تميز (+10)", "✅ مشاركة (+5)", "⚠️ تنبيه (-5)", "❌ غياب (-10)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد وإرسال إيميل"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                    # تحديث النقاط في شيت الطلاب
                    ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                    old_p = int(ws_s.cell(c.row, 10).value or 0)
                    ws_s.update_cell(c.row, 10, old_p + pts)
                    # إرسال إيميل
                    email = ws_s.cell(c.row, 8).value
                    send_email(email, sel_b, b_type, b_note, datetime.now().date())
                    st.success("تم الرصد وتحديث النقاط"); st.rerun()

    # 4. إعلان الاختبارات
    elif menu == "📢 الاختبارات":
        st.header("📢 إعلان اختبار")
        with st.form("ex_form"):
            ex_sub = st.text_input("المادة")
            ex_day = st.selectbox("اليوم", ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            ex_date = st.date_input("التاريخ")
            ex_per = st.text_input("الحصة")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(ex_date), ex_day, ex_sub, ex_per])
                st.success("تم النشر"); st.rerun()
        st.table(fetch_safe("exams"))

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"👋 أهلاً {s_row.iloc[1]}")
    st.info(f"إجمالي نقاطك: {s_row.iloc[9]}")
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📢 الاختبارات", "🎭 سلوكي"])
    with t1: st.table(fetch_safe("grades").query(f"student_id=='{s_row.iloc[1]}'"))
    with t2: st.table(fetch_safe("exams"))
    with t3: st.table(fetch_safe("behavior").query(f"name=='{s_row.iloc[1]}'"))
