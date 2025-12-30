import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

# --- 1. إعداد الصفحة وتنسيق الألوان للجوال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 5px; padding: 10px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. دالة إرسال الإيميل (محمية ومستقرة) ---
def send_email_notification(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع الكود المكون من 16 حرفاً هنا
        
        body = f"ولي أمر الطالب/ة: {student_name}\nنود إشعاركم برصد ملاحظة سلوكية:\n\n📅 التاريخ: {note_date}\n🏷️ النوع: {note_type}\n📝 الملاحظة: {note_text}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"تحديث سلوكي من الأستاذ زياد المعمري", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except: return False

# --- 3. الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=5)
def get_db_connection():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db_connection()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# --- 4. واجهة الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password", key="main_tpwd")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        s_id = st.text_input("الرقم الأكاديمي", key="main_sid")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(s_id); st.rerun()
    st.stop()

# --- 5. واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 الاختبارات"])
    
    df_st = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            with st.form("add_st"):
                st.subheader("📝 إضافة طالب جديد")
                id_v = st.text_input("الرقم الأكاديمي")
                nm_v = st.text_input("الاسم")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = st.text_input("العام الدراسي", value="1447هـ")
                stg_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([id_v, nm_v, cls_v, yr_v, "إنجليزي", stg_v, "", "", 0])
                    st.success("تم الحفظ"); st.rerun()
        with col2:
            st.subheader("🗑️ حذف طالب نهائياً")
            target = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if st.button("تأكيد الحذف من كافة السجلات"):
                if target:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(target)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.warning(f"تم حذف {target}"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        t1, t2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with t1:
            st.subheader("رصد الدرجات")
            sel = st.selectbox("اختر الطالب للدرجات", [""] + df_st['name'].tolist() if not df_st.empty else [], key="g_sel")
            if sel:
                with st.form("g_form"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("تحديث الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try: c = ws_g.find(sel); ws_g.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws_g.append_row([sel, f1, f2, pt])
                        st.success("تم التحديث")
            st.subheader("📊 جدول الدرجات")
            st.dataframe(fetch_data("grades"), use_container_width=True, hide_index=True)

        with t2:
            st.subheader("رصد ملاحظة سلوكية")
            sel_b = st.selectbox("اختر الطالب للملاحظة", [""] + df_st['name'].tolist() if not df_st.empty else [], key="b_sel")
            if sel_b:
                with st.form("b_form"):
                    b_date = st.date_input("تاريخ الملاحظة", datetime.now())
                    b_type = st.radio("التقييم", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد وإرسال إشعار"):
                        with st.spinner("جاري الرصد والإرسال..."):
                            pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                            sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                            ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                            old_p = int(ws_s.cell(c.row, 9).value or 0)
                            ws_s.update_cell(c.row, 9, old_p + pts)
                            email = ws_s.cell(c.row, 7).value
                            send_email_notification(email, sel_b, b_type, b_note, b_date)
                            st.success("تم الرصد بنجاح ✅"); time.sleep(1); st.rerun()
            st.subheader("🔍 السجل التاريخي للسلوك")
            st.dataframe(fetch_data("behavior").iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("ex_form"):
            e_cls = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_subj = st.text_input("موضوع الاختبار")
            e_date = st.date_input("الموعد")
            if st.form_submit_button("نشر الموعد"):
                sh.worksheet("exams").append_row([e_cls, e_subj, str(e_date)]); st.rerun()
        st.subheader("📋 المواعيد الحالية")
        df_ex = fetch_data("exams")
        if not df_ex.empty:
            for i, r in df_ex.iterrows():
                c1, c2 = st.columns([5, 1])
                c1.warning(f"📍 {r.iloc[0]} | 📝 {r.iloc[1]} | 📅 {r.iloc[2]}")
                if c2.button("حذف", key=f"ex_{i}"):
                    sh.worksheet("exams").delete_rows(i+2); st.rerun()

# --- 6. واجهة الطالب ---
if st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align:center; color:#1E88E5;'>أهلاً بك: {s_name}</h1>", unsafe_allow_html=True)
    st.info(f"📅 العام الدراسي: {s_row.iloc[3]} | 🏅 المرحلة: {s_row.iloc[5]} | ⭐ نقاطك: {s_row.iloc[8]}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📅 الاختبارات", "⚙️ بياناتي"])
    
    with tab1:
        dg = fetch_data("grades")
        my_g = dg[dg.iloc[:, 0] == s_name]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1", my_g.iloc[0, 1])
            c2.metric("فترة 2", my_g.iloc[0, 2])
            c3.metric("مشاركة", my_g.iloc[0, 3])

    with tab2:
        db = fetch_data("behavior")
        if not db.empty:
            db['row_idx'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:, 0] == s_name].iloc[::-1]
            for _, r in my_b.iterrows():
                rid = int(r['row_idx'])
                is_read = "✅" in str(r.iloc[4]) or rid in st.session_state.confirmed
                bg = "#D4EDDA" if is_read else "#FFF9C4"
                st.markdown(f"<div style='background:{bg}; padding:15px; border-radius:10px; margin-bottom:10px; color:black; border: 1px solid #ddd;'><b>{r.iloc[2]}</b> - التاريخ: {r.iloc[1]}<br>{r.iloc[3]}</div>", unsafe_allow_html=True)
                if not is_read:
                    if st.button(f"🙏 شكراً أستاذ زياد (تأكيد القراءة)", key=f"sbtn_{rid}"):
                        st.session_state.confirmed.add(rid)
                        try: sh.worksheet("behavior").update_cell(rid, 5, "✅ تمت القراءة")
                        except: pass
                        st.rerun()

    with tab3:
        de = fetch_data("exams")
        if not de.empty:
            st.table(de[(de.iloc[:, 0] == s_row.iloc[2]) | (de.iloc[:, 0] == "الكل")])

    with tab4:
        st.subheader("تحديث بيانات ولي الأمر")
        with st.form("up_st"):
            n_em = st.text_input("الإيميل", value=s_row.iloc[6])
            n_ph = st.text_input("الجوال", value=s_row.iloc[7])
            if st.form_submit_button("حفظ التغييرات"):
                ws = sh.worksheet("students"); c = ws.find(s_name)
                ws.update(f'G{c.row}:H{c.row}', [[n_em, n_ph]])
                st.success("تم التحديث"); st.rerun()
