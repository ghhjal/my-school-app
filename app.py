import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

# إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- دالة إرسال الإيميل الاحترافية ---
def send_email_notification(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع هنا كلمة مرور التطبيقات (16 حرفاً)
        
        msg_content = f"""
        تحية طيبة ولي أمر الطالب/ة: {student_name}
        نود إحاطتكم علماً بأنه تم رصد ملاحظة سلوكية في منصة الأستاذ زياد المعمري:
        
        📅 التاريخ: {note_date}
        🏷️ النوع: {note_type}
        📝 الملاحظة: {note_text}
        
        شاكرين لكم تعاونكم الدائم.
        """
        message = MIMEText(msg_content, 'plain', 'utf-8')
        message['Subject'] = Header(f"إشعار سلوكي جديد: {student_name}", 'utf-8')
        message['From'] = sender
        message['To'] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, message.as_string())
        return True
    except Exception as e:
        return False

# --- الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

# إدارة متغيرات الجلسة للحفاظ على الاستقرار
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed_actions' not in st.session_state: st.session_state.confirmed_actions = set()

# --- نظام الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("دخول كمعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي", key="login_sid")
        if st.button("دخول كطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 رصد الدرجات والسلوك", "📢 إعلانات الاختبارات"])
    
    df_students = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة ملفات الطلاب")
        st.dataframe(df_students, use_container_width=True, hide_index=True)
        
        with st.expander("➕ إضافة طالب جديد"):
            with st.form("add_student_form"):
                col1, col2 = st.columns(2)
                new_id = col1.text_input("الرقم الأكاديمي")
                new_name = col2.text_input("اسم الطالب الثلاثي")
                new_cls = col1.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                new_yr = col2.text_input("العام الدراسي", value="1447هـ")
                new_stg = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([new_id, new_name, new_cls, new_yr, "اللغة الإنجليزية", new_stg, "", "", 0])
                    st.success("تمت الإضافة بنجاح"); time.sleep(1); st.rerun()

        with st.expander("🗑️ حذف طالب (نهائياً)"):
            target = st.selectbox("اختر الاسم المراد حذفه", [""] + df_students['name'].tolist() if not df_students.empty else [])
            if st.button("تأكيد الحذف الشامل"):
                for sheet in ["students", "grades", "behavior"]:
                    try:
                        ws = sh.worksheet(sheet); cell = ws.find(target)
                        if cell: ws.delete_rows(cell.row)
                    except: pass
                st.warning(f"تم حذف {target} من كافة الجداول"); time.sleep(1); st.rerun()

    elif menu == "📊 رصد الدرجات والسلوك":
        tab_g, tab_b = st.tabs(["📝 الدرجات", "🎭 السلوك والملاحظات"])
        
        with tab_g:
            st.subheader("رصد درجات الطالب")
            sel_st = st.selectbox("اختر الطالب للدرجات", [""] + df_students['name'].tolist() if not df_students.empty else [], key="g_sel")
            if sel_st:
                with st.form("grades_form"):
                    f1 = st.number_input("الفترة الأولى", 0, 100)
                    f2 = st.number_input("الفترة الثانية", 0, 100)
                    part = st.number_input("المشاركة", 0, 100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws = sh.worksheet("grades")
                        try:
                            cell = ws.find(sel_st)
                            ws.update(f'B{cell.row}:D{cell.row}', [[f1, f2, part]])
                        except:
                            ws.append_row([sel_st, f1, f2, part])
                        st.success("تم التحديث"); st.rerun()
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with tab_b:
            st.subheader("رصد ملاحظة سلوكية")
            sel_st_b = st.selectbox("اختر الطالب للملاحظة", [""] + df_students['name'].tolist() if not df_students.empty else [], key="b_sel")
            if sel_st_b:
                with st.form("behavior_form"):
                    b_date = st.date_input("تاريخ الملاحظة", datetime.now())
                    b_type = st.radio("التقييم", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    b_note = st.text_input("تفاصيل الملاحظة")
                    if st.form_submit_button("إرسال ورصد"):
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        # 1. حفظ الملاحظة
                        sh.worksheet("behavior").append_row([sel_st_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                        # 2. تحديث النقاط في شيت الطلاب
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st_b)
                        old_p = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_p + pts)
                        # 3. محاولة إرسال الإيميل (بدون تعطيل البرنامج)
                        email_to = ws_st.cell(c.row, 7).value
                        if email_to: send_email_notification(email_to, sel_st_b, b_type, b_note, b_date)
                        st.success("تم الرصد بنجاح وإرسال الإشعار لولي الأمر"); time.sleep(1); st.rerun()
            
            st.divider()
            st.subheader("🔍 السجل التاريخي للملاحظات")
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                filtered_bh = df_bh[df_bh.iloc[:, 0] == sel_st_b] if sel_st_b else df_bh
                st.dataframe(filtered_bh.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 إدارة مواعيد الاختبارات")
        with st.form("exam_form"):
            e_cls = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_subj = st.text_input("موضوع الاختبار")
            e_date = st.date_input("الموعد")
            if st.form_submit_button("نشر الموعد"):
                sh.worksheet("exams").append_row([e_cls, e_subj, str(e_date)])
                st.success("تم النشر"); st.rerun()
        st.dataframe(fetch_data("exams"), use_container_width=True)

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    student_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = student_data.iloc[1]

    st.markdown(f"<h1 style='text-align:center;'>🌟 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📅 المواعيد", "⚙️ بياناتي"])
    
    with t1:
        df_g = fetch_data("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1", my_g.iloc[0, 1])
            c2.metric("فترة 2", my_g.iloc[0, 2])
            c3.metric("مشاركة", my_g.iloc[0, 3])

    with t2:
        st.subheader("سجل ملاحظات الأستاذ زياد")
        df_bh = fetch_data("behavior")
        if not df_bh.empty:
            df_bh['real_idx'] = range(2, len(df_bh) + 2)
            my_bh = df_bh[df_bh.iloc[:, 0] == s_name].iloc[::-1]
            for _, row in my_bh.iterrows():
                r_id = int(row['real_idx'])
                is_read = "✅" in str(row.iloc[4]) or r_id in st.session_state.confirmed_actions
                bg = "#C8E6C9" if is_read else "#FFF9C4" # ألوان واضحة للجوال
                
                st.markdown(f"""
                <div style='background:{bg}; padding:15px; border-radius:10px; margin-bottom:10px; color:black; border: 1px solid #ddd;'>
                    <b>{row.iloc[2]}</b> - التاريخ: {row.iloc[1]}<br>
                    الملاحظة: {row.iloc[3]}
                </div>
                """, unsafe_allow_html=True)
                
                if not is_read:
                    if st.button(f"🙏 شكراً أستاذ زياد (تأكيد القراءة)", key=f"confirm_{r_id}"):
                        st.session_state.confirmed_actions.add(r_id)
                        try:
                            sh.worksheet("behavior").update_cell(r_id, 5, "✅ تمت القراءة")
                            st.rerun()
                        except: pass

    with t3:
        df_ex = fetch_data("exams")
        if not df_ex.empty:
            st.table(df_ex[(df_ex.iloc[:, 0] == student_data.iloc[2]) | (df_ex.iloc[:, 0] == "الكل")])

    with t4:
        st.subheader("تحديث بيانات التواصل")
        with st.form("update_info"):
            u_email = st.text_input("إيميل ولي الأمر", value=student_data.iloc[6])
            u_phone = st.text_input("رقم الجوال", value=student_data.iloc[7])
            if st.form_submit_button("حفظ التعديلات"):
                ws = sh.worksheet("students"); c = ws.find(s_name)
                ws.update(f'G{c.row}:H{c.row}', [[u_email, u_phone]])
                st.success("تم التحديث بنجاح")
