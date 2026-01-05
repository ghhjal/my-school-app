import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import urllib.parse
import io
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إعدادات الصفحة والاتصال
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# ==========================================
# 2. التصميم (CSS) - النسخة الأصلية الكاملة
# ==========================================
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 45px 20px; border-radius: 0 0 40px 40px;
        color: white; text-align: center; margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; 
        justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stButton>button {
        background: #2563eb !important; color: white !important;
        border-radius: 15px !important; font-weight: bold !important;
        height: 3.5em !important; width: 100% !important;
    }
    .btn-auto { background-color: #dc2626 !important; border:none; color:white !important; }
    .btn-wa { background-color: #16a34a !important; border:none; color:white !important; }
    
    .ann-card {
        padding: 15px; border-radius: 10px; margin-bottom: 5px;
        border-right: 5px solid #4F46E5; background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام متابعة الطلاب والتواصل مع أولياء الأمور</p>
    </div>
""", unsafe_allow_html=True)

# دالة مساعدة لتنسيق الرسائل
def get_formatted_msg(name, b_type, b_note, b_date, prefix=""):
    return (
        f"{prefix}تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {name}\n"
        f"----------------------------------------\n"
        f"🏷️ نوع السلوك: {b_type}\n"
        f"📝 الملاحظة: {b_note}\n"
        f"📅 التاريخ: {b_date}\n"
        f"----------------------------------------\n"
        f"🏛️ منصة الأستاذ زياد الذكية"
    )

# دالة الإيميل المحترفة
def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date):
    try:
        email_set = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = email_set["sender_email"]; msg['To'] = to_email
        msg['Subject'] = f"🔔 إشعار سلوكي: {student_name}"
        body = get_formatted_msg(student_name, b_type, b_note, b_date)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_set["sender_email"], email_set["sender_password"])
            server.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. إدارة الجلسة والدخول
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول للمنصة 🚀"):
                df = fetch_safe("students")
                if not df.empty and sid:
                    if sid in df.iloc[:, 0].astype(str).str.strip().values:
                        st.session_state.role = "student"; st.session_state.sid = sid
                        st.balloons(); time.sleep(0.5); st.rerun()
                    else: st.error("عذراً، الرقم غير مسجل")
    with tab2:
        with st.form("te_login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u]
                    if not row.empty and hashlib.sha256(str.encode(p)).hexdigest() == row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("بيانات خاطئة")
    st.stop()

# ==========================================
# 4. واجهة المعلم (كاملة وبدون نواقص)
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs(["👥 إدارة الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1. إدارة الطلاب ---
    with tabs[0]:
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس ملف طالب جديد")
            with st.form("add_student_full", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("🔢 الرقم الأكاديمي")
                nname = c2.text_input("👤 الاسم الثلاثي")
                nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                c4, c5, c6 = st.columns(3)
                nyear = c4.text_input("🗓️ العام الدراسي", value="1447هـ")
                nstage = c5.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
                c7, c8 = st.columns(2)
                nmail = c7.text_input("📧 البريد الإلكتروني")
                nphone = c8.text_input("📱 جوال ولي الأمر (بدون 966)")
                if st.form_submit_button("✅ إضافة الطالب"):
                    if nid and nname:
                        cp = nphone.strip()
                        if cp and not cp.startswith("966"): cp = "966" + cp.lstrip("0")
                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"]
                        sh.worksheet("students").append_row(row)
                        st.success("تمت الإضافة بنجاح"); time.sleep(1); st.rerun()
        st.markdown("---")
        st.markdown("#### 📋 سجل الطلاب الحالي")
        st.dataframe(df_st, use_container_width=True)
        with st.expander("🗑️ منطقة الحذف النهائي"):
            if not df_st.empty:
                del_name = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 حذف نهائي"):
                    for s_ws in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s_ws); cell = ws.find(del_name)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.success("تم الحذف"); time.sleep(1); st.rerun()

    # --- 2. الدرجات (كاملة بالمزايا الذكية) ---
    with tabs[1]:
        st.markdown("### 📝 رصد الدرجات والتقييم")
        df_st = fetch_safe("students")
        df_grades = fetch_safe("grades")
        if not df_st.empty:
            with st.container(border=True):
                with st.form("grades_entry_smart"):
                    c_sel, c_info = st.columns([2, 1])
                    sel_student = c_sel.selectbox("👤 اختر الطالب:", options=df_st.iloc[:, 1].tolist())
                    st_id = df_st[df_st.iloc[:, 1] == sel_student].iloc[0, 0]
                    c_info.text_input("🔢 الرقم الأكاديمي", value=st_id, disabled=True)

                    is_update = False
                    if not df_grades.empty and sel_student in df_grades.iloc[:, 0].values:
                        old_total = df_grades[df_grades.iloc[:, 0] == sel_student].iloc[0, 3]
                        st.warning(f"⚠️ الطالب مرصود له سابقاً (المجموع: {old_total})")
                        is_update = True
                    else: st.info("✨ هذا الطالب يتم رصد درجته لأول مرة.")

                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("📝 المهام والمشاركات (P1)", 0.0, 100.0, step=0.5)
                    p2 = c2.number_input("📄 اختبار الفترة (P2)", 0.0, 100.0, step=0.5)
                    total_score = p1 + p2
                    status = "✅ ناجح" if total_score >= 50 else "❌ يحتاج متابعة"
                    c3.metric("∑ المجموع النهائي", f"{total_score}", delta=status)
                    note = st.text_input("💬 ملاحظة (اختياري)")
                    
                    if st.form_submit_button("🔄 تحديث الدرجة" if is_update else "💾 حفظ الدرجة"):
                        ws_g = sh.worksheet("grades")
                        data_row = [sel_student, p1, p2, total_score, str(datetime.date.today()), note]
                        cell = ws_g.find(sel_student)
                        if cell: ws_g.update(range_name=f"B{cell.row}:F{cell.row}", values=[data_row[1:]])
                        else: ws_g.append_row(data_row)
                        st.success("تم الحفظ"); time.sleep(1); st.rerun()
        st.dataframe(df_grades, use_container_width=True)

    # --- 3. البحث ---
    with tabs[2]:
        st.markdown("### 🔍 البحث الشامل")
        q = st.text_input("ابحث بالاسم أو الرقم:")
        if q:
            df_st = fetch_safe("students")
            res = df_st[df_st.iloc[:, 0].astype(str).str.contains(q) | df_st.iloc[:, 1].str.contains(q)]
            for _, row in res.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.markdown(f"**👤 الاسم:** {row[1]} | **🔢 الرقم:** {row[0]}")
                    c2.markdown(f"**🏫 الصف:** {row[2]} | **📚 المادة:** {row[5]}")
                    st.markdown(f'''<div style="display:flex; gap:10px; margin-top:10px;">
                        <a href="https://wa.me/{row[7]}" target="_blank" style="background:#25D366; color:white; padding:8px 20px; border-radius:8px; text-decoration:none;">واتساب</a>
                        <a href="tel:{row[7]}" style="background:#1e40af; color:white; padding:8px 20px; border-radius:8px; text-decoration:none;">اتصال</a>
                    </div>''', unsafe_allow_html=True)

    # --- 4. السلوك (بكامل الأزرار والجدول) ---
    with tabs[3]:
        st.markdown("### 🎭 رصد السلوك والتواصل")
        df_st = fetch_safe("students")
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + df_st.iloc[:, 1].tolist() if not df_st.empty else [])
        if b_name:
            st_row = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("نص الملاحظة")
                
                col1, col2 = st.columns(2)
                if col1.button("💾 حفظ فقط"):
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    ws_st = sh.worksheet("students"); cell = ws_st.find(b_name)
                    if cell:
                        p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                        curr = int(ws_st.cell(cell.row, 9).value or 0)
                        ws_st.update_cell(cell.row, 9, curr + p_map.get(b_type, 0))
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()

                msg = get_formatted_msg(b_name, b_type, b_note, b_date)
                if col1.button("📧 إيميل يدوي"):
                    st.markdown(f'<script>window.open("mailto:{st_row[6]}?subject=سلوك&body={urllib.parse.quote(msg)}", "_self");</script>', unsafe_allow_html=True)
                if col2.button("⚡ إشعار تلقائي", help="إرسال إيميل آلي بنقرة واحدة"):
                    if send_auto_email_silent(st_row[6], b_name, b_type, b_note, b_date): st.success("تم الإرسال")
                if col2.button("💬 رصد وواتساب"):
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    url = f"https://api.whatsapp.com/send?phone={st_row[7]}&text={urllib.parse.quote(msg)}"
                    st.markdown(f'<script>window.open("{url}", "_blank");</script>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(f"**سجل ملاحظات الطالب: {b_name}**")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                s_notes = df_b[df_b.iloc[:, 0] == b_name].iloc[::-1]
                for i, row in s_notes.iterrows():
                    with st.container(border=True):
                        st.info(f"{row[1]} | {row[2]} | {row[3]}")
                        if st.button("حذف", key=f"del_b_{i}"):
                            c = sh.worksheet("behavior").find(row[3]); sh.worksheet("behavior").delete_rows(c.row); st.rerun()

    # --- 5. الاختبارات (بكامل ميزة المجموعات) ---
    with tabs[4]:
        st.markdown("### 📢 التنبيهات والاختبارات")
        with st.form("exam_add"):
            c1, c2 = st.columns([1,2])
            cls = c1.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            ttl = c2.text_input("العنوان")
            dt, lnk = st.columns(2)
            edate = dt.date_input("التاريخ")
            elink = lnk.text_input("الرابط")
            if st.form_submit_button("نشر التنبيه"):
                sh.worksheet("exams").append_row([str(cls), ttl, str(edate), elink])
                st.success("تم النشر"); time.sleep(1); st.rerun()
        
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iloc[::-1].iterrows():
                with st.container(border=True):
                    c_main, c_act = st.columns([3, 1])
                    c_main.markdown(f"**{row[0]}** | 📅 {row[2]} | {row[1]}")
                    wa_msg = f"📢 تنبيه للصف {row[0]}\nالعنوان: {row[1]}\nالتاريخ: {row[2]}"
                    c_act.markdown(f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}" target="_blank" style="background:#25D366; color:white; padding:8px; border-radius:5px; text-decoration:none;">📤 مجموعة</a>', unsafe_allow_html=True)
                    if c_act.button("🗑️", key=f"dx_{i}"):
                        sh.worksheet("exams").delete_rows(sh.worksheet("exams").find(row[1]).row); st.rerun()

    # --- 6. الإعدادات (كاملة) ---
    with tabs[5]:
        st.markdown("### ⚙️ الإعدادات")
        with st.expander("🔐 بيانات الدخول"):
            with st.form("upd_pass"):
                nu, np = st.text_input("مستخدم جديد"), st.text_input("كلمة مرور جديدة", type="password")
                if st.form_submit_button("تحديث"):
                    ws = sh.worksheet("users"); ws.update_cell(2, 1, nu); ws.update_cell(2, 2, hashlib.sha256(np.encode()).hexdigest())
                    st.success("تم التحديث")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("📥 **تحميل قالب Excel**")
            df_t = pd.DataFrame(columns=["الرقم", "الاسم", "الصف", "السنة", "المرحلة", "المادة", "الايميل", "الجوال", "النقاط"])
            buf = io.BytesIO()
            with pd.ExcelWriter(buf) as writer: df_t.to_excel(writer, index=False)
            st.download_button("تحميل القالب", buf.getvalue(), "template.xlsx")
        with c2:
            st.markdown("📤 **رفع بيانات**")
            f = st.file_uploader("ملف Excel", type=["xlsx"])
            if f and st.button("رفع واستبدال"):
                dfn = pd.read_excel(f); ws = sh.worksheet("students"); ws.clear()
                ws.update([dfn.columns.values.tolist()] + dfn.values.tolist()); st.rerun()
        
        if st.button("🔴 تصفير كافة النقاط"):
            ws = sh.worksheet("students"); cells = ws.range(f'I2:I{len(ws.get_all_values())}')
            for c in cells: c.value = '0'
            ws.update_cells(cells); st.success("تم التصفير")

    with tabs[6]:
        if st.button("خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب (كاملة بكافة التبويبات)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str).str.strip() == str(st.session_state.sid)].iloc[0]
    
    st.markdown(f"<h2 style='text-align:center;'>مرحباً {s_row[1]} | نقاطك: {s_row[8]}</h2>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📢 تنبيهات", "📊 درجات", "🎭 سلوك", "🏆 ترتيب"])
    
    with t1:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            my_ex = df_ex[(df_ex.iloc[:, 0] == s_row[2]) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in my_ex.iloc[::-1].iterrows(): st.info(f"📢 {r[1]} | 📅 {r[2]}")
    
    with t2:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_row[1]]
        if not my_g.empty:
            r = my_g.iloc[0]
            st.metric("المجموع النهائي", r[3]); st.write(f"ملاحظة المعلم: {r[5]}")
        else: st.warning("لا توجد درجات")

    with t3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_row[1]]
        for _, r in my_b.iloc[::-1].iterrows(): st.write(f"{r[2]} | {r[1]} | {r[3]}")

    with t4:
        st.write("🏆 الأوائل:")
        df_st['points_int'] = pd.to_numeric(df_st.iloc[:, 8], errors='coerce').fillna(0)
        top = df_st.nlargest(10, 'points_int')
        for i, r in enumerate(top.values): st.write(f"{i+1}. {r[1]} - {r[8]} نقطة")

    if st.button("خروج"): st.session_state.role = None; st.rerun()
