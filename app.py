import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. إعدادات الصفحة الأساسية ---
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

# --- 2. دوال التعامل مع البيانات الاحترافية ---
def fetch_safe(worksheet_name):
    """جلب البيانات وتحويلها لـ DataFrame مع الحفاظ على أسماء الأعمدة"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records() # تجلب البيانات كقاموس مرتب بأسماء الأعمدة
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def get_col_index(ws, col_name):
    """دالة عبقرية تجد رقم العمود بناءً على اسمه لمنع الانهيار"""
    try:
        headers = ws.row_values(1)
        return headers.index(col_name) + 1
    except:
        return None

# --- 3. التصميم (CSS) ---
# (احتفظت بتصميمك مع تحسين خفيف لضمان عدم تداخل العناصر)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    /* تحسينات لبطاقات الطلاب */
    .st-expander { border-radius: 15px !important; border: 1px solid #e2e8f0 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. منطق تسجيل الدخول ---
if "role" not in st.session_state:
    st.session_state.role = None

# (جزء تسجيل الدخول يظل كما هو مع استبدال iloc بأسماء الأعمدة)
# ... [كود الدخول الأصلي] ...

# --- 5. واجهة المعلم (التعديلات الاحترافية) ---
if st.session_state.role == "teacher":
    st.markdown("### 👨‍🏫 لوحة تحكم المعلم")
    tabs = st.tabs(["👥 إدارة الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[0]: # إدارة الطلاب
        df_st = fetch_safe("students")
        if not df_st.empty:
            # الحذف الاحترافي: نبحث بالرقم الأكاديمي لأنه "فريد" (ID)
            st.markdown("#### 🗑️ حذف طالب")
            del_id = st.selectbox("اختر الرقم الأكاديمي للحذف:", [""] + df_st['الرقم الأكاديمي'].astype(str).tolist())
            if st.button("🚨 حذف نهائي"):
                ws = sh.worksheet("students")
                # البحث عن الصف باستخدام الرقم الأكاديمي في العمود الأول
                cell = ws.find(del_id)
                if cell:
                    ws.delete_rows(cell.row)
                    st.success("تم الحذف بنجاح")
                    st.rerun()

    with tabs[1]: # الدرجات
        st.markdown("### 📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            with st.form("grade_form"):
                student_name = st.selectbox("الطالب:", df_st['الاسم الثلاثي'].tolist())
                p1 = st.number_input("المشاركة التفاعلية", 0, 20)
                if st.form_submit_button("حفظ"):
                    # جلب رقم الصف الصحيح للطالب
                    ws_g = sh.worksheet("grades")
                    # إضافة صف جديد مع ربطه بالرقم الأكاديمي (أكثر استقراراً)
                    s_id = df_st[df_st['الاسم الثلاثي'] == student_name]['الرقم الأكاديمي'].values[0]
                    ws_g.append_row([str(s_id), p1, datetime.date.today().isoformat()])
                    st.success("تم الرصد")

    with tabs[2]: # السلوك (تحديث النقاط ديناميكياً)
        st.markdown("### 🥇 رصد السلوك")
        if not df_st.empty:
            target_student = st.selectbox("اختر الطالب للرصد السلوكي:", df_st['الاسم الثلاثي'].tolist())
            b_type = st.radio("نوع السلوك:", ["🌟 متميز (+10)", "❌ مخالفة (-10)"])
            
            if st.button("تحديث النقاط"):
                ws_st = sh.worksheet("students")
                # إيجاد رقم عمود "النقاط" ديناميكياً
                points_col = get_col_index(ws_st, "النقاط")
                name_col = get_col_index(ws_st, "الاسم الثلاثي")
                
                # البحث عن الطالب
                cell = ws_st.find(target_student)
                if cell and points_col:
                    current_points = int(ws_st.cell(cell.row, points_col).value or 0)
                    change = 10 if "+" in b_type else -10
                    ws_st.update_cell(cell.row, points_col, current_points + change)
                    st.success(f"تم تحديث نقاط {target_student}")
                    st.rerun()

# (واجهة الطالب تتبع نفس منطق أسماء الأعمدة لضمان عدم حدوث شاشة بيضاء)
