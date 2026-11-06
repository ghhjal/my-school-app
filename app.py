import datetime
import hashlib
import io
import math
import re
import urllib.parse
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

# ==========================================
# ⚙️ 1. إعدادات النظام والاتصال الذكي
# ==========================================
st.set_page_config(
    page_title="منصة زياد الذكية",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(ttl=3600)
def get_gspread_client():
  try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
  except Exception as e:
    st.error(f"⚠️ خطأ اتصال بسيرفر جوجل: {e}")
    return None


sh = get_gspread_client()


def normalize_arabic(text):
  if not isinstance(text, str):
    text = str(text)
  text = re.sub(r"[أإآا]", "ا", text)
  text = re.sub(r"ة", "ه", text)
  text = re.sub(r"ى", "ي", text)
  return text.strip()


def clean_phone_number(phone):
  p = str(phone).strip().replace(" ", "")
  if p.startswith("0"):
    p = p[1:]
  if not p.startswith("966") and p != "":
    p = "966" + p
  return p


@st.cache_data(ttl=600)
def fetch_safe(worksheet_name):
  try:
    current_sh = get_gspread_client()
    if not current_sh:
      return pd.DataFrame()
    ws = current_sh.worksheet(worksheet_name)
    data = ws.get_all_values()
    if not data:
      return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])
    if not df.empty:
      df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    return df
  except Exception:
    st.cache_resource.clear()
    st.toast("⚠️ تم تحديث الاتصال مع السيرفر، حاول مجدداً.", icon="🔄")
    return pd.DataFrame()


def safe_append_row(worksheet_name, data_dict):
  try:
    current_sh = get_gspread_client()
    ws = current_sh.worksheet(worksheet_name)
    headers = ws.row_values(1)
    row = [data_dict.get(h, "") for h in headers]
    ws.append_row(row)
    return True
  except Exception:
    st.cache_resource.clear()
    st.error("⚠️ حدث انقطاع، تم التحديث. يرجى الضغط مرة أخرى.")
    return False


@st.cache_data(ttl=3600)
def get_cached_settings():
  try:
    current_sh = get_gspread_client()
    if not current_sh:
      return {}
    sett = current_sh.worksheet("settings").get_all_records()
    return {row["key"]: row["value"] for row in sett}
  except Exception:
    return {}


# --- تحميل الإعدادات في الجلسة ---
if "class_options" not in st.session_state:
  s_map = get_cached_settings()
  if s_map:
    st.session_state.max_tasks = int(s_map.get("max_tasks", 60))
    st.session_state.max_quiz = int(s_map.get("max_quiz", 40))
    st.session_state.current_year = str(s_map.get("current_year", "1447هـ"))
    st.session_state.current_period = str(
        s_map.get("current_period", "الفترة الأولى")
    ).strip()
    st.session_state.app_theme = str(
        s_map.get("app_theme", "الرئيسي (الافتراضي)")
    ).strip()
    st.session_state.class_options = [
        x.strip()
        for x in str(s_map.get("class_list", "الأول")).split(",")
        if x.strip()
    ]
    st.session_state.stage_options = [
        x.strip()
        for x in str(s_map.get("stage_list", "ابتدائي")).split(",")
        if x.strip()
    ]
  else:
    st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
    st.session_state.current_year = "1447هـ"
    st.session_state.current_period = "الفترة الأولى"
    st.session_state.app_theme = "الرئيسي (الافتراضي)"
    st.session_state.class_options = ["الأول"]
    st.session_state.stage_options = ["ابتدائي"]

if "role" not in st.session_state:
  st.session_state.role = None
if "username" not in st.session_state:
  st.session_state.username = None

# --- 🎨 نظام القوالب الديناميكية للمناسبات ---
active_theme_name = st.session_state.get("app_theme", "الرئيسي (الافتراضي)")

themes = {
    "الرئيسي (الافتراضي)": {
        "primary": "#2563EB",
        "accent": "#3B82F6",
        "header_grad": "linear-gradient(135deg, #1E40AF 0%, #2563EB 100%)",
        "title_color": "#ffffff",
        "sub_color": "#DBEAFE",
        "btn_hover": "linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%)",
        "icon": "🎓",
        "title": "منصة زياد الذكية",
        "subtitle": "بوابة التعليم الذكية 2026",
        "bg_pattern": "none",
    },
    "اليوم الوطني 🇸🇦": {
        "primary": "#006C5B",
        "accent": "#10B981",
        "header_grad": "linear-gradient(135deg, #004D40 0%, #006C5B 100%)",
        "title_color": "#ffffff",
        "sub_color": "#D4AF37",
        "btn_hover": "linear-gradient(135deg, #00332a 0%, #004D40 100%)",
        "icon": "🇸🇦",
        "title": "منصة زياد الذكية",
        "subtitle": (
            "عزّنا بطبعنا<br><span style='font-size:1.1rem; color:#ffffff;"
            " opacity:0.9;'>اليوم الوطني السعودي 96</span>"
        ),
        "bg_pattern": (
            "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0"
            " 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'"
            " fill-rule='evenodd'%3E%3Cg fill='%23ffffff'"
            " fill-opacity='0.08'%3E%3Cpath d='M36"
            " 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6"
            " 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6"
            ' 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")'
        ),
    },
    "يوم التأسيس 🏛️": {
        "primary": "#8B4513",
        "accent": "#D97706",
        "header_grad": "linear-gradient(135deg, #5C4033 0%, #8B4513 100%)",
        "title_color": "#F5DEB3",
        "sub_color": "#FAEBD7",
        "btn_hover": "linear-gradient(135deg, #3e2723 0%, #5d4037 100%)",
        "icon": "🐎",
        "title": "منصة زياد الذكية",
        "subtitle": (
            "يوم بدينا<br><span style='font-size:1.1rem; color:#F5DEB3;"
            " opacity:0.9;'>ثلاثة قرون من العز والفخر</span>"
        ),
        "bg_pattern": (
            "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0"
            " 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20"
            " 0l20 20-20 20L0 20z' fill='%23ffffff' fill-opacity='0.05'"
            ' fill-rule=\'evenodd\'/%3E%3C/svg%3E")'
        ),
    },
    "رمضان المبارك 🌙": {
        "primary": "#1E3A8A",
        "accent": "#D4AF37",
        "header_grad": "linear-gradient(135deg, #060D23 0%, #1E3A8A 100%)",
        "title_color": "#D4AF37",
        "sub_color": "#E2E8F0",
        "btn_hover": "linear-gradient(135deg, #0F172A 0%, #1E40AF 100%)",
        "icon": "🌙",
        "title": "منصة زياد الذكية",
        "subtitle": (
            "مبارك عليكم الشهر<br><span style='font-size:1.1rem;"
            " color:#D4AF37; opacity:0.9;'>رمضان يجمعنا</span>"
        ),
        "bg_pattern": (
            "url(\"data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0"
            " 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='2'"
            " cy='2' r='2' fill='%23ffffff'"
            ' fill-opacity=\'0.05\'/%3E%3C/svg%3E")'
        ),
    },
    "التفوق والنجاح 🏆": {
        "primary": "#B45309",
        "accent": "#F59E0B",
        "header_grad": "linear-gradient(135deg, #92400E 0%, #D97706 100%)",
        "title_color": "#ffffff",
        "sub_color": "#FEF3C7",
        "btn_hover": "linear-gradient(135deg, #78350F 0%, #B45309 100%)",
        "icon": "🏆",
        "title": "منصة زياد الذكية",
        "subtitle": (
            "حصاد التفوق والنجاح<br><span style='font-size:1.1rem;"
            " color:#ffffff; opacity:0.9;'>نهاية العام الدراسي</span>"
        ),
        "bg_pattern": (
            "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0"
            " 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'"
            " fill-rule='evenodd'%3E%3Cg fill='%23ffffff'"
            " fill-opacity='0.15'%3E%3Cpath d='M10.1"
            " 23l4.6-4.6-3.2-3.2-4.6 4.6 3.2 3.2zm14.2 0l-4.6-4.6"
            " 3.2-3.2 4.6 4.6-3.2"
            ' 3.2z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")'
        ),
    },
}

t_colors = themes.get(active_theme_name, themes["الرئيسي (الافتراضي)"])

text_color = "#0F172A"
sub_text = "#94A3B8"
border_color = "rgba(148, 163, 184, 0.28)"
success_color = "#10B981"
warning_color = "#F59E0B"
danger_color = "#EF4444"
shadow_val = "0 4px 12px rgba(0, 0, 0, 0.12)"

primary_color = t_colors["primary"]
accent_color = t_colors["accent"]
header_grad = t_colors["header_grad"]


def get_professional_msg(name, b_type, b_desc, date):
  msg = (
      f"🔔 *إشعار من منصة الأستاذ زياد*\n👤 *الطالب:* {name}\n📍 *الملاحظة:*"
      f" {b_type}\n📝 *التفاصيل:* {b_desc if b_desc else 'متابعة'}\n📅"
      f" *التاريخ:* {date}"
  )
  return urllib.parse.quote(msg)


def get_school_name_dynamic(cls_name):
  if cls_name == "الكل":
    return "ابتدائية عبادة بن قيس الأنصاري<br>متوسطة عبدالرحمن الناصر"
  elif "متوسط" in str(cls_name):
    return "متوسطة عبدالرحمن الناصر"
  else:
    return "ابتدائية عبادة بن قيس الأنصاري"


def show_footer():
  st.markdown("<br><br>", unsafe_allow_html=True)
  st.markdown(
      f"""
    <div style='text-align: center; color: var(--text-color); opacity: 0.8; padding: 20px; border-top: 1px solid {border_color};'>
        <p style='margin-bottom: 10px; font-size: 0.95rem; font-weight: 700;'>جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية © 2026</p>
    </div>
    """,
      unsafe_allow_html=True,
  )
  c1, c2, c3 = st.columns(3)
  c1.link_button(
      "📢 تليجرام الإدارة",
      "https://t.me/@ZiyadAlmoami",
      use_container_width=True,
  )
  c2.link_button(
      "💬 واتساب المعلم",
      "https://wa.me/966534900049",
      use_container_width=True,
  )
  c3.link_button(
      "📧 البريد الإلكتروني",
      "mailto:ziad.platform.alerts@gmail.com",
      use_container_width=True,
  )


# ==========================================
# 🎨 2. التصميم الاحترافي وشبكة (2×2) للوضع الليلي والجوال
# ==========================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
    
    :root {{
        --border-color: rgba(148, 163, 184, 0.28);
        --card-surface: var(--secondary-background-color);
        --subtle-text: #94A3B8;
    }}

    section[data-testid="stSidebar"] {{ display: none; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    html, body, [data-testid="stAppViewContainer"] {{ 
        font-family: 'Tajawal', sans-serif !important; 
        direction: RTL; text-align: right; 
        background-color: var(--background-color) !important; 
        color: var(--text-color) !important; 
    }}
    
    .block-container {{ padding-top: 1rem !important; padding-bottom: 5rem; max-width: 1050px; }}
    
    .header-container {{
        background: {header_grad};
        background-image: {t_colors["bg_pattern"]}, {header_grad};
        background-blend-mode: overlay;
        padding: 65px 20px 35px 20px;
        border-radius: 0 0 36px 36px;
        margin: -1rem -5rem 25px -5rem;
        box-shadow: 0 10px 30px -10px rgba(0,0,0, 0.45);
        color: white; 
        text-align: center;
        position: relative;
        overflow: hidden;
        border-bottom: 2px solid rgba(255,255,255,0.15);
    }}
    
    .title-wrapper {{
        display: flex; align-items: center; justify-content: center;
        gap: 15px; margin-bottom: 8px; position: relative; z-index: 2;
    }}
    
    .logo-icon {{ 
        font-size: 3.6rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
        animation: float 4s ease-in-out infinite; line-height: 1; margin-top: 10px;
    }}
    
    .main-title {{ 
        margin: 0; font-size: 2.8rem; font-weight: 900; 
        color: {t_colors["title_color"]} !important; line-height: 1.1;
    }}
    
    .sub-title {{ 
        margin: 0; color: {t_colors["sub_color"]}; font-size: 1.25rem; 
        font-weight: 600; position: relative; z-index: 2; line-height: 1.5;
    }}
    
    /* ✳️ حقول الإدخال والقوائم المنسدلة بتباين واضح جداً في الوضع الليلي */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] {{ 
        background-color: var(--secondary-background-color) !important; 
        border: 1.5px solid rgba(148, 163, 184, 0.35) !important; 
        border-radius: 12px !important; 
        min-height: 48px; 
    }}
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {{
        border-color: {accent_color} !important;
        box-shadow: 0 0 0 2px {primary_color}40 !important;
    }}
    input, textarea, select {{ 
        color: var(--text-color) !important; 
        -webkit-text-fill-color: var(--text-color) !important; 
        caret-color: {accent_color} !important;
        background-color: transparent !important; 
        font-weight: 700 !important; 
        font-size: 1.02rem !important;
    }}
    ::placeholder {{ color: #94A3B8 !important; opacity: 0.85 !important; -webkit-text-fill-color: #94A3B8 !important; }}
    div[data-baseweb="select"] div {{ color: var(--text-color) !important; font-weight: 700 !important; }}
    
    /* ✳️ الأزرار الرئيسية بتباين مرتفع وحواف واضحة */
    [data-testid="stFormSubmitButton"] button, 
    [data-testid="baseButton-primary"], 
    div.stButton > button,
    div.stDownloadButton > button {{
        background: {header_grad} !important;
        background-color: {primary_color} !important;
        color: #FFFFFF !important; 
        border: 1px solid rgba(255, 255, 255, 0.2) !important; 
        font-weight: 800 !important;
        font-size: 1.05rem !important; 
        border-radius: 14px !important; 
        padding: 10px 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important; 
        transition: all 0.2s ease !important; 
        width: 100%; 
        min-height: 50px;
    }}
    [data-testid="stFormSubmitButton"] button:hover, 
    [data-testid="baseButton-primary"]:hover, 
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {{ 
        background: {t_colors["btn_hover"]} !important; 
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35) !important; 
        border-color: rgba(255, 255, 255, 0.45) !important;
    }}
    
    /* ✳️ شبكة التبويبات والأزرار (2×2) المتجاوبة مع الجوال والوضع الليلي */
    .stTabs [data-baseweb="tab-list"] {{ 
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 10px !important; 
        background-color: transparent !important; 
        border: none !important; 
        margin-bottom: 12px !important;
        padding: 4px 2px !important;
    }}
    /* إذا كان عدد التبويبات فردياً، يمتد التبويب الأخير بعرض الشبكة بتناسق تام */
    .stTabs [data-baseweb="tab-list"] > button:last-child:nth-child(odd) {{
        grid-column: span 2 !important;
    }}
    .stTabs [data-baseweb="tab"] {{ 
        height: 54px !important; 
        width: 100% !important;
        margin: 0 !important;
        padding: 8px 12px !important;
        background-color: var(--secondary-background-color) !important; 
        border-radius: 14px !important; 
        border: 1.5px solid rgba(148, 163, 184, 0.3) !important; 
        color: var(--text-color) !important; 
        font-weight: 800 !important; 
        font-size: 0.98rem !important;
        justify-content: center !important; 
        align-items: center !important;
        text-align: center !important;
        white-space: normal !important;
        line-height: 1.25 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.25s ease !important; 
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        border-color: {accent_color} !important;
        transform: translateY(-1px);
    }}
    .stTabs [aria-selected="true"] {{ 
        background: {header_grad} !important; 
        color: #FFFFFF !important; 
        border: 2px solid #F59E0B !important; 
        border-radius: 14px !important; 
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35) !important; 
    }}
    .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {{
        color: #FFFFFF !important;
        font-weight: 900 !important;
    }}
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

    /* ✳️ البطاقات الإحصائية والعناصر المتجاوبة */
    .metric-container {{ 
        display: grid; 
        grid-template-columns: repeat(3, 1fr); 
        gap: 12px; 
        margin-bottom: 20px; 
        direction: rtl; 
    }}
    .metric-card {{
        background-color: var(--secondary-background-color); 
        border: 1.5px solid rgba(148, 163, 184, 0.28); 
        border-radius: 16px;
        padding: 18px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        box-shadow: {shadow_val};
    }}
    .metric-info {{ text-align: right; }}
    .metric-title {{ color: #94A3B8; font-size: 13.5px; font-weight: 800; margin-bottom: 4px; }}
    .metric-val {{ color: var(--text-color); font-size: 26px; font-weight: 900; line-height: 1.1; }}
    .metric-sub {{ color: #64748B; font-size: 12px; font-weight: 700; margin-top: 2px; }}
    .metric-icon {{ width: 50px; height: 50px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 24px; }}
    .ic-green {{ background-color: rgba(16, 185, 129, 0.15); color: {success_color}; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .ic-blue {{ background-color: rgba(59, 130, 246, 0.15); color: {accent_color}; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .ic-red {{ background-color: rgba(245, 158, 11, 0.15); color: {warning_color}; border: 1px solid rgba(245, 158, 11, 0.3); }}

    .app-card {{ 
        background: var(--secondary-background-color); 
        padding: 20px; border-radius: 16px; 
        box-shadow: {shadow_val}; 
        border: 1.5px solid rgba(148, 163, 184, 0.28); 
        margin-bottom: 15px; 
    }}
    
    .mobile-list-item {{ 
        background: var(--secondary-background-color); 
        border-radius: 14px; padding: 16px; margin-bottom: 12px; 
        border: 1.5px solid rgba(148, 163, 184, 0.28); 
        box-shadow: 0 2px 6px rgba(0,0,0,0.08); 
        display: flex; align-items: center; justify-content: space-between; 
        color: var(--text-color); 
    }}
    
    .medal-flex {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; direction: rtl; }}
    .m-card {{ background: var(--secondary-background-color); padding: 15px 5px; border-radius: 16px; text-align: center; border: 1.5px solid rgba(148, 163, 184, 0.28); box-shadow: {shadow_val}; color: var(--text-color); }}
    .m-active {{ border: 2px solid {warning_color} !important; background: rgba(245, 158, 11, 0.15) !important; }}
    
    .points-banner {{ background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%); color: white; padding: 25px; border-radius: 18px; text-align: center; margin-bottom: 20px; box-shadow: 0 6px 15px rgba(245, 158, 11, 0.35); border: 1px solid rgba(255,255,255,0.2); }}
    .welcome-card {{ background: {header_grad}; color: white; padding: 20px; border-radius: 18px; margin-bottom: 15px; box-shadow: 0 6px 15px rgba(0,0,0, 0.3); border: 1px solid rgba(255,255,255,0.15); }}

    [data-testid="stDataFrame"] {{ direction: rtl; }}

    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
    @keyframes pulse-red {{ 0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }} 70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }} }}
    .urgent-box {{ background-color: rgba(239, 68, 68, 0.12); border: 2px solid {danger_color}; color: {danger_color}; padding: 15px; border-radius: 14px; text-align: center; animation: pulse-red 2s infinite; font-weight: bold; margin-bottom: 20px; }}

    @media (max-width: 768px) {{
        .header-container {{ padding: 55px 15px 25px 15px; margin: -1rem -1rem 20px -1rem; border-radius: 0 0 28px 28px; }}
        .main-title {{ font-size: 1.85rem; }}
        .logo-icon {{ font-size: 2.3rem; }}
        .sub-title {{ font-size: 1.05rem; }}
        .metric-container {{ grid-template-columns: repeat(2, 1fr); }}
        .metric-container > .metric-card:last-child:nth-child(odd) {{ grid-column: span 2; }}
        .stTabs [data-baseweb="tab"] {{ font-size: 0.92rem !important; height: 52px !important; padding: 6px 8px !important; }}
    }}
    </style>

    <div class="header-container">
        <div class="title-wrapper">
            <div class="logo-icon">{t_colors["icon"]}</div>
            <h1 class="main-title">{t_colors["title"]}</h1>
        </div>
        <p class="sub-title">{t_colors["subtitle"]}</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 🔐 3. نظام تسجيل الدخول
# ==========================================
if st.session_state.role is None:
  t1, t2, t3 = st.tabs(
      ["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم", "🏫 بوابة الإدارة (مشاهد)"]
  )

  with t1:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("st_login"):
      st.markdown(
          "<h4 style='text-align:center; margin-bottom:15px;'>تسجيل دخول"
          " الطالب</h4>",
          unsafe_allow_html=True,
      )
      sid = st.text_input(
          "رقم الهوية / الرقم الأكاديمي", placeholder="أدخل الرقم هنا..."
      ).strip()
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button(
          "🚀 دخول للمنصة", type="primary", use_container_width=True
      ):
        arabic_to_english = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        sid = sid.translate(arabic_to_english)
        df = fetch_safe("students")
        if not df.empty:
          df["clean_id"] = (
              df.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
          )
          if sid.split(".")[0] in df["clean_id"].values:
            st.session_state.username = sid.split(".")[0]
            st.session_state.role = "student"
            st.rerun()
          else:
            st.error("⚠️ الرقم غير مسجل في النظام")

  with t2:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("tr_login"):
      st.markdown(
          "<h4 style='text-align:center; margin-bottom:15px;'>تسجيل دخول"
          " المعلم</h4>",
          unsafe_allow_html=True,
      )
      u = st.text_input("اسم المستخدم", placeholder="User")
      p = st.text_input("كلمة المرور", type="password", placeholder="******")
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button(
          "🛠️ دخول لوحة التحكم", type="primary", use_container_width=True
      ):
        df = fetch_safe("users")
        if not df.empty and u in df["username"].values:
          ud = df[df["username"] == u].iloc[0]
          if hashlib.sha256(p.encode()).hexdigest() == ud["password_hash"]:
            if ud.get("role", "teacher") in ["teacher", ""]:
              try:
                ws_u = sh.worksheet("users")
                c_u = ws_u.find(u)
                if c_u:
                  headers_u = ws_u.row_values(1)
                  if "last_login" not in headers_u:
                    ws_u.update_cell(1, len(headers_u) + 1, "last_login")
                    headers_u.append("last_login")
                  idx_u = headers_u.index("last_login") + 1
                  now_str = (
                      datetime.datetime.utcnow() + datetime.timedelta(hours=3)
                  ).strftime("%Y-%m-%d %I:%M %p")
                  ws_u.update_cell(c_u.row, idx_u, now_str)
              except Exception:
                pass
              st.session_state.username = u
              st.session_state.role = "teacher"
              st.rerun()
            else:
              st.error("❌ هذا الحساب لا يملك صلاحية المعلم.")
          else:
            st.error("❌ كلمة المرور غير صحيحة.")
        else:
          st.error("❌ اسم المستخدم غير موجود.")

  with t3:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("admin_login"):
      st.markdown(
          "<h4 style='text-align:center; margin-bottom:15px;'>دخول الإدارة"
          " (قراءة واستخراج تقارير)</h4>",
          unsafe_allow_html=True,
      )
      u_admin = st.text_input(
          "اسم المستخدم", placeholder="أدخل اسم المستخدم للإدارة..."
      )
      p_admin = st.text_input(
          "كلمة المرور", type="password", placeholder="أدخل كلمة المرور..."
      )
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button(
          "👁️ دخول الإشراف", type="primary", use_container_width=True
      ):
        df_u = fetch_safe("users")
        if not df_u.empty and u_admin in df_u["username"].values:
          ud = df_u[df_u["username"] == u_admin].iloc[0]
          if (
              hashlib.sha256(p_admin.encode()).hexdigest()
              == ud["password_hash"]
          ):
            if ud.get("role", "") == "viewer":
              try:
                ws_u = sh.worksheet("users")
                c_u = ws_u.find(u_admin)
                if c_u:
                  headers_u = ws_u.row_values(1)
                  if "last_login" not in headers_u:
                    ws_u.update_cell(1, len(headers_u) + 1, "last_login")
                    headers_u.append("last_login")
                  idx_u = headers_u.index("last_login") + 1
                  now_str = (
                      datetime.datetime.utcnow() + datetime.timedelta(hours=3)
                  ).strftime("%Y-%m-%d %I:%M %p")
                  ws_u.update_cell(c_u.row, idx_u, now_str)
              except Exception:
                pass
              st.session_state.username = u_admin
              st.session_state.role = "viewer"
              st.rerun()
            else:
              st.error("❌ هذا الحساب لا يملك صلاحية الإدارة (قراءة فقط).")
          else:
            st.error("❌ كلمة المرور غير صحيحة.")
        else:
          st.error("❌ بيانات الدخول غير صحيحة.")

  show_footer()
  st.stop()

# ==========================================
# 🔄 4. تحميل البيانات المركزية وتجهيز التبويبات الرئيسية
# ==========================================
if "db_loaded" not in st.session_state:
  with st.spinner("⏳ جاري الاتصال بالمنصة وتحديث البيانات المركزية..."):
    try:
      st.session_state.df_students = fetch_safe("students")
      st.session_state.df_grades = fetch_safe("grades")
      st.session_state.df_behavior = fetch_safe("behavior")
      st.session_state.db_loaded = True
    except Exception as e:
      st.error(f"❌ حدث خطأ أثناء الاتصال: {e}")
      st.stop()

if st.session_state.get("show_refresh_success"):
  st.toast("✅ تم تحديث البيانات ومزامنتها بنجاح!", icon="🔄")
  st.session_state["show_refresh_success"] = False

if st.session_state.role in ["teacher", "viewer"]:
  if st.session_state.role == "teacher":
    (
        tab_students,
        tab_eval,
        tab_honor,
        tab_reports,
        tab_alerts,
        tab_settings,
        tab_logout,
    ) = st.tabs([
        "👥 إدارة الطلاب",
        "📊 الرصد والتقييم",
        "🏆 الشرف والشهادات",
        "🖨️ مركز التقارير",
        "📢 التنبيهات",
        "⚙️ الإعدادات والبيانات",
        "🛑 خروج",
    ])
  else:
    tab_students, tab_eval, tab_honor, tab_reports, tab_alerts, tab_logout = (
        st.tabs([
            "👥 إدارة الطلاب",
            "📊 الرصد والتقييم",
            "🏆 الشرف والشهادات",
            "🖨️ مركز التقارير",
            "📢 التنبيهات",
            "🛑 خروج",
        ])
    )
    tab_settings = None

# ==========================================
# 👥 5. التبويب الأول: إدارة الطلاب (عرض، إضافة، تعديل، حذف)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_students:
    st.subheader("👥 إدارة بيانات الطلاب")
    df_st = st.session_state.df_students.copy()

    if "toast_msg" in st.session_state:
      st.toast(st.session_state.toast_msg, icon="🔔")
      del st.session_state["toast_msg"]

    if not df_st.empty:
      df_st["clean_id"] = (
          df_st.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      )
      df_st["النقاط"] = pd.to_numeric(df_st["النقاط"], errors="coerce").fillna(
          0
      )
    else:
      df_st["clean_id"] = []
      df_st["النقاط"] = []

    total_students = len(df_st)
    total_classes = (
        len(df_st["class"].dropna().unique())
        if "class" in df_st.columns and not df_st.empty
        else 0
    )
    avg_points = (
        round(df_st["النقاط"].mean(), 1)
        if "النقاط" in df_st.columns and not df_st.empty
        else 0
    )

    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-info">
                    <div class="metric-title">العدد الإجمالي</div>
                    <div class="metric-val">{total_students}</div>
                    <div class="metric-sub">طالب مسجل</div>
                </div>
                <div class="metric-icon ic-green">👥</div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <div class="metric-title">الفصول الدراسية</div>
                    <div class="metric-val">{total_classes}</div>
                    <div class="metric-sub">فصل نشط</div>
                </div>
                <div class="metric-icon ic-blue">🏫</div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <div class="metric-title">متوسط النقاط</div>
                    <div class="metric-val" dir="ltr">{avg_points}</div>
                    <div class="metric-sub">نقطة تميز</div>
                </div>
                <div class="metric-icon ic-red">📈</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # شبكة (2×2) لإدارة الطلاب
    action_tabs = st.tabs([
        "🔍 عرض وبحث الطلاب",
        "➕ إضافة طالب جديد",
        "✏️ تعديل بيانات طالب",
        "🗑️ حذف طالب",
    ])

    # 1. عرض وبحث الطلاب
    with action_tabs[0]:
      if not df_st.empty:
        if "current_page" not in st.session_state:
          st.session_state.current_page = 1

        col_search, col_cls_f, col_rows = st.columns([2.5, 1.5, 1])
        with col_search:
          sq = st.text_input(
              "🔍 بحث:",
              placeholder="ابحث بالاسم أو الرقم الأكاديمي...",
              label_visibility="collapsed",
          )
        with col_cls_f:
          cls_filter_opts = ["كل الفصول"] + list(
              df_st["class"].dropna().unique()
          )
          cls_filter = st.selectbox(
              "الفصل:",
              cls_filter_opts,
               index=0,
              label_visibility="collapsed",
          )
        with col_rows:
          rows_per_page = st.selectbox(
              "الصفوف:",
              [10, 20, 50, 100],
              index=0,
              label_visibility="collapsed",
          )

        display_df = df_st.copy()
        if cls_filter != "كل الفصول":
          display_df = display_df[display_df["class"] == cls_filter]

        if "clean_id" in display_df.columns:
          display_df = display_df.drop(columns=["clean_id"])

        rename_dict = {
            "id": "الرقم الأكاديمي",
            "name": "الاسم",
            "class": "الصف",
            "year": "العام",
            "sem": "المرحلة",
            "subject": "المادة",
        }
        display_df = display_df.rename(columns=rename_dict)
        display_df = display_df[display_df.columns[::-1]]

        if sq:
          norm_sq = normalize_arabic(sq)
          mask = display_df["الرقم الأكاديمي"].astype(str).str.contains(
              norm_sq
          ) | display_df["الاسم"].astype(str).apply(
              normalize_arabic
          ).str.contains(
              norm_sq
          )
          display_df = display_df[mask]
          st.session_state.current_page = 1

        total_rows = len(display_df)
        total_pages = max(1, math.ceil(total_rows / rows_per_page))
        if st.session_state.current_page > total_pages:
          st.session_state.current_page = total_pages

        start_idx = (st.session_state.current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page

        st.dataframe(
            display_df.iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True,
        )

        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
          if st.button(
              "▶ التالي",
              disabled=(st.session_state.current_page >= total_pages),
              use_container_width=True,
          ):
            st.session_state.current_page += 1
            st.rerun()
        with pc2:
          st.markdown(
              "<div style='text-align: center; font-weight: bold; padding-top:"
              " 8px; color: #94A3B8;'>صفحة"
              f" {st.session_state.current_page} من"
              f" {total_pages}<br><small>(إجمالي النتائج: {total_rows}"
              " طالب)</small></div>",
              unsafe_allow_html=True,
          )
        with pc3:
          if st.button(
              "السابق ◀",
              disabled=(st.session_state.current_page <= 1),
              use_container_width=True,
          ):
            st.session_state.current_page -= 1
            st.rerun()
      else:
        st.info("لا توجد بيانات طلاب مسجلة حالياً.")

    # 2. إضافة طالب جديد
    with action_tabs[1]:
      if st.session_state.role == "teacher":
        with st.form("add_st_v26", clear_on_submit=True):
          st.markdown("#### 👤 بيانات الطالب الأساسية")
          c1, c2 = st.columns(2)
          f_name = c1.text_input("الاسم الكامل", placeholder="أدخل الاسم الرباعي")
          f_id = c2.text_input(
              "الرقم الأكاديمي / الهوية", placeholder="أدخل الرقم الأكاديمي"
          )

          c3, c4, c5 = st.columns(3)
          f_stage = c3.selectbox("المرحلة", st.session_state.stage_options)
          f_class = c4.selectbox("الصف", st.session_state.class_options)
          f_year = c5.text_input("العام الدراسي", st.session_state.current_year)

          st.markdown("#### 📞 معلومات التواصل ونمط التعلم")
          c6, c7, c8 = st.columns(3)
          f_phone = c6.text_input("رقم الجوال", placeholder="05xxxxxxxx")
          f_mail = c7.text_input(
              "البريد الإلكتروني", placeholder="example@mail.com"
          )
          f_style = c8.selectbox(
              "نمط التعلم (اختياري)",
              ["", "بصري 👀", "سمعي 👂", "حركي ✋", "متعدد الأنماط 🌟"],
          )

          if st.form_submit_button(
              "✅ حفظ الطالب في المنصة",
              type="primary",
              use_container_width=True,
          ):
            if f_id and f_name:
              clean_new_id = f_id.strip().split(".")[0]
              if (
                  not df_st.empty
                  and clean_new_id in df_st["clean_id"].values
              ):
                st.error(f"⚠️ الرقم {clean_new_id} مسجل مسبقاً!")
              else:
                cl_p = clean_phone_number(f_phone) if f_phone else ""
                st_map = {
                    "id": clean_new_id,
                    "name": f_name.strip(),
                    "class": f_class,
                    "year": f_year,
                    "sem": f_stage,
                    "الجوال": cl_p,
                    "الإيميل": f_mail.strip(),
                    "النقاط": "0",
                    "نمط التعلم": f_style,
                }
                if safe_append_row("students", st_map):
                  st.session_state.toast_msg = (
                      f"✅ تم إضافة الطالب '{f_name}' بنجاح!"
                  )
                  if "db_loaded" in st.session_state:
                    del st.session_state["db_loaded"]
                  st.cache_data.clear()
                  st.rerun()
            else:
              st.warning("الرجاء إكمال البيانات الأساسية (الاسم والرقم)!")
      else:
        st.info("💡 وضع القراءة فقط: ليس لديك صلاحية لإضافة طلاب.")

    # 3. تعديل بيانات طالب
    with action_tabs[2]:
      if st.session_state.role == "teacher":
        if not df_st.empty:
          edit_options = df_st.index.tolist()
          selected_idx = st.selectbox(
              "✏️ اختر الطالب المطلوب تعديل بياناته (يمكنك البحث بالكتابة):",
              edit_options,
              format_func=lambda x: (
                  f"{df_st.loc[x, 'name']} - ({df_st.loc[x, 'class']}) - الرقم:"
                  f" {df_st.loc[x, 'id']}"
              ),
              key="edit_select",
          )

          with st.form("edit_form_single"):
            st.markdown(
                f"**📝 تعديل بيانات: <span style='color:{accent_color};'>"
                f"{df_st.loc[selected_idx, 'name']}</span>**",
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            new_vals = []

            valid_columns = [
                c
                for c in df_st.columns
                if c not in ["clean_id"]
                and not str(c).startswith("Unnamed")
                and str(c).strip() != ""
            ]

            for col_idx, col_name in enumerate(valid_columns):
              with cols[col_idx % 3]:
                current_val = (
                    ""
                    if pd.isna(df_st.loc[selected_idx, col_name])
                    else str(df_st.loc[selected_idx, col_name]).strip()
                )

                if col_name == "class":
                  c_opts = list(st.session_state.get("class_options", []))
                  if current_val not in c_opts and current_val != "":
                    c_opts.insert(0, current_val)
                  c_idx = (
                      c_opts.index(current_val)
                      if current_val in c_opts
                      else 0
                  )
                  val = st.selectbox(
                      col_name,
                      c_opts,
                      index=c_idx,
                      key=f"inp_edit_{selected_idx}_{col_idx}",
                  )
                elif col_name == "sem":
                  s_opts = list(st.session_state.get("stage_options", []))
                  if current_val not in s_opts and current_val != "":
                    s_opts.insert(0, current_val)
                  s_idx = (
                      s_opts.index(current_val)
                      if current_val in s_opts
                      else 0
                  )
                  val = st.selectbox(
                      col_name,
                      s_opts,
                      index=s_idx,
                      key=f"inp_edit_{selected_idx}_{col_idx}",
                  )
                elif col_name == "نمط التعلم":
                  ls_opts = [
                      "",
                      "بصري 👀",
                      "سمعي 👂",
                      "حركي ✋",
                      "متعدد الأنماط 🌟",
                  ]
                  if current_val not in ls_opts and current_val != "":
                    ls_opts.insert(0, current_val)
                  ls_idx = (
                      ls_opts.index(current_val)
                      if current_val in ls_opts
                      else 0
                  )
                  val = st.selectbox(
                      col_name,
                      ls_opts,
                      index=ls_idx,
                      key=f"inp_edit_{selected_idx}_{col_idx}",
                  )
                else:
                  val = st.text_input(
                      col_name,
                      current_val,
                      key=f"inp_edit_{selected_idx}_{col_idx}",
                  )
                new_vals.append(val)

            if st.form_submit_button(
                "💾 حفظ التعديلات", type="primary", use_container_width=True
            ):
              row_index = int(selected_idx) + 2
              try:
                sh.worksheet("students").update(f"A{row_index}", [new_vals])
                st.session_state.toast_msg = (
                    f"🔄 تم تحديث بيانات '{new_vals[1]}' بنجاح!"
                )
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                st.cache_data.clear()
                st.rerun()
              except Exception as e:
                st.error(f"❌ حدث خطأ أثناء التعديل: {e}")
        else:
          st.info("لا توجد بيانات للطلاب بعد.")
      else:
        st.info("💡 وضع القراءة فقط: ليس لديك صلاحية لتعديل البيانات.")

    # 4. حذف طالب
    with action_tabs[3]:
      if st.session_state.role == "teacher":
        if not df_st.empty:
          del_options = df_st.index.tolist()
          del_idx = st.selectbox(
              "🗑️ اختر الطالب المطلوب حذفه نهائياً:",
              del_options,
              format_func=lambda x: (
                  f"{df_st.loc[x, 'name']} - (الرقم: {df_st.loc[x, 'id']})"
              ),
              key="del_select",
          )
          student_to_delete = df_st.loc[del_idx, "name"]
          st.error(
              f"⚠️ تحذير: سيتم حذف بيانات ({student_to_delete}) نهائياً من"
              " قاعدة البيانات."
          )
          if st.button(
              f"🚨 نعم، تأكيد حذف {student_to_delete}",
              type="primary",
              use_container_width=True,
          ):
            sh.worksheet("students").delete_rows(int(del_idx) + 2)
            st.session_state.toast_msg = (
                f"🗑️ تم حذف '{student_to_delete}' بشكل نهائي!"
            )
            if "db_loaded" in st.session_state:
              del st.session_state["db_loaded"]
            st.cache_data.clear()
            st.rerun()
        else:
          st.info("لا توجد بيانات للطلاب بعد.")
      else:
        st.info("💡 وضع القراءة فقط: ليس لديك صلاحية لحذف الطلاب.")
# ==========================================
# 📊 6. التبويب الثاني: الرصد والتقييم (فردي، جماعي، مدقق الرصد)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_eval:
    st.subheader("📊 الرصد والتقييم الأكاديمي والسلوكي")
    eval_tabs = st.tabs([
        "👤 التقييم الفردي",
        "👥 الرصد الجماعي السريع",
        "🔍 مدقق رصد الدرجات (النواقص)",
    ])

    # --- 1. التقييم الفردي ---
    with eval_tabs[0]:
      df_ev = st.session_state.df_students
      if not df_ev.empty:
        col_f_cls, col_f_st = st.columns([1, 2.5])
        cls_list_ev = ["الكل"] + list(df_ev["class"].dropna().unique())
        sel_cls_ev = col_f_cls.selectbox(
            "🏫 تصفية بالصف:", cls_list_ev, key="eval_cls_filter"
        )

        df_ev_filtered = (
            df_ev if sel_cls_ev == "الكل" else df_ev[df_ev["class"] == sel_cls_ev]
        )
        st_dict = {
            f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0]
            for _, r in df_ev_filtered.iterrows()
        }
        sel = col_f_st.selectbox(
            "🎯 اختر الطالب من القائمة:",
            [""] + list(st_dict.keys()),
            key="single_eval_sel",
        )

        if sel:
          sid = str(st_dict[sel]).strip().split(".")[0]
          student_idx = df_ev[
              df_ev.iloc[:, 0].astype(str).str.split(".").str[0] == sid
          ].index[0]
          s_inf = df_ev.loc[student_idx]

          s_nm = s_inf["name"]
          clp = clean_phone_number(s_inf.get("الجوال", ""))
          s_eml = s_inf.get("الإيميل", "")
          current_points = int(
              pd.to_numeric(s_inf.get("النقاط", 0), errors="coerce") or 0
          )

          c1, c2 = st.columns(2)

          # --- قسم السلوك الفردي ---
          with c2:
            with st.container(border=True):
              st.markdown(
                  f"##### 🎭 السلوك والملاحظات (الرصيد: <span style='color:{warning_color};'>{current_points}</span> نقطة)",
                  unsafe_allow_html=True,
              )
              if st.session_state.role == "teacher":
                with st.form("beh_add", clear_on_submit=True):
                  bt = st.selectbox(
                      "نوع السلوك",
                      [
                          "🌟 متميز (+10)",
                          "✅ إيجابي (+5)",
                          "📝 حل الواجب (+5)",
                          "🎯 أداء المهمة (+10)",
                          "📂 ملف الإنجاز (+10)",
                          "⚠️ تنبيه (0)",
                          "📚 نقص كتاب (-5)",
                          "✍️ نقص واجب (-5)",
                          "🖊️ نقص أدوات الكتابة (-5)",
                          "💤 النوم داخل الفصل (-3)",
                          "🏃 تأخر عن الحصة (-5)",
                          "❌ عدم إحضار ملف الإنجاز (-10)",
                          "🚫 سلبي (-10)",
                      ],
                  )
                  bn = st.text_area("تفاصيل الملاحظة (اختياري)")

                  if st.form_submit_button(
                      "💾 تسجيل السلوك",
                      type="primary",
                      use_container_width=True,
                  ):
                    new_b_row = {
                        "student_id": sid,
                        "date": str(datetime.date.today()),
                        "type": bt,
                        "note": bn,
                    }
                    if safe_append_row("behavior", new_b_row):
                      match = re.search(r"\(([\+\-]?\d+)\)", bt)
                      chg = int(match.group(1)) if match else 0
                      if chg != 0:
                        try:
                          ws = sh.worksheet("students")
                          c = ws.find(sid)
                          if c:
                            h = ws.row_values(1)
                            if "النقاط" in h:
                              idx = h.index("النقاط") + 1
                              new_val = current_points + chg
                              ws.update_cell(c.row, idx, str(new_val))
                              st.session_state.df_students.loc[
                                  student_idx, "النقاط"
                              ] = str(new_val)
                        except Exception as e:
                          st.error(f"خطأ: {e}")

                      st.cache_data.clear()
                      if "db_loaded" in st.session_state:
                        del st.session_state["db_loaded"]
                      st.toast(
                          f"✅ تم إضافة الملاحظة للطالب {s_nm} وتحديث رصيده!",
                          icon="🎉",
                      )
                      st.rerun()
              else:
                st.info("💡 وضع القراءة فقط.")

          # --- قسم الدرجات الأكاديمية ---
          with c1:
            with st.container(border=True):
              cp = st.session_state.get("current_period", "الفترة الأولى").strip()
              st.markdown(f"##### 📝 رصد الدرجات ({cp})")

              df_g = st.session_state.df_grades.copy()
              cur_p1, cur_p2 = 0, 0

              if not df_g.empty:
                df_g["clean_id"] = (
                    df_g.iloc[:, 0].astype(str).str.split(".").str[0]
                )
                if "period" not in df_g.columns:
                  df_g["period"] = "الفترة الأولى"
                df_g["period"] = (
                    df_g["period"]
                    .replace(["", None, "nan", "NaN"], "الفترة الأولى")
                    .astype(str)
                    .str.strip()
                )

                gr_match = df_g[
                    (df_g["clean_id"] == sid) & (df_g["period"] == cp)
                ]
                if not gr_match.empty:
                  cur_p1 = int(
                      pd.to_numeric(gr_match.iloc[-1]["p1"], errors="coerce")
                      or 0
                  )
                  cur_p2 = int(
                      pd.to_numeric(gr_match.iloc[-1]["p2"], errors="coerce")
                      or 0
                  )

              if st.session_state.role == "teacher":
                with st.form("gr_upd", clear_on_submit=False):
                  v1 = st.number_input(
                      "درجة المشاركة والمهام",
                      0,
                      st.session_state.get("max_tasks", 60),
                      cur_p1,
                  )
                  v2 = st.number_input(
                      "درجة الاختبارات",
                      0,
                      st.session_state.get("max_quiz", 40),
                      cur_p2,
                  )

                  if st.form_submit_button(
                      "💾 حفظ الدرجات",
                      type="primary",
                      use_container_width=True,
                  ):
                    tot = v1 + v2
                    ws_g = sh.worksheet("grades")

                    headers = ws_g.row_values(1)
                    if "period" not in headers:
                      ws_g.update_cell(1, len(headers) + 1, "period")
                      headers.append("period")

                    records = ws_g.get_all_records()
                    row_to_update = None

                    for i, r in enumerate(records):
                      r_id = str(r.get(headers[0], "")).strip().split(".")[0]
                      r_period = str(r.get("period", "الفترة الأولى")).strip()
                      if r_id == sid and r_period == cp:
                        row_to_update = i + 2
                        break

                    if row_to_update:
                      ws_g.update_cell(row_to_update, 2, v1)
                      ws_g.update_cell(row_to_update, 3, v2)
                      ws_g.update_cell(row_to_update, 4, tot)
                      ws_g.update_cell(
                          row_to_update, 5, str(datetime.date.today())
                      )
                      ws_g.update_cell(
                          row_to_update, headers.index("period") + 1, cp
                      )
                    else:
                      new_row = [sid, v1, v2, tot, str(datetime.date.today())]
                      while len(new_row) < len(headers) - 1:
                        new_row.append("")
                      new_row.append(cp)
                      ws_g.append_row(new_row)

                    st.session_state["show_refresh_success"] = True
                    if "db_loaded" in st.session_state:
                      del st.session_state["db_loaded"]
                    st.cache_data.clear()
                    st.rerun()
              else:
                st.info("💡 وضع القراءة فقط.")
              st.caption(f"📊 المجموع الحالي لـ {cp}: {cur_p1 + cur_p2}")

          # --- سجل السلوك السفلي ---
          st.markdown("#### 📜 سجل السلوك الأخير للطالب")
          df_b = st.session_state.df_behavior
          if not df_b.empty:
            cid = (
                "student_id"
                if "student_id" in df_b.columns
                else df_b.columns[0]
            )
            df_b["clean_cid"] = (
                df_b[cid].astype(str).str.strip().str.split(".").str[0]
            )
            my_b = df_b[df_b["clean_cid"] == sid].copy()

            if not my_b.empty:
              my_b = my_b.iloc[::-1]
              my_b["date_parsed"] = pd.to_datetime(
                  my_b["date"], errors="coerce"
              )
              my_b = my_b.sort_values(
                  by="date_parsed", ascending=False, kind="mergesort"
              )

              def delete_behavior(global_idx, b_type):
                try:
                  sh.worksheet("behavior").delete_rows(int(global_idx) + 2)
                  match = re.search(r"\(([\+\-]?\d+)\)", str(b_type))
                  chg = int(match.group(1)) if match else 0
                  if chg != 0:
                    ws_st = sh.worksheet("students")
                    c = ws_st.find(sid)
                    if c:
                      h = ws_st.row_values(1)
                      if "النقاط" in h:
                        idx = h.index("النقاط") + 1
                        curr = int(
                            pd.to_numeric(
                                ws_st.cell(c.row, idx).value, errors="coerce"
                            )
                            or 0
                        )
                        ws_st.update_cell(c.row, idx, str(curr - chg))
                  st.cache_data.clear()
                  if "db_loaded" in st.session_state:
                    del st.session_state["db_loaded"]
                except Exception:
                  pass

              if "edit_beh_idx" not in st.session_state:
                st.session_state.edit_beh_idx = None

              beh_options_list = [
                  "🌟 متميز (+10)",
                  "✅ إيجابي (+5)",
                  "📝 حل الواجب (+5)",
                  "🎯 أداء المهمة (+10)",
                  "📂 ملف الإنجاز (+10)",
                  "⚠️ تنبيه (0)",
                  "📚 نقص كتاب (-5)",
                  "✍️ نقص واجب (-5)",
                  "🖊️ نقص أدوات الكتابة (-5)",
                  "💤 النوم داخل الفصل (-3)",
                  "🏃 تأخر عن الحصة (-5)",
                  "❌ عدم إحضار ملف الإنجاز (-10)",
                  "🚫 سلبي (-10)",
              ]

              for global_idx, r in my_b.iterrows():
                with st.container():
                  if st.session_state.edit_beh_idx == global_idx:
                    st.markdown(
                        f"<div style='background: var(--secondary-background-color); padding: 15px; border-radius: 12px; border: 2px dashed {accent_color}; margin-bottom: 10px;'>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("###### ✏️ تعديل الملاحظة السلوكية")

                    current_type = str(r.get("type"))
                    type_idx = (
                        beh_options_list.index(current_type)
                        if current_type in beh_options_list
                        else 0
                    )

                    new_type = st.selectbox(
                        "نوع السلوك",
                        beh_options_list,
                        index=type_idx,
                        key=f"edit_type_{global_idx}",
                        label_visibility="collapsed",
                    )
                    new_note = st.text_input(
                        "التفاصيل",
                        value=str(r.get("note", "")),
                        key=f"edit_note_{global_idx}",
                        label_visibility="collapsed",
                    )

                    c_save, c_cancel = st.columns(2)
                    if c_save.button(
                        "💾 حفظ التعديل",
                        type="primary",
                        key=f"save_{global_idx}",
                        use_container_width=True,
                    ):
                      try:
                        with st.spinner("جاري التحديث..."):
                          ws_beh = sh.worksheet("behavior")
                          headers_beh = ws_beh.row_values(1)
                          idx_type = (
                              headers_beh.index("type") + 1
                              if "type" in headers_beh
                              else 3
                          )
                          idx_note = (
                              headers_beh.index("note") + 1
                              if "note" in headers_beh
                              else 4
                          )

                          ws_beh.update_cell(global_idx + 2, idx_type, new_type)
                          ws_beh.update_cell(global_idx + 2, idx_note, new_note)

                          old_match = re.search(
                              r"\(([\+\-]?\d+)\)", current_type
                          )
                          old_pts = int(old_match.group(1)) if old_match else 0

                          new_match = re.search(r"\(([\+\-]?\d+)\)", new_type)
                          new_pts = int(new_match.group(1)) if new_match else 0

                          diff = new_pts - old_pts
                          if diff != 0:
                            ws_st = sh.worksheet("students")
                            c = ws_st.find(sid)
                            if c:
                              h = ws_st.row_values(1)
                              if "النقاط" in h:
                                idx_pts = h.index("النقاط") + 1
                                curr = int(
                                    pd.to_numeric(
                                        ws_st.cell(c.row, idx_pts).value,
                                        errors="coerce",
                                    )
                                    or 0
                                )
                                ws_st.update_cell(
                                    c.row, idx_pts, str(curr + diff)
                                )

                          st.session_state.edit_beh_idx = None
                          st.cache_data.clear()
                          if "db_loaded" in st.session_state:
                            del st.session_state["db_loaded"]
                          st.toast("✅ تم التعديل بنجاح!", icon="✏️")
                          st.rerun()
                      except Exception as e:
                        st.error(f"خطأ في التعديل: {e}")

                    if c_cancel.button(
                        "❌ إلغاء",
                        key=f"cancel_{global_idx}",
                        use_container_width=True,
                    ):
                      st.session_state.edit_beh_idx = None
                      st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                  else:
                    color = (
                        danger_color
                        if "سلبي" in str(r.get("type"))
                        or "-" in str(r.get("type"))
                        else success_color
                    )
                    st.markdown(
                        f"""
                        <div class="mobile-list-item" style="border-right: 5px solid {color};">
                            <div><b>{r.get('type')}</b> | <small style="color:#94A3B8;">{r.get('date')}</small><br><span style="color:#94A3B8;">{r.get('note')}</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    c_edit, c_del, c_wa, c_em = st.columns([0.5, 0.5, 1, 1])
                    lnk = get_professional_msg(
                        s_nm, r.get("type"), r.get("note"), r.get("date")
                    )
                    c_wa.link_button(
                        "💬 واتساب",
                        f"https://api.whatsapp.com/send?phone={clp}&text={lnk}",
                        use_container_width=True,
                    )
                    c_em.link_button(
                        "📧 إيميل",
                        f"mailto:{s_eml}?subject=ملاحظة: {s_nm}&body={lnk}",
                        use_container_width=True,
                    )

                    if st.session_state.role == "teacher":
                      if c_edit.button(
                          "✏️",
                          key=f"ed_beh_{global_idx}",
                          help="تعديل السجل",
                          use_container_width=True,
                      ):
                        st.session_state.edit_beh_idx = global_idx
                        st.rerun()
                      c_del.button(
                          "❌",
                          key=f"dl_beh_{global_idx}",
                          on_click=delete_behavior,
                          args=(global_idx, r.get("type")),
                          help="حذف نهائي",
                          use_container_width=True,
                      )
            else:
              st.success("✨ سجل الطالب نظيف ولا توجد ملاحظات مسجلة.")
      else:
        st.info("لا توجد بيانات طلاب.")

    # --- 2. الرصد الجماعي السريع ---
    with eval_tabs[1]:
      if st.session_state.role == "teacher":
        st.markdown("#### 🚀 الرصد الجماعي للملاحظات والواجبات")
        st.info(
            "💡 اختر الصف، وحدد الملاحظات للطلاب المعنيين فقط، ثم اضغط حفظ بالأسفل لترصد للجميع دفعة واحدة."
        )

        bulk_class = st.selectbox(
            "🎯 اختر الصف للرصد الجماعي:",
            st.session_state.class_options,
            key="bulk_class_sel",
        )
        df_st_bulk = st.session_state.df_students.copy()

        if not df_st_bulk.empty:
          df_st_bulk["clean_class"] = (
              df_st_bulk.iloc[:, 2].astype(str).str.strip()
          )
          class_students = df_st_bulk[
              df_st_bulk["clean_class"] == bulk_class.strip()
          ]

          if not class_students.empty:
            class_students = class_students.sort_values("name")

            with st.form("bulk_behavior_form", clear_on_submit=True):
              beh_options = [
                  "--- بدون ملاحظة ---",
                  "🌟 متميز (+10)",
                  "✅ إيجابي (+5)",
                  "📝 حل الواجب (+5)",
                  "🎯 أداء المهمة (+10)",
                  "📂 ملف الإنجاز (+10)",
                  "⚠️ تنبيه (0)",
                  "📚 نقص كتاب (-5)",
                  "✍️ نقص واجب (-5)",
                  "🖊️ نقص أدوات الكتابة (-5)",
                  "💤 النوم داخل الفصل (-3)",
                  "🏃 تأخر عن الحصة (-5)",
                  "❌ عدم إحضار ملف الإنجاز (-10)",
                  "🚫 سلبي (-10)",
              ]

              bulk_data = {}
              col_n, col_b, col_t = st.columns([1.5, 2, 2])
              col_n.markdown("**👤 اسم الطالب**")
              col_b.markdown("**🎭 السلوك**")
              col_t.markdown("**📝 ملاحظة (اختياري)**")
              st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

              for _, row in class_students.iterrows():
                sid_b = str(row.iloc[0]).split(".")[0].strip()
                sname_b = row.iloc[1]

                c1, c2, c3 = st.columns([1.5, 2, 2])
                c1.markdown(
                    f"<div style='padding-top:12px; font-weight:700;'>{sname_b}</div>",
                    unsafe_allow_html=True,
                )
                b_type = c2.selectbox(
                    "السلوك",
                    beh_options,
                    key=f"b_type_{sid_b}",
                    label_visibility="collapsed",
                )
                b_note = c3.text_input(
                    "تفاصيل",
                    key=f"b_note_{sid_b}",
                    label_visibility="collapsed",
                    placeholder="أضف تفاصيل...",
                )

                bulk_data[sid_b] = {"type": b_type, "note": b_note}
                st.markdown(
                    "<div style='border-bottom: 1px dashed rgba(148,163,184,0.25); margin: 4px 0;'></div>",
                    unsafe_allow_html=True,
                )

              if st.form_submit_button(
                  "🚀 حفظ الرصد الجماعي للجميع",
                  type="primary",
                  use_container_width=True,
              ):
                behavior_rows_to_add = []
                point_updates = {}

                for sid_key, data in bulk_data.items():
                  if data["type"] != "--- بدون ملاحظة ---":
                    behavior_rows_to_add.append([
                        sid_key,
                        str(datetime.date.today()),
                        data["type"],
                        data["note"],
                    ])
                    match = re.search(r"\(([\+\-]?\d+)\)", data["type"])
                    if match:
                      point_updates[sid_key] = int(match.group(1))

                if behavior_rows_to_add:
                  try:
                    with st.spinner("جاري حفظ الرصد الجماعي وتحديث النقاط..."):
                      sh.worksheet("behavior").append_rows(behavior_rows_to_add)
                      ws_st = sh.worksheet("students")
                      all_st = ws_st.get_all_records()
                      headers = ws_st.row_values(1)

                      if "النقاط" in headers:
                        p_idx = headers.index("النقاط") + 1
                        from gspread import Cell
                        cells_to_update = []
                        for i, r in enumerate(all_st):
                          st_id = str(r.get("id", "")).split(".")[0].strip()
                          if st_id in point_updates:
                            cur_p = int(
                                pd.to_numeric(
                                    r.get("النقاط", 0), errors="coerce"
                                )
                                or 0
                            )
                            new_p = cur_p + point_updates[st_id]
                            cells_to_update.append(
                                Cell(row=i + 2, col=p_idx, value=str(new_p))
                            )
                        if cells_to_update:
                          ws_st.update_cells(cells_to_update)

                      st.success(
                          f"✅ تمت المهمة بنجاح! تم رصد ({len(behavior_rows_to_add)}) ملاحظة."
                      )
                      st.cache_data.clear()
                      if "db_loaded" in st.session_state:
                        del st.session_state["db_loaded"]
                      st.rerun()
                  except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
                else:
                  st.warning(
                      "⚠️ لم تقم باختيار أي سلوك لأي طالب ليتم حفظه."
                  )
          else:
            st.info("لا يوجد طلاب مسجلين في هذا الصف.")
      else:
        st.info("💡 وضع القراءة فقط.")

    # --- 3. مدقق رصد الدرجات (كشف النواقص) ---
    with eval_tabs[2]:
      cp_aud = st.session_state.get("current_period", "الفترة الأولى").strip()
      st.markdown(f"#### 🔍 مدقق رصد الدرجات ({cp_aud})")
      st.info(
          "💡 يعرض هذا المدقق قائمة الطلاب الذين لم تُرصد لهم درجات في الفترة النشطة حالياً."
      )

      df_st_audit = st.session_state.df_students.copy()
      df_gr_audit = st.session_state.df_grades.copy()

      if not df_st_audit.empty:
        df_st_audit["clean_id"] = (
            df_st_audit.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]
        )

        if not df_gr_audit.empty:
          df_gr_audit["clean_id"] = (
              df_gr_audit.iloc[:, 0]
              .astype(str)
              .str.strip()
              .str.split(".")
              .str[0]
          )
          if "period" not in df_gr_audit.columns:
            df_gr_audit["period"] = "الفترة الأولى"
          df_gr_audit["period"] = (
              df_gr_audit["period"]
              .replace(["", None, "nan", "NaN"], "الفترة الأولى")
              .astype(str)
              .str.strip()
          )
          df_gr_curr = df_gr_audit[df_gr_audit["period"] == cp_aud]

          audit_merge = pd.merge(
              df_st_audit[["clean_id", "name", "class", "sem"]],
              df_gr_curr[["clean_id", "perf"]],
              on="clean_id",
              how="left",
          )
          missing_grades = audit_merge[audit_merge["perf"].isna()]
        else:
          missing_grades = df_st_audit[["clean_id", "name", "class", "sem"]]

        if not missing_grades.empty:
          st.warning(
              f"⚠️ يوجد ({len(missing_grades)}) طالب لم ترصد لهم درجات في ({cp_aud})."
          )
          display_missing = missing_grades[
              ["clean_id", "name", "class", "sem"]
          ].rename(
              columns={
                  "clean_id": "الرقم الأكاديمي",
                  "name": "اسم الطالب",
                  "class": "الصف",
                  "sem": "المرحلة",
              }
          )
          st.dataframe(
              display_missing, use_container_width=True, hide_index=True
          )

          b_audit = io.BytesIO()
          with pd.ExcelWriter(b_audit, engine="xlsxwriter") as writer:
            display_missing.to_excel(
                writer, index=False, sheet_name="Missing_Grades"
            )

          st.download_button(
              label="📥 تحميل قائمة نواقص الرصد (Excel)",
              data=b_audit.getvalue(),
              file_name=f"missing_grades_{datetime.date.today()}.xlsx",
              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              type="primary",
              use_container_width=True,
          )
        else:
          st.success(
              f"✅ ممتاز! جميع الطلاب المسجلين تم رصد درجاتهم في ({cp_aud}) بنجاح."
          )
      else:
        st.info("لا توجد بيانات طلاب للتدقيق.")


# ==========================================
# 🏆 7. التبويب الثالث: الشرف والشهادات الإلكترونية
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_honor:
    st.subheader("🏆 لوحات الشرف وإصدار الشهادات الإلكترونية")
    df_st_h = st.session_state.df_students.copy()
    if not df_st_h.empty:
      df_st_h["clean_id"] = (
          df_st_h.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      )
      df_st_h["النقاط"] = pd.to_numeric(
          df_st_h["النقاط"], errors="coerce"
      ).fillna(0)

    honor_tabs = st.tabs([
        "🌟 لوحة الشرف (النقاط)",
        "🎓 المتفوقون أكاديمياً (90%+)",
        "📜 استخراج شهادات المتفوقين إلكترونياً",
    ])

    lux_css = """
        * { box-sizing: border-box; } 
        body { margin: 0; padding: 0; background: #F8FAFC; font-family: 'Cairo', sans-serif; text-align: center; direction: rtl; }
        .page { width: 210mm; padding: 10mm; display: flex; flex-wrap: wrap; justify-content: center; gap: 4%; margin: 0 auto; }
        .card { width: 46%; height: 135mm; border-radius: 15px; position: relative; overflow: hidden; background: #fff; box-shadow: 0 15px 35px rgba(0,0,0,0.15); page-break-inside: avoid; margin-bottom: 20px; }
        .ribbon { position: absolute; top: 20px; right: -35px; padding: 5px 40px; font-weight: 900; font-size: 15px; transform: rotate(45deg); z-index: 10; box-shadow: 0 4px 6px rgba(0,0,0,0.2); font-family: 'Cairo', sans-serif; letter-spacing: 1px; }
        .ribbon.gold { background: linear-gradient(45deg, #FFD700, #FFA500); color: #8B4513; }
        .ribbon.silver { background: linear-gradient(45deg, #E2E8F0, #94A3B8); color: #1E293B; }
        .ribbon.bronze { background: linear-gradient(45deg, #FDBA74, #D97706); color: #78350F; }
        .card-inner { position: absolute; top: 12px; bottom: 12px; left: 12px; right: 12px; border: 2px dashed #b68a36; border-radius: 10px; padding: 20px 10px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; background-color: rgba(255,255,255,0.95); }
        .c-icon { font-size: 45px; line-height: 1; margin-bottom: 5px; width: 100%; text-align: center; }
        .c-header { font-family: 'Aref Ruqaa', serif; font-size: 30px; font-weight: bold; width: 100%; text-align: center; margin-bottom: 5px; color: #b68a36; }
        .c-teacher { font-size: 14px; color: #475569; font-weight: bold; width: 100%; text-align: center; margin-bottom: 10px; }
        .c-name { font-size: 26px; font-weight: 900; line-height: 1.4; width: 100%; text-align: center; display: flex; align-items: center; justify-content: center; flex-grow: 1; padding: 0 10px; word-wrap: break-word; }
        .c-badge { width: 80%; margin: 10px auto; padding: 15px 5px; border-radius: 12px; background: #fff; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; }
        .c-badge.rank-1 { background: linear-gradient(145deg, #FFF8DC, #FFD700); border-color: #DAA520; }
        .c-badge.rank-2 { background: linear-gradient(145deg, #F8F9FA, #E2E8F0); border-color: #94A3B8; }
        .c-badge.rank-3 { background: linear-gradient(145deg, #FFF1F2, #FECDD3); border-color: #CD7F32; }
        .b-val { display: block; font-size: 30px; font-weight: 900; line-height: 1; margin-bottom: 5px; }
        .b-lbl { display: block; font-size: 14px; font-weight: bold; color: #64748B; }
        .rank-1 .b-val { color: #8B4513; font-size: 36px; } .rank-1 .b-lbl { color: #A0522D; }
        .rank-2 .b-val { color: #1E293B; font-size: 34px; } .rank-2 .b-lbl { color: #334155; }
        .rank-3 .b-val { color: #78350F; font-size: 34px; } .rank-3 .b-lbl { color: #92400E; }
        .c-footer { font-family: 'Amiri', serif; font-size: 18px; font-weight: bold; width: 100%; text-align: center; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1); }
        .theme-honor { border: 14px solid #1E40AF; } 
        .theme-honor .c-name, .theme-honor .b-val:not(.rank-1 .b-val):not(.rank-2 .b-val):not(.rank-3 .b-val), .theme-honor .c-footer { color: #1E40AF; }
        .theme-academic { border: 14px solid #881337; } 
        .theme-academic .c-name, .theme-academic .b-val, .theme-academic .c-footer { color: #881337; }
        @media print { @page { size: A4 portrait; margin: 5mm; } body { background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; } .card { box-shadow: none; margin-bottom: 10mm; border-width: 10px; } }
    """

    # --- 1. لوحة الشرف (النقاط) ---
    with honor_tabs[0]:
      st.markdown("#### 🌟 أفضل 10 طلاب (حسب نقاط التميز)")
      if not df_st_h.empty:
        active_students = df_st_h[df_st_h["النقاط"] > 0]
        if not active_students.empty:
          top_10 = active_students.sort_values(
              "النقاط", ascending=False
          ).head(10)

          for i, (_, r) in enumerate(top_10.iterrows(), 1):
            ic = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            brd_col = "#F59E0B" if i <= 3 else "rgba(148, 163, 184, 0.35)"
            st.markdown(
                f"""
                <div style='background:var(--secondary-background-color); border:1.5px solid rgba(148,163,184,0.28); border-right:5px solid {brd_col}; padding:15px; border-radius:14px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                    <div style='display:flex; align-items:center; gap:15px;'>
                        <span style='font-size:1.5rem; font-weight:bold; min-width:45px; display:inline-block; text-align:center; white-space:nowrap;'>{ic}</span>
                        <div style='text-align: right;'>
                            <b style='font-size:1.1rem; color:{accent_color};'>{r.get('name', '')}</b><br>
                            <small style='color:#94A3B8;'>🏫 الصف: {r.get('class', '')} | 🆔 ID: {r.get('clean_id', '')}</small>
                        </div>
                    </div>
                    <div style='background:rgba(245, 158, 11, 0.15); border:1px solid rgba(245, 158, 11, 0.4); padding:6px 15px; border-radius:10px; color:#F59E0B; font-weight:900; font-size:1.15rem;'>
                        {int(r.get('النقاط', 0))} نقطة
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

          st.markdown("---")
          honor_cards_content = ""
          summary_list_html = ""

          for rank, (_, row) in enumerate(top_10.iterrows(), 1):
            student_name = row.get("name", "اسم غير متوفر")
            s_cls = row.get("class", "")
            score = int(row.get("النقاط", 0))

            if rank == 1:
              rank_text, icon, ribbon_html, badge_class = (
                  "المركز الأول",
                  "🏆",
                  '<div class="ribbon gold">الأول</div>',
                  "rank-1",
              )
              med, bg, brd, txt = (
                  "🥇",
                  "linear-gradient(135deg, #FFF8DC, #FFFAF0)",
                  "#DAA520",
                  "#8B4513",
              )
            elif rank == 2:
              rank_text, icon, ribbon_html, badge_class = (
                  "المركز الثاني",
                  "🥈",
                  '<div class="ribbon silver">الثاني</div>',
                  "rank-2",
              )
              med, bg, brd, txt = (
                  "🥈",
                  "linear-gradient(135deg, #F8F9FA, #FFFFFF)",
                  "#94A3B8",
                  "#1E293B",
              )
            elif rank == 3:
              rank_text, icon, ribbon_html, badge_class = (
                  "المركز الثالث",
                  "🥉",
                  '<div class="ribbon bronze">الثالث</div>',
                  "rank-3",
              )
              med, bg, brd, txt = (
                  "🥉",
                  "linear-gradient(135deg, #FFF1F2, #FFFBFB)",
                  "#CD7F32",
                  "#92400E",
              )
            else:
              rank_text, icon, ribbon_html, badge_class = (
                  f"المركز {rank}",
                  "🌟",
                  "",
                  "",
              )
              med, bg, brd, txt = f"#{rank}", "#FFFFFF", "#E2E8F0", "#334155"

            honor_cards_content += f"""
            <div class="card theme-honor">
                {ribbon_html}
                <div class="card-inner">
                    <div class="c-icon">{icon}</div>
                    <div class="c-header">بطاقة تميز طالب</div>
                    <div class="c-teacher">إشراف الأستاذ/ زياد المعمري</div>
                    <div class="c-name">{student_name}</div>
                    <div class="c-badge {badge_class}">
                        <span class="b-val">{score}</span>
                        <span class="b-lbl">نقطة تميز</span>
                    </div>
                    <div class="c-footer">{rank_text}</div>
                </div>
            </div>
            """

            summary_list_html += f"""
            <div class="row-card" style="background:{bg}; border-color:{brd};">
                <div style="display:flex; align-items:center; gap:15px;">
                    <div class="rank-icon">{med}</div>
                    <div style="text-align: right;">
                        <div class="student-name" style="color:{txt};">{student_name}</div>
                        <div class="student-class">الصف: {s_cls}</div>
                    </div>
                </div>
                <div class="score-badge" style="color:{txt}; border-color:{brd};">
                    {score} <span>نقطة</span>
                </div>
            </div>
            """

          honor_full_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet"><style>{lux_css}</style></head><body><div class="page">{honor_cards_content}</div><script>window.onload = function() {{ window.print(); }}</script></body></html>"""

          top10_summary_html = f"""
          <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>لوحة الشرف - أفضل 10 طلاب</title>
          <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
          <style>
              body {{ font-family: 'Cairo', sans-serif; background: #F8FAFC; margin: 0; padding: 20px; -webkit-print-color-adjust: exact; print-color-adjust: exact; direction: rtl; }}
              .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 16px; border: 1px solid #E2E8F0; }}
              .header {{ text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px dashed #E2E8F0; }}
              .h-title {{ font-size: 32px; font-weight: 900; color: #1E40AF; margin: 0 0 5px 0; }}
              .h-sub {{ font-size: 18px; color: #64748B; margin: 0; }}
              .h-date {{ display: inline-block; margin-top: 10px; background: #EFF6FF; color: #2563EB; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
              .row-card {{ display: flex; justify-content: space-between; align-items: center; border: 1px solid; border-right-width: 6px; padding: 12px 20px; border-radius: 10px; margin-bottom: 12px; }}
              .rank-icon {{ font-size: 24px; font-weight: 900; width: 45px; text-align: center; }}
              .student-name {{ font-size: 20px; font-weight: 900; }}
              .student-class {{ font-size: 14px; color: #64748B; }}
              .score-badge {{ font-size: 24px; font-weight: 900; background: rgba(255,255,255,0.7); padding: 5px 15px; border-radius: 8px; border: 1px dashed; }}
              .score-badge span {{ font-size: 14px; font-weight: bold; }}
              @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} body {{ padding: 0; background: white; }} .container {{ padding: 0; border: none; }} .row-card {{ padding: 6px 15px; margin-bottom: 7px; }} }}
          </style></head><body>
          <div class="container">
              <div class="header">
                  <h1 class="h-title">🌟 لوحة الشرف والتميز 🌟</h1>
                  <p class="h-sub">أفضل 10 طلاب متصدرين في المنصة بإشراف الأستاذ/ زياد المعمري</p>
                  <div class="h-date">تاريخ الإصدار: {datetime.date.today().strftime('%Y-%m-%d')}</div>
              </div>
              <div>{summary_list_html}</div>
          </div><script>window.onload = function() {{ window.print(); }}</script></body></html>
          """

          c_btn1, c_btn2 = st.columns(2)
          c_btn1.download_button(
              label="🎴 طباعة البطاقات الفردية للمتصدرين",
              data=honor_full_html,
              file_name=f"Honor_Cards_{datetime.date.today()}.html",
              mime="text/html",
              use_container_width=True,
              type="primary",
          )
          c_btn2.download_button(
              label="📋 طباعة كشف الشرف الشامل (أفضل 10)",
              data=top10_summary_html,
              file_name=f"Top10_Summary_{datetime.date.today()}.html",
              mime="text/html",
              use_container_width=True,
          )
        else:
          st.info("لم يحصل أي طالب على نقاط تميز حتى الآن.")

    # --- 2. المتفوقون أكاديمياً (90%+) ---
    with honor_tabs[1]:
      cp = st.session_state.get("current_period", "الفترة الأولى").strip()
      st.markdown(f"#### 🎓 لوحة المتفوقين أكاديمياً ({cp})")

      if (
          "df_grades" in st.session_state
          and not st.session_state.df_grades.empty
          and not df_st_h.empty
      ):
        df_g = st.session_state.df_grades.copy()
        df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0]
        if "period" not in df_g.columns:
          df_g["period"] = "الفترة الأولى"
        df_g["period"] = (
            df_g["period"]
            .replace(["", None, "nan", "NaN"], "الفترة الأولى")
            .astype(str)
            .str.strip()
        )
        df_g = df_g[df_g["period"] == cp]

        merged_df = pd.merge(
            df_g,
            df_st_h[["clean_id", "name", "class", "الجوال"]],
            on="clean_id",
            how="inner",
        )

        if not merged_df.empty:
          max_total = st.session_state.get(
              "max_tasks", 60
          ) + st.session_state.get("max_quiz", 40)
          if max_total > 0:
            merged_df["perf_num"] = pd.to_numeric(
                merged_df["perf"], errors="coerce"
            ).fillna(0)
            merged_df["percentage"] = (merged_df["perf_num"] / max_total) * 100
            top_academic = merged_df[merged_df["percentage"] >= 90].sort_values(
                "percentage", ascending=False
            )

            if not top_academic.empty:
              for _, r in top_academic.iterrows():
                st.markdown(
                    f"""
                    <div style='background:var(--secondary-background-color); border:1.5px solid rgba(148,163,184,0.28); border-right:5px solid {success_color}; padding:15px; border-radius:14px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                        <div style='display:flex; align-items:center; gap:15px;'>
                            <span style='font-size:1.5rem;'>🎓</span>
                            <div style='text-align:right;'>
                                <b style='font-size:1.1rem; color:{success_color};'>{r.get('name', '')}</b><br>
                                <small style='color:#94A3B8;'>🏫 الصف: {r.get('class', '')} | 📊 الدرجة: {int(r.get('perf_num', 0))}/{max_total} ({round(r.get('percentage', 0), 1)}%)</small>
                            </div>
                        </div>
                        <div style='background:rgba(16, 185, 129, 0.15); border:1px solid rgba(16, 185, 129, 0.4); padding:5px 15px; border-radius:10px; color:{success_color}; font-weight:900;'>
                            ممتاز 🌟
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

              st.markdown("---")
              academic_cards_content = ""
              for _, row in top_academic.iterrows():
                academic_cards_content += f"""
                <div class="card theme-academic">
                    <div class="ribbon gold">متفوق</div>
                    <div class="card-inner">
                        <div class="c-icon">🎖️</div>
                        <div class="c-header">وسام التميز الأكاديمي</div>
                        <div class="c-teacher">إشراف الأستاذ/ زياد المعمري</div>
                        <div class="c-name">{row.get('name', 'طالب')}</div>
                        <div class="c-badge rank-1">
                            <span class="b-val">ممتاز</span>
                            <span class="b-lbl">في مادة اللغة الإنجليزية</span>
                        </div>
                        <div class="c-footer">مع تمنياتنا بدوام التألق والنجاح</div>
                    </div>
                </div>
                """

              academic_full_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet"><style>{lux_css}</style></head><body><div class="page">{academic_cards_content}</div><script>window.onload = function() {{ window.print(); }}</script></body></html>"""

              st.download_button(
                  label="🌐 تحميل بطاقات المتفوقين (تصميم واقعي للطباعة)",
                  data=academic_full_html,
                  file_name=f"Excellence_Cards_{datetime.date.today()}.html",
                  mime="text/html",
                  use_container_width=True,
                  type="primary",
              )
            else:
              st.info(f"لم يصل أحد لنسبة 90% في ({cp}) حتى الآن.")
        else:
          st.info(f"لا توجد درجات مطابقة للطلاب في ({cp}).")
      else:
        st.info("لم يتم رصد درجات بعد.")

    # --- 3. ✳️ إضافة جديدة: استخراج شهادات المتفوقين إلكترونياً ---
    with honor_tabs[2]:
      st.markdown("#### 📜 مركز إصدار شهادات التفوق والشكر الإلكترونية (A4 Landscape)")
      st.info(
          "💡 يمكنك استخراج شهادات شكر وتقدير إلكترونية رسمية ومختومة (لطالب محدد أو لجميع المتفوقين في فصل كامل دفعة واحدة) جاهزة للطباعة أو الحفظ كـ PDF وإرسال التهنئة لولي الأمر عبر واتساب."
      )

      if not df_st_h.empty:
        c_cert1, c_cert2, c_cert3 = st.columns(3)
        cert_mode = c_cert1.selectbox(
            "1️⃣ نظام الإصدار:",
            [
                "🌟 جميع المتفوقين (90%+) في فصل",
                "👤 طالب محدد (بالاسم)",
                "🏆 أبطال لوحة الشرف (أعلى النقاط)",
            ],
            key="cert_gen_mode",
        )
        cert_period = c_cert2.selectbox(
            "2️⃣ الفترة الدراسية:",
            [
                "الفترة الأولى",
                "الفترة الثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
            ],
            index=0,
            key="cert_gen_period",
        )
        cert_title_opt = c_cert3.selectbox(
            "3️⃣ عنوان الوسام:",
            [
                "وسام التميز الأكاديمي",
                "وسام التفوق والإبداع",
                "شهادة شكر وانضباط سلوكي",
            ],
            key="cert_gen_title",
        )

        target_students_cert = pd.DataFrame()

        if cert_mode == "🌟 جميع المتفوقين (90%+) في فصل":
          cls_cert_opts = ["الكل"] + list(df_st_h["class"].dropna().unique())
          sel_cls_cert = st.selectbox(
              "🏫 اختر الصف:", cls_cert_opts, key="cert_cls_sel"
          )

          df_g_c = st.session_state.df_grades.copy()
          if not df_g_c.empty:
            df_g_c["clean_id"] = (
                df_g_c.iloc[:, 0].astype(str).str.split(".").str[0]
            )
            if "period" not in df_g_c.columns:
              df_g_c["period"] = "الفترة الأولى"
            df_g_c["period"] = (
                df_g_c["period"]
                .replace(["", None, "nan", "NaN"], "الفترة الأولى")
                .astype(str)
                .str.strip()
            )
            df_g_c = df_g_c[df_g_c["period"] == cert_period]

            m_cert = pd.merge(
                df_st_h, df_g_c[["clean_id", "perf"]], on="clean_id", how="inner"
            )
            if sel_cls_cert != "الكل":
              m_cert = m_cert[m_cert["class"] == sel_cls_cert]

            max_t = st.session_state.get(
                "max_tasks", 60
            ) + st.session_state.get("max_quiz", 40)
            if max_t > 0 and not m_cert.empty:
              m_cert["perf_num"] = pd.to_numeric(
                  m_cert["perf"], errors="coerce"
              ).fillna(0)
              m_cert["pct"] = (m_cert["perf_num"] / max_t) * 100
              target_students_cert = m_cert[m_cert["pct"] >= 90].sort_values(
                  "pct", ascending=False
              )

        elif cert_mode == "👤 طالب محدد (بالاسم)":
          st_cert_dict = {
              f"{r['name']} - ({r.get('class', '')})": r["clean_id"]
              for _, r in df_st_h.iterrows()
          }
          sel_st_cert = st.selectbox(
              "🎯 ابحث عن الطالب:", list(st_cert_dict.keys()), key="cert_st_sel"
          )
          if sel_st_cert:
            chosen_id = st_cert_dict[sel_st_cert]
            target_students_cert = df_st_h[df_st_h["clean_id"] == chosen_id]

        elif cert_mode == "🏆 أبطال لوحة الشرف (أعلى النقاط)":
          target_students_cert = (
              df_st_h[df_st_h["النقاط"] > 0]
              .sort_values("النقاط", ascending=False)
              .head(10)
          )

        custom_reason = st.text_input(
            "✍️ عبارة التكريم في الشهادة (قابلة للتعديل):",
            value="وذلك نظير تفوقه العلمي وتميزه وحصوله على تقدير ممتاز في مادة اللغة الإنجليزية.",
            key="cert_custom_reason",
        )

        if not target_students_cert.empty:
          st.success(
              f"✅ تم تجهيز ({len(target_students_cert)}) شهادة إلكترونية جاهزة للإصدار والطباعة."
          )

          all_certs_pages_html = ""
          for _, s_row in target_students_cert.iterrows():
            st_name_c = s_row.get("name", "طالب متفوق")
            st_cls_c = s_row.get("class", "")
            school_c = get_school_name_dynamic(st_cls_c).replace("<br>", " - ")

            all_certs_pages_html += f"""
            <div class="cert-page">
                <div class="border-outer">
                    <div class="border-inner">
                        <div class="corner tl"></div><div class="corner tr"></div>
                        <div class="corner bl"></div><div class="corner br"></div>
                        
                        <div style="display:flex; justify-content:space-between; align-items:center; font-family:'Cairo',sans-serif; font-size:14px; font-weight:bold; color:#193b68; margin-bottom:5px; padding:0 15px;">
                            <div>المملكة العربية السعودية - وزارة التعليم<br>{school_c}</div>
                            <div>العام الدراسي: {st.session_state.get('current_year', '1447هـ')}<br>{cert_period}</div>
                        </div>

                        <h1>شهادة شكر وتقدير</h1>
                        <h2>⭐ {cert_title_opt} ⭐</h2>

                        <p class="intro">يتقدم معلم المادة الأستاذ/ <strong>زياد المعمري</strong> وإدارة المدرسة بوافر الشكر والتقدير للطالب المبدع:</p>
                        <div class="student-name">{st_name_c} <span style="font-size:24px; color:#193b68;">({st_cls_c})</span></div>
                        
                        <div class="reason-container">
                            <p class="reason">{custom_reason}</p>
                            <p class="reason">متمنين له دوام التوفيق ومزيداً من التألق والنجاح.</p>
                        </div>

                        <div class="footer-section">
                            <div class="date-box">
                                <div class="sig-title">مدير المدرسة</div>
                                <div class="sig-line"></div>
                                <div class="date-val">أ. عبدالمجيد الحربي</div>
                            </div>
                            
                            <div class="stamp-wrapper">
                                <div style="width: 130px; height: 130px; border: 3px dashed #d32f2f; border-radius: 50%; transform: rotate(-12deg); color: #d32f2f; text-align: center; opacity: 0.85; position: relative; padding-top: 20px; margin: 0 auto; background-color: rgba(255, 255, 255, 0.8);">
                                    <div style="position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px; border: 1px solid #d32f2f; border-radius: 50%;"></div>
                                    <div style="font-family: 'Cairo', sans-serif; font-size: 14px; font-weight: 900;">منصة زياد الذكية</div>
                                    <div style="font-family: 'Aref Ruqaa', serif; font-size: 30px; font-weight: bold; line-height: 1.2;">ختم التميز</div>
                                    <div style="font-family: 'Cairo', sans-serif; font-size: 12px; font-weight: bold;">{datetime.date.today().strftime('%Y-%m-%d')}</div>
                                </div>
                            </div>

                            <div class="sig-box">
                                <div class="sig-title">معلم المادة</div>
                                <div class="sig-line"></div>
                                <div class="sig-name">زياد المعمري</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """

          master_certs_html = f"""
          <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>شهادات التفوق الإلكترونية</title>
          <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
          <style>
              * {{ box-sizing: border-box; }}
              body {{ margin: 0; padding: 20px; background-color: #f0f2f5; display: flex; flex-direction: column; align-items: center; gap: 25px; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
              .cert-page {{ width: 297mm; height: 209mm; padding: 10mm; background: #ffffff; position: relative; box-shadow: 0 5px 20px rgba(0,0,0,0.12); overflow: hidden; page-break-after: always; }}
              .border-outer {{ border: 12px solid #193b68; height: 100%; width: 100%; padding: 6px; position: relative; }}
              .border-inner {{ border: 3px solid #b68a36; height: 100%; width: 100%; position: relative; padding: 20px 35px; text-align: center; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 25px 25px; display: flex; flex-direction: column; justify-content: space-between; }}
              .corner {{ position: absolute; width: 28px; height: 28px; border: 4px solid #b68a36; }}
              .tl {{ top: -8px; left: -8px; border-right: none; border-bottom: none; }}
              .tr {{ top: -8px; right: -8px; border-left: none; border-bottom: none; }}
              .bl {{ bottom: -8px; left: -8px; border-right: none; border-top: none; }}
              .br {{ bottom: -8px; right: -8px; border-left: none; border-top: none; }}
              h1 {{ font-family: 'Aref Ruqaa', serif; font-size: 62px; color: #b68a36; margin: 0; font-weight: normal; line-height: 1.1; }}
              h2 {{ font-family: 'Cairo', sans-serif; font-size: 28px; color: #193b68; margin: 5px 0 10px 0; font-weight: 900; }}
              p.intro {{ font-family: 'Cairo', sans-serif; font-size: 20px; color: #193b68; margin: 5px 0; }}
              .student-name {{ font-family: 'Cairo', sans-serif; font-size: 46px; font-weight: 900; color: #d32f2f; margin: 8px auto; display: inline-block; border-bottom: 3px solid #b68a36; padding: 0 30px 4px 30px; }}
              .reason-container {{ margin: 10px 0; }}
              p.reason {{ font-family: 'Cairo', sans-serif; font-size: 22px; font-weight: 700; color: #334155; line-height: 1.6; margin: 0; }}
              .footer-section {{ display: flex; justify-content: space-between; align-items: flex-end; padding: 0 30px; font-family: 'Cairo', sans-serif; }}
              .sig-box, .date-box {{ text-align: center; color: #193b68; width: 220px; }}
              .sig-title {{ font-size: 20px; font-weight: bold; }}
              .sig-line {{ border-bottom: 1px solid #b68a36; width: 150px; margin: 6px auto; }}
              .sig-name {{ font-family: 'Aref Ruqaa', serif; font-size: 32px; color: #193b68; }}
              .date-val {{ font-size: 20px; font-weight: 900; color: #193b68; margin-top: 6px; }}
              @media print {{
                  @page {{ size: A4 landscape; margin: 0mm; }}
                  body {{ padding: 0; background: white; gap: 0; }}
                  .cert-page {{ box-shadow: none; width: 297mm; height: 210mm; margin: 0; }}
              }}
          </style></head><body>
          {all_certs_pages_html}
          <script>window.onload = function() {{ window.print(); }}</script>
          </body></html>
          """

          st.download_button(
              label=f"🖨️ استخراج وتحميل الشهادات الإلكترونية ({len(target_students_cert)} شهادة - جاهزة للطباعة والـ PDF)",
              data=master_certs_html,
              file_name=f"Electronic_Certificates_{datetime.date.today()}.html",
              mime="text/html",
              type="primary",
              use_container_width=True,
          )

          with st.expander("📲 إرسال تهنئة سريعة لأولياء أمور المتفوقين عبر واتساب"):
            for _, s_row in target_students_cert.iterrows():
              s_n = s_row.get("name", "")
              s_p = clean_phone_number(s_row.get("الجوال", ""))
              congrats_msg = urllib.parse.quote(
                  f"🌟 *تهنئة تفوق وتميز من منصة الأستاذ زياد المعمري* 🌟\n\n"
                  f"يسرنا تهنئتكم بتفوق الابن المبدع: *{s_n}*\n"
                  f"وحصوله على *{cert_title_opt}* في مادة اللغة الإنجليزية ({cert_period}).\n"
                  f"📜 يمكنكم تحميل شهادة التفوق الإلكترونية مباشرة عبر حساب الطالب في المنصة.\n"
                  f"مع خالص تمنياتنا له بدوام التوفيق والنجاح! 🎉"
              )
              col_w1, col_w2 = st.columns([3, 1])
              col_w1.markdown(
                  f"<div style='padding-top:10px; font-weight:bold;'>🎓 {s_n} ({s_row.get('class', '')})</div>",
                  unsafe_allow_html=True,
              )
              col_w2.link_button(
                  "📲 إرسال تهنئة واتساب",
                  f"https://api.whatsapp.com/send?phone={s_p}&text={congrats_msg}",
                  use_container_width=True,
              )
        else:
          st.warning("⚠️ لا يوجد طلاب يطابقون معيار الشهادات المحدد حالياً.")
# ==========================================
# 🖨️ 8. التبويب الرابع: مركز التقارير والطباعة الشامل (مستقل بالكامل)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_reports:
    st.subheader("🖨️ مركز التقارير والطباعة والاستخراج")
    st.caption(
        "جميع تقارير الطباعة، شواهد الأداء، الكشوفات المرنة، وتصدير ملفات Excel"
        " في مكان واحد"
    )

    df_s_rep = st.session_state.df_students.copy()
    if not df_s_rep.empty:
      df_s_rep["clean_id"] = (
          df_s_rep.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      )
      df_s_rep["النقاط"] = pd.to_numeric(
          df_s_rep["النقاط"], errors="coerce"
      ).fillna(0)

    rep_tabs = st.tabs([
        "📑 تقرير طالب شامل",
        "📊 كشف الدرجات المرصودة",
        "📝 كشف متابعة فارغ (مرن)",
        "🖨️ مساعد التفريغ الورقي",
        "📈 حصر المتفوقين والمتعثرين",
        "🧠 تقرير أنماط التعلم (VARK)",
        "📱 كشف أرقام التواصل",
    ])

    # ---------------------------------------------------------
    # 1. تقرير الطالب الشامل المفصل
    # ---------------------------------------------------------
    with rep_tabs[0]:
      st.markdown("#### 📑 التقرير الشامل المفصل للطالب")
      if not df_s_rep.empty:
        col_r_cls, col_r_st = st.columns([1, 2.5])
        cls_r_opts = ["الكل"] + list(df_s_rep["class"].dropna().unique())
        sel_r_cls = col_r_cls.selectbox(
            "🏫 تصفية بالصف:", cls_r_opts, key="rep_single_cls_filter"
        )

        df_s_rep_f = (
            df_s_rep
            if sel_r_cls == "الكل"
            else df_s_rep[df_s_rep["class"] == sel_r_cls]
        )
        st_dict = {
            f"{r['name']} ({r['clean_id']})": r["clean_id"]
            for _, r in df_s_rep_f.iterrows()
        }
        sel_rep = col_r_st.selectbox(
            "🔍 ابحث عن الطالب لاستخراج التقرير:",
            [""] + list(st_dict.keys()),
            key="rep_sel",
        )

        if sel_rep:
          sid = st_dict[sel_rep]
          s_inf = df_s_rep[df_s_rep["clean_id"] == sid].iloc[0]
          st.markdown("---")

          l_style = "لم يختبر ⏳"
          if "نمط التعلم" in df_s_rep.columns:
            val = s_inf.get("نمط التعلم", "")
            if pd.notna(val) and str(val).strip() not in ["", "nan", "None"]:
              l_style = str(val).strip()

          style_color = (
              "#3B82F6"
              if "بصري" in l_style
              else "#10B981"
              if "سمعي" in l_style
              else "#F59E0B"
              if "حركي" in l_style
              else "#8B5CF6"
              if "متعدد" in l_style
              else "#94A3B8"
          )

          st.markdown(
              f"""
              <div style='background:var(--secondary-background-color); padding:18px; border-radius:14px; border:1.5px solid rgba(148,163,184,0.28); display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px;'>
                  <div>
                      <div style='color:var(--text-color); font-size:1.2rem;'><b>الاسم:</b> <span style='color:{accent_color}; font-weight:900;'>{s_inf['name']}</span></div>
                      <div style='color:#94A3B8; margin-top:5px; font-weight:700;'><b>الصف:</b> {s_inf.get('class', 'غير محدد')} | <b>الرقم الأكاديمي:</b> {sid}</div>
                  </div>
                  <div style='display:flex; gap:12px; text-align:center;'>
                      <div style='background:{style_color}20; border:1.5px solid {style_color}; padding:8px 15px; border-radius:10px;'>
                          <div style='font-size:0.8rem; color:#94A3B8; font-weight:bold;'>🧠 نمط التعلم</div>
                          <div style='font-size:1.05rem; font-weight:900; color:{style_color};'>{l_style}</div>
                      </div>
                      <div style='background:rgba(245, 158, 11, 0.15); border:1.5px solid #F59E0B; padding:8px 15px; border-radius:10px;'>
                          <div style='font-size:0.8rem; color:#F59E0B; font-weight:bold;'>🌟 رصيد النقاط</div>
                          <div style='font-size:1.25rem; font-weight:900; color:#F59E0B;'>{int(s_inf['النقاط'])}</div>
                      </div>
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )
          st.markdown("<br>", unsafe_allow_html=True)

          grades_html_table = (
              "<div style='text-align:center; padding:20px; color:#64748B;'>لا"
              " توجد درجات مرصودة لهذا الطالب في هذه الفترة.</div>"
          )
          behavior_html_table = (
              "<div style='text-align:center; padding:20px; color:#64748B;'>✨"
              " سجل السلوك نظيف.</div>"
          )

          st.markdown("##### 📊 الدرجات الأكاديمية")
          df_g = st.session_state.df_grades.copy()
          cp_report = st.session_state.get(
              "current_period", "الفترة الأولى"
          ).strip()

          if not df_g.empty:
            df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0]
            if "period" not in df_g.columns:
              df_g["period"] = "الفترة الأولى"
            df_g["period"] = (
                df_g["period"]
                .replace(["", None, "nan", "NaN"], "الفترة الأولى")
                .astype(str)
                .str.strip()
            )
            my_g = df_g[
                (df_g["clean_id"] == sid) & (df_g["period"] == cp_report)
            ]

            if not my_g.empty:
              g_inf = my_g.iloc[-1]
              k1, k2, k3 = st.columns(3)
              k1.metric("📝 المشاركة والواجبات", g_inf.get("p1", 0))
              k2.metric("✍️ الاختبارات", g_inf.get("p2", 0))
              k3.metric("🏆 المجموع الكلي", g_inf.get("perf", 0))

              grades_html_table = f"""
              <table>
                  <tr><th>الفترة النشطة</th><th>المشاركة والواجبات</th><th>الاختبارات</th><th>المجموع الكلي</th></tr>
                  <tr>
                      <td style="text-align: center;">{cp_report}</td>
                      <td style="text-align: center;">{g_inf.get('p1', 0)}</td>
                      <td style="text-align: center;">{g_inf.get('p2', 0)}</td>
                      <td style="text-align: center; font-weight:bold; color:{primary_color};">{g_inf.get('perf', 0)}</td>
                  </tr>
              </table>
              """
            else:
              st.info(
                  f"لم يتم رصد درجات أكاديمية لهذا الطالب في ({cp_report}) بعد."
              )

          st.markdown("<br>", unsafe_allow_html=True)
          st.markdown("##### 📜 سجل السلوك والملاحظات")
          df_b = st.session_state.df_behavior.copy()
          if not df_b.empty:
            df_b["clean_id"] = df_b.iloc[:, 0].astype(str).str.split(".").str[0]
            my_b = df_b[df_b["clean_id"] == sid].copy()

            if not my_b.empty:
              my_b["date_parsed"] = pd.to_datetime(
                  my_b["date"], errors="coerce"
              )
              my_b = my_b.sort_values(by="date_parsed", ascending=False)

              display_df = my_b[["date", "type", "note"]].rename(
                  columns={
                      "date": "📅 التاريخ",
                      "type": "🎯 نوع السلوك",
                      "note": "📝 التفاصيل",
                  }
              )
              st.dataframe(display_df, use_container_width=True, hide_index=True)

              rows_html = ""
              for _, r_b in display_df.iterrows():
                rows_html += f"<tr><td>{r_b['📅 التاريخ']}</td><td>{r_b['🎯 نوع السلوك']}</td><td>{r_b['📝 التفاصيل']}</td></tr>"
                )
              behavior_html_table = (
                  "<table><tr><th>التاريخ</th><th>نوع"
                  f" السلوك</th><th>التفاصيل</th></tr>{rows_html}</table>"
              )
            else:
              st.success("✨ سجله نظيف، لا توجد ملاحظات مسجلة في السجل.")
          else:
            st.info("سجل السلوك فارغ تماماً في المنصة.")

          st.divider()
          final_report = f"""
          <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>تقرير الطالب: {s_inf['name']}</title>
          <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
          <style>
              body {{ font-family: 'Cairo', sans-serif; background-color: #F8FAFC; padding: 20px; color: #0F172A; line-height: 1.6; }}
              .container {{ max-width: 800px; margin: 0 auto; background: #FFFFFF; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
              .banner {{ background: {header_grad}; color: white; text-align: center; padding: 15px; border-radius: 12px; margin-bottom: 30px; font-weight: 800; font-size: 24px; }}
              .header {{ text-align: center; margin-bottom: 30px; }}
              .header h1 {{ color: #0F172A; margin-bottom: 5px; font-weight: 800; font-size: 28px; }}
              .header p {{ color: #64748B; font-size: 14px; margin-top: 0; }}
              .student-card {{ background: #F8FAFC; border-right: 5px solid {primary_color}; padding: 25px; border-radius: 12px; margin-bottom: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
              .student-card h2 {{ grid-column: 1 / -1; margin-top: 0; color: {primary_color}; border-bottom: 1px dashed #CBD5E1; padding-bottom: 15px; margin-bottom: 10px; display:flex; justify-content:space-between; }}
              .student-card .info-item {{ font-size: 16px; }}
              .student-card .info-item span {{ font-weight: 800; color: #475569; margin-left: 5px; }}
              h3 {{ color: {primary_color}; margin-top: 35px; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px; }}
              .table-container {{ overflow: hidden; border-radius: 12px; margin-bottom: 20px; border: 1px solid #E2E8F0; }}
              table {{ width: 100%; border-collapse: collapse; background: #fff; text-align: right; }}
              th {{ background-color: #F8FAFC; color: #0F172A; font-weight: 800; padding: 12px; border-bottom: 2px solid #E2E8F0; }}
              td {{ padding: 12px; border-bottom: 1px solid #F1F5F9; color: #475569; font-weight: 600; }}
              .footer-sigs {{ margin-top: 50px; display: flex; justify-content: space-between; align-items: center; padding-top: 25px; border-top: 2px dashed #CBD5E1; color: #0F172A; font-weight: 800; }}
              .footer-sigs > div {{ text-align: center; flex: 1; }}
              .sig-line {{ margin-top: 30px; color: #94A3B8; font-weight: normal; }}
              @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; padding: 0; max-width: 100%; border: none; }} .banner, th, .student-card {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
          </style></head><body>
              <div class="container">
                  <div class="banner">✨ منصة زياد الذكية ✨</div>
                  <div class="header"><h1>تقرير متابعة طالب</h1><p>تاريخ استخراج التقرير: {pd.Timestamp.now().strftime('%Y-%m-%d')}</p></div>
                  <div class="student-card">
                      <h2><span>👤 {s_inf['name']}</span> <span style="font-size:16px; background:#e2e8f0; padding:5px 15px; border-radius:8px; color:#475569;">🧠 {l_style}</span></h2>
                      <div class="info-item"><span>🆔 الرقم الأكاديمي:</span> {sid}</div>
                      <div class="info-item"><span>🏫 الصف:</span> {s_inf.get('class', 'غير محدد')}</div>
                      <div class="info-item"><span>⭐ نقاط التميز:</span> <span style="color:#d97706; font-size:1.2em;">{int(s_inf['النقاط'])}</span></div>
                  </div>
                  <h3>📊 الأداء الأكاديمي ({cp_report})</h3>
                  <div class="table-container">{grades_html_table}</div>
                  <h3>📜 سجل السلوك والملاحظات</h3>
                  <div class="table-container">{behavior_html_table}</div>
                  <div class="footer-sigs">
                      <div>وكيل شؤون الطلاب<div class="sig-line">.................................</div></div>
                      <div>المعلم<div style="margin-top: 20px; color: {primary_color}; font-size: 18px;">زياد المعمري</div></div>
                      <div>الموجه الطلابي<div class="sig-line">.................................</div></div>
                  </div>
              </div>
              <script>window.onload = function() {{ window.print(); }}</script>
          </body></html>
          """
          st.download_button(
              label="🖨️ تحميل وطباعة تقرير الطالب الشامل",
              data=final_report,
              file_name=f"Report_{sid}_{s_inf['name']}.html",
              mime="text/html",
              type="primary",
              use_container_width=True,
          )
      else:
        st.info("لا توجد بيانات طلاب.")

    # ---------------------------------------------------------
    # 2. كشف الدرجات المرصودة (مطبوع)
    # ---------------------------------------------------------
    with rep_tabs[1]:
      st.markdown("#### 📊 استخراج كشف الدرجات المرصودة للطباعة")
      st.info(
          "💡 قم بطباعة كشف درجات الطلاب معبأً بالدرجات من قاعدة البيانات للفصل"
          " والفترة المحددة."
      )

      if not df_s_rep.empty:
        col_g1, col_g2 = st.columns(2)
        grades_print_cls = col_g1.selectbox(
            "1️⃣ اختر الصف:",
            st.session_state.get("class_options", []),
            key="grades_print_cls",
        )
        grades_print_period = col_g2.selectbox(
            "2️⃣ اختر الفترة:",
            [
                "الفترة الأولى",
                "الفترة الثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
                "الفترة الثالثة",
            ],
            key="grades_print_period",
        )

        if st.button(
            "🖨️ توليد كشف الدرجات المرصودة للطباعة",
            type="primary",
            use_container_width=True,
        ):
          df_cls_students = df_s_rep[
              df_s_rep["class"] == grades_print_cls
          ].sort_values("name")

          if df_cls_students.empty:
            st.warning("⚠️ لا يوجد طلاب مسجلين في هذا الصف.")
          else:
            df_g = st.session_state.get("df_grades", pd.DataFrame()).copy()
            if df_g.empty:
              st.warning("⚠️ لا توجد أي درجات مرصودة في قاعدة البيانات بعد.")
            else:
              df_g["clean_id"] = (
                  df_g.iloc[:, 0].astype(str).str.split(".").str[0]
              )
              if "period" not in df_g.columns:
                df_g["period"] = "الفترة الأولى"
              df_g["period"] = (
                  df_g["period"]
                  .replace(["", None, "nan", "NaN"], "الفترة الأولى")
                  .astype(str)
                  .str.strip()
              )
              df_g_period = df_g[df_g["period"] == grades_print_period]
              df_merged = pd.merge(
                  df_cls_students, df_g_period, on="clean_id", how="left"
              )

              rows_html = ""
              for i, (_, row) in enumerate(df_merged.iterrows(), 1):
                p1 = (
                    str(row.get("p1", ""))
                    if pd.notna(row.get("p1"))
                    else ""
                )
                p2 = (
                    str(row.get("p2", ""))
                    if pd.notna(row.get("p2"))
                    else ""
                )
                perf = (
                    str(row.get("perf", ""))
                    if pd.notna(row.get("perf"))
                    else ""
                )
                rows_html += (
                    f"<tr><td>{i}</td><td"
                    f" class='name-col'>{row['name']}</td><td>{p1}</td><td>{p2}</td><td"
                    " style='font-weight:bold; color:#174A5B; font-size:14px;"
                    f" background-color:#f5f5f5;'>{perf}</td></tr>"
                )

              school_name = get_school_name_dynamic(grades_print_cls)

              grades_sheet_html = f"""
              <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>كشف الدرجات - {grades_print_cls}</title>
              <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
              <style>
                  body {{ font-family: 'Cairo', sans-serif; background: #fff; margin: 0; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                  .header-box {{ background-color: #174A5B; color: white; border-radius: 10px; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                  .header-text {{ text-align: center; font-weight: bold; line-height: 1.3; font-size: 11px; }}
                  .title-box {{ background-color: #174A5B; color: white; text-align: center; padding: 4px; font-weight: bold; width: 60%; margin: -20px auto 5px auto; border-radius: 6px; border: 2px solid white; position: relative; z-index: 2; font-size: 13px; }}
                  table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; margin-top: 10px; }}
                  th, td {{ border: 1px solid #b0bec5; padding: 3px 5px; height: 22px; }}
                  th {{ background-color: #e0e0e0; font-weight: bold; color: #333; font-size: 12px; }}
                  .name-col {{ width: 40%; background-color: #f8fafc; text-align: right; padding-right: 10px !important; font-weight: bold; }}
                  .footer {{ display: flex; justify-content: space-between; margin-top: 20px; font-weight: bold; padding: 0 50px; font-size: 12px; }}
                  @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} body {{ padding: 0; }} thead {{ display: table-header-group; }} tr {{ page-break-inside: avoid; }} }}
              </style></head><body>
                  <div class="header-box">
                      <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                      <div class="header-text" style="font-size: 18px;">وزارة التعليم<br><span style="font-size: 9px; font-weight:normal;">Ministry of Education</span></div>
                      <div class="header-text">العام الدراسي {st.session_state.current_year}<br>{grades_print_period}</div>
                  </div>
                  <div class="title-box">كشف الدرجات الأكاديمية المرصودة - مادة اللغة الانجليزية - {grades_print_cls}</div>
                  <table>
                      <thead>
                          <tr>
                              <th style="width: 5%;">م</th>
                              <th class="name-col">اسم الطالب</th>
                              <th style="width: 20%;">المشاركة والمهام</th>
                              <th style="width: 20%;">الاختبارات القصيرة</th>
                              <th style="width: 15%;">المجموع الكلي</th>
                          </tr>
                      </thead>
                      <tbody>{rows_html}</tbody>
                  </table>
                  <div class="footer">
                      <div>مدير المدرسة / أ. عبدالمجيد الحربي</div>
                      <div>المعلم / زياد المعمري</div>
                  </div>
                  <script>window.onload = function() {{ window.print(); }}</script>
              </body></html>
              """
              st.download_button(
                  label="📥 تحميل كشف الدرجات (يُفتح للطباعة مباشرة)",
                  data=grades_sheet_html,
                  file_name=f"Filled_Grades_{grades_print_cls}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )

    # ---------------------------------------------------------
    # 3. كشف متابعة فارغ مرن (للرصد اليدوي)
    # ---------------------------------------------------------
    with rep_tabs[2]:
      st.markdown("#### 📝 استخراج كشف متابعة مرن (فارغ للرصد اليدوي)")
      st.info(
          "💡 صمم كشفك بنفسك! اختر الصف، وحدد اتجاه الورقة، ثم اختر الحقول التي"
          " تريدها ليتم رسم الكشف تلقائياً."
      )

      if not df_s_rep.empty:
        col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 2])
        all_classes = st.session_state.get("class_options", ["الرابع", "الخامس"])
        print_cls_choice = col_opt1.selectbox(
            "1️⃣ اختر الصف:", all_classes, key="print_cls_flex"
        )
        page_orientation = col_opt2.radio(
            "2️⃣ اتجاه الطباعة:", ["أفقي (Landscape)", "عمودي (Portrait)"]
        )
        css_orientation = (
            "landscape" if "أفقي" in page_orientation else "portrait"
        )

        available_fields = {
            "الحضور والغياب": 10,
            "المشاركة والتفاعل": 5,
            "الواجبات والمهام": 5,
            "الاختبارات القصيرة": 2,
            "المشاريع والبحوث": 5,
            "السلوك والانضباط": 5,
        }

        selected_fields = col_opt3.multiselect(
            "3️⃣ اختر الحقول المطلوبة في الكشف:",
            list(available_fields.keys()),
            default=["المشاركة والتفاعل", "الواجبات والمهام", "الاختبارات القصيرة"],
        )

        if st.button(
            "🖨️ توليد الكشف المرن للطباعة",
            type="primary",
            use_container_width=True,
        ):
          if not selected_fields:
            st.warning("⚠️ الرجاء اختيار حقل واحد على الأقل ليتم رسم الكشف.")
          else:
            df_print = df_s_rep[
                df_s_rep["class"] == print_cls_choice
            ].sort_values("name")
            if not df_print.empty:
              main_th_html, sub_th_html = "", ""
              total_empty_cells = 0

              for field in selected_fields:
                colspan = available_fields[field]
                main_th_html += (
                    f'<th colspan="{colspan}" class="main-th">{field}</th>'
                )
                for i in range(1, colspan + 1):
                  sub_th_html += f"<th>{i}</th>"
                total_empty_cells += colspan

              rows_html = ""
              empty_cells_str = "<td></td>" * total_empty_cells
              for i, (_, row) in enumerate(df_print.iterrows(), 1):
                rows_html += (
                    f"<tr><td>{i}</td><td style='text-align: right;"
                    " padding-right: 5px; font-weight: bold; white-space:"
                    f" nowrap;'>{row['name']}</td>{empty_cells_str}<td"
                    " class='total-col'></td></tr>"
                )

              school_name = get_school_name_dynamic(print_cls_choice)

              sheet_html = f"""
              <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>كشف متابعة مخصص - {print_cls_choice}</title>
              <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
              <style>
                  body {{ font-family: 'Cairo', sans-serif; background: #fff; margin: 0; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                  .header-box {{ background-color: #174A5B; color: white; border-radius: 10px; padding: 8px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
                  .header-text {{ text-align: center; font-weight: bold; line-height: 1.3; font-size: 12px; }}
                  .title-box {{ background-color: #174A5B; color: white; text-align: center; padding: 4px; font-weight: bold; width: 50%; margin: -25px auto 10px auto; border-radius: 6px; border: 2px solid white; position: relative; z-index: 2; font-size: 13px; }}
                  table {{ width: 100%; border-collapse: collapse; font-size: 11px; text-align: center; }}
                  th, td {{ border: 1px solid #b0bec5; padding: 2px; }}
                  th {{ background-color: #e0e0e0; font-weight: bold; color: #333; }}
                  .main-th {{ font-size: 12px; padding: 4px; background-color: #cfd8dc; }}
                  .sub-th th {{ width: 2.5%; font-size: 9px; color: #555; }}
                  .name-col {{ width: 22%; background-color: #e0e0e0; font-size: 11px; }}
                  .total-col {{ width: 5%; background-color: #f5f5f5; }}
                  td {{ height: 20px; }}
                  .footer {{ display: flex; justify-content: space-between; margin-top: 15px; font-weight: bold; padding: 0 50px; font-size: 12px; }}
                  @media print {{ @page {{ size: A4 {css_orientation}; margin: 5mm; }} body {{ padding: 0; }} thead {{ display: table-header-group; }} tr {{ page-break-inside: avoid; }} }}
              </style></head><body>
                  <div class="header-box">
                      <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                      <div class="header-text" style="font-size: 20px;">وزارة التعليم<br><span style="font-size: 10px; font-weight:normal;">Ministry of Education</span></div>
                      <div class="header-text">العام الدراسي {st.session_state.current_year}<br>{st.session_state.current_period}</div>
                  </div>
                  <div class="title-box">كشف متابعة - مادة اللغة الانجليزية - {print_cls_choice}</div>
                  <table>
                      <thead>
                          <tr>
                              <th rowspan="2" style="width: 2%;">م</th>
                              <th rowspan="2" class="name-col">اسم الطالب</th>
                              {main_th_html}
                              <th rowspan="2" class="total-col">المجموع</th>
                          </tr>
                          <tr class="sub-th">{sub_th_html}</tr>
                      </thead>
                      <tbody>{rows_html}</tbody>
                  </table>
                  <div class="footer">
                      <div>مدير المدرسة / أ. عبدالمجيد الحربي</div>
                      <div>المعلم / زياد المعمري</div>
                  </div>
                  <script>window.onload = function() {{ window.print(); }}</script>
              </body></html>
              """
              st.download_button(
                  label="📥 تحميل الكشف المخصص (يُفتح للطباعة مباشرة)",
                  data=sheet_html,
                  file_name=f"Custom_Grading_Sheet_{print_cls_choice}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )
            else:
              st.warning("لا يوجد طلاب مسجلين في هذا الصف.")

    # ---------------------------------------------------------
    # 4. مساعد التفريغ للسجلات الورقية
    # ---------------------------------------------------------
    with rep_tabs[3]:
      st.markdown("#### 🖨️ مساعد التفريغ للسجلات الورقية (حصر الملاحظات)")
      st.info(
          "💡 هذه الأداة تجمع وتحصي المخالفات والمشاركات لتسهيل نقلها إلى كشف"
          " المتابعة الورقي بسرعة."
      )

      df_b = st.session_state.df_behavior.copy()
      if not df_b.empty and not df_s_rep.empty:
        df_b["clean_id"] = (
            df_b.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]
        )
        merged_df = pd.merge(
            df_b,
            df_s_rep[["clean_id", "name", "class"]],
            on="clean_id",
            how="inner",
        )
        beh_col = "type" if "type" in merged_df.columns else merged_df.columns[1]

        col1, col2 = st.columns(2)
        available_classes = st.session_state.get(
            "class_options", ["الرابع", "الخامس"]
        )
        cls_choice = col1.selectbox(
            "1️⃣ اختر الصف لفرز بياناته:",
            available_classes,
            key="paper_helper_cls",
        )
        class_data = merged_df[merged_df["class"] == cls_choice]

        if not class_data.empty:
          unique_notes = list(class_data[beh_col].unique())
          type_choice = col2.selectbox(
              "2️⃣ نوع الملاحظة المطلوبة:",
              ["الكل (جدول تجميعي لكشف المتابعة)"] + unique_notes,
              key="paper_helper_type",
          )
          st.divider()

          if type_choice == "الكل (جدول تجميعي لكشف المتابعة)":
            st.markdown(f"##### 📊 حصر شامل لجميع ملاحظات (الصف {cls_choice})")
            pivot_table = pd.crosstab(class_data["name"], class_data[beh_col])
            pivot_table.index.name = "اسم الطالب"

            if "note" in class_data.columns:

              def combine_notes(group):
                valid = group[group["note"].astype(str).str.strip() != ""]
                if valid.empty:
                  return ""
                return " ، ".join(valid["note"].astype(str).str.strip())

              notes_series = class_data.groupby("name").apply(combine_notes)
              pivot_table["الملاحظات النصية التفصيلية"] = notes_series

            all_students = (
                df_s_rep[df_s_rep["class"] == cls_choice]
                .sort_values("name")["name"]
                .tolist()
            )
            pivot_table = pivot_table.reindex(all_students)

            for col in pivot_table.columns:
              if col == "الملاحظات النصية التفصيلية":
                pivot_table[col] = pivot_table[col].fillna("")
              else:
                pivot_table[col] = (
                    pd.to_numeric(pivot_table[col], errors="coerce")
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                )

            pivot_table = pivot_table.sort_index()
            st.dataframe(pivot_table, use_container_width=True)

            b_csv = io.BytesIO()
            with pd.ExcelWriter(b_csv, engine="xlsxwriter") as writer:
              pivot_table.to_excel(writer, sheet_name="التفريغ الورقي")
            st.download_button(
                f"📥 تحميل كشف (الصف {cls_choice}) للطباعة (Excel)",
                b_csv.getvalue(),
                f"Behavior_Summary_{cls_choice}.xlsx",
                type="primary",
                use_container_width=True,
            )
          else:
            st.markdown(
                f"##### 📌 حصر الطلاب الذين لديهم ({type_choice}) في (الصف"
                f" {cls_choice})"
            )
            specific_data = class_data[class_data[beh_col] == type_choice]
            if not specific_data.empty:
              summary = (
                  specific_data.groupby(["name", "note"])
                  .size()
                  .reset_index(name="عدد المرات")
              )
              summary.rename(
                  columns={
                      "name": "اسم الطالب",
                      "note": "التفاصيل المكتوبة",
                  },
                  inplace=True,
              )
              summary = summary.sort_values("عدد المرات", ascending=False)
              st.dataframe(summary, use_container_width=True, hide_index=True)
            else:
              st.info("لا يوجد أي طالب مسجل عليه هذه الملاحظة.")
        else:
          st.info(
              f"لا توجد أي ملاحظات مسجلة لطلاب (الصف {cls_choice}) حتى الآن."
          )
      else:
        st.warning("لا توجد بيانات سلوكية كافية لإنشاء التقرير.")

    # ---------------------------------------------------------
    # 5. تقرير حصر المتفوقين ومتدني المستوى (شاهد إثبات)
    # ---------------------------------------------------------
    with rep_tabs[4]:
      st.markdown(
          "#### 📈 تقرير حصر المتفوقين ومتدني المستوى (للخطط العلاجية والتعزيز)"
      )
      st.info(
          "💡 تقرير رسمي لمتابعة مستويات الطلاب وتوثيق تطبيق الخطط العلاجية"
          " وبرامج الرعاية."
      )

      if not df_s_rep.empty:
        c1, c2, c3, c4 = st.columns(4)
        all_cls_rep = ["الكل"] + st.session_state.get("class_options", [])
        rep_cls = c1.selectbox(
            "🏫 اختر الصف:", all_cls_rep, key="rep_lvl_cls"
        )
        rep_per = c2.selectbox(
            "📅 الفترة:",
            [
                "الفترة الأولى",
                "الفترة الثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
                "الفترة الثالثة",
            ],
            key="rep_lvl_per",
        )
        rep_type = c3.selectbox(
            "🎯 الفئة:",
            ["المتفوقين 🌟", "متدني المستوى 📉"],
            key="rep_lvl_type",
        )

        default_thresh = 54 if "المتفوقين" in rep_type else 36
        threshold = c4.number_input(
            "الدرجة الفاصلة:",
            value=default_thresh,
            step=1,
            key=f"thresh_{rep_type}",
        )

        if st.button(
            "🖨️ توليد تقرير الحصر للطباعة",
            type="primary",
            use_container_width=True,
        ):
          df_g_all = st.session_state.get("df_grades", pd.DataFrame()).copy()
          if df_g_all.empty:
            st.warning("⚠️ لا توجد درجات مرصودة في قاعدة البيانات بعد.")
          else:
            df_st_copy = df_s_rep.copy()
            if rep_cls != "الكل":
              df_st_copy = df_st_copy[df_st_copy["class"] == rep_cls]

            df_g_all["clean_id"] = (
                df_g_all.iloc[:, 0].astype(str).str.split(".").str[0]
            )
            if "period" not in df_g_all.columns:
              df_g_all["period"] = "الفترة الأولى"
            df_g_all["period"] = (
                df_g_all["period"]
                .replace(["", None, "nan", "NaN"], "الفترة الأولى")
                .astype(str)
                .str.strip()
            )

            df_g_filtered = df_g_all[df_g_all["period"] == rep_per]
            df_merged_lvl = pd.merge(
                df_st_copy, df_g_filtered, on="clean_id", how="inner"
            )
            df_merged_lvl["perf_num"] = pd.to_numeric(
                df_merged_lvl["perf"], errors="coerce"
            ).fillna(0)

            if "المتفوقين" in rep_type:
              final_df = df_merged_lvl[
                  df_merged_lvl["perf_num"] >= threshold
              ].sort_values(by="perf_num", ascending=False)
              report_title = "حصر الطلاب المتفوقين"
              action_text = "تكريم في لوحة الشرف / تعزيز إيجابي"
              color_theme = "#10B981"
            else:
              final_df = df_merged_lvl[
                  df_merged_lvl["perf_num"] < threshold
              ].sort_values(by="perf_num", ascending=True)
              report_title = "حصر الطلاب متدني المستوى"
              action_text = "إشعار ولي الأمر / إدراج في الخطة العلاجية"
              color_theme = "#EF4444"

            if final_df.empty:
              st.success(
                  f"✅ لا يوجد طلاب يطابقون معيار ({report_title}) في هذا"
                  " الصف/الفترة."
              )
            else:
              school_name = get_school_name_dynamic(rep_cls)
              rows_lvl = ""
              for i, (_, row) in enumerate(final_df.iterrows(), 1):
                rows_lvl += (
                    f"<tr><td>{i}</td><td style='text-align:right;"
                    f" font-weight:bold;'>{row['name']}</td><td>{row.get('class', '')}</td><td"
                    f" style='font-weight:900; color:{color_theme};'>{row['perf_num']}</td><td"
                    f" style='color:#64748B; font-size:11px;'>{action_text}</td></tr>"
                )

              lvl_report_html = f"""
              <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>{report_title}</title>
              <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
              <style>
                  body {{ font-family: 'Cairo', sans-serif; background: #fff; margin: 0; padding: 10px; font-size: 13px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                  .header-box {{ border: 2px solid #1e293b; padding: 10px; border-radius: 8px; display: flex; justify-content: space-between; margin-bottom: 15px; }}
                  .header-text {{ text-align: center; font-weight: bold; font-size: 12px; line-height: 1.4; }}
                  .title-container {{ text-align: center; margin-bottom: 15px; }}
                  .main-title {{ font-size: 18px; font-weight: 900; background: {color_theme}; color: white; display: inline-block; padding: 5px 25px; border-radius: 20px; margin-bottom: 5px; }}
                  .sub-title {{ font-size: 13px; color: #475569; font-weight: bold; }}
                  table {{ width: 100%; border-collapse: collapse; margin-top: 15px; text-align: center; font-size: 12px; }}
                  th, td {{ border: 1px solid #cbd5e1; padding: 5px 8px; height: 22px; }}
                  th {{ background-color: #f8fafc; font-weight: 900; color: #1e293b; }}
                  .footer-sigs {{ margin-top: 40px; display: flex; justify-content: space-between; font-weight: bold; text-align: center; font-size: 13px; }}
                  @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} body {{ padding: 0; }} tr {{ page-break-inside: avoid; }} }}
              </style></head><body>
                  <div class="header-box">
                      <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                      <div class="header-text" style="align-self: center;">
                          <div class="sub-title" style="font-size:15px; color:#1e293b;">تقرير تحليل نتائج الطلاب</div>
                          <div style="font-size: 11px; color: #64748B; margin-top:3px;">تاريخ الإصدار: {pd.Timestamp.now().strftime('%Y-%m-%d')}</div>
                      </div>
                      <div class="header-text">الفصل الدراسي: {st.session_state.get('current_period', '')}<br>{rep_per}<br>المعلم: زياد المعمري</div>
                  </div>
                  <div class="title-container">
                      <div class="main-title">{report_title}</div>
                      <div class="sub-title">مبني على الدرجات المرصودة في المنصة واستخراج آلي لدعم خطط الرعاية والتعزيز</div>
                      <div style="margin-top: 8px; font-size: 12px; font-weight: bold; color: {color_theme}; background:#f8fafc; display:inline-block; padding:4px 15px; border-radius:8px; border:1px dashed {color_theme};">
                          (الصف: {rep_cls}) | (معيار الفرز: {threshold} درجة) | (العدد: {len(final_df)} طالب)
                      </div>
                  </div>
                  <table>
                      <tr>
                          <th style="width: 5%;">م</th>
                          <th style="width: 35%; text-align: right;">اسم الطالب</th>
                          <th style="width: 15%;">الصف</th>
                          <th style="width: 15%;">المجموع ({rep_per})</th>
                          <th style="width: 30%;">الإجراء المتخذ (مقترح)</th>
                      </tr>
                      {rows_lvl}
                  </table>
                  <div class="footer-sigs">
                      <div>الموجه الطلابي <br><br>........................</div>
                      <div>معلم المادة <br><br>زياد المعمري</div>
                      <div>مدير المدرسة <br><br>أ. عبدالمجيد الحربي</div>
                  </div>
                  <script>window.onload = function() {{ window.print(); }}</script>
              </body></html>
              """
              st.download_button(
                  label="📥 تحميل التقرير (يفتح للطباعة مباشرة)",
                  data=lvl_report_html,
                  file_name=f"Performance_Report_{rep_cls}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )

    # ---------------------------------------------------------
    # 6. تقرير حصر أنماط التعلم (VARK) للإدارة والتوثيق
    # ---------------------------------------------------------
    with rep_tabs[5]:
      st.markdown("#### 🧠 استخراج تقرير أنماط التعلم (للإدارة والتوثيق)")
      st.info(
          "💡 يمكنك طباعة هذا التقرير كـ 'شاهد إثبات' رسمي لمدير المدرسة"
          " والمشرف التربوي على تطبيقك لاستراتيجية (التعليم المتمايز) ومراعاة"
          " الفروق الفردية."
      )

      if not df_s_rep.empty:
        c1, c2 = st.columns(2)
        c_opts = ["الكل"] + list(df_s_rep["class"].dropna().unique())
        sel_class = c1.selectbox("🏫 اختر الصف:", c_opts, key="ls_class")

        style_opts = [
            "الكل",
            "تم الاختبار ✅",
            "بصري 👀",
            "سمعي 👂",
            "حركي ✋",
            "متعدد الأنماط 🌟",
            "لم يختبر ⏳",
        ]
        sel_style = c2.selectbox(
            "🎯 اختر النمط المستهدف:", style_opts, key="ls_style"
        )

        if st.button(
            "🖨️ توليد تقرير الأنماط للطباعة",
            type="primary",
            use_container_width=True,
        ):
          df_filtered = df_s_rep.copy()
          if sel_class != "الكل":
            df_filtered = df_filtered[df_filtered["class"] == sel_class]

          if "نمط التعلم" not in df_filtered.columns:
            df_filtered["نمط التعلم"] = ""

          if sel_style == "لم يختبر ⏳":
            df_filtered = df_filtered[
                df_filtered["نمط التعلم"].isna()
                | (
                    df_filtered["نمط التعلم"]
                    .astype(str)
                    .str.strip()
                    .isin(["", "nan", "None"])
                )
            ]
          elif sel_style == "تم الاختبار ✅":
            df_filtered = df_filtered[
                df_filtered["نمط التعلم"].notna()
                & (
                    ~df_filtered["نمط التعلم"]
                    .astype(str)
                    .str.strip()
                    .isin(["", "nan", "None", "لم يختبر ⏳"])
                )
            ]
          elif sel_style != "الكل":
            keyword = sel_style.split()[0]
            df_filtered = df_filtered[
                df_filtered["نمط التعلم"]
                .astype(str)
                .str.contains(keyword, na=False)
            ]

          if df_filtered.empty:
            st.warning("⚠️ لا يوجد طلاب يطابقون خياراتك الحالية.")
          else:
            df_sorted = df_filtered.sort_values(by=["class", "name"])
            rows_html = ""
            for i, (_, r) in enumerate(df_sorted.iterrows(), 1):
              s_val = r.get("نمط التعلم", "")
              if pd.isna(s_val) or str(s_val).strip() in ["", "nan", "None"]:
                s_val = "لم يختبر ⏳"

              clr = (
                  "#3B82F6"
                  if "بصري" in s_val
                  else "#10B981"
                  if "سمعي" in s_val
                  else "#F59E0B"
                  if "حركي" in s_val
                  else "#8B5CF6"
                  if "متعدد" in s_val
                  else "#94A3B8"
              )
              rows_html += (
                  f"<tr><td>{i}</td><td style='text-align:right;"
                  f" font-weight:bold;'>{r['name']}</td><td>{r.get('class', '')}</td><td"
                  f" style='color:{clr}; font-weight:bold;'>{s_val}</td></tr>"
              )

            school_name = get_school_name_dynamic(sel_class)

            ls_report_html = f"""
            <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>تقرير أنماط التعلم</title>
            <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Cairo', sans-serif; background: #fff; padding: 10px; color: #1e293b; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-size: 13px; }}
                .header-box {{ border: 2px solid #1e293b; padding: 10px; border-radius: 8px; display: flex; justify-content: space-between; margin-bottom: 10px; }}
                .header-text {{ text-align: center; font-weight: bold; font-size: 13px; line-height: 1.4; }}
                .title-container {{ text-align: center; margin-bottom: 15px; }}
                .main-title {{ font-size: 20px; font-weight: 900; background: #1e293b; color: white; display: inline-block; padding: 5px 20px; border-radius: 20px; margin-bottom: 5px; }}
                .sub-title {{ font-size: 14px; color: #475569; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; text-align: center; font-size: 13px; }}
                th, td {{ border: 1px solid #cbd5e1; padding: 5px 8px; }}
                th {{ background-color: #f1f5f9; font-weight: 900; font-size: 13px; }}
                .footer-sigs {{ margin-top: 25px; display: flex; justify-content: space-between; font-weight: bold; text-align: center; font-size: 13px; }}
                @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} body {{ padding: 0; }} tr {{ page-break-inside: avoid; }} }}
            </style></head><body>
                <div class="header-box">
                    <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                    <div class="header-text" style="align-self: center;">
                        <div class="sub-title" style="font-size:16px; color:#1e293b;">إحصائية أنماط تعلم الطلاب</div>
                        <div style="font-size: 11px; color: #64748B; margin-top:3px;">تاريخ الإصدار: {pd.Timestamp.now().strftime('%Y-%m-%d')}</div>
                    </div>
                    <div class="header-text">الفصل الدراسي: {st.session_state.get('current_period', '')}<br>العام الدراسي: {st.session_state.get('current_year', '')}<br>المعلم: زياد المعمري</div>
                </div>
                <div class="title-container">
                    <div class="main-title">تقرير حصر أنماط التعلم (VARK)</div>
                    <div class="sub-title">تقرير تطبيق استراتيجية "التعليم المتمايز" ومراعاة الفروق الفردية للطلاب (حركي - سمعي - بصري)</div>
                    <div style="margin-top: 10px; font-size: 13px; font-weight: bold; color: #3b82f6; background:#eff6ff; display:inline-block; padding:4px 15px; border-radius:8px; border:1px dashed #3b82f6;">
                        الفئة المستهدفة: (الصف: {sel_class}) | (النمط: {sel_style}) | (العدد: {len(df_filtered)} طالب)
                    </div>
                </div>
                <table>
                    <tr>
                        <th style="width: 5%;">م</th>
                        <th style="width: 45%; text-align: right;">اسم الطالب</th>
                        <th style="width: 25%;">الصف</th>
                        <th style="width: 25%;">نمط التعلم</th>
                    </tr>
                    {rows_html}
                </table>
                <div class="footer-sigs">
                    <div>الموجه الطلابي <br><br>........................</div>
                    <div>معلم المادة <br><br>زياد المعمري</div>
                    <div>مدير المدرسة <br><br>أ. عبدالمجيد الحربي</div>
                </div>
                <script>window.onload = function() {{ window.print(); }}</script>
            </body></html>
            """
            st.download_button(
                label="📥 تحميل تقرير الأنماط (يفتح للطباعة مباشرة)",
                data=ls_report_html,
                file_name=f"Learning_Styles_Report_{sel_class}.html",
                mime="text/html",
                type="primary",
                use_container_width=True,
            )

    # ---------------------------------------------------------
    # 7. استخراج كشف أسماء وأرقام تواصل الطلاب (Excel)
    # ---------------------------------------------------------
    with rep_tabs[6]:
      st.markdown("#### 📱 استخراج كشف أرقام تواصل الطلاب (واتساب)")
      st.info(
          "💡 سحب قائمة بأسماء طلاب فصل محدد مع أرقام الجوال المسجلة لتسهيل"
          " إضافتهم أو التواصل معهم."
      )

      if not df_s_rep.empty:
        col_t1, col_t2 = st.columns([1, 2])
        all_classes = st.session_state.get("class_options", ["الرابع", "الخامس"])
        contact_cls_choice = col_t1.selectbox(
            "اختر الصف المطلوب:", all_classes, key="contact_cls"
        )

        df_contact = df_s_rep[
            df_s_rep["class"] == contact_cls_choice
        ].sort_values("name")
        if not df_contact.empty:
          df_export = df_contact[["name", "الجوال"]].copy()
          df_export = df_export.rename(
              columns={"name": "اسم الطالب", "الجوال": "رقم الجوال (واتساب)"}
          )

          b_contact = io.BytesIO()
          with pd.ExcelWriter(b_contact, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="أرقام التواصل")

          col_t2.markdown("<br>", unsafe_allow_html=True)
          col_t2.download_button(
              label=f"📥 تحميل كشف أرقام الجوال (Excel) - {contact_cls_choice}",
              data=b_contact.getvalue(),
              file_name=f"Contacts_{contact_cls_choice}.xlsx",
              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              type="primary",
              use_container_width=True,
          )

          with st.expander("👁️ معاينة الأسماء والأرقام قبل التحميل"):
            st.dataframe(df_export, use_container_width=True, hide_index=True)
        else:
          st.warning("لا يوجد طلاب مسجلين في هذا الصف.")
# ==========================================
# 📢 9. التبويب الخامس: لوحة الإعلانات والتعاميم
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_alerts:
    st.subheader("📢 لوحة الإعلانات والتعاميم")

    def perform_delete(row_index):
      try:
        sh.worksheet("exams").delete_rows(int(row_index) + 2)
        st.cache_data.clear()
        st.toast("✅ تم حذف التنبيه بنجاح")
      except Exception as e:
        st.toast(f"❌ حدث خطأ: {e}")

    if st.session_state.role == "teacher":
      with st.form("ann_add", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        at = c1.text_input("عنوان الإعلان أو التعميم")
        atg = c2.selectbox(
            "الفئة المستهدفة", ["الكل"] + st.session_state.class_options
        )
        ad = st.text_area("تفاصيل الإعلان أو الرابط")
        au = c1.checkbox("🔥 تعميم عاجل (يظهر بوميض أحمر أعلى حساب الطالب)")
        if st.form_submit_button(
            "📣 نشر التعميم الآن", type="primary", use_container_width=True
        ):
          if at:
            safe_append_row(
                "exams",
                {
                    "الصف": atg,
                    "عاجل": "نعم" if au else "لا",
                    "العنوان": at,
                    "التاريخ": str(datetime.date.today()),
                    "الرابط": ad,
                },
            )
            st.success("✅ تم نشر التعميم بنجاح!")
            st.cache_data.clear()
            st.rerun()
          else:
            st.warning("⚠️ يرجى كتابة عنوان الإعلان.")

    st.divider()
    df_a = fetch_safe("exams")
    if not df_a.empty:
      for i, r in df_a.iloc[::-1].iterrows():
        with st.container():
          is_urgent = str(r.get("عاجل")).strip() == "نعم"
          anim_class = "urgent-box" if is_urgent else ""
          border_style = (
              f"2px solid {danger_color}"
              if is_urgent
              else "1.5px solid rgba(148, 163, 184, 0.28)"
          )
          bg_style = (
              "rgba(239, 68, 68, 0.12)"
              if is_urgent
              else "var(--secondary-background-color)"
          )
          st.markdown(
              f"""
              <div class="{anim_class}" style="background:{bg_style}; border:{border_style}; border-radius:14px; padding:16px; margin-bottom:10px;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                      <h4 style="margin:0; color:var(--text-color); font-weight:900;">{r.get('العنوان')}</h4>
                      <span style="background:var(--background-color); padding:3px 10px; border-radius:8px; font-size:0.82rem; color:#94A3B8; font-weight:bold;">{r.get('التاريخ')}</span>
                  </div>
                  <p style="margin:8px 0; color:#94A3B8; font-weight:600;">{r.get('الرابط')}</p>
                  <small style="color:{accent_color}; font-weight:800;">🎯 الفئة المستهدفة: {r.get('الصف')}</small>
              </div>
              """,
              unsafe_allow_html=True,
          )
          kc1, kc2 = st.columns([1, 4])
          msg_text = (
              "📢 *تعميم هام من منصة الأستاذ زياد*\n━━━━━━━━━━━━\n📌 *العنوان:*"
              f" {r.get('العنوان')}\n📄 *التفاصيل:* {r.get('الرابط')}\n📅"
              f" *التاريخ:* {r.get('التاريخ')}\n━━━━━━━━━━━━"
          )
          grp_msg = urllib.parse.quote(msg_text)
          kc2.link_button(
              "📲 مشاركة التعميم عبر واتساب",
              f"https://api.whatsapp.com/send?text={grp_msg}",
              use_container_width=True,
          )
          if st.session_state.role == "teacher":
            kc1.button(
                "🗑️ حذف",
                key=f"del_btn_unique_{i}",
                type="secondary",
                on_click=perform_delete,
                args=(i,),
                use_container_width=True,
            )
    else:
      st.info("💡 لا توجد تنبيهات منشورة حالياً.")


# ==========================================
# ⚙️ 10. التبويب السادس: الإعدادات والبيانات ورفع أنماط التعلم (للمعلم فقط)
# ==========================================
if st.session_state.role == "teacher" and tab_settings is not None:
  with tab_settings:
    st.subheader("⚙️ إعدادات النظام وإدارة البيانات")

    set_tabs = st.tabs([
        "🛠️ الصيانة والنسخ الاحتياطي",
        "🎨 الهوية والإعدادات الأكاديمية",
        "📤 استيراد البيانات وأنماط التعلم",
        "🔐 إدارة المستخدمين",
    ])

    # --- 1. الصيانة والنسخ الاحتياطي ---
    with set_tabs[0]:
      st.markdown("#### 🛠️ أدوات الصيانة وتصحيح الأرصدة")
      c1, c2 = st.columns(2)

      if c1.button(
          "🔄 تحديث البيانات ومزامنة السيرفر (Refresh)",
          use_container_width=True,
      ):
        st.cache_data.clear()
        if "db_loaded" in st.session_state:
          del st.session_state["db_loaded"]
        st.session_state["show_refresh_success"] = True
        st.rerun()

      if c2.button("🧹 تصفير جميع النقاط", use_container_width=True):
        try:
          ws = sh.worksheet("students")
          d = ws.get_all_values()
          if len(d) > 1:
            headers = d[0]
            if "النقاط" in headers:
              from gspread.utils import rowcol_to_a1
              col_idx = headers.index("النقاط") + 1
              ws.update(
                  range_name=(
                      f"{rowcol_to_a1(2, col_idx)}:{rowcol_to_a1(len(d), col_idx)}"
                  ),
                  values=[[0]] * (len(d) - 1),
              )
              st.success("✅ تم تصفير جميع النقاط بنجاح")
              if "db_loaded" in st.session_state:
                del st.session_state["db_loaded"]
              st.cache_data.clear()
              st.rerun()
        except Exception as e:
          st.error(f"خطأ: {e}")

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button(
          "🧮 إعادة احتساب النقاط من السجل السلوكي (تصحيح شامل)",
          type="primary",
          use_container_width=True,
      ):
        try:
          with st.spinner("جاري مراجعة السجلات وتصحيح أرصدة الطلاب..."):
            df_beh = fetch_safe("behavior")
            ws_st = sh.worksheet("students")
            students_data = ws_st.get_all_records()
            true_scores = {}

            if not df_beh.empty:
              beh_id_col = df_beh.columns[0]
              beh_type_col = (
                  "type" if "type" in df_beh.columns else df_beh.columns[2]
              )

              for _, row in df_beh.iterrows():
                raw_id = str(row.get(beh_id_col, "")).strip().split(".")[0]
                if not raw_id:
                  continue
                match = re.search(
                    r"\(([\+\-]?\d+)\)", str(row.get(beh_type_col, ""))
                )
                if match:
                  pts = int(match.group(1))
                  true_scores[raw_id] = true_scores.get(raw_id, 0) + pts

            headers = ws_st.row_values(1)
            if "النقاط" in headers:
              col_idx = headers.index("النقاط") + 1
              new_values = []
              id_key = headers[0]

              for st_row in students_data:
                sid_v = str(st_row.get(id_key, "")).strip().split(".")[0]
                new_values.append([str(true_scores.get(sid_v, 0))])

              from gspread.utils import rowcol_to_a1
              ws_st.update(
                  f"{rowcol_to_a1(2, col_idx)}:{rowcol_to_a1(len(new_values) + 1, col_idx)}",
                  new_values,
              )

              st.cache_data.clear()
              if "db_loaded" in st.session_state:
                del st.session_state["db_loaded"]
              st.success(
                  "✅ تم تصحيح جميع الأرصدة بنجاح وفق السجلات الفعلية!"
              )
              st.rerun()
            else:
              st.error("لم يتم العثور على عمود 'النقاط'")
        except Exception as e:
          st.error(f"حدث خطأ: {e}")

      st.divider()
      st.markdown("#### 📥 تنزيل نسخة احتياطية كاملة من البيانات (Backup)")
      b_col1, b_col2 = st.columns(2)
      df_st_full = st.session_state.df_students.copy()
      if not df_st_full.empty:
        b_st = io.BytesIO()
        with pd.ExcelWriter(b_st, engine="xlsxwriter") as writer:
          df_st_full.to_excel(writer, index=False, sheet_name="Students")
        b_col1.download_button(
            label="📂 تنزيل بيانات الطلاب (Excel)",
            data=b_st.getvalue(),
            file_name=f"students_backup_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

      df_gr_full = st.session_state.df_grades.copy()
      if not df_gr_full.empty:
        b_gr = io.BytesIO()
        with pd.ExcelWriter(b_gr, engine="xlsxwriter") as writer:
          df_gr_full.to_excel(writer, index=False, sheet_name="Grades")
        b_col2.download_button(
            label="📊 تنزيل سجل الدرجات (Excel)",
            data=b_gr.getvalue(),
            file_name=f"grades_backup_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # --- 2. الهوية البصرية والإعدادات الأكاديمية ---
    with set_tabs[1]:
      st.markdown("#### 🎨 المظهر والهوية البصرية")
      theme_options = list(themes.keys())
      current_theme_val = st.session_state.get(
          "app_theme", "الرئيسي (الافتراضي)"
      )
      th_index = (
          theme_options.index(current_theme_val)
          if current_theme_val in theme_options
          else 0
      )
      selected_theme = st.selectbox(
          "اختر هوية المنصة (تطبق فوراً للجميع):", theme_options, index=th_index
      )

      st.markdown("#### ⚙️ الإعدادات الأكاديمية والفصول")
      c_y, c_p = st.columns(2)
      cy = c_y.text_input(
          "العام الدراسي", st.session_state.get("current_year", "1447هـ")
      )

      current_period_val = st.session_state.get(
          "current_period", "الفترة الأولى"
      )
      period_options = [
          "الفترة الأولى",
          "الفترة الثانية",
          "الفصل الثاني - فترة أولى",
          "الفصل الثاني - فترة ثانية",
      ]
      cp_index = (
          period_options.index(current_period_val)
          if current_period_val in period_options
          else 0
      )
      cp = c_p.selectbox("الفترة الدراسية النشطة", period_options, index=cp_index)

      cls = st.text_area(
          "قائمة الصفوف (افصل بينها بفاصلة ,)",
          ",".join(st.session_state.get("class_options", ["الرابع"])),
      )
      stg = st.text_area(
          "قائمة المراحل",
          ",".join(st.session_state.get("stage_options", ["ابتدائي"])),
      )

      c1, c2 = st.columns(2)
      mt = c1.number_input(
          "الدرجة العظمى (مشاركة ومهام)",
          0,
          100,
          st.session_state.get("max_tasks", 60),
      )
      mq = c2.number_input(
          "الدرجة العظمى (اختبارات)",
          0,
          100,
          st.session_state.get("max_quiz", 40),
      )

      if st.button(
          "💾 حفظ الإعدادات وتطبيق التغييرات",
          type="primary",
          use_container_width=True,
      ):
        sh.worksheet("settings").batch_update([
            {"range": "A2:B2", "values": [["max_tasks", mt]]},
            {"range": "A3:B3", "values": [["max_quiz", mq]]},
            {"range": "A4:B4", "values": [["current_year", cy]]},
            {"range": "A5:B5", "values": [["class_list", cls]]},
            {"range": "A6:B6", "values": [["stage_list", stg]]},
            {"range": "A7:B7", "values": [["current_period", cp]]},
            {"range": "A8:B8", "values": [["app_theme", selected_theme]]},
        ])

        st.session_state.max_tasks = mt
        st.session_state.max_quiz = mq
        st.session_state.current_year = cy
        st.session_state.current_period = cp
        st.session_state.class_options = [
            x.strip() for x in cls.split(",") if x.strip()
        ]
        st.session_state.stage_options = [
            x.strip() for x in stg.split(",") if x.strip()
        ]
        st.session_state.app_theme = selected_theme

        st.success(f"✅ تم الحفظ بنجاح! المنصة تعمل بهوية: {selected_theme}")
        if "db_loaded" in st.session_state:
          del st.session_state["db_loaded"]
        st.cache_data.clear()
        st.rerun()

    # --- 3. استيراد البيانات + رفع بيانات أنماط التعلم ---
    with set_tabs[2]:
      import_sub = st.tabs([
          "🧠 رفع وتحديث بيانات أنماط التعلم",
          "📂 استيراد الطلاب أو الدرجات (Excel)",
      ])

      # أ) ✳️ إضافة جديدة: رفع وتحديث بيانات أنماط التعلم
      with import_sub[0]:
        st.markdown("#### 🧠 رفع وتحديث بيانات أنماط التعلم (VARK) دفعة واحدة")
        st.info(
            "💡 يمكنك رفع ملف Excel يحتوي على نتائج استبيان أنماط التعلم"
            " (سواء من نماذج جوجل أو القالب الجاهز). سيقوم النظام بمطابقة"
            " الطلاب تلقائياً عبر **الرقم الأكاديمي (`id`)** أو **اسم الطالب"
            " (`name`)** وتحديث ملفاتهم."
        )

        # تجهيز قالب يحتوي على الطلاب الحاليين لتسهيل التعبئة والرفع
        df_curr_st = st.session_state.df_students.copy()
        if not df_curr_st.empty:
          template_ls_df = pd.DataFrame({
              "id": (
                  df_curr_st.iloc[:, 0]
                  .astype(str)
                  .str.split(".")
                  .str[0]
                  .str.strip()
              ),
              "name": df_curr_st.get("name", ""),
              "class": df_curr_st.get("class", ""),
              "نمط التعلم": df_curr_st.get("نمط التعلم", ""),
          })
        else:
          template_ls_df = pd.DataFrame(
              columns=["id", "name", "class", "نمط التعلم"]
          )

        b_ls_tmpl = io.BytesIO()
        with pd.ExcelWriter(b_ls_tmpl, engine="xlsxwriter") as writer:
          template_ls_df.to_excel(
              writer, index=False, sheet_name="Learning_Styles"
          )

        st.download_button(
            label="📥 تحميل قالب أنماط التعلم بأسماء طلابك الحاليين (Excel)",
            data=b_ls_tmpl.getvalue(),
            file_name=f"Learning_Styles_Template_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.markdown("---")
        up_ls = st.file_uploader(
            "📤 ارفع ملف أنماط التعلم (Excel أو CSV):",
            type=["xlsx", "csv"],
            key="ls_file_uploader",
        )

        if st.button(
            "🚀 بدء مزامنة وتحديث أنماط التعلم",
            type="primary",
            use_container_width=True,
        ) and up_ls:
          try:
            with st.spinner("⏳ جاري تحليل الملف وتحديث أنماط تعلم الطلاب..."):
              if up_ls.name.endswith(".csv"):
                df_up_ls = pd.read_csv(up_ls).fillna("")
              else:
                df_up_ls = pd.read_excel(up_ls).fillna("")

              ws_st = sh.worksheet("students")
              headers = ws_st.row_values(1)

              if "نمط التعلم" not in headers:
                ws_st.update_cell(1, len(headers) + 1, "نمط التعلم")
                headers.append("نمط التعلم")

              style_col_idx = headers.index("نمط التعلم") + 1
              all_st_records = ws_st.get_all_records()

              # بناء قواميس البحث السريع (بالرقم وبالاسم المطبع)
              id_to_row = {}
              name_to_row = {}
              for idx_r, r_st in enumerate(all_st_records):
                row_num = idx_r + 2
                c_id = str(r_st.get("id", "")).strip().split(".")[0]
                c_nm = normalize_arabic(str(r_st.get("name", "")))
                if c_id:
                  id_to_row[c_id] = row_num
                if c_nm:
                  name_to_row[c_nm] = row_num

              # تحديد أعمدة الملف المرفوع بمرونة
              id_col_candidates = [
                  c
                  for c in df_up_ls.columns
                  if str(c).strip().lower()
                  in ["id", "student_id", "الرقم الأكاديمي", "رقم الهوية", "السجل المدني"]
              ]
              name_col_candidates = [
                  c
                  for c in df_up_ls.columns
                  if "اسم" in str(c) or str(c).strip().lower() == "name"
              ]
              style_col_candidates = [
                  c
                  for c in df_up_ls.columns
                  if "نمط" in str(c) or "style" in str(c).lower()
              ]

              id_col_ls = id_col_candidates[0] if id_col_candidates else None
              name_col_ls = (
                  name_col_candidates[0] if name_col_candidates else None
              )
              style_col_ls = (
                  style_col_candidates[0]
                  if style_col_candidates
                  else df_up_ls.columns[-1]
              )

              def format_style_badge(raw_s):
                s = str(raw_s).strip()
                if not s or s.lower() in ["nan", "none"]:
                  return ""
                if "بصري" in s:
                  return "بصري 👀"
                if "سمعي" in s:
                  return "سمعي 👂"
                if "حركي" in s:
                  return "حركي ✋"
                if "متعدد" in s:
                  return "متعدد الأنماط 🌟"
                return s

              from gspread import Cell
              cells_to_update = []
              updated_count = 0

              for _, r_up in df_up_ls.iterrows():
                raw_style = format_style_badge(r_up.get(style_col_ls, ""))
                if not raw_style:
                  continue

                target_row = None
                if id_col_ls:
                  up_id = str(r_up.get(id_col_ls, "")).strip().split(".")[0]
                  if up_id in id_to_row:
                    target_row = id_to_row[up_id]

                if target_row is None and name_col_ls:
                  up_nm = normalize_arabic(str(r_up.get(name_col_ls, "")))
                  if up_nm in name_to_row:
                    target_row = name_to_row[up_nm]

                if target_row is not None:
                  cells_to_update.append(
                      Cell(row=target_row, col=style_col_idx, value=raw_style)
                  )
                  updated_count += 1

              if cells_to_update:
                ws_st.update_cells(cells_to_update)
                st.success(
                    f"✅ تم تحديث أنماط التعلم لـ ({updated_count}) طالب بنجاح!"
                )
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                st.cache_data.clear()
                st.rerun()
              else:
                st.warning(
                    "⚠️ لم يتم العثور على طلاب مطابقين أو أن حقل 'نمط التعلم' فارغ في الملف المرفوع."
                )
          except Exception as e:
            st.error(f"❌ حدث خطأ أثناء رفع أنماط التعلم: {e}")

      # ب) استيراد الطلاب أو الدرجات
      with import_sub[1]:
        st.info(
            "📌 **دليل رصد ورفع الدرجات في المنصة:** \n\n* **عمود (p1):** مخصص"
            " لـ **المشاركة والمهام**.\n* **عمود (p2):** مخصص لـ **الاختبارات"
            " القصيرة**."
        )
        up = st.file_uploader(
            "رفع ملف Excel للطلاب أو الدرجات", type=["xlsx"], key="std_gr_up"
        )
        ts = st.radio(
            "نوع البيانات المرفوعة",
            ["students", "grades"],
            horizontal=True,
            format_func=lambda x: (
                "بيانات الطلاب" if x == "students" else "الدرجات الأكاديمية"
            ),
        )
        if (
            st.button(
                "🚀 بدء المزامنة السريعة",
                type="primary",
                use_container_width=True,
            )
            and up
        ):
          try:
            with st.spinner("جاري معالجة ورفع البيانات دفعة واحدة..."):
              df = pd.read_excel(up).fillna("").dropna(how="all")
              ws = sh.worksheet(ts)

              hd = ws.row_values(1)
              if ts == "grades" and "period" not in hd:
                ws.update_cell(1, len(hd) + 1, "period")
                hd.append("period")

              records = ws.get_all_records()
              if ts == "grades":
                existing_keys = set(
                    f"{str(r.get('student_id', '')).strip().split('.')[0]}_{str(r.get('period', 'الفترة الأولى')).strip()}"
                    for r in records
                )
              else:
                existing_keys = set(
                    str(r.get("id", "")).strip().split(".")[0] for r in records
                )

              new_rows_to_append = []
              progress_bar = st.progress(0)
              cp = st.session_state.get("current_period", "الفترة الأولى").strip()

              for idx, row in df.iterrows():
                d = row.to_dict()
                raw_id = (
                    str(d.get("student_id", d.get("id", "")))
                    .strip()
                    .split(".")[0]
                )
                if not raw_id or raw_id == "0" or raw_id.lower() == "nan":
                  continue

                if ts == "grades":
                  d.update({
                      "student_id": raw_id,
                      "p1": int(d.get("p1", 0)),
                      "p2": int(d.get("p2", 0)),
                      "perf": int(d.get("p1", 0)) + int(d.get("p2", 0)),
                      "date": str(datetime.date.today()),
                      "period": str(d.get("period", cp)).strip(),
                  })
                  if "id" in d:
                    del d["id"]
                  check_key = f"{raw_id}_{d['period']}"
                else:
                  d["id"] = raw_id
                  d["الجوال"] = clean_phone_number(d.get("الجوال", ""))
                  if (
                      "النقاط" not in d
                      or str(d.get("النقاط", "")).strip() == ""
                  ):
                    d["النقاط"] = 0
                  check_key = raw_id

                if check_key not in existing_keys:
                  new_rows_to_append.append([str(d.get(k, "")) for k in hd])

                progress_bar.progress(min((idx + 1) / len(df), 1.0))

              if new_rows_to_append:
                ws.append_rows(new_rows_to_append)
                st.success(
                    f"✅ تم إضافة {len(new_rows_to_append)} سجل جديد بنجاح لـ ({cp})!"
                )
              else:
                st.info(
                    f"💡 جميع البيانات المرفوعة موجودة مسبقاً في ({cp})، لم يتم إضافة جديد."
                )

              if "db_loaded" in st.session_state:
                del st.session_state["db_loaded"]
              st.cache_data.clear()
              st.rerun()
          except Exception as e:
            st.error(f"حدث خطأ أثناء المزامنة: {e}")

        st.divider()
        c1, c2 = st.columns(2)
        b1 = io.BytesIO()
        pd.DataFrame(
            columns=[
                "id",
                "name",
                "class",
                "year",
                "sem",
                "الجوال",
                "الإيميل",
                "النقاط",
                "نمط التعلم",
            ]
        ).to_excel(b1, index=False)
        c1.download_button(
            "📥 قالب فارغ (طلاب)",
            b1.getvalue(),
            "students_template.xlsx",
            use_container_width=True,
        )
        b2 = io.BytesIO()
        pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(
            b2, index=False
        )
        c2.download_button(
            "📥 قالب فارغ (درجات)",
            b2.getvalue(),
            "grades_template.xlsx",
            use_container_width=True,
        )

    # --- 4. إدارة المستخدمين ---
    with set_tabs[3]:
      st.markdown("#### 🔐 إدارة حسابات المعلمين والإدارة")
      u_tabs = st.tabs([
          "➕ إضافة مستخدم",
          "🔑 تعديل كلمة المرور",
          "🗑️ حذف مستخدم",
          "🕒 سجل آخر ظهور",
      ])

      with u_tabs[0]:
        with st.form("add_u"):
          nu = st.text_input("اسم المستخدم الجديد")
          np = st.text_input("كلمة المرور", type="password")
          nrole_label = st.selectbox(
              "نوع الحساب والصلاحية",
              [
                  "👨‍🏫 معلم (صلاحيات كاملة)",
                  "👁️ إدارة (مشاهد وقراءة فقط)",
              ],
          )
          if st.form_submit_button(
              "إضافة المستخدم", type="primary", use_container_width=True
          ):
            if nu and np:
              role_val = "teacher" if "معلم" in nrole_label else "viewer"
              safe_append_row(
                  "users",
                  {
                      "username": nu,
                      "password_hash": hashlib.sha256(np.encode()).hexdigest(),
                      "role": role_val,
                  },
              )
              st.success(f"✅ تمت إضافة الحساب ({nu}) بنجاح كـ {role_val}.")
              st.cache_data.clear()
            else:
              st.warning("الرجاء إكمال البيانات.")

      with u_tabs[1]:
        with st.form("chg_pass"):
          df_u_edit = fetch_safe("users")
          if not df_u_edit.empty:
            target_u = st.selectbox(
                "اختر المستخدم لتعديل رقمه السري:",
                df_u_edit["username"].tolist(),
            )
            npwd = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button(
                "تحديث كلمة المرور", type="primary", use_container_width=True
            ):
              if npwd:
                idx = (
                    df_u_edit[df_u_edit["username"] == target_u].index[0] + 2
                )
                sh.worksheet("users").update_cell(
                    idx, 2, hashlib.sha256(npwd.encode()).hexdigest()
                )
                st.success(f"✅ تم تحديث كلمة المرور لـ ({target_u}).")
                st.cache_data.clear()
              else:
                st.warning("الرجاء إدخال كلمة المرور الجديدة.")
          else:
            st.info("لا يوجد مستخدمين بعد.")

      with u_tabs[2]:
        df_u_del = fetch_safe("users")
        if not df_u_del.empty:
          del_u = st.selectbox(
              "اختر المستخدم المراد حذفه:", [""] + df_u_del["username"].tolist()
          )
          if st.button(
              "🗑️ حذف المستخدم نهائياً",
              type="primary",
              use_container_width=True,
          ):
            if del_u:
              if del_u == st.session_state.username:
                st.error("⚠️ لا يمكنك حذف حسابك الحالي!")
              else:
                idx = df_u_del[df_u_del["username"] == del_u].index[0] + 2
                sh.worksheet("users").delete_rows(int(idx))
                st.success(f"✅ تم حذف المستخدم ({del_u}).")
                st.cache_data.clear()
                st.rerun()
            else:
              st.warning("الرجاء اختيار مستخدم للحذف.")

      with u_tabs[3]:
        df_users_log = fetch_safe("users")
        if not df_users_log.empty:
          if "last_login" in df_users_log.columns:
            disp_df = df_users_log[
                ["username", "role", "last_login"]
            ].rename(
                columns={
                    "username": "المستخدم",
                    "role": "الصلاحية",
                    "last_login": "آخر تسجيل دخول",
                }
            )
            disp_df["الصلاحية"] = disp_df["الصلاحية"].replace(
                {"teacher": "👨‍🏫 معلم", "viewer": "👁️ إدارة"}
            )
            st.dataframe(disp_df, use_container_width=True, hide_index=True)
          else:
            st.info("لم يتم تسجيل أي عمليات دخول حديثة بعد التحديث.")
        else:
          st.info("لا توجد بيانات للمستخدمين.")


# ==========================================
# 🛑 11. التبويب السابع: تسجيل الخروج (للمعلم والإدارة)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("هل ترغب في تسجيل الخروج من لوحة التحكم والعودة لشاشة الدخول؟")
    if st.button(
        "🚪 تأكيد تسجيل الخروج", type="primary", use_container_width=True
    ):
      st.session_state.role = None
      if "db_loaded" in st.session_state:
        del st.session_state["db_loaded"]
      st.rerun()

  show_footer()


# ==========================================
# 👨‍🎓 12. واجهة الطالب الكاملة (مع شبكة 2×2 والوضع الليلي)
# ==========================================
if st.session_state.role == "student":
  sid = str(st.session_state.get("username", "")).strip()
  df_st = st.session_state.df_students.copy()
  df_gr = st.session_state.df_grades.copy()
  df_beh = st.session_state.df_behavior.copy()
  df_ann = fetch_safe("exams")

  if not df_st.empty:
    df_st["clean_id"] = (
        df_st.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
    )
    info = df_st[df_st["clean_id"] == sid]
  else:
    info = pd.DataFrame()

  if not info.empty:
    s_dat = info.iloc[0]
    s_nm = s_dat.get("name", "طالب")
    s_cls = str(s_dat.get("class", "")).strip()
    pts = int(pd.to_numeric(s_dat.get("النقاط", 0), errors="coerce") or 0)

    # إشعار التعاميم العاجلة
    if not df_ann.empty:
      df_ann["عاجل"] = df_ann["عاجل"].astype(str).str.strip()
      df_ann["الصف"] = df_ann["الصف"].astype(str).str.strip()
      urg = df_ann[
          (df_ann["عاجل"] == "نعم") & (df_ann["الصف"].isin(["الكل", s_cls]))
      ]
      if not urg.empty:
        u = urg.tail(1).iloc[0]
        link_text = str(u.get("الرابط", ""))
        link_display = (
            f"<a href='{link_text}' target='_blank'"
            f" style='color:{danger_color}; text-decoration:underline;'>اضغط"
            " هنا</a>"
            if link_text.startswith("http")
            else link_text
            if link_text.lower() != "none"
            else ""
        )
        st.markdown(
            f"<div class='urgent-box'>🚨 {u.get('العنوان')}<br><small"
            f" style='color:{danger_color}'>{link_display}</small></div>",
            unsafe_allow_html=True,
        )

    # إشعار المخالفات السلوكية لولي الأمر
    if not df_beh.empty:
      df_beh["clean_id"] = df_beh.iloc[:, 0].astype(str).str.split(".").str[0]
      my_beh_alerts = df_beh[df_beh["clean_id"] == sid]

      if not my_beh_alerts.empty:
        last_record = my_beh_alerts.iloc[-1]
        b_type = str(last_record.get("type", ""))
        if (
            "-" in b_type
            or "سلبي" in b_type
            or "تنبيه" in b_type
            or "نقص" in b_type
            or "تأخر" in b_type
        ):
          st.markdown(
              f"""
              <div class="urgent-box" style="margin-bottom: 15px; padding-bottom: 10px;">
                  <h4 style="margin: 0 0 5px 0;">⚠️ إشعار سلوكي لولي الأمر</h4>
                  <p style="color: var(--text-color); margin: 0; font-weight: bold; font-size: 1.1rem;">{b_type}</p>
                  <span style="color: #94A3B8; font-size: 0.9rem; display:block; margin-bottom: 10px;">التفاصيل: {last_record.get('note', 'لا توجد تفاصيل')} | التاريخ: {last_record.get('date', '')}</span>
                  <div style="background-color: rgba(239, 68, 68, 0.15); padding: 6px; border-radius: 8px; font-size: 0.85rem; color: #EF4444;">
                      👇 <b>فضلاً:</b> نرجو الانتقال إلى تبويب <b>(📝 السلوك)</b> بالأسفل للاطلاع على السجل التفصيلي.
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )

    st.markdown(
        f"""
        <div class="welcome-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div><h2 style="color:white; margin:0; font-size:1.5rem;">👋 أهلاً بك، {s_nm}</h2><p style="color:{t_colors['sub_color']}; margin:5px 0 0 0; font-weight:bold;">{s_cls}</p></div>
                <div style="background:rgba(255,255,255,0.2); padding:5px 15px; border-radius:12px;"><span style="font-weight:bold; font-size:0.9rem; color:#FFFFFF;">ID: {sid}</span></div>
            </div>
        </div>
        <div class="points-banner">
            <p style="margin:0; opacity:0.95; font-size:0.95rem; font-weight:bold;">رصيد النقاط الحالي</p>
            <h1 style="margin:0; font-size:3.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">{pts}</h1>
            <p style="margin:0; font-size:0.85rem; font-weight:bold;">استمر في التفوق!</p>
        </div>
        <div class="medal-flex">
            <div class="m-card {'m-active' if pts>=100 else ''}" style="color: {warning_color};">🥇<br><b>ذهبي (100+)</b></div>
            <div class="m-card {'m-active' if pts>=50 else ''}" style="color: #94A3B8;">🥈<br><b>فضي (50+)</b></div>
            <div class="m-card m-active" style="color: #D97706;">🥉<br><b>برونزي</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📢 التنبيهات",
        "📝 السلوك",
        "📊 الدرجات والشهادة",
        "🏆 لوحة الشرف",
        "🧠 نمط التعلم",
        "⚙️ حسابي والخروج",
    ])

    with tabs[0]:
      st.caption("التعاميم والتنبيهات الموجهة لصفك")
      if not df_ann.empty:
        anns = df_ann[
            df_ann["الصف"].astype(str).str.strip().isin(["الكل", s_cls])
        ]
        for _, r in anns.iloc[::-1].iterrows():
          row_link = str(r.get("الرابط", ""))
          row_link_display = (
              f"<a href='{row_link}' target='_blank'"
              f" style='color:{accent_color}; text-decoration:underline;'>اضغط"
              " هنا للفتح</a>"
              if row_link.startswith("http")
              else row_link
              if row_link.lower() != "none"
              else ""
          )
          st.markdown(
              f"""
              <div class='mobile-list-item'>
                  <div style="width:100%">
                      <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><b>📢 {r.get('العنوان')}</b><small style="background:var(--background-color); color:{accent_color}; padding:2px 8px; border-radius:6px; font-weight:bold;">{r.get('التاريخ')}</small></div>
                      <span style="color:#94A3B8; font-size:0.92rem;">{row_link_display}</span>
                  </div>
              </div>""",
              unsafe_allow_html=True,
          )
      else:
        st.info("لا توجد تنبيهات حالياً.")

    with tabs[1]:
      st.caption("سجل السلوك والملاحظات")
      if not df_beh.empty:
        df_beh["clean_id"] = (
            df_beh.iloc[:, 0].astype(str).str.split(".").str[0]
        )
        nts = df_beh[df_beh["clean_id"] == sid].copy()

        if not nts.empty:
          nts = nts.iloc[::-1]
          nts["date_parsed"] = pd.to_datetime(nts["date"], errors="coerce")
          nts = nts.sort_values(
              by="date_parsed", ascending=False, kind="mergesort"
          )

          for _, n in nts.iterrows():
            color = (
                danger_color
                if "سلبي" in str(n.get("type")) or "-" in str(n.get("type"))
                else success_color
            )
            st.markdown(
                f"<div class='mobile-list-item' style='border-right: 5px solid"
                f" {color};'><div><b"
                f" style='color:{color}'>{n.get('type')}</b><p"
                " style='margin:4px 0; font-size:0.92rem;"
                f" color:var(--text-color);'>{n.get('note')}</p><small"
                f" style='color:#94A3B8;'>{n.get('date')}</small></div></div>",
                unsafe_allow_html=True,
            )
        else:
          st.success("🌟 سجلك نظيف تماماً!")
      else:
        st.success("🌟 سجلك نظيف تماماً!")

    with tabs[2]:
      cp = st.session_state.get("current_period", "الفترة الأولى").strip()
      st.caption(f"درجاتي الأكاديمية - {cp}")

      if not df_gr.empty:
        df_gr["clean_id"] = (
            df_gr.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]
        )
        if "period" not in df_gr.columns:
          df_gr["period"] = "الفترة الأولى"
        df_gr["period"] = (
            df_gr["period"]
            .replace(["", None, "nan", "NaN"], "الفترة الأولى")
            .astype(str)
            .str.strip()
        )

        grs = df_gr[(df_gr["clean_id"] == sid) & (df_gr["period"] == cp)]

        if not grs.empty:
          g = grs.iloc[-1]
          max_total = st.session_state.max_tasks + st.session_state.max_quiz
          perf_score = int(pd.to_numeric(g.get("perf", 0), errors="coerce") or 0)
          percentage = (perf_score / max_total) * 100 if max_total > 0 else 0

          if percentage >= 90:
            title, title_color = "🌟 أسطورة المنصة", warning_color
          elif percentage >= 80:
            title, title_color = "🚀 بطل مبدع", accent_color
          elif percentage >= 70:
            title, title_color = "👍 متألق ومجتهد", success_color
          elif percentage >= 60:
            title, title_color = "💪 واصل تقدمك", primary_color
          else:
            title, title_color = "🌱 أنت قادر على الأفضل", sub_text

          st.markdown(
              f"""
              <div class='mobile-list-item'>
                  <span style="font-weight:bold;">📝 المشاركة والواجبات</span>
                  <div>
                      <span style='font-size:1.4rem; font-weight:900; color:{accent_color};'>{g.get('p1')}</span> 
                      <span style='color:#94A3B8; font-size:0.9rem; font-weight:bold;'>/ {st.session_state.max_tasks}</span>
                  </div>
              </div>
              <div class='mobile-list-item'>
                  <span style="font-weight:bold;">✍️ الاختبارات القصيرة</span>
                  <div>
                      <span style='font-size:1.4rem; font-weight:900; color:{accent_color};'>{g.get('p2')}</span> 
                      <span style='color:#94A3B8; font-size:0.9rem; font-weight:bold;'>/ {st.session_state.max_quiz}</span>
                  </div>
              </div>
              <div class='mobile-list-item' style='background:var(--secondary-background-color); border-color:{accent_color}; display:flex; flex-direction:column; align-items:flex-start;'>
                  <div style="width:100%; display:flex; justify-content:space-between; align-items:center;">
                      <span style="color:{accent_color}; font-weight:900;">🏆 المجموع النهائي ({cp})</span>
                      <div>
                          <span style='font-size:1.6rem; font-weight:900; color:{accent_color};'>{perf_score}</span> 
                          <span style='color:#94A3B8; font-size:1rem; font-weight:bold;'>/ {max_total}</span>
                      </div>
                  </div>
                  <div style="margin-top:10px; width:100%; text-align:center; padding:8px; background:var(--background-color); border-radius:10px; color:{title_color}; font-weight:900; font-size:1.1rem; border:1.5px solid {title_color}55;">
                      {title}
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )

          if percentage >= 90:
            st.divider()
            st.success(
                "🎉 مبروك! لتفوقك وحصولك على درجة الامتياز، تم تفعيل ميزة"
                " استخراج 'شهادة التفوق الإلكترونية'."
            )
            school_st = get_school_name_dynamic(s_cls).replace("<br>", " - ")
            certificate_html = f"""
            <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>شهادة تفوق - {s_nm}</title>
            <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
            <style>
                * {{ box-sizing: border-box; }}
                body {{ margin: 0; padding: 0; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .cert-page {{ width: 297mm; height: 210mm; padding: 10mm; background: #ffffff; position: relative; box-shadow: 0 0 20px rgba(0,0,0,0.1); overflow: hidden; }}
                .border-outer {{ border: 14px solid #193b68; height: 100%; width: 100%; padding: 6px; position: relative; }}
                .border-inner {{ border: 3px solid #b68a36; height: 100%; width: 100%; position: relative; padding: 25px 40px; text-align: center; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 25px 25px; display: flex; flex-direction: column; justify-content: space-between; }}
                .corner {{ position: absolute; width: 30px; height: 30px; border: 4px solid #b68a36; }}
                .tl {{ top: -8px; left: -8px; border-right: none; border-bottom: none; }}
                .tr {{ top: -8px; right: -8px; border-left: none; border-bottom: none; }}
                .bl {{ bottom: -8px; left: -8px; border-right: none; border-top: none; }}
                .br {{ bottom: -8px; right: -8px; border-left: none; border-top: none; }}
                h1 {{ font-family: 'Aref Ruqaa', serif; font-size: 66px; color: #b68a36; margin: 0; font-weight: normal; }}
                h2 {{ font-family: 'Cairo', sans-serif; font-size: 32px; color: #193b68; margin: 5px 0 15px 0; font-weight: 900; }}
                p.intro {{ font-family: 'Cairo', sans-serif; font-size: 22px; color: #193b68; margin-bottom: 10px; }}
                .student-name {{ font-family: 'Cairo', sans-serif; font-size: 50px; font-weight: 900; color: #d32f2f; margin: 10px auto; display: inline-block; border-bottom: 3px solid #b68a36; padding: 0 30px 5px 30px; }}
                p.reason {{ font-family: 'Cairo', sans-serif; font-size: 23px; font-weight: 600; color: #444; line-height: 1.7; margin: 0; }}
                .footer-section {{ display: flex; justify-content: space-between; align-items: flex-end; margin-top: 20px; padding: 0 30px; font-family: 'Cairo', sans-serif; }}
                .sig-box, .date-box {{ text-align: center; color: #193b68; width: 220px; }}
                .sig-title {{ font-size: 20px; font-weight: bold; }}
                .sig-line {{ border-bottom: 1px solid #b68a36; width: 150px; margin: 8px auto; }}
                .sig-name {{ font-family: 'Aref Ruqaa', serif; font-size: 32px; color: #193b68; }}
                .date-val {{ font-size: 20px; font-weight: bold; color: #333; margin-top: 8px; }}
                @media print {{ @page {{ size: A4 landscape; margin: 0mm; }} body {{ background: white; }} .cert-page {{ padding: 0; box-shadow: none; width: 297mm; height: 210mm; }} }}
            </style></head><body>
                <div class="cert-page">
                    <div class="border-outer">
                        <div class="border-inner">
                            <div class="corner tl"></div><div class="corner tr"></div>
                            <div class="corner bl"></div><div class="corner br"></div>
                            <div style="display:flex; justify-content:space-between; font-family:'Cairo',sans-serif; font-size:14px; font-weight:bold; color:#193b68;">
                                <div>المملكة العربية السعودية - وزارة التعليم<br>{school_st}</div>
                                <div>العام الدراسي: {st.session_state.get('current_year', '1447هـ')}<br>{cp}</div>
                            </div>
                            <h1>شهادة شكر وتقدير</h1>
                            <h2>⭐ وسام التميز الأكاديمي ⭐</h2>
                            <p class="intro">يتقدم الأستاذ/ <strong>زياد المعمري</strong> بوافر الشكر والتقدير للطالب المبدع والمتألق:</p>
                            <div class="student-name">{s_nm}</div>
                            <div>
                                <p class="reason">وذلك نظير تفوقه العلمي وحصوله على تقدير <b style="color:#d32f2f;">ممتاز</b> في مادة اللغة الإنجليزية.</p>
                                <p class="reason">متمنين له دوام التوفيق ومزيداً من التألق والنجاح.</p>
                            </div>
                            <div class="footer-section">
                                <div class="date-box">
                                    <div class="sig-title">تاريخ الإصدار</div>
                                    <div class="sig-line"></div>
                                    <div class="date-val">{datetime.date.today().strftime('%Y-%m-%d')}</div>
                                </div>
                                <div style="width: 135px; height: 135px; border: 3px dashed #d32f2f; border-radius: 50%; transform: rotate(-15deg); color: #d32f2f; text-align: center; opacity: 0.85; padding-top: 22px; margin: 0 auto;">
                                    <div style="font-family: 'Cairo', sans-serif; font-size: 15px; font-weight: 900;">وسام</div>
                                    <div style="font-family: 'Aref Ruqaa', serif; font-size: 32px; font-weight: bold; line-height: 1.2;">ختم التميز</div>
                                    <div style="font-family: 'Cairo', sans-serif; font-size: 12px; font-weight: bold;">الأكاديمي</div>
                                </div>
                                <div class="sig-box">
                                    <div class="sig-title">توقيع المعلم</div>
                                    <div class="sig-line"></div>
                                    <div class="sig-name">زياد المعمري</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <script>window.onload = function() {{ window.print(); }}</script>
            </body></html>
            """
            st.download_button(
                label="📜 تحميل وطباعة شهادة التفوق الإلكترونية",
                data=certificate_html,
                file_name=f"Certificate_{sid}_{s_nm}.html",
                mime="text/html",
                type="primary",
                use_container_width=True,
            )
        else:
          st.info(f"لم يتم رصد درجات لك في ({cp}) حتى الآن.")
      else:
        st.info("لم يتم رصد درجات حتى الآن.")

    with tabs[3]:
      st.caption("لوحة الشرف (أفضل 10 طلاب في المنصة)")
      df_st["p_num"] = pd.to_numeric(df_st["النقاط"], errors="coerce").fillna(0)
      active_students = df_st[df_st["p_num"] > 0]

      if not active_students.empty:
        for i, (_, r) in enumerate(
            active_students.sort_values("p_num", ascending=False)
            .head(10)
            .iterrows(),
            1,
        ):
          ic = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
          sty = (
              f"border:2px solid {warning_color}; background:rgba(245, 158, 11, 0.1);"
              if str(r["clean_id"]) == sid
              else ""
          )
          st.markdown(
              f"""
              <div class='mobile-list-item' style='{sty}'>
                  <div style='display:flex; align-items:center; gap:10px;'>
                      <span style='font-weight:900; font-size:1.2rem; min-width:40px; display:inline-block; text-align:center; white-space:nowrap;'>{ic}</span>
                      <span style='font-weight:bold;'>{r['name']}</span>
                  </div>
                  <span style='color:{warning_color}; font-weight:900; font-size:1.1rem;'>{int(r['p_num'])} نقطة</span>
              </div>
              """,
              unsafe_allow_html=True,
          )
      else:
        st.info("لوحة الشرف فارغة حالياً. كن أنت أول المبادرين وتصدر القائمة! 🚀")

    with tabs[4]:
      st.subheader("🧠 اكتشف نمط تعلمك")
      st.caption(
          "أجب عن هذه المواقف السبعة لنعرف الطريقة التي تفضلها وتتفوق بها في التعلم!"
      )

      current_style = ""
      if "نمط التعلم" in df_st.columns:
        val = df_st.loc[df_st["clean_id"] == sid, "نمط التعلم"].values
        if (
            len(val) > 0
            and pd.notna(val[0])
            and str(val[0]).strip() not in ["", "nan", "None"]
        ):
          current_style = str(val[0]).strip()

      if current_style:
        color = (
            "#3B82F6"
            if "بصري" in current_style
            else "#10B981"
            if "سمعي" in current_style
            else "#F59E0B"
            if "حركي" in current_style
            else "#8B5CF6"
        )
        st.markdown(
            f"""
            <div style='background-color:{color}20; border:2px solid {color}; padding:25px; border-radius:16px; text-align:center; margin-top:15px;'>
                <div style='font-size:45px; margin-bottom:10px;'>{current_style.split()[-1] if len(current_style.split())>1 else '🎯'}</div>
                <h3 style='color:{color}; margin-bottom:8px; font-weight:900;'>أنت متعلم {current_style.replace('👀', '').replace('👂', '').replace('✋', '').replace('🌟', '').strip()}</h3>
                <p style='color:#94A3B8; font-size:14px; margin:0; font-weight:bold;'>تم حفظ نمط تعلمك في ملفك الأكاديمي بنجاح.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
      else:
        with st.form("learning_style_quiz"):
          st.info(
              "تخيل نفسك في هذه المواقف، واختر الإجابة التي تشبهك أكثر:"
          )

          q1 = st.radio(
              "1️⃣ عندما تلعب لعبة جديدة (إلكترونية أو ورقية)، كيف تتعلمها؟",
              [
                  "👀 أقرأ التعليمات أو أشاهد الصور التوضيحية (بصري)",
                  "👂 أطلب من صديقي أن يشرح لي طريقة اللعب (سمعي)",
                  "✋ أبدأ باللعب فوراً وأتعلم من أخطائي والتجربة (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q2 = st.radio(
              "2️⃣ عندما تذاكر لاختبار مهم، ما هي طريقتك المفضلة؟",
              [
                  "🖼️ أستخدم الأقلام الملونة، التخطيط، وقراءة الملخصات (بصري)",
                  "🗣️ أقرأ بصوت عالٍ أو أسمع شرح المعلم في عقلي (سمعي)",
                  "🚶 أتحرك في الغرفة أثناء الحفظ أو أكتب بيدي عدة مرات (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q3 = st.radio(
              "3️⃣ في وقت فراغك بالمنزل، ما هو نشاطك المفضل؟",
              [
                  "🎨 مشاهدة اليوتيوب، أو الرسم والتلوين (بصري)",
                  "🎧 الاستماع للأناشيد، البودكاست، أو التحدث مع الأصدقاء (سمعي)",
                  "⚽ اللعب بالكرة، الألعاب الحركية، أو الفك والتركيب (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q4 = st.radio(
              "4️⃣ إذا ذهبت في رحلة لمكان جديد، ما أكثر شيء تتذكره بعد العودة؟",
              [
                  "📸 شكل المكان والأشياء الجميلة التي رأيتها (بصري)",
                  "💬 الأصوات، الأناشيد، والأحاديث التي دارت في الرحلة (سمعي)",
                  "🏃 الألعاب والأنشطة التي قمت بها وحركتي هناك (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q5 = st.radio(
              "5️⃣ عندما يطلب منك المعلم تركيب جهاز أو عمل مشروع، كيف تبدأ؟",
              [
                  "📖 أنظر إلى صورة الشكل النهائي لأعرف كيف سيكون (بصري)",
                  "❓ أسأل المعلم أو زملائي عن الخطوة الأولى (سمعي)",
                  "🛠️ أمسك القطع بيدي وأبدأ بمحاولة تركيبها مباشرة (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q6 = st.radio(
              "6️⃣ عندما تحفظ قصة أو آيات من القرآن، ماذا تفعل غالباً؟",
              [
                  "👁️ أتذكر شكل الصفحة ومكان الكلمات فيها (بصري)",
                  "🎤 أكررها بصوت عالٍ أو أستمع لقارئ (سمعي)",
                  "🖐️ أستخدم أصابعي للعد أو أتحرك ذهاباً وإياباً أثناء الحفظ (حركي)",
              ],
              index=None,
          )
          st.write("---")

          q7 = st.radio(
              "7️⃣ عندما تشتري جهازاً أو لعبة جديدة، ما الذي يلفت انتباهك أولاً؟",
              [
                  "✨ الألوان والتصميم وشكل العلبة الخارجي (بصري)",
                  "🔊 الأصوات التي تصدرها اللعبة أو ما يقوله أصدقاؤك عنها (سمعي)",
                  "🕹️ الأزرار وملمسها وكيفية تحريكها واللعب بها (حركي)",
              ],
              index=None,
          )

          if st.form_submit_button(
              "🚀 إرسال الإجابات واكتشاف نمطي",
              type="primary",
              use_container_width=True,
          ):
            answers = [q1, q2, q3, q4, q5, q6, q7]
            if None in answers:
              st.warning(
                  "⚠️ عذراً يا بطل، يجب عليك اختيار إجابة لجميع المواقف السبعة قبل إرسال النتيجة."
              )
            else:
              v_count = sum(1 for a in answers if "بصري" in a)
              a_count = sum(1 for a in answers if "سمعي" in a)
              k_count = sum(1 for a in answers if "حركي" in a)

              if v_count > a_count and v_count > k_count:
                final_style = "بصري 👀"
              elif a_count > v_count and a_count > k_count:
                final_style = "سمعي 👂"
              elif k_count > v_count and k_count > a_count:
                final_style = "حركي ✋"
              else:
                final_style = "متعدد الأنماط 🌟"

              try:
                ws = sh.worksheet("students")
                headers = ws.row_values(1)
                if "نمط التعلم" not in headers:
                  ws.update_cell(1, len(headers) + 1, "نمط التعلم")
                  headers.append("نمط التعلم")

                style_col_idx = headers.index("نمط التعلم") + 1
                cell = ws.find(sid)
                if cell:
                  ws.update_cell(cell.row, style_col_idx, final_style)
                  st.success(
                      f"🎉 رائع! تم حفظ النتيجة. نمط تعلمك هو: {final_style}"
                  )
                  if "db_loaded" in st.session_state:
                    del st.session_state["db_loaded"]
                  st.cache_data.clear()
                  st.rerun()
              except Exception as e:
                st.error(f"❌ حدث خطأ أثناء حفظ النتيجة، حاول مرة أخرى. ({e})")

    with tabs[5]:
      st.caption("إدارة الملف الشخصي وتسجيل الخروج")
      with st.form("my_profile"):
        nm = st.text_input("📧 البريد الإلكتروني", s_dat.get("الإيميل", ""))
        np = st.text_input("📱 رقم الجوال", s_dat.get("الجوال", ""))
        if st.form_submit_button(
            "💾 تحديث بياناتي", type="primary", use_container_width=True
        ):
          try:
            fp = clean_phone_number(np) if np else ""
            ws = sh.worksheet("students")
            c = ws.find(sid)
            if c:
              h = ws.row_values(1)
              if "الإيميل" in h and "الجوال" in h:
                ws.update_cell(c.row, h.index("الإيميل") + 1, nm)
                ws.update_cell(c.row, h.index("الجوال") + 1, fp)
                st.success("✅ تم تحديث بيانات التواصل بنجاح")
              else:
                st.error("خطأ هيكلي في الأعمدة")
          except Exception as e:
            st.error(f"خطأ: {e}")

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button(
          "🚪 تسجيل الخروج من حسابي",
          type="secondary",
          use_container_width=True,
      ):
        st.session_state.role = None
        if "db_loaded" in st.session_state:
          del st.session_state["db_loaded"]
        st.rerun()

  else:
    st.error("عذراً، لم يتم العثور على بياناتك")
    if st.button("العودة للقائمة الرئيسية"):
      st.session_state.role = None
      st.rerun()

  show_footer()            
