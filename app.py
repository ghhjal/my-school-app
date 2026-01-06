import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    """الاتصال الآمن بجوجل شيت"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_client()

# --- 2. دوال التعامل مع البيانات (الاستقرار) ---
def fetch_safe(worksheet_name):
    """جلب البيانات كقاموس (Dictionary) لضمان الربط بأسماء الأعمدة"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records() # تجلب البيانات مرتبطة بأسماء الأعمدة تلقائياً
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def get_col_index(ws, col_name):
    """دالة ذكية تجد رقم العمود بناءً على اسمه لمنع انهيار البرنامج عند تغيير الجدول"""
    try:
        headers = ws.row_values(1)
        return headers.index(col_name) + 1
    except:
        return None

# --- 3. التصميم المطور (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    .stButton>button { border-radius: 12px; font-weight: bold; transition: 0.3s; }
    /* منع ظهور الشاشة البيضاء بسبب أخطاء التنسيق */
    div[data-testid="stForm"] { border-radius: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. إدارة الجلسة ---
if "role" not in st.session_state:
    st.session_state.role = None

# --- [واجهة تسجيل الدخول - تظل كما هي مع تحسين جلب البيانات] ---
# ... (يمكنك الاحتفاظ بكود الدخول الخاص بك هنا) ...

# --- 5. واجهة المعلم الاحترافية ---
if st.session_state.role == "teacher":
    st.markdown("### 👨‍🏫 لوحة تحكم المعلم")
    
    tabs = st.tabs(["👥 إدارة الطلاب", "📈 رصد الدرجات", "🥇 السلوك", "⚙️ الإعدادات", "🚗 خروج"])

    # --- تبويب إدارة الطلاب (الحذف الآمن) ---
    with tabs[0]:
        st.markdown("#### 🗑️ حذف طالب (بناءً على الرقم الأكاديمي)")
        df_st = fetch_safe("students")
        if not df_st.empty:
            # نستخدم الرقم الأكاديمي كمفتاح أساسي فريد للبحث والحذف
            del_id = st.selectbox("اختر الرقم الأكاديمي للطالب:", [""] + df_st['الرقم الأكاديمي'].astype(str).tolist())
            
            if st.button("🚨 تنفيذ الحذف النهائي", use_container_width=True):
                if del_id:
                    ws = sh.worksheet("students")
                    cell = ws.find(del_id) # البحث عن السطر الذي يحتوي على هذا الرقم
                    if cell:
                        ws.delete_rows(cell.row)
                        st.success(f"✅ تم حذف الطالب صاحب الرقم {del_id} بنجاح")
                        time.sleep(1)
                        st.rerun()

    # --- تبويب رصد الدرجات (الاعتماد على الأسماء) ---
    with tabs[1]:
        st.markdown("#### 📝 إدخال درجات الطلاب")
        if not df_st.empty:
            with st.form("grades_pro_form"):
                student_name = st.selectbox("اختر الطالب:", df_st['الاسم الثلاثي'].tolist())
                col1, col2 = st.columns(2)
                p1 = col1.number_input("المشاركة (p1)", 0.0, 20.0)
                p2 = col2.number_input("الواجبات (p2)", 0.0, 20.0)
                
                if st.form_submit_button("💾 حفظ الدرجات"):
                    # جلب الرقم الأكاديمي للطالب المختار للربط الصحيح
                    s_id = df_st[df_st['الاسم الثلاثي'] == student_name]['الرقم الأكاديمي'].values[0]
                    ws_g = sh.worksheet("grades")
                    ws_g.append_row([str(s_id), p1, p2, datetime.date.today().isoformat()])
                    st.success("✅ تم حفظ الدرجات بنجاح")

    # --- تبويب السلوك (تحديث النقاط الذكي) ---
    with tabs[2]:
        st.markdown("#### 🥇 تحديث نقاط السلوك ديناميكياً")
        if not df_st.empty:
            target_student = st.selectbox("اختر الطالب للرصد:", df_st['الاسم الثلاثي'].tolist(), key="beh_select")
            b_type = st.radio("نوع الملاحظة:", ["🌟 متميز (+10)", "❌ مخالفة (-10)"])
            
            if st.button("🚀 تحديث الرصيد"):
                ws_st = sh.worksheet("students")
                # البحث عن رقم عمود "النقاط" بالاسم بدلاً من رقم (9)
                points_col_idx = get_col_index(ws_st, "النقاط")
                
                cell = ws_st.find(target_student)
                if cell and points_col_idx:
                    # جلب النقاط الحالية بأمان
                    current_val = ws_st.cell(cell.row, points_col_idx).value
                    current_points = int(current_val) if current_val else 0
                    
                    points_change = 10 if "+" in b_type else -10
                    ws_st.update_cell(cell.row, points_col_idx, current_points + points_change)
                    st.success(f"✅ تم تحديث نقاط {target_student}")
                    time.sleep(1)
                    st.rerun()

# --- خروج ---
if st.session_state.role:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
