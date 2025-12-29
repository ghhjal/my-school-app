import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. الإعدادات والربط ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

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

# --- 🆕 دالة إرسال البريد الإلكتروني ---
def send_email_alert(student_name, parent_email, behavior_type, note):
    try:
        # بيانات السيرفر (يتم جلبها من Secrets لضمان الأمان)
        sender_email = st.secrets["email_settings"]["sender_email"]
        sender_password = st.secrets["email_settings"]["sender_password"]
        
        subject = f"🔔 إشعار سلوكي جديد: {student_name}"
        body = f"""
        تحية طيبة،
        نود إحاطتكم بأنه تم رصد ملاحظة سلوكية جديدة لابننا الطالب: {student_name}
        
        التفاصيل:
        - نوع السلوك: {behavior_type}
        - الملاحظة: {note}
        - التاريخ: {datetime.now().strftime('%Y-%m-%d')}
        
        مع تحيات الأستاذ زياد المعمري.
        """
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = parent_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, parent_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        st.divider()
        col_del, col_add = st.columns([1, 2])
        with col_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.error(f"تم حذف {to_del}"); time.sleep(1); st.rerun()
        with col_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                id_v = c1.text_input("الرقم")
                name_v = c2.text_input("الاسم")
                c3, c4, c5 = st.columns(3)
                cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = c4.text_input("العام", value="1446هـ")
                sub_v = c5.text_input("المادة", value="اللغة الإنجليزية")
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة ✅"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        df_st = fetch_data("students")
        with tab1:
            target = st.selectbox("اختر الطالب", df_st['name'].tolist())
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                v1 = c1.number_input("ف1")
                v2 = c2.number_input("ف2")
                v3 = c3.number_input("مشاركة")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        fnd = ws_g.find(target)
                        ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                    except: ws_g.append_row([target, v1, v2, v3])
                    st.success("تم التحديث ✅")

        with tab2:
            st.subheader("🎭 رصد السلوك والتحفيز")
            sel_st = st.selectbox("اسم الطالب", df_st['name'].tolist(), key="bh_sel")
            # جلب إيميل الطالب من جدول الطلاب
            st_info = df_st[df_st['name'] == sel_st].iloc[0]
            target_email = st_info.get('الإيميل', '')

            with st.form("b_form", clear_on_submit=True):
                d_v = st.date_input("التاريخ", datetime.now())
                t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                n_v = st.text_input("ملاحظة السلوك")
                if st.form_submit_button("حفظ الرصد وإرسال إيميل"):
                    pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                    sh.worksheet("behavior").append_row([sel_st, str(d_v), t_v, n_v])
                    
                    # تحديث النقاط
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old + pts)
                    
                    # 📧 إرسال الإيميل تلقائياً
                    if target_email and "@" in target_email:
                        if send_email_alert(sel_st, target_email, t_v, n_v):
                            st.info(f"📧 تم إرسال إشعار للبريد: {target_email}")
                        else:
                            st.warning("⚠️ فشل إرسال الإيميل، يرجى التحقق من الإعدادات.")
                    else:
                        st.warning("⚠️ لا يوجد بريد إلكتروني مسجل لهذا الطالب.")
                    
                    st.success(f"تم حفظ الرصد بنجاح ✅"); time.sleep(1); st.rerun()

            st.divider()
            st.subheader(f"📜 سجل ملاحظات الطالب: {sel_st}")
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                st.dataframe(df_bh[df_bh['student_id'] == sel_st], use_container_width=True, hide_index=True)

# --- 4. واجهة الطالب (مستقرة) ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    df_ex = fetch_data("exams")
    if not df_ex.empty:
        my_ex = df_ex[df_ex['الصف'] == s_data['class']]
        for _, r in my_ex.iterrows():
            st.warning(f"🔔 **تنبيه اختبار:** {r['العنوان']} في تاريخ {r['التاريخ']}")

    st.markdown(f"### 👋 مرحباً بك يا بطل: {s_data['name']}")
    s_lev = s_data.get('المرحلة', 'غير محدد')
    st.info(f"📍 الصف: {s_data['class']} | المرحلة: {s_lev} | المادة: {s_data['sem']}")

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📧 بياناتي"])
    
    with t1:
        st.subheader("📝 درجات الاختبارات والمشاركة")
        df_g = fetch_data("grades")
        my_g = df_g[df_g['student_id'] == s_data['name']].drop_duplicates()
        if not my_g.empty:
            top_g = my_g.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("ف1 (p1)", top_g['p1'])
            c2.metric("ف2 (p2)", top_g['p2'])
            c3.metric("مشاركة (perf)", top_g['perf'])
            st.dataframe(my_g, use_container_width=True, hide_index=True)
        else: st.info("لا توجد درجات مرصودة حالياً.")

    with t2:
        st.subheader(f"⭐ رصيد النقاط الحالي: {s_data.get('النقاط', 0)}")
        df_b = fetch_data("behavior")
        my_b = df_b[df_b['student_id'] == s_data['name']]
        st.dataframe(my_b, use_container_width=True, hide_index=True)

    with t3:
        with st.form("up"):
            m = st.text_input("الإيميل", value=str(s_data.get('الإيميل', '')))
            p = st.text_input("الجوال", value=str(s_data.get('الجوال', '')))
            if st.form_submit_button("حفظ التحديث"):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, m); ws.update_cell(cell.row, 8, p)
                st.success("تم التحديث ✅"); st.rerun()
