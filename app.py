import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
# --- دالة جلب البيانات (تأكد من وجودها في ملفك) ---
def fetch_safe(sheet_name):
    # ضع هنا كود الاتصال بجوجل شيت الخاص بك
    return st.session_state.get(f"df_{sheet_name}") # مثال

# --- تهيئة الجلسة ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None
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
    
    # استخدام أسماء فريدة لتبويبات الدخول لمنع تداخل المتغيرات
auth_tab1, auth_tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])

with auth_tab1:
    with st.form("st_form"):
        sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية للمتابعة")
        if st.form_submit_button("دخول للمنصة 🚀"):
            df = fetch_safe("students")
            if not df.empty and sid:
                df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                if sid.strip() in df.iloc[:, 0].values:
                    # تعيين الجلسة وإعادة التشغيل فوراً
                    st.session_state.role = "student"
                    st.session_state.sid = sid.strip()
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else: 
                    st.error("عذراً، الرقم غير مسجل في النظام")

with auth_tab2:
    with st.form("te_form"):
        u = st.text_input("👤 اسم المستخدم")
        p = st.text_input("🔑 كلمة المرور", type="password")
        if st.form_submit_button("تسجيل الدخول"):
            df = fetch_safe("users")
            if not df.empty:
                # التأكد من مطابقة اسم المستخدم
                row = df[df['username'] == u.strip()]
                if not row.empty:
                    hashed = hashlib.sha256(str.encode(p)).hexdigest()
                    if hashed == row.iloc[0]['password_hash']:
                        # تعيين الجلسة وإعادة التشغيل فوراً
                        st.session_state.role = "teacher"
                        st.rerun()
                    else: 
                        st.error("كلمة المرور غير صحيحة")
                else: 
                    st.error("المستخدم غير موجود")

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


# ==========================================
# 🛑 قسم الطالب (معزول 100٪)
# ==========================================

if st.session_state.role == "student":
    st.title("👨‍🎓 بوابة الطالب الذكية")

    try:
        df_students = fetch_safe("students")
        student_row = df_students[
            df_students.iloc[:, 0].astype(str).str.strip()
            == str(st.session_state.sid)
        ]

        if not student_row.empty:
            s_data = student_row.iloc[0]
            st.success(f"مرحباً بك يا {s_data[1]}")

            t_grades, t_behavior = st.tabs(["📊 درجاتي", "🌟 نقاطي وسلوكي"])

            with t_grades:
                df_g = fetch_safe("grades")
                my_g = df_g[
                    df_g.iloc[:, 0].astype(str).str.strip()
                    == str(st.session_state.sid)
                ]
                st.dataframe(my_g, use_container_width=True)

            with t_behavior:
                st.info(f"رصيد نقاطك الحالي هو: {s_data[8]}")
                st.write("استمر في الاجتهاد للوصول إلى قائمة الشرف! 🏆")

        else:
            st.error("لم يتم العثور على بياناتك.")

    except Exception as e:
        st.error(f"خطأ تقني: {e}")

    if st.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    st.stop()
