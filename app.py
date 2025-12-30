import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

# --- إعداد الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# --- دالة الإرسال (تم زيادة وقت الانتظار لضمان الاستقرار) ---
def send_email_v2(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # تأكد من تحديث هذا الكود (16 حرفاً)
        
        body = f"تحية طيبة ولي أمر الطالب/ة: {student_name}\nنحيطكم علماً بأنه تم رصد ملاحظة سلوكية:\n\n📅 التاريخ: {note_date}\n🏷️ النوع: {note_type}\n📝 الملاحظة: {note_text}\n\nشكراً لاهتمامكم."
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"إشعار سلوكي: {student_name}", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# --- الاتصال بـ Google Sheets ---
@st.cache_resource(ttl=5)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = "teacher" # للتجربة

# --- تصميم الشاشات المستقلة ---
if st.session_state.role == "teacher":
    st.sidebar.title("🛠️ لوحة التحكم")
    # تم فصل الشاشات هنا لتكون مستقلة تماماً
    menu = st.sidebar.selectbox("اختر الشاشة", 
        ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات"])
    
    df_st = fetch("students")

    # 1. شاشة إدارة الطلاب
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # (كود الإضافة والحذف يوضع هنا كما في النسخ السابقة)

    # 2. شاشة رصد الدرجات (مستقلة)
    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد وتحديث درجات الطلاب")
        sel = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
        if sel:
            with st.form("grades_form"):
                f1 = st.number_input("فترة 1", 0, 100)
                f2 = st.number_input("فترة 2", 0, 100)
                pt = st.number_input("مشاركة", 0, 100)
                if st.form_submit_button("حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try: 
                        c = ws.find(sel)
                        ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                    except: 
                        ws.append_row([sel, f1, f2, pt])
                    st.success("✅ تم تحديث الدرجات بنجاح")
        
        st.divider()
        st.subheader("📊 جدول الدرجات الحالي")
        st.dataframe(fetch("grades"), use_container_width=True, hide_index=True)

    # 3. شاشة رصد السلوك (مستقلة وبدون خروج مفاجئ)
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد الملاحظات السلوكية")
        sel_b = st.selectbox("اختر الطالب للملاحظة", [""] + df_st['name'].tolist() if not df_st.empty else [])
        
        if sel_b:
            with st.form("behavior_form"):
                b_date = st.date_input("تاريخ الملاحظة", datetime.now())
                b_type = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("تفاصيل الملاحظة")
                
                if st.form_submit_button("رصد الملاحظة وإرسال الإيميل"):
                    with st.spinner("جاري الرصد والإرسال..."):
                        # الرصد في الشيت أولاً
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                        
                        ws_s = sh.worksheet("students")
                        c = ws_s.find(sel_b)
                        old_p = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old_p + pts)
                        
                        # جلب الإيميل والإرسال
                        email = ws_s.cell(c.row, 7).value
                        sent = send_email_v2(email, sel_b, b_type, b_note, b_date)
                        
                        if sent:
                            st.success(f"✅ تم الرصد وإرسال الإيميل لولي أمر {sel_b}")
                        else:
                            st.warning("⚠️ تم الرصد في النظام، لكن تعذر إرسال الإيميل (تحقق من الإيميل وكلمة السر)")
        
        st.divider()
        st.subheader("🔍 سجل الملاحظات التاريخي")
        st.dataframe(fetch("behavior").iloc[::-1], use_container_width=True, hide_index=True)

    # 4. شاشة الاختبارات
    elif menu == "📢 الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("exam_form"):
            e_cls = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_subj = st.text_input("المادة / الموضوع")
            e_date = st.date_input("موعد الاختبار")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([e_cls, e_subj, str(e_date)])
                st.success("✅ تم النشر")
        
        st.subheader("📋 الإعلانات الحالية")
        st.dataframe(fetch("exams"), use_container_width=True, hide_index=True)
