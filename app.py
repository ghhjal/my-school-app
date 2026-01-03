import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame()

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

    # قنوات التواصل الأربعة (مكتملة الآن)
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

if st.session_state.role:
    st.success("تم تسجيل الدخول بنجاح!")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
# ==========================================
# 👨‍🏫 واجهة المعلم الكاملة (إصلاح خطأ Line 190)
# ==========================================
if st.session_state.role == "teacher":
    # 1. تعريف القائمة الجانبية (Sidebar) أولاً لتعريف متغير menu
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align:center; padding:10px;">
                <i class="bi bi-person-badge" style="font-size:50px; color:#1e40af;"></i>
                <h3 style="margin-top:10px; font-family:'Cairo';">الأستاذ زياد</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # هذا السطر هو الأهم لحل مشكلة NameError
        menu = st.selectbox("🏠 القائمة الرئيسية", 
                            ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🔍 البحث المطور", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
        
        st.divider()
        if st.button("🚗 تسجيل الخروج", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    # --- القسم الأول: إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(135deg,#1e40af,#3b82f6); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:20px;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        
        # عرض الجدول الحالي
        with st.expander("📋 السجل الحالي للطلاب", expanded=True):
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        # نموذج إضافة طالب (مع معالجة 966)
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس طالب جديد")
            with st.form("add_student_final", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("🔢 الرقم الأكاديمي")
                nname = c2.text_input("👤 الاسم الثلاثي")
                nphone = c3.text_input("📱 جوال ولي الأمر")
                
                c4, c5, c6 = st.columns(3)
                nclass = c4.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                nstage = c5.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
                
                if st.form_submit_button("✅ اعتماد التأسيس"):
                    if nid and nname and nphone:
                        # تصحيح رقم الجوال تلقائياً
                        cp = nphone.strip()
                        if cp.startswith('0'): cp = cp[1:]
                        if not cp.startswith('966'): cp = '966' + cp
                        
                        row = [nid, nname, nclass, "1447هـ", nstage, nsub, "", cp, "0"]
                        sh.worksheet("students").append_row(row)
                        st.success("✅ تم الحفظ بنجاح")
                        time.sleep(1); st.rerun()

    # --- القسم الثاني: شاشة الدرجات ---
    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(135deg,#059669,#10b981); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:20px;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        if not df_st.empty:
            with st.form("grades_entry"):
                col1, col2 = st.columns(2)
                s_name = col1.selectbox("🎯 اختر الطالب:", df_st.iloc[:, 1].tolist())
                exam = col2.selectbox("📝 النوع:", ["شهري", "فترتي", "نهائي", "واجبات"])
                col3, col4 = st.columns(2)
                grade = col3.number_input("💯 الدرجة:", 0.0, 100.0)
                note = col4.text_input("💬 ملاحظة المعلم")
                
                if st.form_submit_button("✅ حفظ الدرجة"):
                    student_data = df_st[df_st.iloc[:, 1] == s_name].iloc[0]
                    sid, sub = student_data[0], student_data[5]
                    date = datetime.datetime.now().strftime("%Y-%m-%d")
                    sh.worksheet("grades").append_row([sid, s_name, sub, exam, grade, date, note])
                    st.success(f"✅ تم رصد الدرجة للطالب {s_name}")
                    time.sleep(1); st.rerun()
            
            st.divider()
            df_gr = fetch_safe("grades")
            st.dataframe(df_gr, use_container_width=True, hide_index=True)

    # --- القسم الثالث: البحث المطور ---
    elif menu == "🔍 البحث المطور":
        st.markdown('<div style="background:linear-gradient(135deg,#6366f1,#a855f7); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:20px;"><h1>🔍 نظام البحث المطور</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        query = st.text_input("🔎 ابحث بالاسم أو الرقم الأكاديمي:")
        if query:
            results = df_st[df_st.iloc[:, 0].str.contains(query) | df_st.iloc[:, 1].str.contains(query)]
            st.dataframe(results, use_container_width=True, hide_index=True)
