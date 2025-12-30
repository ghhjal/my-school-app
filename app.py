import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# إعداد الصفحة وتنسيق الجوال
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- دالة الإرسال المستقرة ---
def send_email_safe(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع الرقم السري للتطبيقات هنا
        
        body = f"ولي أمر الطالب: {student_name}\nنحيطكم علماً برصد ملاحظة:\nالتاريخ: {note_date}\nالنوع: {note_type}\nالملاحظة: {note_text}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"إشعار من الأستاذ زياد المعمري", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
    except: pass # منع البرنامج من الانهيار إذا فشل الإنترنت

# --- الربط بقاعدة البيانات ---
@st.cache_resource(ttl=10)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch(sheet_name):
    try:
        return pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# --- واجهة الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔐 المعلم")
        if st.text_input("كلمة المرور", type="password") == "1234":
            if st.button("دخول المعلم"): st.session_state.role = "teacher"; st.rerun()
    with col2:
        st.subheader("👨‍🎓 الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df = fetch("students")
            if not df.empty and str(sid) in df.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    choice = st.sidebar.radio("القائمة", ["إدارة الطلاب", "الدرجات والسلوك", "الاختبارات"])
    df_st = fetch("students")

    if choice == "إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            id_v = c1.text_input("الرقم الأكاديمي")
            nm_v = c2.text_input("الاسم")
            cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            stg_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([id_v, nm_v, cls_v, "1447هـ", "إنجليزي", stg_v, "", "", 0])
                st.success("تم الحفظ"); st.rerun()
        
        st.divider()
        st.subheader("🗑️ حذف طالب")
        target = st.selectbox("اختر الطالب للحذف", [""] + df_st['name'].tolist() if not df_st.empty else [])
        if st.button("حذف نهائي من كل الجداول"):
            for s in ["students", "grades", "behavior"]:
                try: ws = sh.worksheet(s); cell = ws.find(target); ws.delete_rows(cell.row)
                except: pass
            st.rerun()

    elif choice == "الدرجات والسلوك":
        t1, t2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with t1:
            sel = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [], key="g_sel")
            if sel:
                with st.form("gr_form"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws = sh.worksheet("grades")
                        try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws.append_row([sel, f1, f2, pt])
                        st.success("تم التحديث")
            st.subheader("📊 جدول الدرجات الحالي")
            st.dataframe(fetch("grades"), use_container_width=True, hide_index=True)

        with t2:
            sel_b = st.selectbox("الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [], key="b_sel")
            if sel_b:
                with st.form("bh_form"):
                    b_date = st.date_input("تاريخ الملاحظة", datetime.now())
                    ty = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    nt = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد وإرسال إشعار"):
                        val = 10 if "⭐" in ty else 5 if "✅" in ty else -5 if "⚠️" in ty else -10
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), ty, nt, "🕒 لم تقرأ"])
                        # تحديث النقاط
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old + val)
                        # إرسال الإيميل (آمن)
                        email = ws_s.cell(c.row, 7).value
                        send_email_safe(email, sel_b, ty, nt, b_date)
                        st.success("تم الرصد والإرسال بنجاح")
            
            st.subheader("🔍 السجل التاريخي")
            df_b = fetch("behavior")
            if not df_b.empty:
                st.dataframe(df_b[df_b.iloc[:,0]==sel_b].iloc[::-1] if sel_b else df_b.iloc[::-1], use_container_width=True)

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_s = fetch("students")
    s_data = df_s[df_s.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]

    st.title(f"👋 أهلاً {s_name}")
    
    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "🎭 سلوكي", "⚙️ تحديث بياناتي"])
    
    with tab1:
        dg = fetch("grades")
        my_g = dg[dg.iloc[:,0] == s_name]
        if not my_g.empty:
            st.info(f"فترة 1: {my_g.iloc[0,1]} | فترة 2: {my_g.iloc[0,2]} | مشاركة: {my_g.iloc[0,3]}")

    with tab2:
        db = fetch("behavior")
        if not db.empty:
            db['row_num'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:,0] == s_name].iloc[::-1]
            for _, r in my_b.iterrows():
                rid = int(r['row_num'])
                is_read = "✅" in str(r.iloc[4]) or rid in st.session_state.confirmed
                bg = "#e1f5fe" if is_read else "#fff9c4"
                
                st.markdown(f"<div style='background:{bg}; padding:15px; border-radius:10px; margin-bottom:10px; color:black; border:1px solid #ddd;'><b>{r.iloc[2]}</b> - {r.iloc[1]}<br>{r.iloc[3]}</div>", unsafe_allow_html=True)
                
                if not is_read:
                    if st.button(f"🙏 شكراً أستاذ زياد", key=f"sh_{rid}"):
                        st.session_state.confirmed.add(rid)
                        try:
                            sh.worksheet("behavior").update_cell(rid, 5, "✅ تمت القراءة")
                            st.rerun()
                        except: st.rerun()

    with tab3:
        with st.form("up"):
            em = st.text_input("إيميل ولي الأمر", value=s_data.iloc[6])
            ph = st.text_input("الجوال", value=s_data.iloc[7])
            if st.form_submit_button("حفظ"):
                ws = sh.worksheet("students"); c = ws.find(s_name)
                ws.update(f'G{c.row}:H{c.row}', [[em, ph]])
                st.success("تم التحديث")
