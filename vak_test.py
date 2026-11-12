import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import base64
import io
import time

# ==========================================
# 1. إعدادات الصفحة ونظام القوالب الديناميكية (Dynamic Themes) + التوافق الكامل مع الجوال (RTL)
# ==========================================
st.set_page_config(
    page_title="بوابة اختبار أنماط التعلم (VAK) | منصة زياد الذكية",
    page_icon="🎓",
    layout="centered"
)

# تعريف القوالب الديناميكية الأربعة للهوية البصرية
THEMES = {
    "royal": {
        "name": "👑 الأزرق الملكي",
        "desc": "الهوية الرسمية الأساسية للمنصة",
        "bg_page": "#f7f8fb",
        "bg_input": "#f8f9fc",
        "brand_dark": "#141b3e",
        "brand_navy": "#172661",
        "brand_royal": "#1f379c",
        "brand_bright": "#2958d8",
        "brand_light": "#426bda",
        "brand_gold": "#eb9d11",
        "hero_grad": "linear-gradient(135deg, #2b5ce7 0%, #1f379c 45%, #162044 100%)",
        "btn_grad": "linear-gradient(90deg, #141b3e 0%, #1f379c 50%, #2958d8 100%)",
        "shadow_header": "0 12px 28px rgba(31, 55, 156, 0.22)",
        "shadow_btn": "0 4px 14px rgba(31, 55, 156, 0.25)",
        "focus_ring": "rgba(41, 88, 216, 0.14)",
        "tab_hover": "#eef2ff",
        "row_hover": "#eff6ff",
        "report_bg": "#eff6ff",
        "report_border": "#bfdbfe",
        "dot_color": "#2958d8"
    },
    "green": {
        "name": "🌿 الأخضر الوطني",
        "desc": "طابع تعليمي رسمي مستوحى من الهوية الوطنية",
        "bg_page": "#f4f9f6",
        "bg_input": "#f7fbf9",
        "brand_dark": "#0b2e1f",
        "brand_navy": "#0f4c35",
        "brand_royal": "#156f4d",
        "brand_bright": "#1ea371",
        "brand_light": "#34d399",
        "brand_gold": "#d99b16",
        "hero_grad": "linear-gradient(135deg, #1ea371 0%, #156f4d 48%, #0b2e1f 100%)",
        "btn_grad": "linear-gradient(90deg, #0b2e1f 0%, #156f4d 50%, #1ea371 100%)",
        "shadow_header": "0 12px 28px rgba(21, 111, 77, 0.22)",
        "shadow_btn": "0 4px 14px rgba(21, 111, 77, 0.25)",
        "focus_ring": "rgba(30, 163, 113, 0.15)",
        "tab_hover": "#ecfdf5",
        "row_hover": "#f0fdf4",
        "report_bg": "#ecfdf5",
        "report_border": "#a7f3d0",
        "dot_color": "#1ea371"
    },
    "emerald": {
        "name": "💎 الزمرد الفاخر",
        "desc": "تصميم زمردي عميق بلمسات ذهبية ملكية فاخرة",
        "bg_page": "#f3f8f7",
        "bg_input": "#f6fbfa",
        "brand_dark": "#072522",
        "brand_navy": "#0b3b36",
        "brand_royal": "#0f5e56",
        "brand_bright": "#128277",
        "brand_light": "#2dd4bf",
        "brand_gold": "#f59e0b",
        "hero_grad": "linear-gradient(135deg, #149689 0%, #0f5e56 48%, #072522 100%)",
        "btn_grad": "linear-gradient(90deg, #072522 0%, #0f5e56 50%, #149689 100%)",
        "shadow_header": "0 12px 28px rgba(15, 94, 86, 0.24)",
        "shadow_btn": "0 4px 14px rgba(15, 94, 86, 0.26)",
        "focus_ring": "rgba(18, 130, 119, 0.15)",
        "tab_hover": "#f0fdfa",
        "row_hover": "#ccfbf1",
        "report_bg": "#f0fdfa",
        "report_border": "#99f6e4",
        "dot_color": "#0f5e56"
    },
    "horizon": {
        "name": "🌌 الأفق الرقمي",
        "desc": "تدرج تقني عصري يجمع البنفسجي العميق والسماوي المضيء",
        "bg_page": "#f5f7fc",
        "bg_input": "#f8f9fe",
        "brand_dark": "#18143b",
        "brand_navy": "#26205e",
        "brand_royal": "#4338ca",
        "brand_bright": "#0284c7",
        "brand_light": "#38bdf8",
        "brand_gold": "#f59e0b",
        "hero_grad": "linear-gradient(135deg, #0284c7 0%, #4338ca 50%, #1e1b4b 100%)",
        "btn_grad": "linear-gradient(90deg, #1e1b4b 0%, #4338ca 52%, #0284c7 100%)",
        "shadow_header": "0 12px 28px rgba(67, 56, 202, 0.23)",
        "shadow_btn": "0 4px 14px rgba(67, 56, 202, 0.26)",
        "focus_ring": "rgba(2, 132, 199, 0.15)",
        "tab_hover": "#eef2ff",
        "row_hover": "#f0f9ff",
        "report_bg": "#f0f9ff",
        "report_border": "#bae6fd",
        "dot_color": "#4338ca"
    }
}

# ==========================================
# 2. دوال الاتصال المشترك والتخزين المؤقت الآمن (مع حفظ القالب النشط للمنصة)
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

@st.cache_data(ttl=600, max_entries=5)
def get_all_teachers():
    conn = get_gsheets_conn()
    try:
        df_teachers = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", ttl=0, dtype=str)
        for col in ['id', 'name', 'role', 'class_name', 'theme']:
            if col not in df_teachers.columns:
                df_teachers[col] = ""
            df_teachers[col] = df_teachers[col].fillna("").astype(str).str.strip()
        df_teachers['id'] = df_teachers['id'].apply(clean_id)
        df_teachers['role'] = df_teachers['role'].replace("", "teacher")
        df_teachers['class_name'] = df_teachers['class_name'].replace("", "all")
        df_teachers['theme'] = df_teachers['theme'].replace("", "royal")
        return df_teachers
    except:
        return pd.DataFrame(columns=['id', 'name', 'role', 'class_name', 'theme'])

@st.cache_data(ttl=7200, max_entries=5)
def get_all_students():
    conn = get_gsheets_conn()
    try:
        df_students = conn.read(spreadsheet=SHEET_URL, worksheet="df_students", ttl=0, dtype=str)
    except:
        try: df_students = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
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
    st.cache_data.clear()

def get_platform_theme():
    """جلب القالب المحفوظ للمنصة من حساب مدير النظام في قاعدة البيانات ليتوحد لجميع الزوار والمعلمين"""
    if 'active_theme' in st.session_state and st.session_state.active_theme in THEMES:
        return st.session_state.active_theme
    try:
        df_t = get_all_teachers()
        if not df_t.empty and 'theme' in df_t.columns:
            admins = df_t[df_t['role'] == 'admin']
            for val in admins['theme']:
                if val in THEMES:
                    st.session_state.active_theme = val
                    return val
            for val in df_t['theme']:
                if val in THEMES:
                    st.session_state.active_theme = val
                    return val
    except:
        pass
    st.session_state.active_theme = "royal"
    return "royal"

def save_platform_theme(new_theme_key):
    """حفظ القالب الذي يختاره مدير النظام فوراً في الجلسة وفي Google Sheets"""
    st.session_state.active_theme = new_theme_key
    try:
        conn = get_gsheets_conn()
        df_t = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", ttl=0, dtype=str)
        for col in ['id', 'name', 'role', 'class_name', 'theme']:
            if col not in df_t.columns:
                df_t[col] = ""
            df_t[col] = df_t[col].fillna("").astype(str).str.strip()
        df_t['theme'] = new_theme_key
        conn.update(spreadsheet=SHEET_URL, worksheet="teachers", data=df_t)
        clear_all_caches()
    except:
        pass

active_theme_key = get_platform_theme()
cur_t = THEMES.get(active_theme_key, THEMES["royal"])

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

    /* ========================================================
       1. المتغيرات اللونية للقالب الديناميكي النشط ({cur_t['name']})
          + الألوان الدلالية الثابتة والمستقلة لأنماط التعلم (VAK)
       ======================================================== */
    :root {{
        --bg-page: {cur_t['bg_page']};
        --bg-card: #ffffff;
        --bg-input: {cur_t['bg_input']};
        --brand-dark: {cur_t['brand_dark']};
        --brand-navy: {cur_t['brand_navy']};
        --brand-royal: {cur_t['brand_royal']};
        --brand-bright: {cur_t['brand_bright']};
        --brand-light: {cur_t['brand_light']};
        --brand-gold: {cur_t['brand_gold']};
        --hero-grad: {cur_t['hero_grad']};
        --btn-grad: {cur_t['btn_grad']};
        --tab-hover: {cur_t['tab_hover']};
        --row-hover: {cur_t['row_hover']};
        --focus-ring: {cur_t['focus_ring']};
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --border-hover: #cbd5e1;
        --shadow-card: 0 8px 24px rgba(20, 27, 62, 0.05);
        --shadow-header: {cur_t['shadow_header']};
        --shadow-btn: {cur_t['shadow_btn']};

        /* ألوان دلالية ثابتة عالية التباين لأنماط التعلم الثلاثة لا تتداخل مع أي قالب */
        --vak-v-main: #2563eb;
        --vak-v-light: #60a5fa;
        --vak-v-bg: #eff6ff;
        --vak-v-border: #bfdbfe;

        --vak-k-main: #059669;
        --vak-k-light: #34d399;
        --vak-k-bg: #ecfdf5;
        --vak-k-border: #a7f3d0;

        --vak-a-main: #d97706;
        --vak-a-light: #fbbf24;
        --vak-a-bg: #fffbeb;
        --vak-a-border: #fde68a;
    }}

    /* ========================================================
       2. ضبط الاتجاه العام (RTL) والخلفية والخطوط
       ======================================================== */
    :root, html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .stApp {{
        --text-color: #0f172a !important;
        --background-color: var(--bg-page) !important;
        --secondary-background-color: #ffffff !important;
        --primary-color: var(--brand-royal) !important;
        color-scheme: light only !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        background-color: var(--bg-page) !important;
        color: #0f172a !important;
        transition: background-color 0.35s ease;
    }}

    header[data-testid="stHeader"] {{ display: none !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    .block-container {{
        max-width: 1020px !important;
        padding-top: 1.6rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        direction: rtl !important;
    }}

    .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, div,
    .stRadio, .stSelectbox, .stMultiSelect, .stTextInput, .stCheckbox {{
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }}

    /* ========================================================
       3. الهيدر الموحد لمنصة زياد الذكية (يتغير ديناميكياً مع القالب)
       ======================================================== */
    .ziyad-hero-banner {{
        background: var(--hero-grad);
        border-radius: 24px;
        padding: 26px 24px 22px 24px;
        margin-bottom: 16px;
        box-shadow: inset 0 2px 4px rgba(255,255,255,0.35), var(--shadow-header);
        position: relative;
        overflow: hidden;
        border: 1.5px solid rgba(255, 255, 255, 0.22);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 10px;
        transition: all 0.35s ease;
        direction: rtl !important;
        text-align: center !important;
    }}

    .ziyad-hero-banner::before {{
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }}
    .ziyad-hero-banner::after {{
        content: "";
        position: absolute;
        bottom: -70px;
        left: -50px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }}

    .unified-title-row {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        flex-wrap: wrap;
        z-index: 2;
        direction: rtl !important;
    }}

    .unified-main-title {{
        font-family: 'Cairo', sans-serif !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.25 !important;
        letter-spacing: 0px !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.22);
        text-align: center !important;
    }}

    .unified-brand-row {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        z-index: 2;
        direction: rtl !important;
    }}

    .unified-brand-pill {{
        font-family: 'Cairo', sans-serif !important;
        background: rgba(15, 23, 42, 0.34);
        border: 1px solid rgba(255, 255, 255, 0.26);
        box-shadow: inset 0 1px 2px rgba(255,255,255,0.18);
        padding: 5px 18px;
        border-radius: 999px;
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #fde68a !important;
        -webkit-text-fill-color: #fde68a !important;
        white-space: nowrap;
        backdrop-filter: blur(4px);
        text-decoration: none !important;
        transition: all 0.2s ease;
    }}
    a.unified-brand-pill:hover {{
        background: rgba(15, 23, 42, 0.55);
        border-color: var(--brand-gold);
        transform: translateY(-1px);
    }}

    .unified-sub-desc {{
        font-family: 'Cairo', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        color: rgba(255, 255, 255, 0.92) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.92) !important;
        margin: 0 !important;
        line-height: 1.5 !important;
        z-index: 2;
        text-align: center !important;
    }}

    /* ========================================================
       4. شريط اختيار القالب الديناميكي داخل شاشة مدير النظام فقط
       ======================================================== */
    .admin-theme-box {{
        background-color: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 12px 16px 6px 16px;
        margin-bottom: 14px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.03);
    }}
    .theme-switcher-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        flex-wrap: wrap;
        gap: 6px;
    }}
    .theme-switcher-label {{
        font-size: 13px;
        font-weight: 800;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .theme-active-badge {{
        font-size: 11.5px;
        font-weight: 700;
        color: var(--brand-royal) !important;
        -webkit-text-fill-color: var(--brand-royal) !important;
        background: var(--tab-hover);
        border: 1px solid var(--border-color);
        padding: 3px 12px;
        border-radius: 999px;
    }}

    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-thm_"]) {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        margin-bottom: 12px !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-thm_"]) > div {{
        flex: 1 1 calc(25% - 8px) !important;
        min-width: 125px !important;
    }}

    div[class*="st-key-thm_"] button {{
        min-height: 38px !important;
        padding: 5px 10px !important;
        border-radius: 999px !important;
        font-size: 12.5px !important;
        transition: all 0.25s ease !important;
    }}
    div[class*="st-key-thm_active_"] button {{
        background: var(--btn-grad) !important;
        border: 2px solid var(--brand-gold) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        box-shadow: var(--shadow-btn) !important;
        transform: translateY(-1px);
    }}
    div[class*="st-key-thm_active_"] button * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 12.5px !important;
    }}
    div[class*="st-key-thm_idle_"] button {{
        background-color: #ffffff !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
    }}
    div[class*="st-key-thm_idle_"] button:hover {{
        border-color: var(--brand-bright) !important;
        background-color: var(--tab-hover) !important;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
    }}

    /* ========================================================
       5. شريط البوابات والتبويبات الموحد (بلون القالب والإطار الذهبي)
       ======================================================== */
    .portal-Mode-strip {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 10px;
        border-bottom: 1.5px solid var(--border-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
        overflow-x: auto;
    }}
    .portal-pill-active {{
        background: var(--brand-navy);
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 2px solid var(--brand-gold);
        border-radius: 12px;
        padding: 7px 16px;
        font-size: 13.5px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: var(--shadow-btn);
        white-space: nowrap;
    }}
    .portal-pill-muted {{
        color: var(--text-muted) !important;
        -webkit-text-fill-color: var(--text-muted) !important;
        padding: 7px 12px;
        font-size: 13px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        white-space: nowrap;
        text-decoration: none !important;
    }}
    a.portal-pill-muted:hover {{
        color: var(--brand-royal) !important;
        -webkit-text-fill-color: var(--brand-royal) !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
        border-bottom: 1.5px solid var(--border-color);
        padding-bottom: 10px;
        gap: 10px;
        justify-content: flex-start;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border: 1.5px solid transparent !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--tab-hover) !important;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
    }}
    .stTabs [data-baseweb="tab"] * {{
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: var(--brand-navy) !important;
        border: 2px solid var(--brand-gold) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        box-shadow: var(--shadow-btn) !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}

    /* ========================================================
       6. بطاقة تسجيل الدخول والحاويات البيضاء الفاخرة
       ======================================================== */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 22px 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 18px !important;
    }}

    .card-section-title {{
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        margin: 0 0 6px 0 !important;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
        text-align: right !important;
    }}
    .card-section-sub {{
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        margin: 0 0 14px 0 !important;
        text-align: right !important;
        line-height: 1.5;
    }}

    /* تنسيق حقول الإدخال والقوائم المنسدلة (تباين كامل في الوضع الفاتح والداكن + RTL 100%) */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        color-scheme: light !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        min-height: 46px !important;
        direction: rtl !important;
        text-align: right !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] input,
    input, textarea, select {{
        background-color: transparent !important;
        padding: 10px 14px !important;
        font-size: 14.5px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: var(--brand-bright) !important;
        direction: rtl !important;
        text-align: right !important;
        opacity: 1 !important;
    }}
    input::placeholder,
    textarea::placeholder,
    div[data-baseweb="input"] input::placeholder {{
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
        direction: rtl !important;
        text-align: right !important;
        font-weight: 600 !important;
    }}
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--brand-bright) !important;
        box-shadow: 0 0 0 3px var(--focus-ring) !important;
        background-color: #ffffff !important;
    }}

    div[data-baseweb="select"],
    div[data-baseweb="select"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"],
    ul[role="listbox"],
    div[role="listbox"] {{
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }}
    div[data-baseweb="select"] svg,
    div[data-baseweb="input"] svg {{
        fill: #0f172a !important;
        color: #0f172a !important;
    }}
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[role="listbox"],
    div[role="listbox"] {{
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.2) !important;
    }}
    li[role="option"],
    div[role="option"],
    ul[role="listbox"] li {{
        direction: rtl !important;
        text-align: right !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        align-items: center !important;
        width: 100% !important;
        padding: 10px 16px !important;
        font-size: 14px !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }}
    li[role="option"]:hover,
    div[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[role="option"][aria-selected="true"] {{
        background-color: var(--tab-hover) !important;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
    }}
    li[role="option"] > div,
    li[role="option"] span,
    div[role="option"] > div,
    div[role="option"] span {{
        direction: rtl !important;
        text-align: right !important;
        width: 100% !important;
        display: block !important;
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
    }}
    div[data-baseweb="select"] div[value],
    div[data-baseweb="select"] > div > div:first-child {{
        direction: rtl !important;
        text-align: right !important;
        justify-content: flex-start !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }}
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label {{
        width: 100% !important;
        text-align: right !important;
        justify-content: flex-start !important;
        display: block !important;
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        margin-bottom: 6px !important;
    }}

    /* ========================================================
       7. الأزرار الموحدة (تتكيف مع تدرج القالب المختار)
       ======================================================== */
    div[class*="st-key-btn_login"] button,
    div[class*="st-key-rep_active"] button,
    div[class*="st-key-btn_save_perm"] button,
    div[data-testid="stDownloadButton"] button {{
        background: var(--btn-grad) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        padding: 11px 18px !important;
        min-height: 46px !important;
        box-shadow: var(--shadow-btn) !important;
        transition: all 0.25s ease !important;
    }}
    div[class*="st-key-btn_login"] button:hover,
    div[class*="st-key-rep_active"] button:hover,
    div[class*="st-key-btn_save_perm"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {{
        transform: translateY(-1px) !important;
        filter: brightness(1.08);
    }}
    div[class*="st-key-btn_login"] button *,
    div[class*="st-key-rep_active"] button *,
    div[class*="st-key-btn_save_perm"] button *,
    div[data-testid="stDownloadButton"] button * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }}

    /* تمييز زر التقرير النشط بإطار ذهبي مطابق للهوية */
    div[class*="st-key-rep_active"] button {{
        border: 2px solid var(--brand-gold) !important;
    }}

    /* الأزرار الثانوية القياسية */
    button[kind="secondary"] {{
        background-color: #ffffff !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-weight: 700 !important;
        min-height: 44px !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.2s ease !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: var(--brand-bright) !important;
        background-color: var(--tab-hover) !important;
    }}
    button[kind="secondary"] * {{
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }}

    /* زر تسجيل الخروج (Primary = أحمر ناعم أنيق) */
    button[kind="primary"] {{
        background-color: #fff1f2 !important;
        color: #e11d48 !important;
        -webkit-text-fill-color: #e11d48 !important;
        border: 1.5px solid #fecdd3 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        min-height: 44px !important;
    }}
    button[kind="primary"]:hover {{
        background-color: #ffe4e6 !important;
        border-color: #fda4af !important;
    }}
    button[kind="primary"] * {{
        color: #e11d48 !important;
        -webkit-text-fill-color: #e11d48 !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }}

    div[data-testid="stButton"] button p {{
        font-size: 13.5px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

    /* ========================================================
       8. لوحة الترحيب وبطاقات الإحصائيات (KPI Cards)
       ======================================================== */
    .welcome-banner-card {{
        background: linear-gradient(135deg, #ffffff 0%, var(--bg-input) 100%) !important;
        border: 1px solid var(--border-color);
        border-right: 5px solid var(--brand-royal);
        border-radius: 14px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(20, 27, 62, 0.04);
        margin-bottom: 10px;
    }}
    .welcome-user-info {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}
    .welcome-user-name {{
        font-size: 16px;
        font-weight: 800;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
    }}
    .welcome-user-scope {{
        font-size: 12.5px;
        font-weight: 700;
        color: var(--brand-bright) !important;
        -webkit-text-fill-color: var(--brand-bright) !important;
    }}

    .dashboard-stats-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin: 14px 0 22px 0;
        direction: rtl !important;
    }}
    .dash-card {{
        padding: 16px 14px;
        border-radius: 14px;
        text-align: center;
        background-color: #ffffff !important;
        box-shadow: var(--shadow-card);
        border: 1px solid var(--border-color);
        border-top: 4px solid;
        transition: transform 0.2s ease;
    }}
    .dash-card:hover {{ transform: translateY(-2px); }}
    .dash-card.total {{ border-top-color: var(--brand-royal); }}
    .dash-card.completed {{ border-top-color: #10b981; }}
    .dash-card.pending {{ border-top-color: var(--brand-gold); }}
    .dash-title {{
        font-size: 13px;
        margin-bottom: 6px;
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-weight: 700;
    }}
    .dash-value {{
        font-size: 26px;
        font-weight: 800;
        color: var(--brand-dark) !important;
        -webkit-text-fill-color: var(--brand-dark) !important;
        line-height: 1.1;
    }}

    /* ========================================================
       9. تصميم الجداول المخصصة (RTL) + لوحة توزيع أنماط التعلم (VAK) الاحترافية
       ======================================================== */
    .rtl-table-wrapper {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        max-height: 460px;
        overflow-y: auto;
        direction: rtl !important;
        border: 1px solid var(--border-color);
        border-radius: 14px;
        margin: 14px 0 18px 0;
        box-shadow: var(--shadow-card);
        background-color: #ffffff !important;
    }}
    table.custom-rtl-table {{
        width: 100% !important;
        border-collapse: collapse !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        font-size: 14px !important;
        background-color: #ffffff !important;
        color: var(--text-primary) !important;
        margin: 0 !important;
    }}
    table.custom-rtl-table thead th {{
        position: sticky;
        top: 0;
        z-index: 2;
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
        font-weight: 800 !important;
        padding: 12px 14px !important;
        border-bottom: 2px solid var(--border-hover) !important;
        border-left: 1px solid var(--border-color) !important;
        text-align: center !important;
        white-space: nowrap;
    }}
    table.custom-rtl-table tbody td {{
        padding: 10px 14px !important;
        border-bottom: 1px solid var(--border-color) !important;
        border-left: 1px solid #f1f5f9 !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        text-align: center !important;
        white-space: nowrap;
    }}
    table.custom-rtl-table tbody td.name-cell {{
        text-align: right !important;
        font-weight: 700 !important;
        color: var(--brand-dark) !important;
        -webkit-text-fill-color: var(--brand-dark) !important;
    }}
    table.custom-rtl-table tbody tr:nth-child(even) {{
        background-color: #f8fafc !important;
    }}
    table.custom-rtl-table tbody tr:hover {{
        background-color: var(--row-hover) !important;
    }}

    /* 💡 التصميم الاحترافي الجديد لتوزيع أنماط التعلم (ألوان دلالية ثابتة ومستقلة عن القالب) */
    .vak-summary-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin: 14px 0 22px 0;
        direction: rtl !important;
    }}
    .vak-stat-box {{
        border-radius: 16px;
        padding: 16px 14px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .vak-stat-box:hover {{
        transform: translateY(-3px);
    }}
    .vak-stat-box.visual {{
        background: linear-gradient(145deg, #ffffff 0%, #eff6ff 100%);
        border: 1.5px solid #bfdbfe;
        border-right: 5px solid #2563eb;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.08);
    }}
    .vak-stat-box.kinesthetic {{
        background: linear-gradient(145deg, #ffffff 0%, #ecfdf5 100%);
        border: 1.5px solid #a7f3d0;
        border-right: 5px solid #059669;
        box-shadow: 0 6px 18px rgba(5, 150, 105, 0.08);
    }}
    .vak-stat-box.auditory {{
        background: linear-gradient(145deg, #ffffff 0%, #fffbeb 100%);
        border: 1.5px solid #fde68a;
        border-right: 5px solid #d97706;
        box-shadow: 0 6px 18px rgba(217, 119, 6, 0.08);
    }}
    .vak-box-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }}
    .vak-box-label {{
        font-size: 15px;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .vak-stat-box.visual .vak-box-label {{ color: #1d4ed8 !important; -webkit-text-fill-color: #1d4ed8 !important; }}
    .vak-stat-box.kinesthetic .vak-box-label {{ color: #047857 !important; -webkit-text-fill-color: #047857 !important; }}
    .vak-stat-box.auditory .vak-box-label {{ color: #b45309 !important; -webkit-text-fill-color: #b45309 !important; }}

    .vak-pct-pill {{
        font-size: 12px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 999px;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    .vak-stat-box.visual .vak-pct-pill {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); }}
    .vak-stat-box.kinesthetic .vak-pct-pill {{ background: linear-gradient(135deg, #10b981, #047857); }}
    .vak-stat-box.auditory .vak-pct-pill {{ background: linear-gradient(135deg, #f59e0b, #b45309); }}

    .vak-box-number {{
        font-size: 28px;
        font-weight: 800;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        line-height: 1.1;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }}
    .vak-box-unit {{
        font-size: 12.5px;
        font-weight: 700;
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }}
    .vak-mini-track {{
        width: 100%;
        height: 8px;
        background-color: rgba(148, 163, 184, 0.2);
        border-radius: 999px;
        overflow: hidden;
    }}
    .vak-mini-fill {{
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s ease;
    }}
    .vak-stat-box.visual .vak-mini-fill {{ background: linear-gradient(90deg, #60a5fa, #2563eb); }}
    .vak-stat-box.kinesthetic .vak-mini-fill {{ background: linear-gradient(90deg, #34d399, #059669); }}
    .vak-stat-box.auditory .vak-mini-fill {{ background: linear-gradient(90deg, #fbbf24, #d97706); }}

    /* أعمدة المقارنة البصرية الثلاثية */
    .custom-chart-container {{
        display: flex;
        justify-content: space-around;
        align-items: flex-end;
        height: 220px;
        padding: 28px 16px 14px 16px;
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid var(--border-color);
        border-bottom: 2px solid #cbd5e1;
        border-radius: 16px;
        margin-top: 8px;
        position: relative;
    }}
    .chart-bar-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        height: 100%;
        width: 28%;
        max-width: 125px;
    }}
    .chart-value-badge {{
        font-weight: 800;
        font-size: 13.5px;
        margin-bottom: 8px;
        padding: 3px 12px;
        border-radius: 999px;
        white-space: nowrap;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .chart-value-badge.v-badge {{
        background-color: #eff6ff;
        color: #1d4ed8 !important;
        -webkit-text-fill-color: #1d4ed8 !important;
        border: 1px solid #bfdbfe;
    }}
    .chart-value-badge.k-badge {{
        background-color: #ecfdf5;
        color: #047857 !important;
        -webkit-text-fill-color: #047857 !important;
        border: 1px solid #a7f3d0;
    }}
    .chart-value-badge.a-badge {{
        background-color: #fffbeb;
        color: #b45309 !important;
        -webkit-text-fill-color: #b45309 !important;
        border: 1px solid #fde68a;
    }}
    .chart-bar {{
        width: 100%;
        border-radius: 12px 12px 4px 4px;
        transition: height 0.55s ease;
        min-height: 10px;
    }}
    .chart-bar.v-bar {{
        background: linear-gradient(180deg, #60a5fa 0%, #2563eb 65%, #1d4ed8 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.28);
    }}
    .chart-bar.k-bar {{
        background: linear-gradient(180deg, #34d399 0%, #059669 65%, #047857 100%);
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.28);
    }}
    .chart-bar.a-bar {{
        background: linear-gradient(180deg, #fbbf24 0%, #d97706 65%, #b45309 100%);
        box-shadow: 0 6px 16px rgba(217, 119, 6, 0.28);
    }}
    .chart-label {{
        margin-top: 12px;
        font-weight: 800;
        font-size: 14px;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        text-align: center;
        white-space: nowrap;
    }}

    /* ========================================================
       10. التذييل الموحد وبطاقات التواصل المباشرة (بدون إظهار الأرقام)
       ======================================================== */
    .ziyad-footer-wrap {{
        margin-top: 44px;
        padding-top: 22px;
        border-top: 1.5px solid var(--border-color);
        text-align: center;
    }}
    .ziyad-footer-copy {{
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 16px;
    }}
    .ziyad-footer-cards {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        direction: rtl;
    }}
    a.ziyad-footer-btn {{
        background-color: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 13px 12px;
        color: var(--brand-navy) !important;
        -webkit-text-fill-color: var(--brand-navy) !important;
        text-decoration: none !important;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: 13.5px;
        font-weight: 800;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
        transition: all 0.22s ease;
    }}
    a.ziyad-footer-btn:hover {{
        border-color: var(--brand-bright);
        background-color: var(--tab-hover);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }}

    /* ========================================================
       11. التوافق الكامل مع الجوال والشاشات الصغيرة (Mobile-First)
       ======================================================== */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-rep_"]) {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-rep_"]) > div {{
        width: calc(50% - 4px) !important;
        flex: 1 1 calc(50% - 4px) !important;
        min-width: 0 !important;
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 0.8rem !important;
            padding-left: 0.7rem !important;
            padding-right: 0.7rem !important;
            padding-bottom: 2rem !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-thm_"]) > div {{
            width: calc(50% - 4px) !important;
            flex: 1 1 calc(50% - 4px) !important;
            min-width: 0 !important;
        }}
        div[class*="st-key-thm_"] button {{
            min-height: 36px !important;
            padding: 4px 8px !important;
        }}
        div[class*="st-key-thm_"] button p {{
            font-size: 11.5px !important;
        }}
        .ziyad-hero-banner {{
            padding: 20px 14px 18px 14px !important;
            border-radius: 20px !important;
            gap: 8px;
        }}
        .unified-main-title {{
            font-size: 22px !important;
        }}
        .unified-brand-pill {{
            font-size: 13.5px !important;
            padding: 4px 14px !important;
        }}
        .unified-sub-desc {{
            font-size: 12.5px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 16px 14px !important;
            border-radius: 14px !important;
        }}
        .dashboard-stats-container {{
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }}
        .dash-card {{
            padding: 10px 6px;
            border-radius: 10px;
        }}
        .dash-title {{
            font-size: 11px;
        }}
        .dash-value {{
            font-size: 20px;
        }}
        /* بطاقات أنماط التعلم الثلاث متجاوبة على الجوال */
        .vak-summary-grid {{
            grid-template-columns: 1fr;
            gap: 10px;
        }}
        .vak-stat-box {{
            padding: 12px 14px;
        }}
        .vak-box-number {{
            font-size: 22px;
        }}
        .chart-value-badge {{
            font-size: 11.5px;
            padding: 2px 8px;
        }}
        .chart-label {{
            font-size: 12.5px;
        }}
        .stTabs [data-baseweb="tab"] {{
            padding: 6px 11px !important;
            border-radius: 10px !important;
        }}
        .stTabs [data-baseweb="tab"] * {{
            font-size: 12.5px !important;
        }}
        div[data-testid="stButton"] button p {{
            font-size: 12.5px !important;
        }}
        table.custom-rtl-table {{
            font-size: 12.5px !important;
        }}
        table.custom-rtl-table thead th,
        table.custom-rtl-table tbody td {{
            padding: 8px 8px !important;
        }}
        .ziyad-footer-cards {{
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        a.ziyad-footer-btn {{
            padding: 11px 8px;
            font-size: 12.5px;
            border-radius: 11px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# رسم الهيدر الموحد لمنصة زياد الذكية في أعلى الصفحة مباشرة
ZIYAD_LOGO_SVG = '<svg width="56" height="56" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;"><rect width="64" height="64" rx="18" fill="white" fill-opacity="0.16"/><rect x="1.5" y="1.5" width="61" height="61" rx="16.5" stroke="white" stroke-opacity="0.38" stroke-width="2"/><path d="M32 14L12 24L32 34L52 24L32 14Z" fill="#FBBF24"/><path d="M20 29V41C20 44.5 25.5 48 32 48C38.5 48 44 44.5 44 41V29L32 35L20 29Z" fill="white"/><path d="M48 26V40" stroke="#FBBF24" stroke-width="3" stroke-linecap="round"/></svg>'
st.markdown(f"""
<div class="ziyad-hero-banner" dir="rtl">
    <div class="unified-title-row">
        {ZIYAD_LOGO_SVG}
        <h1 class="unified-main-title">بوابة اختبار أنماط التعلم (VAK)</h1>
    </div>
    <div class="unified-brand-row">
        <a href="https://zi-edu.streamlit.app" target="_blank" rel="noopener noreferrer" class="unified-brand-pill">منصة زياد الذكية</a>
    </div>
    <div class="unified-sub-desc">البصري • السمعي • الحركي</div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
(function() {
    try {
        var pDoc = window.parent.document;
        pDoc.documentElement.setAttribute('dir', 'rtl');
        pDoc.body.setAttribute('dir', 'rtl');
        pDoc.documentElement.style.setProperty('color-scheme', 'light only', 'important');

        function enforceLightInputs() {
            var inputBoxes = pDoc.querySelectorAll('[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], [data-baseweb="select"], [data-baseweb="select"] > div');
            inputBoxes.forEach(function(box) {
                box.style.setProperty('background-color', '#ffffff', 'important');
                box.style.setProperty('background', '#ffffff', 'important');
                box.style.setProperty('color', '#0f172a', 'important');
                box.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
                var innerEls = box.querySelectorAll('div, span, input, textarea');
                innerEls.forEach(function(inn) {
                    if (!inn.closest('[data-baseweb="tag"]')) {
                        inn.style.setProperty('color', '#0f172a', 'important');
                        inn.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
                        if (inn.tagName === 'INPUT' || inn.tagName === 'TEXTAREA') {
                            inn.style.setProperty('background-color', '#ffffff', 'important');
                        } else {
                            inn.style.setProperty('background-color', 'transparent', 'important');
                        }
                    }
                });
                var svgs = box.querySelectorAll('svg');
                svgs.forEach(function(s) {
                    s.style.setProperty('fill', '#0f172a', 'important');
                    s.style.setProperty('color', '#0f172a', 'important');
                });
            });

            var popovers = pDoc.querySelectorAll('[data-baseweb="popover"], [data-baseweb="menu"], [data-testid="stSelectboxVirtualDropdown"], ul[role="listbox"], li[role="option"], div[role="option"]');
            popovers.forEach(function(el) {
                el.setAttribute('dir', 'rtl');
                el.style.setProperty('direction', 'rtl', 'important');
                el.style.setProperty('text-align', 'right', 'important');
                el.style.setProperty('background-color', '#ffffff', 'important');
                el.style.setProperty('color', '#0f172a', 'important');
                var chs = el.querySelectorAll('div, span');
                chs.forEach(function(ch) {
                    ch.setAttribute('dir', 'rtl');
                    ch.style.setProperty('direction', 'rtl', 'important');
                    ch.style.setProperty('text-align', 'right', 'important');
                    ch.style.setProperty('color', '#0f172a', 'important');
                    ch.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
                });
            });
        }

        enforceLightInputs();
        if (!window.parent.__ziyadVakLightObserver) {
            var obs = new MutationObserver(function() {
                enforceLightInputs();
            });
            obs.observe(pDoc.body, { childList: true, subtree: true });
            window.parent.__ziyadVakLightObserver = true;
        }
    } catch (e) {}
})();
</script>
""", height=0)

# ==========================================
# 💡 دالة عرض الجداول من اليمين إلى اليسار (RTL) بدلاً من st.dataframe اليساري
# ==========================================
def render_rtl_table(df):
    """عرض أي جدول بيانات على الشاشة باتجاه عربي أصيل من اليمين إلى اليسار (م -> الرقم -> الاسم -> الفصل -> النمط)"""
    if df.empty:
        return
    headers_html = "".join([f"<th>{col}</th>" for col in df.columns])
    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for col in df.columns:
            val = row[col]
            cls_attr = ' class="name-cell"' if col in ['الاسم', 'اسم الطالب', 'اسم المعلم'] else ''
            cells += f"<td{cls_attr}>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"
    table_html = f'<div class="rtl-table-wrapper"><table class="custom-rtl-table"><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)

# ==========================================
# 💡 دوال صلاحيات المعلمين والفلترة الذكية للفصول
# ==========================================
def parse_teacher_classes(class_name_str):
    """تحويل نص الفصول المخصص للمعلم إلى قائمة فصول أو 'all'"""
    if pd.isna(class_name_str):
        return 'all'
    raw = str(class_name_str).strip()
    if not raw or raw.lower() in ['all', 'الكل', 'جميع الفصول', 'nan', 'none']:
        return 'all'
    classes = [c.strip() for c in raw.replace('،', ',').split(',') if c.strip()]
    return classes if classes else 'all'

def filter_df_for_user(df_source, user):
    """تصفية بيانات الطلاب حسب الفصول المسندة للمعلم"""
    if not user or user.get('role') == 'admin':
        return df_source.copy()
    allowed = parse_teacher_classes(user.get('class_name', 'all'))
    if allowed == 'all':
        return df_source.copy()
    return df_source[df_source['class_name'].isin(allowed)].copy()

def infer_grade_name(row):
    g = str(row.get('grade', '')).strip()
    c = str(row.get('class_name', '')).strip()
    if g and g not in ['nan', 'None', '']:
        return g
    if '/' in c:
        return c.split('/')[0].strip()
    return c if c else "غير محدد"

def render_grade_class_Selector(df_source, key_prefix):
    """عرض قوائم اختيار الصف والفصل بشكل مرتب ومتجاوب من اليمين إلى اليسار"""
    df_temp = df_source.copy()
    if df_temp.empty:
        st.warning("⚠️ لا توجد فصول أو بيانات طلاب متاحة في نطاق صلاحياتك.")
        return df_temp, "غير محدد"

    df_temp['_grade_group'] = df_temp.apply(infer_grade_name, axis=1)
    unique_grades = sorted([g for g in df_temp['_grade_group'].unique() if g])
    
    grade_options = ["جميع الصفوف المتاحة"] + unique_grades if len(unique_grades) > 1 else unique_grades
    
    col_g, col_c = st.columns(2)
    with col_g:
        selected_grade = st.selectbox("1️⃣ اختر الصف / المرحلة:", grade_options, key=f"{key_prefix}_grade")
    
    if selected_grade != "جميع الصفوف المتاحة":
        df_filtered_grade = df_temp[df_temp['_grade_group'] == selected_grade].copy()
    else:
        df_filtered_grade = df_temp.copy()
        
    unique_classes = sorted([c for c in df_filtered_grade['class_name'].unique() if c])
    class_options = ["جميع الفصول المتاحة"] + unique_classes if len(unique_classes) > 1 else unique_classes
    with col_c:
        selected_class = st.selectbox("2️⃣ اختر الفصل:", class_options, key=f"{key_prefix}_class")
        
    if selected_class != "جميع الفصول المتاحة":
        df_final = df_filtered_grade[df_filtered_grade['class_name'] == selected_class].copy()
        scope_label = f"فصل {selected_class}"
    elif selected_grade != "جميع الصفوف المتاحة":
        df_final = df_filtered_grade.copy()
        scope_label = f"صف {selected_grade}"
    else:
        df_final = df_filtered_grade.copy()
        scope_label = "جميع الفصول المخصصة"
        
    return df_final.drop(columns=['_grade_group'], errors='ignore'), scope_label

# ==========================================
# 💡 دوال الاستيراد الذكي للطلاب والمعلمين وقالب أنماط التعلم
# ==========================================
def normalize_vak_label(val, v_val="0", a_val="0", k_val="0"):
    """توحيد صيغة النمط الغالب أو حسابه تلقائياً من الدرجات"""
    s = str(val).strip() if not pd.isna(val) else ""
    if "بصري" in s or s.upper() == "V": return "بصري 👁️"
    if "سمعي" in s or s.upper() == "A": return "سمعي 👂"
    if "حركي" in s or s.upper() == "K": return "حركي 🏃‍♂️"
    
    try:
        v = float(str(v_val).strip() or 0)
        a = float(str(a_val).strip() or 0)
        k = float(str(k_val).strip() or 0)
        if (v + a + k) > 0:
            scores = {"V": v, "A": a, "K": k}
            labels = {"V": "بصري 👁️", "A": "سمعي 👂", "K": "حركي 🏃‍♂️"}
            return labels[max(scores, key=scores.get)]
    except:
        pass
    return "غير مختبر"

def standardize_uploaded_columns(df):
    """دعم أسماء الأعمدة بالإنجليزية أو العربية في ملفات الاستيراد"""
    col_map = {
        'رقم الهوية': 'id', 'الهوية': 'id', 'الرقم': 'id',
        'الاسم': 'name', 'اسم الطالب': 'name', 'اسم المعلم': 'name',
        'الصف': 'grade', 'المرحلة': 'grade',
        'الفصل': 'class_name', 'نطاق الفصول': 'class_name', 'الفصول': 'class_name',
        'الصلاحية': 'role',
        'النمط الغالب': 'vak_result', 'النتيجة الغالبة': 'vak_result', 'نمط التعلم': 'vak_result', 'النمط': 'vak_result',
        'بصري': 'v_score', 'درجة البصري': 'v_score',
        'سمعي': 'a_score', 'درجة السمعي': 'a_score',
        'حركي': 'k_score', 'درجة الحركي': 'k_score'
    }
    return df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

def intelligent_merge_students_and_vak(new_df):
    """دمج الطلاب الجدد وتحديث أنماط التعلم والدرجات للطلاب الحاليين أو الجدد بدون أي تكرار"""
    new_df = standardize_uploaded_columns(new_df.copy())
    if 'id' not in new_df.columns:
        return 0, 0, False
        
    current_df = get_all_students().copy()
    current_df['id'] = current_df['id'].apply(clean_id)
    new_df['id'] = new_df['id'].apply(clean_id)
    
    new_df = new_df[new_df['id'] != ""].drop_duplicates(subset=['id'], keep='last').copy()
    
    has_vak_cols = any(c in new_df.columns for c in ['vak_result', 'v_score', 'a_score', 'k_score'])
    added_count = 0
    updated_vak_count = 0
    
    for _, row in new_df.iterrows():
        s_id = row['id']
        mask = (current_df['id'] == s_id)
        if mask.any():
            for info_col in ['name', 'grade', 'class_name']:
                if info_col in new_df.columns and pd.notna(row.get(info_col)):
                    val_str = str(row.get(info_col)).strip()
                    if val_str and val_str not in ['nan', 'None']:
                        current_df.loc[mask, info_col] = val_str

            if has_vak_cols:
                v_sc = str(row.get('v_score', current_df.loc[mask, 'v_score'].iloc[0])).split('.')[0].strip() if 'v_score' in new_df.columns and pd.notna(row.get('v_score')) else current_df.loc[mask, 'v_score'].iloc[0]
                a_sc = str(row.get('a_score', current_df.loc[mask, 'a_score'].iloc[0])).split('.')[0].strip() if 'a_score' in new_df.columns and pd.notna(row.get('a_score')) else current_df.loc[mask, 'a_score'].iloc[0]
                k_sc = str(row.get('k_score', current_df.loc[mask, 'k_score'].iloc[0])).split('.')[0].strip() if 'k_score' in new_df.columns and pd.notna(row.get('k_score')) else current_df.loc[mask, 'k_score'].iloc[0]
                raw_res = row.get('vak_result', '') if 'vak_result' in new_df.columns else ''
                
                norm_res = normalize_vak_label(raw_res, v_sc, a_sc, k_sc)
                if norm_res != "غير مختبر":
                    current_df.loc[mask, 'vak_result'] = norm_res
                    current_df.loc[mask, 'v_score'] = v_sc if v_sc not in ['', 'nan', 'None'] else "0"
                    current_df.loc[mask, 'a_score'] = a_sc if a_sc not in ['', 'nan', 'None'] else "0"
                    current_df.loc[mask, 'k_score'] = k_sc if k_sc not in ['', 'nan', 'None'] else "0"
                    updated_vak_count += 1

    if all(col in new_df.columns for col in ['id', 'name', 'grade', 'class_name']):
        new_students = new_df[~new_df['id'].isin(current_df['id'])].copy()
        if not new_students.empty:
            for col in ['v_score', 'a_score', 'k_score']:
                if col not in new_students.columns:
                    new_students[col] = "0"
                else:
                    new_students[col] = new_students[col].fillna("0").astype(str).apply(lambda x: x.split('.')[0].strip() or "0")
            if 'vak_result' not in new_students.columns:
                new_students['vak_result'] = "غير مختبر"
            
            new_students['vak_result'] = new_students.apply(
                lambda r: normalize_vak_label(r.get('vak_result', ''), r.get('v_score', '0'), r.get('a_score', '0'), r.get('k_score', '0')),
                axis=1
            )
            cols_order = ['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score']
            current_df = pd.concat([current_df, new_students[cols_order]], ignore_index=True)
            added_count = len(new_students)

    if added_count > 0 or updated_vak_count > 0:
        conn = get_gsheets_conn()
        try: conn.update(spreadsheet=SHEET_URL, worksheet="df_students", data=current_df)
        except: conn.update(spreadsheet=SHEET_URL, data=current_df)
        clear_all_caches()
        
    return added_count, updated_vak_count, True

def intelligent_merge_teachers(new_df):
    new_df = standardize_uploaded_columns(new_df.copy())
    current_df = get_all_teachers().copy()
    current_df['id'] = current_df['id'].apply(clean_id)
    new_df['id'] = new_df['id'].apply(clean_id)
    new_df = new_df[new_df['id'] != ""].drop_duplicates(subset=['id'], keep='last').copy()
    
    new_teachers = new_df[~new_df['id'].isin(current_df['id'])].copy()
    if not new_teachers.empty:
        if 'role' not in new_teachers.columns:
            new_teachers['role'] = 'teacher'
        else:
            new_teachers['role'] = new_teachers['role'].fillna('teacher').replace('', 'teacher')
            
        if 'class_name' not in new_teachers.columns:
            new_teachers['class_name'] = 'all'
        else:
            new_teachers['class_name'] = new_teachers['class_name'].fillna('all').replace('', 'all')
            
        if 'theme' not in new_teachers.columns:
            new_teachers['theme'] = st.session_state.get('active_theme', 'royal')
            
        for col in ['role', 'class_name', 'theme']:
            if col not in current_df.columns:
                current_df[col] = ""
        updated_df = pd.concat([current_df, new_teachers[['id', 'name', 'role', 'class_name', 'theme']]], ignore_index=True)
        conn = get_gsheets_conn()
        conn.update(spreadsheet=SHEET_URL, worksheet="teachers", data=updated_df)
        clear_all_caches()
        return len(new_teachers)
    return 0

def update_teacher_permissions(teacher_id, new_role, new_classes_str):
    """تحديث صلاحية المعلم والفصول المسندة إليه مباشرة وبشكل فوري في Google Sheets"""
    conn = get_gsheets_conn()
    try:
        df_teachers = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", ttl=0, dtype=str)
    except:
        df_teachers = get_all_teachers().copy()

    for col in ['id', 'name', 'role', 'class_name']:
        if col not in df_teachers.columns:
            df_teachers[col] = ""
        df_teachers[col] = df_teachers[col].fillna("").astype(str).str.strip()

    df_teachers['id'] = df_teachers['id'].apply(clean_id)
    target_id = clean_id(teacher_id)
    mask = (df_teachers['id'] == target_id)
    
    if mask.any():
        df_teachers.loc[mask, 'role'] = new_role
        df_teachers.loc[mask, 'class_name'] = new_classes_str
        conn.update(spreadsheet=SHEET_URL, worksheet="teachers", data=df_teachers)
        clear_all_caches()
        return True
    return False

# ==========================================
# 3. محرك التصحيح الآلي
# ==========================================
def get_vak_style(answer):
    ans = str(answer).strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    if any(x in ans for x in ["فيديو", "السبوره", "الاحداث", "فيلم", "الاقلام", "التخطيط", "الرسم", "التلوين", "مصوره", "خريطه", "يشاهدني", "الفوضى", "حركه", "النهائي", "كيف يبدو", "شكله", "ملامح", "ابتسم", "تلمع", "الكلمه مكتوبه", "راسي"]): return 'V'
    if any(x in ans for x in ["استمع", "اردد", "شفتي", "مسموع", "تكرار", "تسجيل", "الاصدقاء", "للقصص", "القوانين", "بالكلام", "الاصوات", "الضجيج", "تحدث", "اسال", "يخبرني", "وصوته", "اضحك", "بحماس", "اتهجى", "حروف"]): return 'A'
    if any(x in ans for x in ["تجربه", "اتحرك", "بالملل", "المشي", "الحفظ", "الرياضه", "الركض", "تركيب", "يمسك", "يجربها", "الجلوس", "دون حركه", "القطع", "فورا", "فعلنا", "اين لعبنا", "سلمنا", "اقفز", "اصفق", "ورقه", "مرات"]): return 'K'
    return None

def sync_google_forms():
    conn = get_gsheets_conn()
    try:
        try: df_students_fresh = conn.read(spreadsheet=SHEET_URL, worksheet="df_students", ttl=0, dtype=str)
        except: df_students_fresh = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
        df_forms_fresh = conn.read(spreadsheet=SHEET_URL, worksheet="responses", ttl=0, dtype=str)
    except Exception as e:
        st.error("⚠️ خطأ في الاتصال أو لم يتم العثور على الأوراق.")
        return

    required_cols = ['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score']
    for col in required_cols:
        if col not in df_students_fresh.columns: df_students_fresh[col] = ""
    df_students_fresh['id'] = df_students_fresh['id'].apply(clean_id)
    
    id_col = None
    for col in df_forms_fresh.columns:
        if 'هوي' in str(col) or 'رقم' in str(col) or 'id' in str(col).lower():
            id_col = col
            break
            
    if not id_col:
        st.toast("⚠️ لم يتعرف النظام على عمود الهوية في النموذج.", icon="❌")
        return

    df_forms_fresh[id_col] = df_forms_fresh[id_col].apply(clean_id)
    updates_count = 0
    
    for _, row in df_forms_fresh.iterrows():
        s_id = row.get(id_col, '')
        if not s_id: continue
            
        mask = (df_students_fresh['id'] == s_id)
        if mask.any():
            v, a, k = 0, 0, 0
            for col in df_forms_fresh.columns:
                if col != id_col and not any(skip in str(col).lower() for skip in ['time', 'email', 'name', 'اسم', 'إيميل', 'تاريخ', 'طابع', 'score']):
                    style = get_vak_style(row[col])
                    if style == 'V': v += 1
                    elif style == 'A': a += 1
                    elif style == 'K': k += 1
            
            if (v + a + k) > 0:
                scores = {"V": v, "A": a, "K": k}
                labels = {"V": "بصري 👁️", "A": "سمعي 👂", "K": "حركي 🏃‍♂️"}
                final_result = labels[max(scores, key=scores.get)]
                
                df_students_fresh.loc[mask, 'vak_result'] = final_result
                df_students_fresh.loc[mask, 'v_score'] = str(v)
                df_students_fresh.loc[mask, 'a_score'] = str(a)
                df_students_fresh.loc[mask, 'k_score'] = str(k)
                updates_count += 1
                
    if updates_count > 0:
        try: conn.update(spreadsheet=SHEET_URL, worksheet="df_students", data=df_students_fresh)
        except: conn.update(spreadsheet=SHEET_URL, data=df_students_fresh)
        clear_all_caches()
        st.toast(f"تم استيراد وتحديث نتائج {updates_count} طالب بنجاح! 🎉", icon="✅")
        time.sleep(1) 
        st.rerun()
    else:
        st.toast("اكتمل الفحص ولم يتم رصد درجات جديدة.", icon="ℹ️")

# ==========================================
# 4. الترويسة الذكية وتوليد تقارير HTML والملفات (بألوان VAK الدلالية الثابتة)
# ==========================================
def add_serial_column(df):
    df_out = df.copy().reset_index(drop=True)
    df_out.insert(0, 'م', range(1, len(df_out) + 1))
    return df_out

def get_school_name(df_subset):
    text_to_search = " ".join(df_subset['grade'].fillna("").astype(str)) + " " + " ".join(df_subset['class_name'].fillna("").astype(str))
    if "ابتدائي" in text_to_search and "متوسط" in text_to_search: return "ابتدائية عبادة بن قيس الأنصاري<br>متوسطة عبدالرحمن الناصر"
    elif "متوسط" in text_to_search: return "متوسطة عبدالرحمن الناصر"
    else: return "ابتدائية عبادة بن قيس الأنصاري"

def generate_html_page(title, content, school_names_html):
    curr_user = st.session_state.get('current_user')
    if curr_user and curr_user.get('role') != 'admin':
        teacher_name_display = f"أ. {curr_user.get('name')}"
    else:
        teacher_name_display = "............................................."

    signature_html = f"""
    <div class="signature-section">
        <div class="sig-box">
            <div class="sig-title">معلم المادة / المختص</div>
            <div class="sig-line">الاسم: {teacher_name_display}</div>
            <div class="sig-line">التوقيع: .............................................</div>
        </div>
        <div class="sig-stamp">
            <div class="stamp-circle">الختم الرسمي</div>
        </div>
        <div class="sig-box">
            <div class="sig-title">يعتمد ،، مدير المدرسة</div>
            <div class="sig-line">الاسم: أ. عبدالمجيد الحربي</div>
            <div class="sig-line">التوقيع: .............................................</div>
        </div>
    </div>
    """

    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>{title}</title><style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap'); body {{ font-family: 'Cairo', sans-serif; margin: 0; padding: 20px; background: #fff; color: #000; direction: rtl; }} @page {{ margin: 15mm; }} thead {{ display: table-header-group; }} tfoot {{ display: table-footer-group; }} .official-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px double #000; padding-bottom: 10px; margin-bottom: 20px; font-weight: bold; }} .header-right {{ text-align: right; flex: 1; font-size: 13px; line-height: 1.5; }} .header-center {{ text-align: center; flex: 1; font-size: 16px; color: {cur_t['brand_navy']}; line-height: 1.3; }} .header-left {{ text-align: left; flex: 1; font-size: 13px; line-height: 1.5; }} .report-main-title {{ text-align: center; color: {cur_t['brand_navy']}; background-color: {cur_t['report_bg']}; border: 1px solid {cur_t['report_border']}; border-radius: 8px; padding: 10px; margin-bottom: 20px; font-size: 20px; font-weight: bold; }} table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; page-break-inside: auto; direction: rtl; }} tr {{ page-break-inside: avoid; page-break-after: auto; }} th, td {{ border: 1px solid #000; padding: 6px; text-align: center; }} th {{ background-color: #f2f2f2; font-weight: bold; }} td:first-child, th:first-child {{ width: 40px; font-weight: bold; background-color: #f4f6f7; }} tr:nth-child(even) {{ background-color: #f9f9f9; }} .summary-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #fafafa; font-size: 15px; }} .bar-bg {{ background-color: #e0e0e0; border-radius: 5px; width: 100%; height: 14px; margin-bottom: 8px; border: 1px solid #ccc; overflow: hidden; }} .bar-v {{ background-color: #2563eb; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .bar-a {{ background-color: #d97706; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .bar-k {{ background-color: #059669; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .stats-container {{ display: flex; justify-content: space-between; margin-top: 15px; gap: 10px; }} .stat-card {{ flex: 1; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #ccc; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }} .stat-card.visual {{ border-color: #2563eb; color: #1d4ed8; background-color: #eff6ff; }} .stat-card.auditory {{ border-color: #d97706; color: #b45309; background-color: #fffbeb; }} .stat-card.kinesthetic {{ border-color: #059669; color: #047857; background-color: #ecfdf5; }} .stat-title {{ font-size: 14px; margin-bottom: 5px; font-weight: bold; }} .stat-value {{ font-size: 18px; font-weight: bold; }} .signature-section {{ display: flex; justify-content: space-between; align-items: center; margin-top: 35px; padding-top: 15px; border-top: 1px dashed #ccc; page-break-inside: avoid; }} .sig-box {{ flex: 1; text-align: center; font-size: 14px; line-height: 2; }} .sig-title {{ font-weight: bold; font-size: 15px; color: {cur_t['brand_navy']}; margin-bottom: 5px; }} .sig-line {{ font-weight: bold; }} .sig-stamp {{ flex: 0.6; display: flex; justify-content: center; align-items: center; }} .stamp-circle {{ width: 85px; height: 85px; border: 2px dashed #bbb; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px; font-weight: bold; }} .no-print {{ text-align: center; margin-bottom: 15px; }} .print-btn {{ background: {cur_t['btn_grad']}; color: white; border: none; padding: 8px 18px; font-size: 14px; border-radius: 8px; cursor: pointer; font-family: 'Cairo', sans-serif; font-weight: bold; }} @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; margin: 0; }} .stat-card {{ box-shadow: none; }} .official-header {{ border-bottom: 2px solid #000; }} .header-center {{ color: #000; }} }}</style></head><body>
    <div class="no-print"><button class="print-btn" onclick="window.print()">🖨️ طباعة التقرير / حفظ PDF</button></div>
    <table style="width: 100%; border: none;"><thead style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0; background: none;">
    <div class="official-header"><div class="header-right">المملكة العربية السعودية<br>{school_names_html}</div><div class="header-center">وزارة التعليم<br><span style="font-size: 12px; font-weight: normal; color: #7f8c8d;">Ministry of Education</span></div><div class="header-left">العام الدراسي: 1448 هـ<br>تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}</div></div>
    </td></tr></thead><tbody style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0; text-align: right; font-weight: normal; background: none;"><div class="report-main-title">{title}</div>{content}{signature_html}</td></tr></tbody></table>
    </body></html>"""

def create_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# ==========================================
# 5. منطق تسجيل الدخول والواجهة الإدارية الموحدة
# ==========================================
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'active_report' not in st.session_state: st.session_state.active_report = "comp"

if st.session_state.current_user is None:
    # شريط البوابات العلوي المطابق لهوية المنصة
    st.markdown("""
    <div class="portal-Mode-strip">
        <span class="portal-pill-active">👨‍🏫 بوابة المعلمين والإدارة</span>
        <span class="portal-pill-muted">📊 تشخيص أنماط التعلم (VAK)</span>
        <a href="https://zi-edu.streamlit.app" target="_blank" rel="noopener noreferrer" class="portal-pill-muted">🌐 بوابة المنصة الرئيسية</a>
    </div>
    """, unsafe_allow_html=True)

    # بطاقة تسجيل الدخول البيضاء الفاخرة
    with st.container(border=True):
        st.markdown("""
        <div class="card-section-title">تسجيل دخول المعلمين والإدارة</div>
        <p class="card-section-sub">أدخل رقم الهوية لاستعراض الإحصائيات وطباعة تقارير أنماط التعلم المعتمدة للطلاب والفصول</p>
        """, unsafe_allow_html=True)
        
        teacher_id_input = st.text_input("رقم الهوية / السجل المدني", placeholder="أدخل الرقم هنا...", key="login_id_input")
        
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 دخول للمنصة", use_container_width=True, key="btn_login_submit"):
            if teacher_id_input:
                with st.spinner("جاري التحقق من الهوية..."):
                    try:
                        get_all_teachers.clear()
                        df_teachers = get_all_teachers()
                        norm_id = clean_id(teacher_id_input)
                        t_row = df_teachers[df_teachers['id'] == str(norm_id)]
                        if not t_row.empty:
                            t_data = t_row.iloc[0]
                            st.session_state.current_user = {
                                "id": t_data['id'],
                                "name": t_data['name'],
                                "role": t_data['role'],
                                "class_name": t_data.get('class_name', 'all')
                            }
                            st.rerun()
                        else:
                            st.error("رقم الهوية غير مسجل في قاعدة بيانات المعلمين. راجع إدارة المدرسة.")
                    except Exception as e:
                        st.error("⚠️ خطأ: لم يتم العثور على ورقة 'teachers' في Google Sheets.")
            else:
                st.warning("الرجاء إدخال رقم الهوية أولاً.")
else:
    df_teachers_latest = get_all_teachers()
    curr_u_id = clean_id(st.session_state.current_user.get('id', ''))
    if curr_u_id and not df_teachers_latest.empty:
        u_match = df_teachers_latest[df_teachers_latest['id'] == curr_u_id]
        if not u_match.empty:
            st.session_state.current_user['role'] = u_match.iloc[0]['role']
            st.session_state.current_user['class_name'] = u_match.iloc[0]['class_name']
            st.session_state.current_user['name'] = u_match.iloc[0]['name']

    user = st.session_state.current_user
    
    if user['role'] == 'admin':
        st.markdown(f"""
        <div class="welcome-banner-card">
            <div class="welcome-user-info">
                <div class="welcome-user-name">👋 مرحباً بك: {user["name"]}</div>
                <div class="welcome-user-scope">🛡️ الصلاحية: مدير النظام (وصول كامل لجميع الصفوف والفصول)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # شريط اختيار القوالب الديناميكية (يظهر فقط داخل شاشة مدير النظام)
        st.markdown(f"""
        <div class="admin-theme-box">
            <div class="theme-switcher-header">
                <span class="theme-switcher-label">🎨 تخصيص القالب البصري للمنصة:</span>
                <span class="theme-active-badge">{cur_t['name']} — {cur_t['desc']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        t_cols = st.columns(4)
        for idx, (t_key, t_info) in enumerate(THEMES.items()):
            with t_cols[idx]:
                is_curr_t = (active_theme_key == t_key)
                btn_t_key = f"thm_active_{t_key}" if is_curr_t else f"thm_idle_{t_key}"
                btn_t_lbl = f"✨ {t_info['name']}" if is_curr_t else t_info['name']
                if st.button(btn_t_lbl, key=btn_t_key, use_container_width=True):
                    if not is_curr_t:
                        with st.spinner("جاري تطبيق القالب البصري على المنصة..."):
                            save_platform_theme(t_key)
                            st.rerun()

        col_act1, col_act2, col_logout = st.columns([2, 2, 1.5])
        with col_act1:
            if st.button("📥 جلب وتصحيح النتائج", use_container_width=True, key="btn_sync_forms"):
                with st.spinner("جاري جلب وتصحيح الإجابات..."):
                    sync_google_forms()
        with col_act2:
            if st.button("🔄 تحديث البيانات", use_container_width=True, key="btn_refresh_admin"):
                clear_all_caches()
                st.rerun()
        with col_logout:
            if st.button("تسجيل الخروج", type="primary", use_container_width=True, key="logout"):
                st.session_state.current_user = None
                st.rerun()
                
    else:
        parsed_cls = parse_teacher_classes(user.get('class_name', 'all'))
        cls_badge = "جميع الفصول" if parsed_cls == 'all' else " ، ".join(parsed_cls)
        col_user, col_logout = st.columns([4, 1.2])
        with col_user:
            st.markdown(f"""
            <div class="welcome-banner-card" style="margin-bottom: 0;">
                <div class="welcome-user-info">
                    <div class="welcome-user-name">👋 مرحباً بك: أ. {user["name"]}</div>
                    <div class="welcome-user-scope">🏫 الفصول المسندة: {cls_badge}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_logout:
            if st.button("تسجيل الخروج", type="primary", use_container_width=True, key="logout"):
                st.session_state.current_user = None
                st.rerun()
            
    df_all_raw = get_all_students()
    df_all = filter_df_for_user(df_all_raw, user)

    df_tested = df_all[df_all['vak_result'] != 'غير مختبر'].copy()
    for col in ['v_score', 'a_score', 'k_score']:
        df_tested[col] = pd.to_numeric(df_tested[col], errors='coerce').fillna(0)

    total_students = len(df_all)
    completed_tests = len(df_tested)
    pending_tests = total_students - completed_tests
    
    st.markdown(f"""
    <div class="dashboard-stats-container">
        <div class="dash-card total"><div class="dash-title">👥 إجمالي الطلاب</div><div class="dash-value">{total_students}</div></div>
        <div class="dash-card completed"><div class="dash-title">✅ الاختبارات المكتملة</div><div class="dash-value">{completed_tests}</div></div>
        <div class="dash-card pending"><div class="dash-title">⏳ لم يؤدوا الاختبار</div><div class="dash-value">{pending_tests}</div></div>
    </div>
    """, unsafe_allow_html=True)

    if user['role'] == 'admin':
        tabs = st.tabs(["🏠 الرئيسية (الإحصائيات)", "📊 التقارير (طباعة)", "👥 إدارة البيانات والصلاحيات"])
        tab_main, tab_reports, tab_data = tabs
    else:
        tabs = st.tabs(["📊 التقارير (طباعة)"])
        tab_reports = tabs[0]
        tab_main, tab_data = None, None

    if tab_main is not None:
        with tab_main:
            with st.container(border=True):
                st.markdown("<div class='card-section-title' style='text-align: center !important;'>📊 توزيع أنماط التعلم في المدرسة</div>", unsafe_allow_html=True)
                st.markdown("<p class='card-section-sub' style='text-align: center !important;'>إحصائية تحليلية مقارنة لأعداد ونسب الطلاب وفق النمط الغالب (بصري / حركي / سمعي)</p>", unsafe_allow_html=True)
                if len(df_tested) > 0:
                    v_count = len(df_tested[df_tested['vak_result'].str.contains('بصري', na=False)])
                    a_count = len(df_tested[df_tested['vak_result'].str.contains('سمعي', na=False)])
                    k_count = len(df_tested[df_tested['vak_result'].str.contains('حركي', na=False)])
                    
                    total_tested_cnt = len(df_tested)
                    v_pct = round(v_count / total_tested_cnt * 100, 1) if total_tested_cnt > 0 else 0
                    k_pct = round(k_count / total_tested_cnt * 100, 1) if total_tested_cnt > 0 else 0
                    a_pct = round(a_count / total_tested_cnt * 100, 1) if total_tested_cnt > 0 else 0

                    max_val = max(v_count, a_count, k_count)
                    h_v = max(int((v_count / max_val * 100)), 8) if max_val > 0 else 8
                    h_k = max(int((k_count / max_val * 100)), 8) if max_val > 0 else 8
                    h_a = max(int((a_count / max_val * 100)), 8) if max_val > 0 else 8
                    
                    chart_html = f"""
                    <div class="vak-summary-grid">
                        <div class="vak-stat-box visual">
                            <div class="vak-box-top">
                                <span class="vak-box-label">👁️ النمط البصري</span>
                                <span class="vak-pct-pill">{v_pct}%</span>
                            </div>
                            <div class="vak-box-number">{v_count} <span class="vak-box-unit">طالب</span></div>
                            <div class="vak-mini-track"><div class="vak-mini-fill" style="width: {v_pct}%;"></div></div>
                        </div>
                        <div class="vak-stat-box kinesthetic">
                            <div class="vak-box-top">
                                <span class="vak-box-label">🏃‍♂️ النمط الحركي</span>
                                <span class="vak-pct-pill">{k_pct}%</span>
                            </div>
                            <div class="vak-box-number">{k_count} <span class="vak-box-unit">طالب</span></div>
                            <div class="vak-mini-track"><div class="vak-mini-fill" style="width: {k_pct}%;"></div></div>
                        </div>
                        <div class="vak-stat-box auditory">
                            <div class="vak-box-top">
                                <span class="vak-box-label">👂 النمط السمعي</span>
                                <span class="vak-pct-pill">{a_pct}%</span>
                            </div>
                            <div class="vak-box-number">{a_count} <span class="vak-box-unit">طالب</span></div>
                            <div class="vak-mini-track"><div class="vak-mini-fill" style="width: {a_pct}%;"></div></div>
                        </div>
                    </div>

                    <div class="custom-chart-container">
                        <div class="chart-bar-wrapper">
                            <div class="chart-value-badge v-badge">{v_count} ({v_pct}%)</div>
                            <div class="chart-bar v-bar" style="height: {h_v}%;"></div>
                            <div class="chart-label">بصري 👁️</div>
                        </div>
                        <div class="chart-bar-wrapper">
                            <div class="chart-value-badge k-badge">{k_count} ({k_pct}%)</div>
                            <div class="chart-bar k-bar" style="height: {h_k}%;"></div>
                            <div class="chart-label">حركي 🏃‍♂️</div>
                        </div>
                        <div class="chart-bar-wrapper">
                            <div class="chart-value-badge a-badge">{a_count} ({a_pct}%)</div>
                            <div class="chart-bar a-bar" style="height: {h_a}%;"></div>
                            <div class="chart-label">سمعي 👂</div>
                        </div>
                    </div>
                    """
                    st.markdown(chart_html, unsafe_allow_html=True)
                else:
                    st.info("لا توجد بيانات كافية لعرض الرسم البياني.")

    with tab_reports:
        with st.container(border=True):
            curr_rep = st.session_state.active_report
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                lbl_comp = "✅ 📋 الفصول الشامل" if curr_rep == "comp" else "📋 الفصول الشامل"
                key_comp = "rep_active_comp" if curr_rep == "comp" else "rep_idle_comp"
                if st.button(lbl_comp, key=key_comp, use_container_width=True):
                    st.session_state.active_report = "comp"
                    st.rerun()
            with r_col2:
                lbl_style = "✅ 🎨 فرز الأنماط" if curr_rep == "style" else "🎨 فرز الأنماط"
                key_style = "rep_active_style" if curr_rep == "style" else "rep_idle_style"
                if st.button(lbl_style, key=key_style, use_container_width=True):
                    st.session_state.active_report = "style"
                    st.rerun()

            r_col3, r_col4 = st.columns(2)
            with r_col3:
                lbl_unt = "✅ ⏳ غير المختبرين" if curr_rep == "untested" else "⏳ غير المختبرين"
                key_unt = "rep_active_unt" if curr_rep == "untested" else "rep_idle_unt"
                if st.button(lbl_unt, key=key_unt, use_container_width=True):
                    st.session_state.active_report = "untested"
                    st.rerun()
            with r_col4:
                lbl_ind = "✅ 👤 التقرير الفردي" if curr_rep == "indiv" else "👤 التقرير الفردي"
                key_ind = "rep_active_ind" if curr_rep == "indiv" else "rep_idle_ind"
                if st.button(lbl_ind, key=key_ind, use_container_width=True):
                    st.session_state.active_report = "indiv"
                    st.rerun()

            st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            
            # 1️⃣ تقرير الفصول الشامل
            if curr_rep == "comp":
                df_class, scope_label = render_grade_class_Selector(df_all, "comp")
                style_filter = st.selectbox("3️⃣ تصفية حسب نمط التعلم:", ["جميع الأنماط", "بصري", "سمعي", "حركي"], key="sty_comp")
                    
                df_class_tested = df_class[df_class['vak_result'] != 'غير مختبر'].copy()
                
                if style_filter != "جميع الأنماط":
                    df_class_tested = df_class_tested[df_class_tested['vak_result'].str.contains(style_filter, na=False)].copy()
                
                if len(df_class_tested) > 0:
                    display_cols = df_class_tested[['id', 'name', 'class_name', 'vak_result']].rename(
                        columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب'}
                    )
                    display_cols = add_serial_column(display_cols)
                    render_rtl_table(display_cols)
                    
                    html_table = display_cols.to_html(index=False, classes="table", justify="center")
                    v_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('بصري', na=False)]) / len(df_class_tested) * 100, 1)
                    a_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('سمعي', na=False)]) / len(df_class_tested) * 100, 1)
                    k_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('حركي', na=False)]) / len(df_class_tested) * 100, 1)
                    
                    class_content = f"""
                    <div class="summary-box"><h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">الإحصائية الإجمالية: <span style="font-weight: normal; font-size: 15px;">عدد الطلاب في هذا التقرير: {len(df_class_tested)} طالب</span></h3>
                    <div class="stats-container"><div class="stat-card visual"><div class="stat-title">👁️ بصري</div><div class="stat-value">{v_pct}%</div></div><div class="stat-card auditory"><div class="stat-title">👂 سمعي</div><div class="stat-value">{a_pct}%</div></div><div class="stat-card kinesthetic"><div class="stat-title">🏃‍♂️ حركي</div><div class="stat-value">{k_pct}%</div></div></div></div>
                    <h3 style="margin-top: 20px; font-size: 16px;">قائمة بيانات الطلاب:</h3>{html_table}"""
                    
                    base_title = f"تقرير أنماط التعلم - {scope_label}"
                    if style_filter != "جميع الأنماط":
                        base_title += f" (النمط ال{style_filter})"
                    full_html = generate_html_page(base_title, class_content, get_school_name(df_class_tested))
                    st.download_button(
                        label="📥 تحميل التقرير للطباعة (A4)",
                        data=full_html.encode('utf-8'),
                        file_name=f"Group_Report_{scope_label}_{style_filter}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    st.warning("لا يوجد طلاب مختبرين مطابقين لهذا الفلتر في النطاق المحدد.")

            # 2️⃣ تقرير فرز الأنماط المخصص
            elif curr_rep == "style":
                df_style_sub, scope_label = render_grade_class_Selector(df_all, "style_only")
                chosen_style_label = st.selectbox("3️⃣ اختر نمط التعلم المطلوب استخراجه:", ["بصري 👁️", "سمعي 👂", "حركي 🏃‍♂️"])
                chosen_style_key = chosen_style_label.split()[0]
                    
                df_style_matched = df_style_sub[df_style_sub['vak_result'].str.contains(chosen_style_key, na=False)].copy()
                
                if len(df_style_matched) > 0:
                    display_cols = df_style_matched[['id', 'name', 'class_name', 'vak_result']].rename(
                        columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب'}
                    )
                    display_cols = add_serial_column(display_cols)
                    render_rtl_table(display_cols)
                    
                    html_table = display_cols.to_html(index=False, classes="table", justify="center")
                    
                    if chosen_style_key == "بصري":
                        style_tips = "<li>الاعتماد على الخرائط الذهنية، الصور، والرسوم البيانية على السبورة.</li><li>استخدام الأقلام الملونة لتمييز الكلمات والمفاهيم الأساسية.</li><li>عرض مقاطع الفيديو التعليمية والعروض المرئية.</li>"
                    elif chosen_style_key == "سمعي":
                        style_tips = "<li>التركيز على الشرح الشفهي المباشر والحوار والنقاش الجماعي.</li><li>توظيف القراءة الجهرية والترديد الصوتي للمعلومات المهمة.</li><li>تشجيع الطلاب على تلخيص الدرس شفهياً لزملائهم.</li>"
                    else:
                        style_tips = "<li>دمج الأنشطة الحركية والتجارب العملية والمجسمات اليدوية في الدرس.</li><li>تطبيق استراتيجية لعب الأدوار والتعلم بالمحاكاة.</li><li>تقسيم المهام الطويلة وإتاحة فرص للحركة الهادفة داخل الفصل.</li>"

                    style_content = f"""
                    <div class="summary-box">
                        <h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">
                            إحصائية النمط ({chosen_style_label}): <span style="font-weight: normal; font-size: 15px;">العدد الإجمالي: {len(df_style_matched)} طالب</span>
                        </h3>
                        <p style="margin: 5px 0; font-weight: bold; color: {cur_t['brand_royal']};">💡 استراتيجيات التدريس الموصى بها لهذه المجموعة داخل الفصل:</p>
                        <ul style="margin: 5px 0 0 0; line-height: 1.6; font-size: 14px;">{style_tips}</ul>
                    </div>
                    <h3 style="margin-top: 20px; font-size: 16px;">قائمة بأسماء طلاب النمط ال{chosen_style_key}:</h3>{html_table}"""
                    
                    report_title = f"تقرير حصر طلاب النمط ال{chosen_style_key} ({chosen_style_label}) - {scope_label}"
                    full_html = generate_html_page(report_title, style_content, get_school_name(df_style_matched))
                    st.download_button(
                        label=f"📥 تحميل تقرير النمط ال{chosen_style_key} للطباعة (A4)",
                        data=full_html.encode('utf-8'),
                        file_name=f"Style_Report_{chosen_style_key}_{scope_label}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    st.warning(f"لا يوجد طلاب مسجلين ضمن النمط ({chosen_style_label}) في هذا النطاق.")

            # 3️⃣ تقرير غير المختبرين
            elif curr_rep == "untested":
                df_scope, scope_label = render_grade_class_Selector(df_all, "untested")
                df_untested = df_scope[df_scope['vak_result'] == 'غير مختبر'].copy()
                
                if len(df_untested) > 0:
                    display_cols = df_untested[['id', 'name', 'class_name']].rename(columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل'})
                    display_cols = add_serial_column(display_cols)
                    render_rtl_table(display_cols)
                    
                    html_table = display_cols.to_html(index=False, classes="table", justify="center")
                    untested_content = f"""<div class="summary-box"><h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">إحصائية المتأخرين: <span style="font-weight: normal; font-size: 15px;">العدد الإجمالي: {len(df_untested)} طالب</span></h3></div><h3 style="margin-top: 20px; font-size: 16px;">قائمة بأسماء الطلاب المطالبين بإجراء الاختبار:</h3>{html_table}"""
                    report_title = f"تقرير حصر الطلاب غير المختبرين - {scope_label}"
                    full_html = generate_html_page(report_title, untested_content, get_school_name(df_untested))
                    st.download_button(
                        label="📥 تحميل تقرير غير المختبرين للطباعة (A4)",
                        data=full_html.encode('utf-8'),
                        file_name=f"Untested_Report_{scope_label}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    st.success("🎉 رائع! جميع الطلاب في هذا النطاق أتموا الاختبار.")

            # 4️⃣ التقرير الفردي لطالب
            elif curr_rep == "indiv":
                st.info("💡 اكتب اسم الطالب أو رقم هويته ثم اضغط على زر (بحث).")
                
                col_search_in, col_search_btn = st.columns([4, 1.2])
                with col_search_in:
                    search_query = st.text_input("🔍 ابحث باسم الطالب أو رقم الهوية:", placeholder="مثال: أحمد خالد أو رقم الهوية...", key="indiv_search_input")
                with col_search_btn:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    search_clicked = st.button("🔍 بحث", use_container_width=True, key="btn_indiv_search")
                    
                if search_query or search_clicked:
                    norm_query = search_query.strip()
                    if not norm_query:
                        st.warning("الرجاء كتابة اسم الطالب أو رقم الهوية في مربع البحث أولاً.")
                    else:
                        matches = df_all[
                            df_all['name'].apply(lambda x: norm_query in str(x)) |
                            df_all['id'].apply(lambda x: norm_query in str(x))
                        ]
                        if matches.empty:
                            st.warning("لم يتم العثور على طالب يطابق هذا البحث ضمن الفصول المسندة إليك.")
                        else:
                            options = matches['name'] + " | الهوية: " + matches['id'] + " | الفصل: " + matches['class_name']
                            selected_choice = st.selectbox("الطلاب المطابقين للبحث:", options)
                            
                            exact_id = selected_choice.split("الهوية: ")[1].split(" |")[0]
                            s = df_all[df_all['id'] == exact_id].iloc[0]
                            
                            if s['vak_result'] == 'غير مختبر':
                                st.error("⚠️ هذا الطالب لم يجرِ الاختبار بعد.")
                            else:
                                school_names_html = get_school_name(pd.DataFrame([s]))
                                v_pct = int(float(s['v_score'])) * 10
                                a_pct = int(float(s['a_score'])) * 10
                                k_pct = int(float(s['k_score'])) * 10
                                if "بصري" in s['vak_result']:
                                    summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل البصرية المرئية."
                                    recs = "<li>استخدام الصور والخرائط الذهنية في الشرح.</li><li>الاعتماد على العروض المرئية والفيديوهات.</li><li>استخدام الألوان في التلخيص والتنظيم.</li>"
                                elif "سمعي" in s['vak_result']:
                                    summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل السمعية والحوارية."
                                    recs = "<li>توظيف الشرح الشفهي والنقاشات الجماعية.</li><li>الاعتماد على الترديد والتسجيلات الصوتية.</li><li>تشجيع الطالب على القراءة بصوت مسموع.</li>"
                                else:
                                    summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل الحركية والعملية."
                                    recs = "<li>دمج الأنشطة والتطبيقات العملية اليدوية.</li><li>السماح بالحركة أثناء التعلم أو استخدام المجسمات.</li><li>تطبيق استراتيجية لعب الأدوار.</li>"
                                student_content = f"""
                                <div class="summary-box"><p><b>اسم الطالب:</b> {s['name']}</p><p><b>الصف والفصل:</b> {s['grade']} - {s['class_name']}</p><p><b>الرقم المدرسي (الهوية):</b> {s['id']}</p></div>
                                <h3 style="font-size: 16px;">النتيجة التفصيلية:</h3>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>بصري Visual</span><span>{v_pct}%</span></div><div class="bar-bg"><div class="bar-v" style="width: {v_pct}%;"></div></div>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>سمعي Auditory</span><span>{a_pct}%</span></div><div class="bar-bg"><div class="bar-a" style="width: {a_pct}%;"></div></div>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>حركي Kinesthetic</span><span>{k_pct}%</span></div><div class="bar-bg"><div class="bar-k" style="width: {k_pct}%;"></div></div>
                                <div class="summary-box" style="margin-top: 20px;"><h3 style="color:{cur_t['brand_navy']}; text-align:center; margin: 0 0 10px 0; font-size: 18px;">النمط الغالب: {s['vak_result']}</h3><p style="text-align:center; margin: 0; font-size: 14px;">{summary}</p></div>
                                <h3 style="font-size: 16px;">مقترحات تعليمية للطالب:</h3><ul style="font-size: 15px; line-height: 1.6;">{recs}</ul>
                                """
                                full_html = generate_html_page("تقرير مقياس أنماط التعلم (VAK)", student_content, school_names_html)
                                st.download_button(
                                    label=f"📥 تحميل التقرير الفردي للطالب ({s['name']}) للطباعة",
                                    data=full_html.encode('utf-8'),
                                    file_name=f"Student_{s['id']}_Report.html",
                                    mime="text/html",
                                    use_container_width=True
                                )

    if tab_data is not None:
        with tab_data:
            with st.container(border=True):
                st.markdown("<div class='card-section-title'>⚙️ إدارة قواعد البيانات والصلاحيات</div>", unsafe_allow_html=True)
                st.markdown("<p class='card-section-sub'>تحديث قوائم الطلاب، استيراد أنماط التعلم، وتخصيص الفصول المسندة للمعلمين</p>", unsafe_allow_html=True)
                sub_tab_students, sub_tab_vak, sub_tab_teachers = st.tabs(["👨‍🎓 بيانات الطلاب", "🧠 بيانات أنماط التعلم", "👨‍🏫 المعلمين وصلاحيات الفصول"])
                
                # 1️⃣ تبويب بيانات الطلاب
                with sub_tab_students:
                    col1_s, col2_s, col3_s = st.columns(3)
                    with col1_s:
                        template_s_df = pd.DataFrame(columns=['id', 'name', 'grade', 'class_name'])
                        st.download_button("📥 تحميل قالب إضافة الطلاب", data=create_excel_bytes(template_s_df), file_name='students_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_s")
                    with col2_s:
                        template_vak_df = pd.DataFrame(columns=['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score'])
                        st.download_button("🧠 تحميل قالب أنماط التعلم", data=create_excel_bytes(template_vak_df), file_name='vak_learning_styles_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_vak_main")
                    with col3_s:
                        st.download_button("💾 تحميل نسخة احتياطية (الطلاب)", data=create_excel_bytes(df_all_raw), file_name='students_backup.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_bkp_s")
                    
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    st.write("**📤 الاستيراد الذكي لبيانات الطلاب أو قالب أنماط التعلم:**")
                    uploaded_s_file = st.file_uploader("اختر ملف Excel (.xlsx أو .csv) للطلاب أو أنماط التعلم", type=['xlsx', 'csv'], key="up_s")
                    if uploaded_s_file is not None:
                        try:
                            new_s_data = pd.read_csv(uploaded_s_file) if uploaded_s_file.name.endswith('.csv') else pd.read_excel(uploaded_s_file)
                            added_cnt, updated_vak_cnt, ok_flag = intelligent_merge_students_and_vak(new_s_data)
                            if not ok_flag:
                                st.error("⚠️ الملف لا يحتوي على عمود رقم الهوية المطلوب (id).")
                            elif added_cnt > 0 or updated_vak_cnt > 0:
                                st.success(f"✅ تمت العملية بنجاح! (إضافة طلاب جدد: {added_cnt} | تحديث أنماط تعلم: {updated_vak_cnt})")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("⚠️ جميع البيانات الموجودة في الملف مسجلة ومحدثة بالفعل في النظام.")
                        except Exception as e:
                            st.error("حدث خطأ أثناء قراءة الملف.")
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    
                    col_db_q, col_db_b = st.columns([4, 1.2])
                    with col_db_q:
                        db_search_q = st.text_input("🔍 بحث سريع في سجل الطلاب:", placeholder="ابحث بالاسم أو الهوية أو الفصل...", key="db_s_q")
                    with col_db_b:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        st.button("🔍 بحث", use_container_width=True, key="btn_db_s")
                    
                    df_s_view = df_all_raw.copy()
                    if db_search_q.strip():
                        q_str = db_search_q.strip()
                        df_s_view = df_s_view[
                            df_s_view['name'].apply(lambda x: q_str in str(x)) |
                            df_s_view['id'].apply(lambda x: q_str in str(x)) |
                            df_s_view['class_name'].apply(lambda x: q_str in str(x))
                        ]
                    
                    display_s_df = df_s_view.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة الغالبة'})
                    display_s_df = add_serial_column(display_s_df[['رقم الهوية', 'الاسم', 'الصف', 'الفصل', 'النتيجة الغالبة']])
                    render_rtl_table(display_s_df)

                # 2️⃣ تبويب مخصص لاستيراد وتصدير قالب أنماط التعلم (VAK)
                with sub_tab_vak:
                    st.info("💡 يمكنك تحميل قالب أنماط التعلم فارغاً، أو محملاً بأسماء الطلاب الحاليين لرصد وتعديل أنماطهم ودرجاتهم (بصري / سمعي / حركي) ثم إعادة رفعه.")
                    col1_v, col2_v = st.columns(2)
                    with col1_v:
                        empty_vak_df = pd.DataFrame(columns=['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score'])
                        st.download_button("📥 تحميل قالب أنماط التعلم (فارغ)", data=create_excel_bytes(empty_vak_df), file_name='vak_empty_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_vak_empty")
                    with col2_v:
                        prefilled_vak_df = df_all_raw[['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score']].copy()
                        st.download_button("📋 تحميل كشف رصد الأنماط للطلاب المسجلين", data=create_excel_bytes(prefilled_vak_df), file_name='vak_students_sheet.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_vak_prefilled")
                    
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    st.write("**📤 استيراد وتحديث ملف أنماط التعلم (VAK):**")
                    uploaded_vak_file = st.file_uploader("ارفع ملف قالب أنماط التعلم (.xlsx أو .csv) بعد تعبئته", type=['xlsx', 'csv'], key="up_vak_only")
                    if uploaded_vak_file is not None:
                        try:
                            new_vak_data = pd.read_csv(uploaded_vak_file) if uploaded_vak_file.name.endswith('.csv') else pd.read_excel(uploaded_vak_file)
                            added_cnt, updated_vak_cnt, ok_flag = intelligent_merge_students_and_vak(new_vak_data)
                            if not ok_flag:
                                st.error("⚠️ الملف لا يحتوي على عمود رقم الهوية المطلوب (id).")
                            elif added_cnt > 0 or updated_vak_cnt > 0:
                                st.success(f"🎉 تم تحديث أنماط التعلم لـ {updated_vak_cnt} طالب وإضافة {added_cnt} طالب جديد بنجاح!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("⚠️ لم يتم رصد أي تغييرات جديدة في أنماط التعلم.")
                        except Exception as e:
                            st.error("حدث خطأ أثناء قراءة ملف أنماط التعلم.")
                    
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    display_vak_df = df_all_raw[['id', 'name', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score']].rename(
                        columns={'id': 'رقم الهوية', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب', 'v_score': 'بصري (V)', 'a_score': 'سمعي (A)', 'k_score': 'حركي (K)'}
                    )
                    display_vak_df = add_serial_column(display_vak_df)
                    render_rtl_table(display_vak_df)

                # 3️⃣ تبويب بيانات المعلمين والتحكم في صلاحيات الفصول
                with sub_tab_teachers:
                    try: df_teachers = get_all_teachers()
                    except: df_teachers = pd.DataFrame(columns=['id', 'name', 'role', 'class_name'])

                    st.markdown("#### 🔐 التحكم في صلاحيات المعلمين وتخصيص الفصول")
                    st.info("💡 اختر المعلم لتحديد الفصول المسموح له باستعراضها وطباعة تقاريرها (يمكنك اختيار فصل واحد، عدة فصول، أو منح صلاحية جميع الفصول).")
                    
                    all_available_classes = sorted([c for c in df_all_raw['class_name'].unique() if str(c).strip()])
                    
                    if not df_teachers.empty:
                        teacher_options = df_teachers['name'] + " | الهوية: " + df_teachers['id']
                        selected_teacher_opt = st.selectbox("👤 اختر المعلم لتعديل صلاحيته وفصوله:", teacher_options, key="sel_teacher_perm")
                        
                        sel_t_id = selected_teacher_opt.split("الهوية: ")[1].strip()
                        sel_t_row = df_teachers[df_teachers['id'] == sel_t_id].iloc[0]
                        
                        curr_t_role = str(sel_t_row.get('role', 'teacher')).strip()
                        curr_t_classes_parsed = parse_teacher_classes(sel_t_row.get('class_name', 'all'))
                        
                        role_label_map = {"teacher": "معلم (صلاحية حسب الفصول)", "admin": "مدير النظام (صلاحية كاملة)"}
                        rev_role_map = {v: k for k, v in role_label_map.items()}
                        default_role_idx = 1 if curr_t_role == 'admin' else 0
                        chosen_role_label = st.selectbox("🛡️ نوع الحساب:", list(role_label_map.values()), index=default_role_idx, key=f"role_{sel_t_id}")
                        chosen_role = rev_role_map[chosen_role_label]
                            
                        is_all_default = (curr_t_classes_parsed == 'all') or (chosen_role == 'admin')
                        grant_all_classes = st.checkbox(
                            "✅ منح صلاحية الوصول وطباعة جميع الفصول (الكل)",
                            value=is_all_default,
                            disabled=(chosen_role == 'admin'),
                            key=f"chk_all_{sel_t_id}"
                        )
                        
                        if chosen_role == 'admin' or grant_all_classes:
                            st.caption("📌 هذا الحساب لديه صلاحية استعراض وطباعة **جميع الفصول** في المدرسة.")
                            final_classes_str = "all"
                            can_save = True
                        else:
                            default_selected_classes = [c for c in curr_t_classes_parsed if c in all_available_classes] if isinstance(curr_t_classes_parsed, list) else []
                            selected_multi_classes = st.multiselect(
                                "🏫 اختر الفصول المحددة لهذا المعلم (قائمة اختيار متعدد):",
                                options=all_available_classes,
                                default=default_selected_classes,
                                placeholder="اختر فصلاً واحداً أو أكثر...",
                                key=f"multi_cls_{sel_t_id}"
                            )
                            final_classes_str = ", ".join(selected_multi_classes)
                            can_save = len(selected_multi_classes) > 0
                            if not can_save:
                                st.warning("⚠️ يرجى اختيار فصل واحد على الأقل من القائمة، أو تفعيل خيار (جميع الفصول).")
                                
                        if st.button("💾 حفظ صلاحيات وفصول المعلم فوراً", use_container_width=True, key=f"btn_save_perm_{sel_t_id}"):
                            if not can_save:
                                st.error("⚠️ لا يمكن الحفظ بدون اختيار فصول للمعلم.")
                            else:
                                with st.spinner("جاري حفظ الصلاحيات وتحديث قاعدة البيانات فوراً..."):
                                    if update_teacher_permissions(sel_t_id, chosen_role, final_classes_str):
                                        st.success(f"✅ تم تحديث صلاحيات وفصول الأستاذ ({sel_t_row['name']}) فوراً بنجاح!")
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error("حدث خطأ أثناء تحديث بيانات المعلم.")
                    else:
                        st.warning("لا يوجد معلمون مسجلون حالياً.")

                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    col1_t, col2_t = st.columns(2)
                    with col1_t:
                        template_t_df = pd.DataFrame(columns=['id', 'name', 'role', 'class_name'])
                        st.download_button("📥 تحميل قالب إضافة المعلمين", data=create_excel_bytes(template_t_df), file_name='teachers_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_t")
                    with col2_t:
                        st.download_button("💾 تحميل نسخة احتياطية (المعلمين)", data=create_excel_bytes(df_teachers), file_name='teachers_backup.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_bkp_t")
                    
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    st.write("**📤 الاستيراد الذكي التلقائي لبيانات المعلمين:**")
                    uploaded_t_file = st.file_uploader("اختر ملف Excel (.xlsx أو .csv) للمعلمين", type=['xlsx', 'csv'], key="up_t")
                    if uploaded_t_file is not None:
                        try:
                            new_t_data = pd.read_csv(uploaded_t_file) if uploaded_t_file.name.endswith('.csv') else pd.read_excel(uploaded_t_file)
                            std_t_data = standardize_uploaded_columns(new_t_data.copy())
                            if all(col in std_t_data.columns for col in ['id', 'name']):
                                added_t_count = intelligent_merge_teachers(std_t_data)
                                if added_t_count > 0:
                                    st.success(f"✅ تم إضافة {added_t_count} حساب معلم جديد بنجاح!")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ جميع المعلمين الموجودين في الملف مسجلون بالفعل في النظام.")
                            else:
                                st.error("⚠️ الملف لا يحتوي على الأعمدة المطلوبة (id, name).")
                        except Exception as e:
                            st.error("حدث خطأ أثناء قراءة الملف.")
                    
                    st.markdown("<hr style='margin: 14px 0; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    display_t_df = df_teachers.copy()
                    display_t_df['class_name'] = display_t_df['class_name'].apply(lambda x: "جميع الفصول (الكل)" if parse_teacher_classes(x) == 'all' else str(x))
                    display_t_df['role'] = display_t_df['role'].apply(lambda x: "مدير النظام (admin)" if str(x).strip() == 'admin' else "معلم (teacher)")
                    display_t_df = display_t_df.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'role': 'الصلاحية', 'class_name': 'نطاق الفصول المسموحة'})
                    display_t_df = add_serial_column(display_t_df[['رقم الهوية', 'الاسم', 'الصلاحية', 'نطاق الفصول المسموحة']])
                    render_rtl_table(display_t_df)

# ==========================================
# 6. تذييل الصفحة الموحد وبطاقات التواصل المباشرة (بدون إظهار الأرقام أو الحسابات)
# ==========================================
st.markdown(f"""
<div class="ziyad-footer-wrap">
    <div class="ziyad-footer-copy">جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية © {datetime.now().year}</div>
    <div class="ziyad-footer-cards">
        <a href="https://zi-edu.streamlit.app" target="_blank" rel="noopener noreferrer" class="ziyad-footer-btn">
            🎓 منصة زياد الذكية
        </a>
        <a href="https://t.me/ZiyadAlmoamri" target="_blank" rel="noopener noreferrer" class="ziyad-footer-btn">
            📢 تليجرام الإدارة
        </a>
        <a href="https://wa.me/966534900049" target="_blank" rel="noopener noreferrer" class="ziyad-footer-btn">
            💬 واتساب المعلم
        </a>
        <a href="mailto:ziyadalamri30@gmail.com" class="ziyad-footer-btn">
            📧 البريد الإلكتروني
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
