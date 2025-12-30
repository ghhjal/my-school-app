import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- دالة إرسال الإيميل (محدثة لضمان الوصول) ---
def send_notification(to_email, student_name, note_type, note_text):
    if not to_email or "@" not in to_email: return False
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 465
        sender = "ziyadalamri30@gmail.com" 
        password = "your_app_password" # تأكد من وضع كلمة مرور التطبيقات هنا

        content = f"ولي أمر الطالب: {student_name}\nتم رصد ملاحظة جديدة:\nالنوع: {note_type}\nالملاحظة: {note_text}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}"
        message = MIMEText(content, 'plain', 'utf-8')
        message['Subject'] = Header(f"تحديث سلوكي: {student_name}", 'utf-8')
        message['From'] = sender
        message['To'] = to_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, message.as_string())
        return True
    except: return False

# الربط بقاعدة البيانات
@st.cache_resource(ttl=30)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            return pd.DataFrame(ws.get_all_records())
        return pd.DataFrame()
    except: return pd.DataFrame()

# الحالة العامة للجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# --- واجهة الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if p == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df = fetch_data("students")
            if not df.empty and str(sid) in df.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    m = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 الاختبارات"])
    df_st = fetch_data("students")

    if m == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            id_v = c1.text_input("الرقم الأكاديمي")
            name_v = c2.text_input("الاسم")
            cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            yr_v = st.text_input("العام الدراسي", value="1447هـ")
            em_v = st.text_input("إيميل ولي الأمر")
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, "إنجليزي", "ابتدائي", em_v, "", 0])
                st.cache_data.clear(); st.success("تم الحفظ"); st.rerun()

    elif m == "📊 الدرجات والسلوك":
        t1, t2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with t1:
            sel = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel:
                with st.form("gr"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("حفظ"):
                        ws = sh.worksheet("grades")
                        try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws.append_row([sel, f1, f2, pt])
                        st.success("تم الحفظ")
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with t2:
            st.subheader("رصد السلوك والإرسال")
            sel_b = st.selectbox("الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [], key="sb")
            if sel_b:
                with st.form("bh"):
                    ty = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    nt = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد وإرسال إيميل"):
                        val = 10 if "⭐" in ty else 5 if "✅" in ty else -5 if "⚠️" in ty else -10
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), ty, nt, "🕒 لم تقرأ"])
                        # تحديث النقاط
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old + val)
                        # إرسال الإيميل فوراً
                        email = ws_s.cell(c.row, 7).value
                        if email: send_notification(email, sel_b, ty, nt)
                        st.cache_data.clear(); st.success("تم الرصد والإرسال بنجاح ✅"); st.rerun()

    elif m == "📢 الاختبارات":
        with st.form("ex"):
            c_v = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_v = st.text_input("الموضوع"); d_v = st.date_input("الموعد")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([c_v, t_v, str(d_v)]); st.rerun()
        df_ex = fetch_data("exams")
        if not df_ex.empty:
            for i, r in df_ex.iterrows():
                c1, c2 = st.columns([5,1])
                c1.warning(f"{r.iloc[0]} | {r.iloc[1]} | {r.iloc[2]}")
                if c2.button("حذف", key=f"d_{i}"): sh.worksheet("exams").delete_rows(i+2); st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]
    
    st.markdown(f"<h2 style='color:#1E88E5; text-align:center;'>أهلاً بك: {s_name}</h2>", unsafe_allow_html=True)
    pts = int(s_row.iloc[8] or 0)
    st.markdown(f"<div style='text-align:center; background:#f0f2f6; padding:10px; border-radius:10px;'><b>رصيدك: {pts} نقطة | اللقب: {'🏆 بطل' if pts>=100 else '🥇 ذهبي' if pts>=50 else '🥈 فضي'}</b></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📢 المواعيد"])
    
    with tab1:
        dg = fetch_data("grades")
        my_g = dg[dg.iloc[:, 0] == s_name] if not dg.empty else pd.DataFrame()
        if not my_g.empty:
            st.info(f"فترة 1: {my_g.iloc[0,1]} | فترة 2: {my_g.iloc[0,2]} | مشاركة: {my_g.iloc[0,3]}")

    with tab2:
        st.subheader("سجل السلوك")
        db = fetch_data("behavior")
        if not db.empty:
            db['idx'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:, 0] == s_name].iloc[::-1]
            for _, r in my_b.iterrows():
                r_id = int(r['idx'])
                is_read = "✅" in str(r.iloc[4]) or r_id in st.session_state.confirmed
                # ألوان واضحة للجوال
                txt_color = "#000000"
                bg = "#C8E6C9" if is_read else "#FFF9C4" # أخضر فاتح للمقروء، أصفر واضح للتنبيه
                
                st.markdown(f"""
                <div style='background-color:{bg}; color:{txt_color}; padding:15px; border-radius:8px; margin-bottom:10px; border: 2px solid #ccc;'>
                    <b>{r.iloc[2]}</b> ({r.iloc[1]})<br>الملاحظة: {r.iloc[3]}
                </div>
                """, unsafe_allow_html=True)
                
                if not is_read:
                    @st.fragment
                    def show_btn(rid=r_id):
                        if st.button(f"🙏 شكراً أستاذي (تأكيد القراءة)", key=f"btn_{rid}"):
                            st.session_state.confirmed.add(rid)
                            try:
                                time.sleep(0.2) # تأخير بسيط لمنع تصادم جوجل
                                sh.worksheet("behavior").update_cell(rid, 5, "✅ تمت القراءة")
                                st.rerun()
                            except: pass
                    show_btn()

    with tab3:
        de = fetch_data("exams")
        if not de.empty:
            st.table(de[(de.iloc[:, 0] == s_row.iloc[2]) | (de.iloc[:, 0] == "الكل")])
