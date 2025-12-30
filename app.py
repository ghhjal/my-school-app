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

# --- دالة إرسال الإيميل (الإعدادات النهائية) ---
def send_email_notification(to_email, student_name, note_type, note_text):
    if not to_email or "@" not in str(to_email): return False
    try:
        smtp_server, smtp_port = "smtp.gmail.com", 465
        sender = "ziyadalamri30@gmail.com" 
        password = "your_app_password" # ضع هنا كلمة مرور التطبيقات الـ 16 حرفاً

        msg_body = f"ولي أمر الطالب/ة: {student_name}\nتم رصد ملاحظة سلوكية:\nالنوع: {note_type}\nالملاحظة: {note_text}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}"
        message = MIMEText(msg_body, 'plain', 'utf-8')
        message['Subject'] = Header(f"إشعار سلوكي: {student_name}", 'utf-8')
        message['From'] = sender
        message['To'] = to_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, message.as_string())
        return True
    except: return False

# الاتصال بقاعدة البيانات
@st.cache_resource(ttl=20)
def get_db_connection():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db_connection()

def fetch_data(sheet_name):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            return pd.DataFrame(ws.get_all_records())
        return pd.DataFrame()
    except: return pd.DataFrame()

# متغيرات الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed_notes' not in st.session_state: st.session_state.confirmed_notes = set()

# --- نظام الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="p1")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي", key="s1")
        if st.button("دخول الطالب"):
            df = fetch_data("students")
            if not df.empty and str(sid) in df.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 الاختبارات"])
    df_st = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_form"):
                id_v = st.text_input("الرقم الأكاديمي")
                name_v = st.text_input("اسم الطالب")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                yr_v = st.text_input("العام الدراسي", value="1447هـ")
                if st.form_submit_button("إضافة الطالب"):
                    # الأعمدة: id, name, class, year, sem, stage, email, phone, points
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, "إنجليزي", lev_v, "", "", 0])
                    st.success("تمت الإضافة"); st.rerun()
        
        with col2:
            st.subheader("🗑️ منطقة الحذف")
            to_del = st.selectbox("اختر طالب لحذفه نهائياً", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if st.button("حذف الطالب من جميع السجلات"):
                if to_del:
                    for s_name in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s_name); cell = ws.find(to_del); ws.delete_rows(cell.row)
                        except: pass
                    st.warning(f"تم حذف {to_del} بالكامل"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        t1, t2 = st.tabs(["📝 رصد الدرجات", "🎭 سجل السلوك"])
        with t1:
            sel = st.selectbox("اختر الطالب للدرجات", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel:
                with st.form("g_f"):
                    f1 = st.number_input("فترة 1", 0, 100); f2 = st.number_input("فترة 2", 0, 100); pt = st.number_input("المشاركة", 0, 100)
                    if st.form_submit_button("تحديث الدرجات"):
                        ws = sh.worksheet("grades")
                        try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws.append_row([sel, f1, f2, pt])
                        st.success("تم الحفظ")
        
        with t2:
            st.subheader("رصد ملاحظة جديدة")
            sel_b = st.selectbox("الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [], key="sb_key")
            if sel_b:
                with st.form("b_f"):
                    ty = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    nt = st.text_input("الملاحظة")
                    if st.form_submit_button("إرسال ورصد"):
                        pts = 10 if "⭐" in ty else 5 if "✅" in ty else -5 if "⚠️" in ty else -10
                        # 1. إضافة للملاحظات مع التاريخ
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), ty, nt, "🕒 لم تقرأ"])
                        # 2. تحديث النقاط
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old_p = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old_p + pts)
                        # 3. إرسال الإيميل
                        email_addr = ws_s.cell(c.row, 7).value
                        if email_addr: send_email_notification(email_addr, sel_b, ty, nt)
                        st.success("تم الرصد وإرسال التنبيه ✅"); st.rerun()
            
            st.divider()
            st.subheader("🔍 السجل التاريخي للسلوك")
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                show_bh = df_bh[df_bh.iloc[:, 0] == sel_b] if sel_b else df_bh
                st.dataframe(show_bh.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 الاختبارات":
        with st.form("ex_f"):
            c_v = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_v = st.text_input("الموضوع"); d_v = st.date_input("الموعد")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([c_v, t_v, str(d_v)]); st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align:center; color:#2c3e50;'>🌟 أهلاً بك: {s_name}</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📢 الاختبارات", "⚙️ بياناتي"])
    
    with tab1:
        dg = fetch_data("grades")
        my_g = dg[dg.iloc[:, 0] == s_name] if not dg.empty else pd.DataFrame()
        if not my_g.empty:
            st.info(f"الفترة الأولى: {my_g.iloc[0,1]} | الفترة الثانية: {my_g.iloc[0,2]} | المشاركة: {my_g.iloc[0,3]}")
    
    with tab2:
        st.subheader("سجل الملاحظات السلوكية")
        db = fetch_data("behavior")
        if not db.empty:
            db['row_idx'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:, 0] == s_name].iloc[::-1]
            for _, r in my_b.iterrows():
                rid = int(r['row_idx'])
                is_read = "✅" in str(r.iloc[4]) or rid in st.session_state.confirmed_notes
                
                # ألوان متباينة جداً للجوال
                bg = "#D4EDDA" if is_read else "#FFF3CD"
                border = "#28A745" if is_read else "#FFC107"
                
                st.markdown(f"""
                <div style='background:{bg}; border-left:8px solid {border}; padding:15px; border-radius:10px; margin-bottom:10px; color:black;'>
                    <span style='font-size:1.1em;'><b>{r.iloc[2]}</b></span> | <small>{r.iloc[1]}</small><br>
                    الملاحظة: {r.iloc[3]}
                </div>
                """, unsafe_allow_html=True)
                
                if not is_read:
                    if st.button(f"🙏 شكراً أستاذي زياد (تأكيد القراءة)", key=f"btn_{rid}"):
                        st.session_state.confirmed_notes.add(rid)
                        try:
                            # تحديث صامت بدون رسائل خطأ حمراء
                            sh.worksheet("behavior").update_cell(rid, 5, "✅ تمت القراءة")
                            st.rerun()
                        except: pass # إذا فشل الخادم يبقى الزر مختفياً محلياً

    with tab3:
        de = fetch_data("exams")
        if not de.empty:
            st.table(de[(de.iloc[:, 0] == s_row.iloc[2]) | (de.iloc[:, 0] == "الكل")])

    with tab4:
        st.subheader("تحديث بيانات التواصل")
        with st.form("info_f"):
            new_em = st.text_input("إيميل ولي الأمر", value=s_row.iloc[6])
            new_ph = st.text_input("رقم الجوال", value=s_row.iloc[7])
            if st.form_submit_button("حفظ البيانات"):
                ws_s = sh.worksheet("students"); c = ws_s.find(s_name)
                ws_s.update(f'G{c.row}:H{c.row}', [[new_em, new_ph]])
                st.success("تم تحديث بياناتك بنجاح")
