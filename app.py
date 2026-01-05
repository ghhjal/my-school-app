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

# --- 1. الإعدادات العامة وتنسيق الواجهة ---
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
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# --- 2. التصميم (CSS) - النسخة الأصلية المطورة ---
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
    .stButton>button {
        background: #2563eb !important; color: white !important;
        border-radius: 12px !important; font-weight: bold !important;
        height: 3.5em !important; width: 100% !important;
    }
    .ann-card {
        padding: 15px; border-radius: 10px; margin-bottom: 5px;
        border-right: 5px solid #4F46E5; background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <h1 style="font-size:26px; font-weight:700; color:white;">منصة زياد الذكية</h1>
        <p style="color:white;">نظام متابعة الطلاب المطور - النسخة المستقرة</p>
    </div>
""", unsafe_allow_html=True)

# --- 3. منطق الدخول والحماية ---
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_form"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df = fetch_safe("students")
                if not df.empty and sid.strip() in df.iloc[:, 0].astype(str).str.strip().values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip()
                    st.balloons(); time.sleep(0.5); st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with tab2:
        with st.form("te_form"):
            u, p = st.text_input("👤 اسم المستخدم"), st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u.strip()]
                    if not row.empty and hashlib.sha256(str.encode(p)).hexdigest() == row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("بيانات الدخول غير صحيحة")
    st.stop()

# --- 4. واجهة المعلم (كافة الميزات) ---
if st.session_state.role == "teacher":
    tabs = st.tabs(["👥 إدارة الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- إدارة الطلاب ---
    with tabs[0]:
        st.markdown("### 👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        with st.form("add_student_final"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nphone = c3.text_input("📱 جوال ولي الأمر")
            if st.form_submit_button("✅ إضافة الطالب"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, "الأول", "1447هـ", "ابتدائي", "لغة إنجليزية", "", nphone, "0"])
                    st.success("تمت الإضافة"); time.sleep(0.5); st.rerun()
        
        with st.expander("🗑️ حذف طالب"):
            if not df_st.empty:
                del_name = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 تنفيذ الحذف"):
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s)
                            cell = ws.find(del_name)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.success("تم الحذف"); time.sleep(0.5); st.rerun()

    # --- شاشة الدرجات ---
    with tabs[1]:
        st.markdown("### 📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            with st.form("grades_form"):
                sel_student = st.selectbox("اختر الطالب", df_st.iloc[:, 1].tolist())
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("المشاركة", 0.0, 20.0)
                p2 = c2.number_input("الواجبات", 0.0, 20.0)
                perf = c3.number_input("الاختبارات", 0.0, 20.0)
                if st.form_submit_button("💾 حفظ الدرجات"):
                    ws_g = sh.worksheet("grades")
                    cell = ws_g.find(sel_student)
                    row_data = [sel_student, p1, p2, perf, str(datetime.date.today()), ""]
                    if cell: ws_g.update(f"B{cell.row}:F{cell.row}", [row_data[1:]])
                    else: ws_g.append_row(row_data)
                    st.success("تم الحفظ")

    # --- رصد السلوك والتواصل (كافة أزرار الواتساب والإيميل) ---
    with tabs[3]:
        st.markdown("### 🎭 السلوك والتواصل الفوري")
        df_st = fetch_safe("students")
        if not df_st.empty:
            b_name = st.selectbox("🎯 اختر الطالب:", [""] + df_st.iloc[:, 1].tolist(), key="behav_sel")
            if b_name:
                st_row = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
                phone = str(st_row[7])
                with st.container(border=True):
                    b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                    b_note = st.text_area("نص الملاحظة")
                    
                    col1, col2 = st.columns(2)
                    if col1.button("💾 حفظ فقط"):
                        sh.worksheet("behavior").append_row([b_name, str(datetime.date.today()), b_type, b_note])
                        st.success("تم الحفظ")
                    
                    if col2.button("💬 واتساب"):
                        msg = f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\nنوع السلوك: {b_type}\nالملاحظة: {b_note}"
                        wa_url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(msg)}"
                        st.markdown(f'<script>window.open("{wa_url}", "_blank");</script>', unsafe_allow_html=True)

    # --- الإعدادات (رفع إكسل وتغيير كلمة المرور) ---
    with tabs[5]:
        st.markdown("### ⚙️ الإعدادات")
        with st.expander("🔐 تغيير بيانات الحساب"):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_p = st.text_input("كلمة المرور الجديدة", type="password")
            if st.button("حفظ التغييرات"):
                ws_u = sh.worksheet("users")
                ws_u.update_cell(2, 1, new_u)
                ws_u.update_cell(2, 2, hashlib.sha256(str.encode(new_p)).hexdigest())
                st.success("تم التحديث")

    with tabs[6]:
        if st.button("تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()
