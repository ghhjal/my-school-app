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
        sender_email = "ziyadalamri30@gmail.com" 
        password = "your_app_password" # ضع كلمة مرور التطبيقات هنا

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

# الربط بقاعدة البيانات مع ذاكرة مؤقتة ذكية
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

# تهيئة الحالة
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed_rows' not in st.session_state: st.session_state.confirmed_rows = set()

# --- دالة التحديث السريع لزر شكراً (تمنع الخروج) ---
@st.fragment
def behavior_row_fragment(r_id, type_str, date_str, note_str, is_already_read):
    is_confirmed = r_id in st.session_state.confirmed_rows or is_already_read
    bg_color = "#E8F5E9" if is_confirmed else "#FFF3E0"
    
    st.markdown(f"""
    <div style='background-color:{bg_color}; padding:12px; border-radius:8px; margin-bottom:8px; border-right: 5px solid {"#2E7D32" if is_confirmed else "#EF6C00"}'>
        <b>{type_str}</b> | 📅 {date_str}<br>
        الملاحظة: {note_str}
    </div>
    """, unsafe_allow_html=True)
    
    if not is_confirmed:
        if st.button(f"🙏 شكراً أستاذي زياد", key=f"btn_v_{r_id}"):
            st.session_state.confirmed_rows.add(r_id)
            try:
                sh.worksheet("behavior").update_cell(r_id, 5, "✅ تمت القراءة")
                st.rerun() # تحديث الصفحة فقط عند الضغط لضمان اختفائه
            except:
                st.error("الخادم مشغول، سيتم التحديث لاحقاً")

# --- نظام الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="t_login")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي", key="s_login")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid_input) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_input); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])
    df_st = fetch_data("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📝 إضافة طالب")
            with st.form("add_st"):
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
            to_del = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if st.button("حذف نهائي"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del); ws.delete_rows(cell.row)
                        except: pass
                    st.cache_data.clear(); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with tab1:
            sel = st.selectbox("الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
            if sel:
                with st.form("g_f"):
                    f1 = st.number_input("ف1", 0, 100); f2 = st.number_input("ف2", 0, 100); pt = st.number_input("مشاركة", 0, 100)
                    if st.form_submit_button("حفظ"):
                        ws = sh.worksheet("grades")
                        try: c = ws.find(sel); ws.update(f'B{c.row}:D{c.row}', [[f1, f2, pt]])
                        except: ws.append_row([sel, f1, f2, pt])
                        st.success("تم التحديث")
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with tab2:
            st.subheader("🎭 رصد السلوك")
            sel_b = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [], key="beh_sel")
            if sel_b:
                with st.form("b_form"):
                    dt = st.date_input("التاريخ", datetime.now())
                    ty = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    nt = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد وإرسال"):
                        val = 10 if "⭐" in ty else 5 if "✅" in ty else -5 if "⚠️" in ty else -10
                        sh.worksheet("behavior").append_row([sel_b, str(dt), ty, nt, "🕒 لم تقرأ"])
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old = int(ws_s.cell(c.row, 9).value or 0)
                        ws_s.update_cell(c.row, 9, old + val)
                        # إرسال إيميل
                        em = ws_s.cell(c.row, 7).value
                        if em: send_email(em, sel_b, ty, nt)
                        st.cache_data.clear(); st.success("تم الرصد"); st.rerun()
            st.divider()
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                st.dataframe(df_bh[df_bh.iloc[:, 0] == sel_b].iloc[::-1] if sel_b else df_bh.iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 إعلانات الاختبارات":
        with st.form("ex"):
            c_v = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_v = st.text_input("الموضوع"); d_v = st.date_input("الموعد")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([c_v, t_v, str(d_v)])
                st.rerun()
        de = fetch_data("exams")
        if not de.empty:
            for i, row in de.iterrows():
                col1, col2 = st.columns([5, 1])
                col1.info(f"{row.iloc[0]} | {row.iloc[1]} | {row.iloc[2]}")
                if col2.button("حذف", key=f"d_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]
    
    st.title(f"🌟 أهلاً بك: {s_name}")
    pts = int(s_data.iloc[8] or 0)
    medal = "🏆 بطل التحدي" if pts >= 100 else "🥇 وسام ذهبي" if pts >= 50 else "🥈 وسام فضي"
    c1, c2 = st.columns(2); c1.metric("رصيد نقاطك ⭐", pts); c2.metric("لقبك الحالي 🏆", medal)

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📢 الاختبارات"])
    
    with t1:
        dg = fetch_data("grades")
        my_g = dg[dg.iloc[:, 0] == s_name] if not dg.empty else pd.DataFrame()
        if not my_g.empty:
            ca, cb, cc = st.columns(3)
            ca.metric("فترة 1", my_g.iloc[0, 1]); cb.metric("فترة 2", my_g.iloc[0, 2]); cc.metric("مشاركة", my_g.iloc[0, 3])
    
    with t2:
        st.subheader("🎭 سجل الملاحظات")
        db = fetch_data("behavior")
        if not db.empty:
            db['r_idx'] = range(2, len(db) + 2)
            my_b = db[db.iloc[:, 0] == s_name].iloc[::-1]
            for _, row in my_b.iterrows():
                behavior_row_fragment(
                    int(row['r_idx']), 
                    str(row.iloc[2]), 
                    str(row.iloc[1]), 
                    str(row.iloc[3]), 
                    "✅" in str(row.iloc[4])
                )

    with t3:
        de = fetch_data("exams")
        if not de.empty:
            st.table(de[(de.iloc[:, 0] == s_data.iloc[2]) | (de.iloc[:, 0] == "الكل")])
