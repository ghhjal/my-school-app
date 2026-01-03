import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) ---
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 45px 20px;
        border-radius: 0 0 40px 40px;
        color: white;
        text-align: center;
        margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; 
        justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .welcome-card {
        background: rgba(30, 64, 175, 0.05);
        border-right: 5px solid #1e40af;
        padding: 20px;
        border-radius: 12px;
        margin: 25px 0;
        text-align: justify;
        line-height: 1.8;
    }
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 25px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        padding: 30px !important;
    }
    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    
    .contact-section {
        margin-top: 30px;
        text-align: center;
        padding: 20px;
    }
    .contact-icons {
        display: flex;
        justify-content: center;
        gap: 25px;
        margin-top: 15px;
    }
    .contact-icons a {
        text-decoration: none;
        color: #1e40af;
        font-size: 28px;
        transition: 0.3s;
    }
    .contact-icons a:hover {
        color: #3b82f6;
        transform: scale(1.15);
    }
    .footer-text {
        text-align: center;
        opacity: 0.8;
        font-size: 13px;
        margin-top: 30px;
        padding: 15px;
        border-top: 1px solid rgba(128, 128, 128, 0.1);
    }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام متابعة الطلاب والتواصل مع أولياء الأمور</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #1e40af; margin-top: 0; font-weight: 700;">أهلًا بكم في منصة زياد الذكية</h4>
            <p style="color: inherit; font-size: 15px; margin-bottom: 0;">
                مبادرة تعليمية تهدف إلى تسهيل متابعة مستوى الطلاب أكاديمياً وسلوكياً، وتعزيز التواصل السريع والفعّال مع أولياء الأمور.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_form"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية للمتابعة")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df = fetch_safe("students")
                if not df.empty and sid:
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    if sid.strip() in df.iloc[:, 0].values:
                        st.session_state.role = "student"; st.session_state.sid = sid.strip()
                        st.balloons(); time.sleep(1); st.rerun()
                    else: st.error("عذراً، الرقم غير مسجل في النظام")
    with tab2:
        with st.form("te_form"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u.strip()]
                    if not row.empty:
                        hashed = hashlib.sha256(str.encode(p)).hexdigest()
                        if hashed == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"; st.rerun()
                        else: st.error("كلمة المرور غير صحيحة")
                    else: st.error("المستخدم غير موجود")

    st.markdown("""
        <div class="contact-section">
            <p style="font-weight: 700; color: #1e40af; margin-bottom: 10px;">قنوات التواصل المباشرة</p>
            <div class="contact-icons">
                <a href="mailto:info@example.com" title="البريد الإلكتروني"><i class="bi bi-envelope-at-fill"></i></a>
                <a href="https://wa.me/966XXXXXXXXX" target="_blank" title="واتساب"><i class="bi bi-whatsapp"></i></a>
                <a href="https://t.me/YourUser" target="_blank" title="تليجرام"><i class="bi bi-telegram"></i></a>
                <a href="https://www.snapchat.com/add/YourUser" target="_blank" title="سناب شات"><i class="bi bi-snapchat"></i></a>
            </div>
        </div>
        <div class="footer-text">© منصة زياد الذكية – مبادرة تعليمية بإشراف الأستاذ زياد</div>
    """, unsafe_allow_html=True)
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.markdown('<div style="background:linear-gradient(135deg,#1e40af,#3b82f6); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:10px;"><h1>👨‍🏫 لوحة تحكم المعلم</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 إدارة الطلاب", 
        "📈 شاشة الدرجات", 
        "🔍 البحث المطور", 
        "🥇 رصد السلوك", 
        "📢 الاختبارات", 
        "⚙️ الإعدادات", 
        "🚗 خروج"
    ])

    with tab7:
        if st.button("تأكيد تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()

    with tab1:
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس ملف طالب جديد")
            with st.form("add_student_final_form", clear_on_submit=True):
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
                
                if st.form_submit_button("✅ اعتماد وإضافة الطالب", use_container_width=True):
                    if nid and nname and nphone:
                        cp = nphone.strip()
                        if cp.startswith('0'): cp = cp[1:]
                        if not cp.startswith('966'): cp = '966' + cp
                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"]
                        sh.worksheet("students").append_row(row)
                        st.success(f"✅ تم إضافة {nname} بنجاح"); time.sleep(1); st.rerun()

        with st.expander("📋 السجل الحالي للطلاب"):
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("🗑️ منطقة الحذف النهائي الشامل"):
            st.error("⚠️ سيتم حذف كافة بيانات الطالب من جميع الجداول")
            if not df_st.empty:
                del_name = st.selectbox("🎯 اختر الطالب للحذف:", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 تنفيذ الحذف النهائي الآن", use_container_width=True):
                    if del_name:
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s); cell = ws.find(del_name)
                                if cell: ws.delete_rows(cell.row)
                            except: pass
                        st.success("💥 تم المسح بنجاح"); time.sleep(1); st.rerun()

    with tab2:
        st.markdown("### 📝 رصد درجات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            with st.container(border=True):
                with st.form("grades_integrated_form", clear_on_submit=True):
                    student_list = df_st.iloc[:, 1].tolist()
                    selected_student = st.selectbox("👤 اختر الطالب:", options=student_list, index=None, placeholder="ابحث عن اسم الطالب...")
                    c1, c2, c3 = st.columns(3)
                    val_p1 = c1.number_input("⭐ المشاركة (p1)", 0.0, 20.0, step=0.5)
                    val_p2 = c2.number_input("📚 الواجبات (p2)", 0.0, 20.0, step=0.5)
                    val_perf = c3.number_input("📝 اختبارات (perf)", 0.0, 20.0, step=0.5)
                    teacher_note = st.text_input("💬 ملاحظة المعلم")
                    if st.form_submit_button("✅ حفظ الدرجات", use_container_width=True):
                        if selected_student:
                            student_row = df_st[df_st.iloc[:, 1] == selected_student].iloc[0]
                            s_id = student_row[0]
                            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                            sh.worksheet("grades").append_row([s_id, val_p1, val_p2, val_perf, current_date, teacher_note])
                            st.success("✅ تم الرصد"); time.sleep(1); st.rerun()

    with tab3:
        st.markdown("### 🔍 محرك البحث الذكي")
        df_st = fetch_safe("students")
        search_query = st.text_input("🔎 ابحث باسم الطالب أو الرقم:")
        if search_query:
            results = df_st[df_st.iloc[:, 0].astype(str).str.contains(search_query) | df_st.iloc[:, 1].str.contains(search_query)]
            for i in range(len(results)):
                with st.container(border=True):
                    st.markdown(f"**👤 {results.iloc[i, 1]}** | 🔢 {results.iloc[i, 0]}")
                    phone = results.iloc[i, 7]
                    st.markdown(f'''
                        <div style="display: flex; gap: 10px;">
                            <a href="https://wa.me/{phone}" target="_blank" style="flex: 1; background:#25D366; color:white; padding:10px; border-radius:8px; text-align:center; text-decoration:none;">واتساب</a>
                            <a href="tel:{phone}" style="flex: 1; background:#1e40af; color:white; padding:10px; border-radius:8px; text-align:center; text-decoration:none;">اتصال</a>
                        </div>
                    ''', unsafe_allow_html=True)

    with tab4:
        st.subheader("🎭 رصد السلوك والتواصل الفوري")
        df_st = fetch_safe("students")
        all_names = df_st.iloc[:, 1].tolist() if not df_st.empty else []
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + all_names, key="behavior_select")
        if b_name:
            st_row = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_phone = str(st_row[7]).split('.')[0]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_date = c2.date_input("📅 التاريخ", key="beh_date")
                b_note = st.text_area("📝 الملاحظة")
                
                msg = f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\nالنوع: {b_type}\nالملاحظة: {b_note}\nالتاريخ: {b_date}"
                
                col1, col2 = st.columns(2)
                if col1.button("💾 حفظ فقط", use_container_width=True):
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    st.success("✅ تم الحفظ"); st.rerun()
                
                wa_url = f"https://wa.me/{s_phone}?text={urllib.parse.quote(msg)}"
                col2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; background:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; text-decoration:none; font-weight:bold;">💬 واتساب</a>', unsafe_allow_html=True)

    with tab5:
        st.markdown("### 📢 لوحة الاختبارات")
        with st.form("ann_form"):
            c1, c2 = st.columns([1, 2])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"], key="ex_class")
            a_title = c2.text_input("📝 العنوان")
            a_date = st.date_input("📅 التاريخ", key="ex_date")
            a_link = st.text_input("🔗 رابط")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([str(a_class), str(a_title), str(a_date), str(a_link)])
                st.success("✅ تم النشر"); st.rerun()

    with tab6:
        st.markdown("### ⚙️ الإعدادات")
        with st.expander("🔐 تغيير بيانات الحساب"):
            with st.form("update_auth"):
                new_user = st.text_input("المستخدم الجديد")
                new_pass = st.text_input("السر الجديد", type="password")
                if st.form_submit_button("💾 حفظ"):
                    ws_u = sh.worksheet("users")
                    ws_u.update_cell(2, 1, new_user)
                    ws_u.update_cell(2, 2, hashlib.sha256(str.encode(new_pass)).hexdigest())
                    st.success("✅ تم التحديث")
        
        st.markdown("#### 📥 تحميل البيانات")
        df_all = fetch_safe("students")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_all.to_excel(writer, index=False)
        st.download_button(label="📥 تحميل سجل الطلاب Excel", data=buffer.getvalue(), file_name="students_report.xlsx")

# --- واجهة الطالب ---
if st.session_state.role == "student":
    df_st = fetch_safe("students")
    me = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
    st.markdown(f"## أهلاً بك يا {me[1]} 👋")
    c1, c2 = st.columns(2)
    with c1:
        st.info("📊 درجاتك")
        df_g = fetch_safe("grades")
        if not df_g.empty:
            st.dataframe(df_g[df_g.iloc[:, 0] == st.session_state.sid], hide_index=True)
    with c2:
        st.success("🥇 السلوك")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            st.dataframe(df_b[df_b.iloc[:, 0] == me[1]], hide_index=True)
    if st.button("خروج"):
        st.session_state.role = None
        st.rerun()
