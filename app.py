import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

# --- التنسيق الاحترافي الجديد (CSS) ---
st.markdown("""
    <style>
    /* تحسين الخلفية العامة */
    .main { 
        background-color: #f0f2f6; 
        direction: rtl;
    }
    
    /* تنسيق العنوان الترحيبي */
    .welcome-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white !important;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* حل مشكلة اختفاء النصوص في البطاقات */
    [data-testid="stMetricLabel"] {
        color: #1e3a8a !important; 
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #111827 !important; /* لون داكن جداً للوضوح */
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
    .stMetric {
        background-color: white !important;
        border-radius: 15px !important;
        padding: 20px !important;
        border-right: 8px solid #1e3a8a !important; /* لمسة جمالية جانبية */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    /* تنسيق جداول البيانات لتكون احترافية */
    .stTable, .stDataFrame {
        background-color: white !important;
        border-radius: 12px !important;
        padding: 10px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    }
    
    /* تنسيق الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background: #1e3a8a;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #3b82f6;
        transform: translateY(-2px);
    }

    /* إخفاء شعارات Streamlit */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام الدخول والخروج (بدون تعديل هيكلي) ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='welcome-header'><h1>🏛️ منصة الأستاذ زياد المعمري التعليمية</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("تسجيل الدخول"):
            if pwd == "1234": 
                st.session_state.role = "teacher"
                st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب", key="login_sid")
        if st.button("دخول الطالب"):
            if sid_in:
                df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
                match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.student_id = str(sid_in)
                    st.session_state.student_name = match.iloc[0]["الاسم"]
                    st.rerun()
                else: st.error("عذراً، الرقم الأكاديمي غير مسجل.")
    st.stop()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown("## 🏛️ القائمة")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])
    # (بقية كود المعلم الخاص بك تبقى هنا كما هي)
    st.info("لوحة تحكم المعلم")

# --- 4. واجهة الطالب (التنسيق الجمالي والوضوح) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='welcome-header'><h3>🎓 أهلاً بك: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    
    # بطاقات البيانات (أصبحت واضحة جداً الآن)
    c1, c2, c3 = st.columns(3)
    c1.metric("الصف الدراسي", my_info["الصف"])
    c2.metric("المرحلة", my_info["المرحلة"])
    c3.metric("المادة المسجلة", my_info["المادة"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 تقرير الدرجات")
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    if not my_grades.empty: 
        st.dataframe(my_grades, use_container_width=True, hide_index=True) # استخدام DataFrame للوضوح العالي
    else: 
        st.info("لم ترصد درجاتك حتى الآن.")
        
    st.divider()
    st.subheader("🎭 سجل الملاحظات السلوكية")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            st.info(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
    else: 
        st.success("سجلك السلوكي متميز!")
