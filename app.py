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

# --- دالة إرسال الإيميل ---
def send_email(to_email, student_name, note_type, note_text):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 465
        sender_email = "ziyadalamri30@gmail.com" # إيميلك المسجل في الصور
        password = "your_app_password" # يجب وضع كلمة مرور التطبيقات هنا

        msg_content = f"تحية طيبة ولي أمر الطالب: {student_name}\nنود إحاطتكم برصد ملاحظة سلوكية جديدة:\nالنوع: {note_type}\nالملاحظة: {note_text}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}"
        message = MIMEText(msg_content, 'plain', 'utf-8')
        message['Subject'] = Header(f"إشعار سلوكي: {student_name}", 'utf-8')
        message['From'] = sender_email
        message['To'] = to_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())
        return True
    except:
        return False

# الربط بقاعدة البيانات
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
        if sh:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame()
        return pd.DataFrame()
    except: return pd.DataFrame()

if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed_rows' not in st.session_state: st.session_state.confirmed_rows = set()

# --- نظام الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid_input) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_input); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])
    df_st = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📝 إضافة طالب")
            with st.form("add_st", clear_on_submit=True):
                c1, c2 = st.columns(2)
                id_v = c1.text_input("الرقم الأكاديمي")
                name_v = c2.text_input("اسم الطالب")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = st.text_input("العام الدراسي", value="1447هـ")
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, "اللغة الإنجليزية", lev_v, "", "", 0])
                    st.cache_data.clear(); st.success("تم الحفظ"); st.rerun()
        
        with col2:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اختر الطالب للحذف", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if st.button("حذف من كافة الجداول"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.cache_data.clear(); st.success("تم الحذف الشامل"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with tab1:
            sel_st = st.selectbox("اختر الطالب للدرجات", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel_st:
                with st.form("g_form"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); part = st.number_input("المشاركة", 0, 100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws = sh.worksheet("grades")
                        try:
                            c = ws.find(sel_st); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, part]])
                        except: ws.append_row([sel_st, f1, f2, part])
                        st.success("تم التحديث")
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with tab2:
            st.subheader("🎭 رصد السلوك")
            sel_st_b = st.selectbox("الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel_st_b:
                with st.form("b_form"):
                    date_v = st.date_input("التاريخ", datetime.now())
                    type_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    note_v = st.text_input("الملاحظة")
                    if st.form_submit_button("حفظ وإرسال إيميل"):
                        pts = 10 if "⭐" in type_v else 5 if "✅" in type_v else -5 if "⚠️" in type_v else -10
                        sh.worksheet("behavior").append_row([sel_st_b, str(date_v), type_v, note_v, "🕒 لم تقرأ"])
                        # تحديث النقاط وإرسال الإيميل
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st_b)
                        old_pts = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_pts + pts)
                        email = ws_st.cell(c.row, 7).value
                        if email: send_email(email, sel_st_b, type_v, note_v)
                        st.cache_data.clear(); st.success("تم الرصد والإرسال ✅"); st.rerun()
            
            st.divider()
            st.subheader("🔍 سجل السلوك التاريخي")
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                filtered_bh = df_bh[df_bh.iloc[:, 0] == sel_st_b] if sel_st_b else df_bh
                st.dataframe(filtered_bh.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 الاختبارات")
        with st.form("ex_form"):
            c_v = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_v = st.text_input("الموضوع"); d_v = st.date_input("الموعد")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([c_v, t_v, str(d_v)])
                st.rerun()
        
        st.divider()
        df_ex = fetch_data("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"📌 {row.iloc[0]} | {row.iloc[1]} | {row.iloc[2]}")
                if col2.button("حذف", key=f"del_ex_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2)
                    st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]
    
    st.title(f"🌟 أهلاً بك: {s_name}")
    pts = int(s_data.iloc[8] or 0)
    medal = "🏆 بطل" if pts >= 100 else "🥇 ذهبي" if pts >= 50 else "🥈 فضي"
    c1, c2 = st.columns(2); c1.metric("النقاط", pts); c2.metric("اللقب", medal)

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📢 المواعيد"])
    with t1:
        dg = fetch_data("grades")
        my_g = dg[dg.iloc[:, 0] == s_name] if not dg.empty else pd.DataFrame()
        if not my_g.empty:
            ca, cb, cc = st.columns(3)
            ca.metric("فترة 1", my_g.iloc[0, 1]); cb.metric("فترة 2", my_g.iloc[0, 2]); cc.metric("مشاركة", my_g.iloc[0, 3])
    
    with t2:
        db = fetch_data("behavior")
        if not db.empty:
            db['idx'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:, 0] == s_name].iloc[::-1]
            for _, row in my_b.iterrows():
                r_id = int(row['idx'])
                is_r = any(x in str(row.iloc[4]) for x in ["✅", "تمت"]) or r_id in st.session_state.confirmed_rows
                bg = "#E8F5E9" if is_r else "#FFF3E0"
                st.markdown(f"<div style='background-color:{bg}; padding:10px; border-radius:5px; margin-bottom:5px;'><b>{row.iloc[2]}</b>: {row.iloc[3]} (تاريخ: {row.iloc[1]})</div>", unsafe_allow_html=True)
                if not is_r:
                    if st.button("🙏 شكراً أستاذ زياد (تأكيد القراءة)", key=f"thx_{r_id}"):
                        st.session_state.confirmed_rows.add(r_id)
                        try:
                            sh.worksheet("behavior").update_cell(r_id, 5, "✅ تمت القراءة")
                            st.cache_data.clear(); st.rerun()
                        except: pass

    with t3:
        de = fetch_data("exams")
        if not de.empty:
            st.table(de[(de.iloc[:, 0] == s_data.iloc[2]) | (de.iloc[:, 0] == "الكل")])
