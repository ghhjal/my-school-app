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
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- دالة الإرسال المستقرة ---
def send_email_notification(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع الكود المكون من 16 حرفاً هنا
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

# --- الاتصال بقاعدة البيانات ---
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

# إدارة حالة الدخول
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# ==========================================
# 🚪 شاشة الدخول المزدوجة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    col_t, col_s = st.columns(2)
    
    with col_t:
        st.markdown("### 🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": # يمكنك تغيير كلمة المرور هنا
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
            
    with col_s:
        st.markdown("### 👨‍🎓 منطقة الطالب")
        s_id = st.text_input("أدخل الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch("students")
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id)
                st.rerun()
            else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات"])
    
    df_st = fetch("students")

    # --- 1. شاشة إدارة الطلاب (الإضافة والحذف الشامل) ---
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        
        # عرض الجدول الرئيسي (المصدر الوحيد للحقيقة)
        st.subheader("📋 قائمة الطلاب المسجلين حالياً")
        df_st = fetch("students") # جلب أحدث بيانات
        if not df_st.empty:
            st.dataframe(df_st, use_container_width=True, hide_index=True)
        else:
            st.info("لا يوجد طلاب مسجلون حالياً.")

        # تقسيم الشاشة لجزئين: إضافة وحذف
        col_add, col_del = st.columns(2)
        
        # --- قسم إضافة طالب جديد ---
        with col_add:
            st.markdown("### ➕ إضافة طالب جديد")
            with st.form("new_student_form", clear_on_submit=True):
                n_id = st.text_input("الرقم الأكاديمي (ID)")
                n_name = st.text_input("اسم الطالب الثلاثي")
                n_stage = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                n_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                n_year = st.text_input("العام الدراسي", value="1447هـ")
                
                st.info("💡 ملاحظة: الإيميل والجوال يضيفهما الطالب من حسابه")
                
                if st.form_submit_button("✅ حفظ البيانات"):
                    if n_id and n_name:
                        ws_s = sh.worksheet("students")
                        # إضافة الصف بالترتيب: [ID, الاسم, الصف, العام, الفصل, المادة, المرحلة, الايميل, الجوال, النقاط]
                        ws_s.append_row([n_id, n_name, n_class, n_year, "الفصل الأول", "اللغة الإنجليزية", n_stage, "", "", 0])
                        st.success(f"تم تسجيل الطالب {n_name} بنجاح!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("⚠️ يرجى إدخال الاسم والرقم الأكاديمي")

        # --- قسم الحذف النهائي من كل الجداول ---
        with col_del:
            st.markdown("### 🗑️ حذف بيانات طالب نهائياً")
            if not df_st.empty:
                target_student = st.selectbox("اختر الطالب الذي تريد حذفه", [""] + df_st['name'].tolist())
                
                st.warning("⚠️ سيؤدي هذا الإجراء إلى حذف الطالب من جداول (الطلاب، الدرجات، والسلوك) فوراً.")
                if st.button("❌ تأكيد الحذف الشامل"):
                    if target_student:
                        with st.spinner(f"جاري حذف {target_student}..."):
                            # 1. الحذف من جدول الطلاب
                            ws_st = sh.worksheet("students")
                            try:
                                cell = ws_st.find(target_student)
                                ws_st.delete_rows(cell.row)
                                
                                # 2. الحذف من جدول الدرجات
                                try:
                                    ws_gr = sh.worksheet("grades")
                                    # نحذف جميع الصفوف المرتبطة بهذا الطالب (في حال وجود أكثر من صف)
                                    cells_gr = ws_gr.findall(target_student)
                                    for c in sorted(cells_gr, key=lambda x: x.row, reverse=True):
                                        ws_gr.delete_rows(c.row)
                                except: pass
                                
                                # 3. الحذف من جدول السلوك
                                try:
                                    ws_bh = sh.worksheet("behavior")
                                    cells_bh = ws_bh.findall(target_student)
                                    for c in sorted(cells_bh, key=lambda x: x.row, reverse=True):
                                        ws_bh.delete_rows(c.row)
                                except: pass
                                
                                st.success(f"تم مسح بيانات {target_student} من كافة السجلات.")
                                time.sleep(1)
                                st.rerun()
                            except:
                                st.error("حدث خطأ أثناء محاولة الحذف.")
                    else:
                        st.error("يرجى اختيار اسم طالب.")

    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات")
        sel = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
        if sel:
            with st.form("g_form"):
                f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                if st.form_submit_button("تحديث"):
                    ws = sh.worksheet("grades")
                    try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                    except: ws.append_row([sel, f1, f2, pt])
                    st.success("تم التحديث")
        st.dataframe(fetch("grades"), use_container_width=True)

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
        if sel_b:
            with st.form("b_form"):
                b_date = st.date_input("التاريخ", datetime.now())
                b_type = st.radio("التقييم", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("رصد وإرسال إشعار"):
                    with st.spinner("جاري الرصد..."):
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old_p = int(ws_s.cell(c.row, 10).value or 0) # العمود العاشر هو النقاط
                        ws_s.update_cell(c.row, 10, old_p + pts)
                        email = ws_s.cell(c.row, 8).value # العمود الثامن هو الإيميل
                        send_email_notification(email, sel_b, b_type, b_note, b_date)
                        st.success("تم الرصد بنجاح"); st.rerun()
        st.dataframe(fetch("behavior").iloc[::-1], use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
if st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]

    st.markdown(f"<h1 style='text-align:center;'>👋 أهلاً بك: {s_name}</h1>", unsafe_allow_html=True)
    st.info(f"المرحلة: {s_data.iloc[6]} | العام: {s_data.iloc[3]} | النقاط: {s_data.iloc[9]}")

    t1, t2, t3, t4 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📅 الاختبارات", "⚙️ بياناتي"])
    # (هنا يتم وضع كود عرض البيانات للطالب كما في النسخ السابقة لضمان التنسيق)
