import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import io
import time

# ==========================================
# 1. إعدادات الصفحة والـ CSS المتوافق مع الوضع الليلي والنهاري
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية | أنماط التعلم (VAK)", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio, .stSelectbox, .stTextInput {
        direction: rtl; text-align: right; font-family: 'Tajawal', 'Arial', sans-serif;
    }
    
    /* 💡 الهيدر المطور بهوية المنصة وشارة قسم أنماط التعلم */
    .custom-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #2980b9 100%);
        padding: 16px 15px;
        border-radius: 12px;
        color: white !important;
        margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .title-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 8px;
        width: 100%;
    }
    .header-main-title {
        font-size: 25px !important;
        font-weight: bold;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }
    
    @keyframes float-cap {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-3px) rotate(-10deg); }
        50% { transform: translateY(-5px) rotate(0deg); }
        75% { transform: translateY(-3px) rotate(10deg); }
    }
    .header-icon { font-size: 27px; display: inline-block; animation: float-cap 3.5s ease-in-out infinite; }
    
    .header-badge {
        background-color: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px !important;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        font-weight: bold;
        display: inline-block;
        margin: 0 auto !important;
        text-align: center !important;
    }

    /* 💡 بطاقة تسجيل الدخول الاحترافية المتناسقة مع المنصة الأم */
    .login-card-header {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1;
        border-right: 4px solid #2980b9;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 15px;
        text-align: center;
    }
    .login-card-title {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        margin-bottom: 5px;
    }
    .login-card-sub {
        font-size: 13px !important;
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        margin: 0;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 2px solid #cbd5e1;
        padding-bottom: 8px;
        gap: 8px;
        justify-content: right;
        margin-bottom: 18px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab"] * {
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-size: 13.5px !important;
        font-weight: bold !important;
        margin: 0 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2980b9 0%, #1f618d 100%) !important;
        border-color: #1f618d !important;
        box-shadow: 0 3px 8px rgba(41, 128, 185, 0.25) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    .dashboard-stats-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .dash-card { flex: 1; padding: 12px; border-radius: 8px; text-align: center; background-color: #ffffff !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid; }
    .dash-card.total { border-color: #9b59b6; } 
    .dash-card.completed { border-color: #2ecc71; } 
    .dash-card.pending { border-color: #f1c40f; } 
    .dash-title { font-size: 12px; margin-bottom: 5px; color: #475569 !important; -webkit-text-fill-color: #475569 !important; font-weight: bold; }
    .dash-value { font-size: 22px; font-weight: bold; color: #1e293b !important; -webkit-text-fill-color: #1e293b !important; }
    .welcome-box { background-color: #ebf5fb !important; border: 1px solid #3498db; border-radius: 8px; padding: 10px; color: #1f618d !important; -webkit-text-fill-color: #1f618d !important; font-size: 14px; font-weight: bold; }
    
    /* 💡 تنسيق الأزرار القياسية وأزرار التحميل (واضحة تماماً في الدارك مود واللايت مود) */
    button[kind="secondary"], div[data-testid="stDownloadButton"] button {
        background-color: #f8f9fa !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-weight: bold !important;
    }
    button[kind="secondary"] *, div[data-testid="stDownloadButton"] button * {
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-weight: bold !important;
        font-size: 13px !important;
    }
    button[kind="primary"] {
        background-color: #ffeaeb !important;
        color: #d63031 !important;
        -webkit-text-fill-color: #d63031 !important;
        border: 1px solid #ffb8b8 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    button[kind="primary"] * {
        color: #d63031 !important;
        -webkit-text-fill-color: #d63031 !important;
        font-weight: bold !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 13px !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }

    /* 💡 تلوين زر التقرير النشط باللون الأزرق الملكي والنص الأبيض */
    div[class*="st-key-rep_active"] button {
        background: linear-gradient(135deg, #2c3e50 0%, #2980b9 100%) !important;
        border: 1.5px solid #1f618d !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        box-shadow: 0 3px 8px rgba(41, 128, 185, 0.35) !important;
    }
    div[class*="st-key-rep_active"] button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* 💡 الحفاظ على شبكة أزرار التقارير (2×2) متجاوبة في شاشة الجوال */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-rep_"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-rep_"]) > div {
        width: calc(50% - 4px) !important;
        flex: 1 1 calc(50% - 4px) !important;
        min-width: 0 !important;
    }
    
    .custom-chart-container { display: flex; justify-content: space-around; align-items: flex-end; height: 200px; padding: 20px 0; border-bottom: 1px solid #cbd5e1; margin-top: 20px; }
    .chart-bar-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; width: 25%; }
    .chart-value { font-weight: bold; font-size: 15px; margin-bottom: 5px; } 
    .chart-bar { width: 100%; border-radius: 6px 6px 0 0; transition: height 0.5s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .chart-label { margin-top: 10px; font-weight: bold; font-size: 13px; }
    
    .custom-footer { text-align: center; color: #7f8c8d; font-size: 13px; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-family: 'Tajawal', sans-serif; }
</style>
""", unsafe_allow_html=True)

# رسم الهيدر فوراً على الشاشة بالهوية الموحدة والشارة التخصصية
st.markdown("""
<div class="custom-header">
    <div class="title-wrapper">
        <span class="header-icon">🎓</span>
        <h1 class="header-main-title">منصة زياد الذكية</h1>
    </div>
    <div class="header-badge">🧠 نظام تشخيص أنماط التعلم (VAK) | بوابة المعلمين والإدارة</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. دوال الاتصال المشترك والتخزين المؤقت الآمن
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit#gid=0"

def clean_id(val):
    if pd.isna(val): return ""
    val = str(val).translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    return val.split('.')[0].strip()

@st.cache_resource
def get_gsheets_conn():
    from streamlit_gsheets import GSheetsConnection
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=7200, max_entries=5)
def get_all_teachers():
    conn = get_gsheets_conn()
    try:
        df_teachers = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", dtype=str)
        df_teachers['id'] = df_teachers['id'].apply(clean_id)
        return df_teachers
    except:
        return pd.DataFrame(columns=['id', 'name', 'role', 'class_name'])

@st.cache_data(ttl=7200, max_entries=5)
def get_all_students():
    conn = get_gsheets_conn()
    try: 
        df_students = conn.read(spreadsheet=SHEET_URL, worksheet="df_students", dtype=str)
    except: 
        try: df_students = conn.read(spreadsheet=SHEET_URL, dtype=str)
        except: df_students = pd.DataFrame()
        
    required_cols = ['id', 'name', 'grade', 'class_name']
    for col in required_cols:
        if col not in df_students.columns: df_students[col] = ""
        df_students[col] = df_students[col].fillna("").astype(str).str.strip()
            
    if 'vak_result' not in df_students.columns: df_students['vak_result'] = "غير مختبر"
    df_students['vak_result'] = df_students['vak_result'].replace("", "غير مختبر").fillna("غير مختبر")
    
    for col in ['v_score', 'a_score', 'k_score']:
        if col not in df_students.columns: df_students[col] = "0"
        df_students[col] = df_students[col].replace("", "0").fillna("0")
        
    df_students['id'] = df_students['id'].apply(clean_id)
    return df_students

def clear_all_caches():
    get_all_students.clear()
    get_all_teachers.clear()

# ==========================================
# 💡 دالة الفلترة الذكية المقسمة (الصف الدراسي -> الفصل)
# ==========================================
def infer_grade_name(row):
    g = str(row.get('grade', '')).strip()
    c = str(row.get('class_name', '')).strip()
    if g and g not in ['nan', 'None', '']:
        return g
    if '/' in c:
        return c.split('/')[0].strip()
    return c if c else "غير محدد"

def render_grade_class_Selector(df_source, key_prefix):
    df_temp = df_source.copy()
    df_temp['_grade_group'] = df_temp.apply(infer_grade_name, axis=1)
    
    unique_grades = sorted([g for g in df_temp['_grade_group'].unique() if g])
    
    col_g, col_c = st.columns(2)
    with col_g:
        selected_grade = st.selectbox("1️⃣ اختر الصف / المرحلة:", ["جميع الصفوف"] + unique_grades, key=f"{key_prefix}_grade")
    
    if selected_grade != "جميع الصفوف":
        df_filtered_grade = df_temp[df_temp['_grade_group'] == selected_grade].copy()
    else:
        df_filtered_grade = df_temp.copy()
        
    unique_classes = sorted([c for c in df_filtered_grade['class_name'].unique() if c])
    
    with col_c:
        selected_class = st.selectbox("2️⃣ اختر الفصل:", ["جميع الفصول"] + unique_classes, key=f"{key_prefix}_class")
        
    if selected_class != "جميع الفصول":
        df_final = df_filtered_grade[df_filtered_grade['class_name'] == selected_class].copy()
        scope_label = f"فصل {selected_class}"
    elif selected_grade != "جميع الصفوف":
        df_final = df_filtered_grade.copy()
        scope_label = f"صف {selected_grade}"
    else:
        df_final = df_filtered_grade.copy()
        scope_label = "جميع الفصول"
        
    return df_final.drop(columns=['_grade_group'], errors='ignore'), scope_label

# ==========================================
# 💡
