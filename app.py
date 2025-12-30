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

# --- دالة الإرسال (محمية من الانهيار) ---
def send_notification(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع الكود المكون من 16 حرفاً هنا
        body = f"ولي أمر الطالب: {student_name}\nتم رصد ملاحظة سلوكية جديدة:\nالتاريخ: {note_date}\nالنوع: {note_type}\nالملاحظة: {note_text}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"إشعار سلوكي: {student_name}", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
    except: pass

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

# --- إدارة الجلسة ---
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# --- شاشة الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password", key="t_pwd")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        s_id = st.text_input("الرقم الأكاديمي", key="s_id")
        if st.button("دخول الطالب"):
            df_st = fetch("students")
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(s_id); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 الاختبارات"])
    
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_students = fetch("students")
        st.dataframe(df_students, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 إضافة طالب")
            with st.form("add_form"):
                id_v = st.text_input("الرقم الأكاديمي")
                name_v = st.text_input("الاسم الثلاثي")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = st.text_input("العام الدراسي", value="1447هـ")
                stg_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, "إنجليزي", stg_v, "", "", 0])
                    st.success("تم الحفظ بنجاح"); st.rerun()
        with col2:
            st.subheader("🗑️ حذف طالب")
            target = st.selectbox("اختر الطالب للحذف", [""] + df_students['name'].tolist() if not df_students.empty else [])
            if st.button("حذف الطالب نهائياً من كل السجلات"):
                if target:
                    for s in ["students", "grades", "behavior"]:
                        try: ws = sh.worksheet(s); cell = ws.find(target); ws.delete_rows(cell.row)
                        except: pass
                    st.warning(f"تم حذف {target}"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        df_st = fetch("students")
        
        with tab1:
            sel = st.selectbox("اختر الطالب للدرجات", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel:
                with st.form("g_form"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("تحديث الدرجات"):
                        ws = sh.worksheet("grades")
                        try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws.append_row([sel, f1, f2, pt])
                        st.success("تم التحديث")
            st.subheader("📊 جدول الدرجات")
            st.dataframe(fetch("grades"), use_container_width=True, hide_index=True)

        with tab2:
            sel_b = st.selectbox("اختر الطالب للملاحظة", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel_b:
                with st.form("b_form"):
                    b_date = st.date_input("تاريخ الملاحظة", datetime.now())
                    b_type = st.radio("التقييم", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    b_note = st.text_input("تفاصيل الملاحظة")
                    if st.form_submit_button("رصد وإرسال"):
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old_p = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old_p + pts)
                        # إرسال الإيميل
                        email = ws_s.cell(c.row, 7).value
                        send_notification(email, sel_b, b_type, b_note, b_date)
                        st.success("تم الرصد والإرسال"); st.rerun()
            st.subheader("🔍 سجل الملاحظات التاريخي")
            st.dataframe(fetch("behavior").iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 الاختبارات":
        with st.form("ex_form"):
            c_v = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_v = st.text_input("الموضوع"); d_v = st.date_input("الموعد")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([c_v, t_v, str(d_v)]); st.rerun()
        st.dataframe(fetch("exams"), use_container_width=True)

# --- واجهة الطالب ---
if st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align:center;'>👋 أهلاً بك: {s_name}</h1>", unsafe_allow_html=True)
    st.info(f"العام الدراسي: {s_row.iloc[3]} | المرحلة: {s_row.iloc[5]} | النقاط: {s_row.iloc[8]}")

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي وملاحظاتي", "⚙️ تحديث بياناتي"])
    
    with t1:
        df_g = fetch("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1", my_g.iloc[0, 1])
            c2.metric("فترة 2", my_g.iloc[0, 2])
            c3.metric("مشاركة", my_g.iloc[0, 3])

    with t2:
        df_b = fetch("behavior")
        if not df_b.empty:
            df_b['row_idx'] = range(2, len(df_b) + 2)
            my_b = df_b[df_b.iloc[:, 0] == s_name].iloc[::-1]
            for _, r in my_b.iterrows():
                rid = int(r['row_idx'])
                is_read = "✅" in str(r.iloc[4]) or rid in st.session_state.confirmed
                bg = "#D4EDDA" if is_read else "#FFF3CD"
                st.markdown(f"<div style='background:{bg}; padding:15px; border-radius:10px; margin-bottom:10px; color:black; border: 1px solid #ddd;'><b>{r.iloc[2]}</b> - {r.iloc[1]}<br>{r.iloc[3]}</div>", unsafe_allow_html=True)
                
                if not is_read:
                    if st.button(f"🙏 شكراً أستاذي زياد", key=f"btn_{rid}"):
                        st.session_state.confirmed.add(rid)
                        try:
                            sh.worksheet("behavior").update_cell(rid, 5, "✅ تمت القراءة")
                            st.rerun()
                        except: st.rerun()

    with t3:
        with st.form("up_info"):
            new_em = st.text_input("إيميل ولي الأمر", value=s_row.iloc[6])
            new_ph = st.text_input("رقم الجوال", value=s_row.iloc[7])
            if st.form_submit_button("حفظ البيانات"):
                ws = sh.worksheet("students"); c = ws.find(s_name)
                ws.update(f'G{c.row}:H{c.row}', [[new_em, new_ph]])
                st.success("تم التحديث بنجاح")
