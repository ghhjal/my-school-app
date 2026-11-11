import datetime
import hashlib
import io
import json
import math
import re
import urllib.parse
from google.oauth2.service_account import Credentials
import gspread
from gspread import Cell
from gspread.utils import rowcol_to_a1
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
      if worksheet_name == "grades" and "period" in df.columns:
        df["period"] = (
            df["period"]
            .astype(str)
            .str.strip()
            .replace({
                "": "الفصل الأول - فترة أولى",
                "nan": "الفصل الأول - فترة أولى",
                "None": "الفصل الأول - فترة أولى",
                "الفترة الأولى": "الفصل الأول - فترة أولى",
                "الفترة الثانية": "الفصل الأول - فترة ثانية",
            })
        )
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


@st.cache_data(ttl=600)
def build_excel_bytes(df_to_export, sheet_name="Sheet1", include_index=False):
  b_io = io.BytesIO()
  with pd.ExcelWriter(b_io, engine="xlsxwriter") as writer:
    df_to_export.to_excel(writer, index=include_index, sheet_name=sheet_name)
  return b_io.getvalue()


@st.cache_data(ttl=3600)
def generate_pdf_bytes_cached(html_str):
  from weasyprint import HTML
  return HTML(string=html_str).write_pdf()


# --- تحميل الإعدادات وخريطة المراحل في الجلسة منذ لحظة التشغيل ---
if "class_options" not in st.session_state:
  s_map = get_cached_settings()
  if s_map:
    st.session_state.max_tasks = int(s_map.get("max_tasks", 60))
    st.session_state.max_quiz = int(s_map.get("max_quiz", 40))
    st.session_state.current_year = str(s_map.get("current_year", "1448هـ")).strip()
    raw_per = str(s_map.get("current_period", "الفصل الأول - فترة أولى")).strip()
    if raw_per == "الفترة الأولى":
      raw_per = "الفصل الأول - فترة أولى"
    elif raw_per == "الفترة الثانية":
      raw_per = "الفصل الأول - فترة ثانية"
    st.session_state.current_period = raw_per
    st.session_state.app_theme = str(s_map.get("app_theme", "الرئيسي (الافتراضي)")).strip()
    st.session_state.class_options = [
        x.strip() for x in str(s_map.get("class_list", "الأول")).split(",") if x.strip()
    ]
    st.session_state.stage_options = [
        x.strip() for x in str(s_map.get("stage_list", "ابتدائي")).split(",") if x.strip()
    ]
    raw_cs = s_map.get("class_stage_map", "")
    loaded_cs = {}
    if raw_cs:
      try:
        loaded_cs = json.loads(raw_cs)
      except Exception:
        loaded_cs = {}
    for c_it in st.session_state.class_options:
      if c_it not in loaded_cs:
        loaded_cs[c_it] = "متوسط" if "متوسط" in str(c_it) else "ابتدائي"
    st.session_state.class_stage_map = loaded_cs
  else:
    st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
    st.session_state.current_year = "1448هـ"
    st.session_state.current_period = "الفصل الأول - فترة أولى"
    st.session_state.app_theme = "الرئيسي (الافتراضي)"
    st.session_state.class_options = ["الأول"]
    st.session_state.stage_options = ["ابتدائي"]
    st.session_state.class_stage_map = {"الأول": "ابتدائي"}

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
        "subtitle": "عزّنا بطبعنا<br><span style='font-size:1.1rem; color:#ffffff; opacity:0.9;'>اليوم الوطني السعودي 96</span>",
        "bg_pattern": "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
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
        "subtitle": "يوم بدينا<br><span style='font-size:1.1rem; color:#F5DEB3; opacity:0.9;'>ثلاثة قرون من العز والفخر</span>",
        "bg_pattern": "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 0l20 20-20 20L0 20z' fill='%23ffffff' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E\")",
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
        "subtitle": "مبارك عليكم الشهر<br><span style='font-size:1.1rem; color:#D4AF37; opacity:0.9;'>رمضان يجمعنا</span>",
        "bg_pattern": "url(\"data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='2' cy='2' r='2' fill='%23ffffff' fill-opacity='0.05'/%3E%3C/svg%3E\")",
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
        "subtitle": "حصاد التفوق والنجاح<br><span style='font-size:1.1rem; color:#ffffff; opacity:0.9;'>نهاية العام الدراسي</span>",
        "bg_pattern": "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.15'%3E%3Cpath d='M10.1 23l4.6-4.6-3.2-3.2-4.6 4.6 3.2 3.2zm14.2 0l-4.6-4.6 3.2-3.2 4.6 4.6-3.2 3.2z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
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
  stage_mapped = st.session_state.get("class_stage_map", {}).get(str(cls_name).strip(), "")
  if stage_mapped == "متوسط" or "متوسط" in str(cls_name):
    return "متوسطة عبدالرحمن الناصر"
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
  c1.link_button("📢 تليجرام الإدارة", "https://t.me/@ZiyadAlmoami", use_container_width=True)
  c2.link_button("💬 واتساب المعلم", "https://wa.me/966534900049", use_container_width=True)
  c3.link_button("📧 البريد الإلكتروني", "mailto:ziad.platform.alerts@gmail.com", use_container_width=True)


# ==========================================
# 🎨 2. التصميم الاحترافي والمحاذاة العربية الكاملة (RTL) وشبكة الجوال (2×2)
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

section[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stHeaderActionElements"] {{
    display: none !important;
}}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* ✳️ 1. فرض الاتجاه العربي (من اليمين إلى اليسار) على كامل المنصة والعناوين */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container {{
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    max-width: 1080px !important;
}}

/* ✳️ 2. محاذاة جميع العناوين الفرعية والتسميات والتنبيهات والقوائم المطوية لليمين */
h1, h2, h3, h4, h5, h6, p, label,
[data-testid="stHeadingWithActionElements"],
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stHeadingWithActionElements"] h3,
[data-testid="stHeadingWithActionElements"] h4,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6,
[data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stAlert"],
[data-testid="stAlert"] div,
[data-testid="stAlert"] p,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stRadio"] > div,
[data-testid="stCheckbox"] label {{
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
}}

/* ✳️ 3. إصلاح القوائم المنسدلة (Selectbox & Multiselect) لتبدأ من اليمين والسهم في اليسار */
div[data-baseweb="select"],
div[data-baseweb="select"] > div,
div[data-baseweb="select"] [class*="control"],
div[data-baseweb="select"] [class*="ValueContainer"] {{
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Tajawal', sans-serif !important;
}}

div[data-baseweb="select"] div {{
    color: var(--text-color) !important;
    font-weight: 700 !important;
}}

/* شارات الاختيار المتعدد (Tags) تبدأ من اليمين */
span[data-baseweb="tag"] {{
    direction: rtl !important;
    margin-left: 5px !important;
    margin-right: 0px !important;
    font-family: 'Tajawal', sans-serif !important;
    font-weight: 700 !important;
}}

/* القائمة المنبثقة عند فتح القائمة المنسدلة (Popover Menu) */
div[data-baseweb="popover"],
div[data-baseweb="popover"] div,
div[data-baseweb="popover"] ul,
ul[data-baseweb="menu"],
li[role="option"] {{
    direction: rtl !important;
    text-align: right !important;
    justify-content: flex-start !important;
    font-family: 'Tajawal', sans-serif !important;
    font-weight: 700 !important;
}}

/* ✳️ 4. حقول الإدخال النصية والرقمية من اليمين لليسار */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {{
    background-color: var(--secondary-background-color) !important;
    border: 1.5px solid rgba(148, 163, 184, 0.35) !important;
    border-radius: 12px !important;
    min-height: 48px;
    direction: rtl !important;
    text-align: right !important;
}}

div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="textarea"]:focus-within {{
    border-color: {accent_color} !important;
    box-shadow: 0 0 0 2px {primary_color}40 !important;
}}

input, textarea, select {{
    direction: rtl !important;
    text-align: right !important;
    color: var(--text-color) !important;
    -webkit-text-fill-color: var(--text-color) !important;
    caret-color: {accent_color} !important;
    background-color: transparent !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    font-family: 'Tajawal', sans-serif !important;
}}

::placeholder {{
    color: #94A3B8 !important;
    opacity: 0.85 !important;
    -webkit-text-fill-color: #94A3B8 !important;
    text-align: right !important;
}}

/* ✳️ 5. البنر العلوي الرئيسي (يبقى في المنتصف) */
.header-container {{
    background: {header_grad};
    background-image: {t_colors["bg_pattern"]}, {header_grad};
    background-blend-mode: overlay;
    padding: 60px 20px 32px 20px;
    border-radius: 0 0 36px 36px;
    margin: -1rem -5rem 25px -5rem;
    box-shadow: 0 10px 30px -10px rgba(0,0,0, 0.45);
    color: white;
    text-align: center !important;
    position: relative;
    overflow: hidden;
    border-bottom: 2px solid rgba(255,255,255,0.15);
}}

.title-wrapper {{
    display: flex;
    align-items: center;
    justify-content: center !important;
    gap: 15px;
    margin-bottom: 8px;
    position: relative;
    z-index: 2;
}}

.logo-icon {{
    font-size: 3.5rem;
    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    animation: float 4s ease-in-out infinite;
    line-height: 1;
    margin-top: 10px;
}}

.main-title {{
    margin: 0 !important;
    font-size: 2.7rem !important;
    font-weight: 900 !important;
    color: {t_colors["title_color"]} !important;
    line-height: 1.1 !important;
    text-align: center !important;
}}

.sub-title {{
    margin: 0 !important;
    color: {t_colors["sub_color"]} !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    position: relative;
    z-index: 2;
    line-height: 1.5 !important;
    text-align: center !important;
}}

/* ✳️ 6. الأزرار الرئيسية والثانوية */
[data-testid="stFormSubmitButton"] button, [data-testid="baseButton-primary"], div.stButton > button, div.stDownloadButton > button {{
    background: {header_grad} !important;
    background-color: {primary_color} !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    font-weight: 800 !important;
    font-size: 1.03rem !important;
    border-radius: 14px !important;
    padding: 10px 18px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22) !important;
    transition: all 0.2s ease !important;
    width: 100%;
    min-height: 48px;
}}

[data-testid="stFormSubmitButton"] button:hover, [data-testid="baseButton-primary"]:hover, div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background: {t_colors["btn_hover"]} !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.32) !important;
    border-color: rgba(255, 255, 255, 0.45) !important;
}}

div.stButton > button[kind="secondary"],
div.stDownloadButton > button[kind="secondary"] {{
    background: var(--secondary-background-color) !important;
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1.5px solid rgba(148, 163, 184, 0.35) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.06) !important;
}}

div.stButton > button[kind="secondary"]:hover,
div.stDownloadButton > button[kind="secondary"]:hover {{
    border-color: {accent_color} !important;
    background: rgba(59, 130, 246, 0.08) !important;
}}

/* ✳️ 7. تصميم التبويبات: شريط أفقي أنيق على الكمبيوتر + شبكة (2×2) على الجوال */
.stTabs [data-baseweb="tab-list"] {{
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    background-color: transparent !important;
    border: none !important;
    margin-bottom: 14px !important;
    padding: 4px 2px !important;
    direction: rtl !important;
}}

.stTabs [data-baseweb="tab"] {{
    height: 48px !important;
    margin: 0 !important;
    padding: 8px 14px !important;
    background-color: var(--secondary-background-color) !important;
    border-radius: 12px !important;
    border: 1.5px solid rgba(148, 163, 184, 0.3) !important;
    color: var(--text-color) !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    flex: 1 1 auto !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08) !important;
    transition: all 0.2s ease !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    border-color: {accent_color} !important;
    transform: translateY(-1px);
}}

.stTabs [aria-selected="true"] {{
    background: {header_grad} !important;
    color: #FFFFFF !important;
    border: 2px solid #F59E0B !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3) !important;
}}

.stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {{
    color: #FFFFFF !important;
    font-weight: 900 !important;
}}

.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* ✳️ 8. البطاقات الإحصائية وبطاقات السلوك */
.metric-container {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; direction: rtl; }}
.metric-card {{ background-color: var(--secondary-background-color); border: 1.5px solid rgba(148, 163, 184, 0.28); border-radius: 16px; padding: 18px; display: flex; justify-content: space-between; align-items: center; box-shadow: {shadow_val}; }}
.metric-info {{ text-align: right; }}
.metric-title {{ color: #94A3B8; font-size: 13.5px; font-weight: 800; margin-bottom: 4px; }}
.metric-val {{ color: var(--text-color); font-size: 26px; font-weight: 900; line-height: 1.1; }}
.metric-sub {{ color: #64748B; font-size: 12px; font-weight: 700; margin-top: 2px; }}
.metric-icon {{ width: 50px; height: 50px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 24px; }}
.ic-green {{ background-color: rgba(16, 185, 129, 0.15); color: {success_color}; border: 1px solid rgba(16, 185, 129, 0.3); }}
.ic-blue {{ background-color: rgba(59, 130, 246, 0.15); color: {accent_color}; border: 1px solid rgba(59, 130, 246, 0.3); }}
.ic-red {{ background-color: rgba(245, 158, 11, 0.15); color: {warning_color}; border: 1px solid rgba(245, 158, 11, 0.3); }}

.app-card {{ background: var(--secondary-background-color); padding: 20px; border-radius: 16px; box-shadow: {shadow_val}; border: 1.5px solid rgba(148, 163, 184, 0.28); margin-bottom: 15px; }}
.mobile-list-item {{ background: var(--secondary-background-color); border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1.5px solid rgba(148, 163, 184, 0.28); box-shadow: 0 2px 6px rgba(0,0,0,0.08); display: flex; align-items: center; justify-content: space-between; color: var(--text-color); direction: rtl; text-align: right; }}

.student-list-card {{
    background: var(--secondary-background-color);
    border-radius: 14px; padding: 15px 18px; margin-bottom: 8px;
    border: 1.5px solid rgba(148, 163, 184, 0.28);
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    display: block !important; width: 100% !important;
    text-align: right !important; direction: rtl !important; color: var(--text-color);
}}
.student-card-header {{
    display: flex !important; flex-direction: row !important;
    justify-content: space-between !important; align-items: center !important;
    gap: 10px !important; width: 100% !important; direction: rtl !important; margin-bottom: 6px !important;
}}
.student-card-title {{
    text-align: right !important; direction: rtl !important;
    font-weight: 900 !important; font-size: 1.05rem !important;
    line-height: 1.4 !important; flex: 1 !important; unicode-bidi: plaintext !important;
}}
.student-card-date {{
    background: var(--background-color); padding: 4px 10px; border-radius: 8px;
    font-size: 0.82rem; font-weight: 800; white-space: nowrap !important;
    flex-shrink: 0 !important; direction: ltr !important; border: 1px solid rgba(148, 163, 184, 0.2);
}}
.student-card-body {{
    text-align: right !important; direction: rtl !important;
    width: 100% !important; font-size: 0.95rem !important;
    line-height: 1.5 !important; margin: 0 !important; unicode-bidi: plaintext !important;
}}

.action-bar-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 6px; margin-bottom: 8px; direction: rtl; }}
.soft-link-btn {{ display: flex; align-items: center; justify-content: center; gap: 6px; padding: 8px 12px; border-radius: 12px; font-weight: 800; font-size: 0.92rem; text-decoration: none !important; transition: all 0.2s ease; height: 44px; }}
.btn-whatsapp {{ background-color: rgba(16, 185, 129, 0.12) !important; color: #10B981 !important; border: 1.5px solid rgba(16, 185, 129, 0.35) !important; }}
.btn-whatsapp:hover {{ background-color: rgba(16, 185, 129, 0.22) !important; transform: translateY(-1px); }}
.btn-telegram {{ background-color: rgba(14, 165, 233, 0.12) !important; color: #0EA5E9 !important; border: 1.5px solid rgba(14, 165, 233, 0.35) !important; }}
.btn-telegram:hover {{ background-color: rgba(14, 165, 233, 0.22) !important; transform: translateY(-1px); }}

div[data-testid="stElementContainer"]:has(.btn-edit-marker),
div[data-testid="stElementContainer"]:has(.btn-del-marker),
div.element-container:has(.btn-edit-marker),
div.element-container:has(.btn-del-marker) {{ display: none !important; }}

div[data-testid="stHorizontalBlock"]:has(.btn-edit-marker) {{
    display: grid !important; grid-template-columns: repeat(2, 1fr) !important;
    gap: 8px !important; direction: rtl !important; margin-top: 0px !important; margin-bottom: 16px !important;
}}
div[data-testid="stHorizontalBlock"]:has(.btn-edit-marker) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.btn-edit-marker) > div[data-testid="column"] {{
    width: 100% !important; min-width: 0 !important; flex: unset !important;
}}
div[data-testid="stColumn"]:has(.btn-edit-marker) div.stButton > button,
div[data-testid="column"]:has(.btn-edit-marker) div.stButton > button {{
    background: rgba(99, 102, 241, 0.12) !important; background-color: rgba(99, 102, 241, 0.12) !important;
    color: #6366F1 !important; border: 1.5px solid rgba(99, 102, 241, 0.35) !important;
    border-radius: 12px !important; height: 44px !important; min-height: 44px !important;
    padding: 8px 12px !important; font-size: 0.92rem !important; font-weight: 800 !important; box-shadow: none !important;
}}
div[data-testid="stColumn"]:has(.btn-edit-marker) div.stButton > button:hover,
div[data-testid="column"]:has(.btn-edit-marker) div.stButton > button:hover {{ background: rgba(99, 102, 241, 0.22) !important; transform: translateY(-1px); }}

div[data-testid="stColumn"]:has(.btn-del-marker) div.stButton > button,
div[data-testid="column"]:has(.btn-del-marker) div.stButton > button {{
    background: rgba(239, 68, 68, 0.12) !important; background-color: rgba(239, 68, 68, 0.12) !important;
    color: #EF4444 !important; border: 1.5px solid rgba(239, 68, 68, 0.35) !important;
    border-radius: 12px !important; height: 44px !important; min-height: 44px !important;
    padding: 8px 12px !important; font-size: 0.92rem !important; font-weight: 800 !important; box-shadow: none !important;
}}
div[data-testid="stColumn"]:has(.btn-del-marker) div.stButton > button:hover,
div[data-testid="column"]:has(.btn-del-marker) div.stButton > button:hover {{ background: rgba(239, 68, 68, 0.22) !important; transform: translateY(-1px); }}

.medal-flex {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; direction: rtl; }}
.m-card {{ background: var(--secondary-background-color); padding: 15px 5px; border-radius: 16px; text-align: center !important; border: 1.5px solid rgba(148, 163, 184, 0.28); box-shadow: {shadow_val}; color: var(--text-color); }}
.m-active {{ border: 2px solid {warning_color} !important; background: rgba(245, 158, 11, 0.15) !important; }}

.points-banner {{ background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%); color: white; padding: 25px; border-radius: 18px; text-align: center !important; margin-bottom: 20px; box-shadow: 0 6px 15px rgba(245, 158, 11, 0.35); border: 1px solid rgba(255,255,255,0.2); }}
.welcome-card {{ background: {header_grad}; color: white; padding: 20px; border-radius: 18px; margin-bottom: 15px; box-shadow: 0 6px 15px rgba(0,0,0, 0.3); border: 1px solid rgba(255,255,255,0.15); }}

[data-testid="stDataFrame"] {{ direction: rtl !important; }}

@keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
@keyframes pulse-red {{ 0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }} 70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }} }}
.urgent-box {{ background-color: rgba(239, 68, 68, 0.12); border: 2px solid {danger_color}; color: {danger_color}; padding: 15px; border-radius: 14px; text-align: center !important; animation: pulse-red 2s infinite; font-weight: bold; margin-bottom: 20px; }}

/* ✳️ 9. تحويل التبويبات تلقائياً إلى شبكة (2×2) على الجوال فقط */
@media (max-width: 768px) {{
    .header-container {{ padding: 55px 15px 25px 15px; margin: -1rem -1rem 20px -1rem; border-radius: 0 0 28px 28px; }}
    .main-title {{ font-size: 1.85rem !important; }}
    .logo-icon {{ font-size: 2.3rem; }}
    .sub-title {{ font-size: 1.05rem !important; }}
    .metric-container {{ grid-template-columns: repeat(2, 1fr); }}
    .metric-container > .metric-card:last-child:nth-child(odd) {{ grid-column: span 2; }}
    .stTabs [data-baseweb="tab-list"] {{
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }}
    .stTabs [data-baseweb="tab-list"] > button:last-child:nth-child(odd) {{
        grid-column: span 2 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        width: 100% !important;
        font-size: 0.9rem !important;
        height: 50px !important;
        padding: 6px 8px !important;
        white-space: normal !important;
    }}
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
  t1, t2, t3 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم", "🏫 بوابة الإدارة (مشاهد)"])

  with t1:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("st_login"):
      st.markdown("<h4 style='text-align:center; margin-bottom:15px;'>تسجيل دخول الطالب</h4>", unsafe_allow_html=True)
      sid = st.text_input("رقم الهوية / الرقم الأكاديمي", placeholder="أدخل الرقم هنا...").strip()
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button("🚀 دخول للمنصة", type="primary", use_container_width=True):
        arabic_to_english = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        sid = sid.translate(arabic_to_english)
        df = fetch_safe("students")
        if not df.empty:
          df["clean_id"] = df.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
          if sid.split(".")[0] in df["clean_id"].values:
            st.session_state.username = sid.split(".")[0]
            st.session_state.role = "student"
            st.rerun()
          else:
            st.error("⚠️ الرقم غير مسجل في النظام")

  with t2:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("tr_login"):
      st.markdown("<h4 style='text-align:center; margin-bottom:15px;'>تسجيل دخول المعلم</h4>", unsafe_allow_html=True)
      u = st.text_input("اسم المستخدم", placeholder="User")
      p = st.text_input("كلمة المرور", type="password", placeholder="******")
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button("🛠️ دخول لوحة التحكم", type="primary", use_container_width=True):
        df = fetch_safe("users")
        if not df.empty and u in df["username"].values:
          ud = df[df["username"] == u].iloc[0]
          if hashlib.sha256(p.encode()).hexdigest() == ud["password_hash"]:
            if ud.get("role", "teacher") in ["teacher", ""]:
              try:
                ws_u = get_gspread_client().worksheet("users")
                c_u = ws_u.find(u)
                if c_u:
                  headers_u = ws_u.row_values(1)
                  if "last_login" not in headers_u:
                    ws_u.update_cell(1, len(headers_u) + 1, "last_login")
                    headers_u.append("last_login")
                  idx_u = headers_u.index("last_login") + 1
                  now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %I:%M %p")
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
      st.markdown("<h4 style='text-align:center; margin-bottom:15px;'>دخول الإدارة (قراءة واستخراج تقارير)</h4>", unsafe_allow_html=True)
      u_admin = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم للإدارة...")
      p_admin = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور...")
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button("👁️ دخول الإشراف", type="primary", use_container_width=True):
        df_u = fetch_safe("users")
        if not df_u.empty and u_admin in df_u["username"].values:
          ud = df_u[df_u["username"] == u_admin].iloc[0]
          if hashlib.sha256(p_admin.encode()).hexdigest() == ud["password_hash"]:
            if ud.get("role", "") == "viewer":
              try:
                ws_u = get_gspread_client().worksheet("users")
                c_u = ws_u.find(u_admin)
                if c_u:
                  headers_u = ws_u.row_values(1)
                  if "last_login" not in headers_u:
                    ws_u.update_cell(1, len(headers_u) + 1, "last_login")
                    headers_u.append("last_login")
                  idx_u = headers_u.index("last_login") + 1
                  now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %I:%M %p")
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
    tab_students, tab_eval, tab_honor, tab_reports, tab_alerts, tab_settings, tab_logout = st.tabs([
        "👥 إدارة الطلاب",
        "📊 الرصد والتقييم",
        "🏆 الشرف والشهادات",
        "🖨️ مركز التقارير",
        "📢 التنبيهات",
        "⚙️ الإعدادات والبيانات",
        "🛑 خروج",
    ])
  else:
    tab_students, tab_eval, tab_honor, tab_reports, tab_alerts, tab_logout = st.tabs([
        "👥 إدارة الطلاب",
        "📊 الرصد والتقييم",
        "🏆 الشرف والشهادات",
        "🖨️ مركز التقارير",
        "📢 التنبيهات",
        "🛑 خروج",
    ])
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
      df_st["clean_id"] = df_st.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      df_st["النقاط"] = pd.to_numeric(df_st["النقاط"], errors="coerce").fillna(0)
    else:
      df_st["clean_id"] = []
      df_st["النقاط"] = []

    total_students = len(df_st)
    total_classes = len(df_st["class"].dropna().unique()) if "class" in df_st.columns and not df_st.empty else 0
    avg_points = round(df_st["النقاط"].mean(), 1) if "النقاط" in df_st.columns and not df_st.empty else 0

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

    action_tabs = st.tabs([
        "🔍 عرض وبحث الطلاب",
        "➕ إضافة طالب جديد",
        "✏️ تعديل بيانات طالب",
        "🗑️ حذف طالب",
    ])

    # 1. عرض وبحث الطلاب (يدعم اختيار عدة فصول معاً)
    with action_tabs[0]:
      if not df_st.empty:
        if "current_page" not in st.session_state:
          st.session_state.current_page = 1

        col_search, col_cls_f, col_rows = st.columns([2, 2, 0.8])
        with col_search:
          sq = st.text_input("🔍 بحث:", placeholder="ابحث بالاسم أو الرقم الأكاديمي...", label_visibility="collapsed")
        with col_cls_f:
          avail_st_classes = list(df_st["class"].dropna().unique())
          cls_filter_list = st.multiselect(
              "🏫 الفصول:",
              options=["كل الفصول"] + avail_st_classes,
              default=["كل الفصول"],
              placeholder="اختر فصلاً أو أكثر...",
              label_visibility="collapsed",
              key="st_view_multi_cls",
          )
        with col_rows:
          rows_per_page = st.selectbox("الصفوف:", [10, 20, 50, 100], index=0, label_visibility="collapsed")

        display_df = df_st.copy()
        if cls_filter_list and "كل الفصول" not in cls_filter_list:
          display_df = display_df[display_df["class"].isin(cls_filter_list)]
        elif not cls_filter_list:
          display_df = display_df.iloc[0:0]

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

        if sq and not display_df.empty:
          norm_sq = normalize_arabic(sq)
          mask = display_df["الرقم الأكاديمي"].astype(str).str.contains(norm_sq) | display_df["الاسم"].astype(str).apply(normalize_arabic).str.contains(norm_sq)
          display_df = display_df[mask]
          st.session_state.current_page = 1

        total_rows = len(display_df)
        total_pages = max(1, math.ceil(total_rows / rows_per_page))
        if st.session_state.current_page > total_pages:
          st.session_state.current_page = total_pages

        start_idx = (st.session_state.current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page

        st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)

        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
          if st.button("▶ التالي", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
            st.session_state.current_page += 1
            st.rerun()
        with pc2:
          st.markdown(
              f"<div style='text-align: center; font-weight: bold; padding-top: 8px; color: #94A3B8;'>صفحة {st.session_state.current_page} من {total_pages}<br><small>(إجمالي النتائج: {total_rows} طالب)</small></div>",
              unsafe_allow_html=True,
          )
        with pc3:
          if st.button("السابق ◀", disabled=(st.session_state.current_page <= 1), use_container_width=True):
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
          f_id = c2.text_input("الرقم الأكاديمي / الهوية", placeholder="أدخل الرقم الأكاديمي")

          c3, c4, c5 = st.columns(3)
          f_class = c3.selectbox("الصف", st.session_state.class_options)
          auto_stage = st.session_state.get("class_stage_map", {}).get(
              f_class, "متوسط" if "متوسط" in str(f_class) else "ابتدائي"
          )
          stg_opts = list(st.session_state.stage_options)
          if auto_stage not in stg_opts:
            stg_opts.insert(0, auto_stage)
          f_stage = c4.selectbox("المرحلة (تتحدد تلقائياً)", stg_opts, index=stg_opts.index(auto_stage))
          f_year = c5.text_input("العام الدراسي", st.session_state.current_year)

          st.markdown("#### 📞 معلومات التواصل ونمط التعلم")
          c6, c7, c8 = st.columns(3)
          f_phone = c6.text_input("رقم الجوال", placeholder="05xxxxxxxx")
          f_mail = c7.text_input("البريد الإلكتروني", placeholder="example@mail.com")
          f_style = c8.selectbox("نمط التعلم (اختياري)", ["", "بصري 👀", "سمعي 👂", "حركي ✋", "متعدد الأنماط 🌟"])

          if st.form_submit_button("✅ حفظ الطالب في المنصة", type="primary", use_container_width=True):
            if f_id and f_name:
              clean_new_id = f_id.strip().split(".")[0]
              if not df_st.empty and clean_new_id in df_st["clean_id"].values:
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
                  st.session_state.toast_msg = f"✅ تم إضافة الطالب '{f_name}' بنجاح!"
                  if "db_loaded" in st.session_state:
                    del st.session_state["db_loaded"]
                  fetch_safe.clear()
                  st.rerun()
            else:
              st.warning("الرجاء إكمال البيانات الأساسية (الاسم والرقم)!")
      else:
        st.info("💡 وضع القراءة فقط: ليس لديك صلاحية لإضافة طلاب.")

    # 3. تعديل بيانات طالب
    with action_tabs[2]:
      if st.session_state.role == "teacher":
        if not df_st.empty:
          raw_df_st = st.session_state.df_students
          edit_options = raw_df_st.index.tolist()
          selected_idx = st.selectbox(
              "✏️ اختر الطالب المطلوب تعديل بياناته (يمكنك البحث بالكتابة):",
              edit_options,
              format_func=lambda x: f"{raw_df_st.loc[x, 'name']} - ({raw_df_st.loc[x, 'class']}) - الرقم: {raw_df_st.loc[x, 'id']}",
              key="edit_select",
          )

          with st.form("edit_form_single"):
            st.markdown(f"**📝 تعديل بيانات: <span style='color:{accent_color};'>{raw_df_st.loc[selected_idx, 'name']}</span>**", unsafe_allow_html=True)
            cols = st.columns(3)
            new_vals = []

            valid_columns = [
                c for c in raw_df_st.columns
                if c not in ["clean_id"] and not str(c).startswith("Unnamed") and str(c).strip() != ""
            ]

            for col_idx, col_name in enumerate(valid_columns):
              with cols[col_idx % 3]:
                current_val = "" if pd.isna(raw_df_st.loc[selected_idx, col_name]) else str(raw_df_st.loc[selected_idx, col_name]).strip()

                if col_name == "class":
                  c_opts = list(st.session_state.get("class_options", []))
                  if current_val not in c_opts and current_val != "":
                    c_opts.insert(0, current_val)
                  c_idx = c_opts.index(current_val) if current_val in c_opts else 0
                  val = st.selectbox(col_name, c_opts, index=c_idx, key=f"inp_edit_{selected_idx}_{col_idx}")
                elif col_name == "sem":
                  s_opts = list(st.session_state.get("stage_options", []))
                  if current_val not in s_opts and current_val != "":
                    s_opts.insert(0, current_val)
                  s_idx = s_opts.index(current_val) if current_val in s_opts else 0
                  val = st.selectbox(col_name, s_opts, index=s_idx, key=f"inp_edit_{selected_idx}_{col_idx}")
                elif col_name == "نمط التعلم":
                  ls_opts = ["", "بصري 👀", "سمعي 👂", "حركي ✋", "متعدد الأنماط 🌟"]
                  if current_val not in ls_opts and current_val != "":
                    ls_opts.insert(0, current_val)
                  ls_idx = ls_opts.index(current_val) if current_val in ls_opts else 0
                  val = st.selectbox(col_name, ls_opts, index=ls_idx, key=f"inp_edit_{selected_idx}_{col_idx}")
                else:
                  val = st.text_input(col_name, current_val, key=f"inp_edit_{selected_idx}_{col_idx}")
                new_vals.append(str(val))

            if st.form_submit_button("💾 حفظ التعديلات", type="primary", use_container_width=True):
              row_index = int(selected_idx) + 2
              try:
                end_col_a1 = rowcol_to_a1(row_index, len(new_vals))
                get_gspread_client().worksheet("students").update(range_name=f"A{row_index}:{end_col_a1}", values=[new_vals])
                st.session_state.toast_msg = f"🔄 تم تحديث بيانات '{new_vals[1] if len(new_vals) > 1 else ''}' بنجاح!"
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                fetch_safe.clear()
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
              format_func=lambda x: f"{df_st.loc[x, 'name']} - (الرقم: {df_st.loc[x, 'id']})",
              key="del_select",
          )
          student_to_delete = df_st.loc[del_idx, "name"]
          st.error(f"⚠️ تحذير: سيتم حذف بيانات ({student_to_delete}) نهائياً من قاعدة البيانات.")
          if st.button(f"🚨 نعم، تأكيد حذف {student_to_delete}", type="primary", use_container_width=True):
            get_gspread_client().worksheet("students").delete_rows(int(del_idx) + 2)
            st.session_state.toast_msg = f"🗑️ تم حذف '{student_to_delete}' بشكل نهائي!"
            if "db_loaded" in st.session_state:
              del st.session_state["db_loaded"]
            fetch_safe.clear()
            st.rerun()
        else:
          st.info("لا توجد بيانات للطلاب بعد.")
      else:
        st.info("💡 وضع القراءة فقط: ليس لديك صلاحية لحذف الطلاب.")

# ==========================================
# 📊 6. التبويب الثاني: الرصد والتقييم (مطور وسريع الاستجابة)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_eval:
    st.subheader("📊 الرصد والتقييم الأكاديمي والسلوكي")

    BEHAVIOR_OPTIONS = [
        "🌟 متميز (+10)",
        "🎯 أداء المهمة (+15)",
        "📂 ملف الإنجاز (+10)",
        "✅ إيجابي (+5)",
        "📝 حل الواجب (+5)",
        "⚠️ تنبيه (0)",
        "🪑 غائب (0)",
        "🖊️ نقص أدوات الكتابة (-2)",
        "📚 نقص كتاب (-3)",
        "🏃 تأخر عن الحصة (-3)",
        "💤 النوم داخل الفصل (-5)",
        "✍️ نقص واجب (-5)",
        "⏳ عدم أداء المهمة (-10)",
        "❌ عدم إحضار ملف الإنجاز (-10)",
        "🚫 سلبي (-10)",
    ]

    eval_tabs = st.tabs([
        "🎭 السلوك اليومي",
        "👥 السلوك الجماعي",
        "📝 رصد الدرجات",
        "🔍 مدقق النواقص",
    ])

    # ---------------------------------------------------------
    # 1. السلوك اليومي (فردي سريع + أزرار تعديل وحذف وواتساب وتليجرام هادئة)
    # ---------------------------------------------------------
    with eval_tabs[0]:
      df_ev = st.session_state.df_students
      if not df_ev.empty:
        col_f_cls, col_f_st = st.columns([1, 2.5])
        cls_list_ev = ["الكل"] + list(df_ev["class"].dropna().unique())
        sel_cls_ev = col_f_cls.selectbox("🏫 تصفية بالصف:", cls_list_ev, key="eval_cls_filter_2")

        df_ev_filtered = df_ev if sel_cls_ev == "الكل" else df_ev[df_ev["class"] == sel_cls_ev]
        st_dict = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_ev_filtered.iterrows()}
        sel = col_f_st.selectbox("🎯 اختر الطالب من القائمة:", [""] + list(st_dict.keys()), key="single_eval_sel_2")

        if sel:
          sid = str(st_dict[sel]).strip().split(".")[0]
          student_idx = df_ev[df_ev.iloc[:, 0].astype(str).str.split(".").str[0] == sid].index[0]
          s_inf = df_ev.loc[student_idx]

          s_nm = s_inf["name"]
          clp = clean_phone_number(s_inf.get("الجوال", ""))
          current_points = int(pd.to_numeric(s_inf.get("النقاط", 0), errors="coerce") or 0)

          with st.container(border=True):
            st.markdown(
                f"##### 🎭 السلوك والملاحظات اليومية لـ: <span style='color:{accent_color};'>{s_nm}</span> (الرصيد: <span style='color:{warning_color}; font-weight:900;'>{current_points}</span> نقطة)",
                unsafe_allow_html=True,
            )
            if st.session_state.role == "teacher":
              with st.form("beh_add_opt2", clear_on_submit=True):
                b_col1, b_col2 = st.columns([1.3, 2])
                bt = b_col1.selectbox("نوع السلوك", BEHAVIOR_OPTIONS)
                bn = b_col2.text_input("تفاصيل الملاحظة (اختياري)", placeholder="اكتب ملاحظة سريعة...")

                if st.form_submit_button("💾 تسجيل السلوك فوراً", type="primary", use_container_width=True):
                  today_str = str(datetime.date.today())
                  new_b_row = {
                      "student_id": sid,
                      "date": today_str,
                      "type": bt,
                      "note": bn,
                  }
                  if safe_append_row("behavior", new_b_row):
                    match = re.search(r"\(([\+\-]?\d+)\)", bt)
                    chg = int(match.group(1)) if match else 0
                    if chg != 0:
                      try:
                        ws = get_gspread_client().worksheet("students")
                        c = ws.find(sid)
                        if c:
                          h = ws.row_values(1)
                          if "النقاط" in h:
                            idx = h.index("النقاط") + 1
                            new_val = current_points + chg
                            ws.update_cell(c.row, idx, str(new_val))
                            st.session_state.df_students.loc[student_idx, "النقاط"] = str(new_val)
                      except Exception as e:
                        st.error(f"خطأ: {e}")

                    fetch_safe.clear()
                    st.session_state.df_behavior = fetch_safe("behavior")
                    st.toast(f"✅ تم تسجيل الملاحظة للطالب {s_nm} فوراً!", icon="🎉")
                    st.rerun()
            else:
              st.info("💡 وضع القراءة فقط.")

          # --- سجل السلوك السفلي للطالب ---
          st.markdown("#### 📜 سجل السلوك الأخير للطالب")
          df_b = st.session_state.df_behavior.copy()
          if not df_b.empty:
            cid = "student_id" if "student_id" in df_b.columns else df_b.columns[0]
            df_b["clean_cid"] = df_b[cid].astype(str).str.strip().str.split(".").str[0]
            my_b = df_b[df_b["clean_cid"] == sid].copy()

            if not my_b.empty:
              my_b = my_b.iloc[::-1]
              my_b["date_parsed"] = pd.to_datetime(my_b["date"], errors="coerce")
              my_b = my_b.sort_values(by="date_parsed", ascending=False, kind="mergesort")

              def delete_behavior_opt2(global_idx, b_type):
                try:
                  get_gspread_client().worksheet("behavior").delete_rows(int(global_idx) + 2)
                  match = re.search(r"\(([\+\-]?\d+)\)", str(b_type))
                  chg = int(match.group(1)) if match else 0
                  if chg != 0:
                    ws_st = get_gspread_client().worksheet("students")
                    c = ws_st.find(sid)
                    if c:
                      h = ws_st.row_values(1)
                      if "النقاط" in h:
                        idx = h.index("النقاط") + 1
                        curr = int(pd.to_numeric(ws_st.cell(c.row, idx).value, errors="coerce") or 0)
                        new_pts_v = curr - chg
                        ws_st.update_cell(c.row, idx, str(new_pts_v))
                        st.session_state.df_students.loc[student_idx, "النقاط"] = str(new_pts_v)
                  fetch_safe.clear()
                  st.session_state.df_behavior = fetch_safe("behavior")
                except Exception:
                  pass

              if "edit_beh_idx_2" not in st.session_state:
                st.session_state.edit_beh_idx_2 = None

              for global_idx, r in my_b.iterrows():
                with st.container():
                  if st.session_state.edit_beh_idx_2 == global_idx:
                    st.markdown(
                        f"<div style='background: var(--secondary-background-color); padding: 15px; border-radius: 12px; border: 2px dashed {accent_color}; margin-bottom: 10px;'>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("###### ✏️ تعديل الملاحظة السلوكية")

                    current_type = str(r.get("type"))
                    edit_opts = list(BEHAVIOR_OPTIONS)
                    if current_type not in edit_opts and current_type:
                      edit_opts.insert(0, current_type)
                    type_idx = edit_opts.index(current_type) if current_type in edit_opts else 0

                    new_type = st.selectbox("نوع السلوك", edit_opts, index=type_idx, key=f"edit_type_opt2_{global_idx}", label_visibility="collapsed")
                    new_note = st.text_input("التفاصيل", value=str(r.get("note", "")), key=f"edit_note_opt2_{global_idx}", label_visibility="collapsed")

                    c_save, c_cancel = st.columns(2)
                    if c_save.button("💾 حفظ التعديل", type="primary", key=f"save_opt2_{global_idx}", use_container_width=True):
                      try:
                        with st.spinner("جاري التحديث..."):
                          ws_beh = get_gspread_client().worksheet("behavior")
                          headers_beh = ws_beh.row_values(1)
                          idx_type = headers_beh.index("type") + 1 if "type" in headers_beh else 3
                          idx_note = headers_beh.index("note") + 1 if "note" in headers_beh else 4

                          ws_beh.update_cell(global_idx + 2, idx_type, new_type)
                          ws_beh.update_cell(global_idx + 2, idx_note, new_note)

                          old_match = re.search(r"\(([\+\-]?\d+)\)", current_type)
                          old_pts = int(old_match.group(1)) if old_match else 0

                          new_match = re.search(r"\(([\+\-]?\d+)\)", new_type)
                          new_pts = int(new_match.group(1)) if new_match else 0

                          diff = new_pts - old_pts
                          if diff != 0:
                            ws_st = get_gspread_client().worksheet("students")
                            c = ws_st.find(sid)
                            if c:
                              h = ws_st.row_values(1)
                              if "النقاط" in h:
                                idx_pts = h.index("النقاط") + 1
                                curr = int(pd.to_numeric(ws_st.cell(c.row, idx_pts).value, errors="coerce") or 0)
                                ws_st.update_cell(c.row, idx_pts, str(curr + diff))
                                st.session_state.df_students.loc[student_idx, "النقاط"] = str(curr + diff)

                          st.session_state.df_behavior.loc[global_idx, "type"] = new_type
                          st.session_state.df_behavior.loc[global_idx, "note"] = new_note
                          st.session_state.edit_beh_idx_2 = None
                          fetch_safe.clear()
                          st.toast("✅ تم التعديل بنجاح!", icon="✏️")
                          st.rerun()
                      except Exception as e:
                        st.error(f"خطأ في التعديل: {e}")

                    if c_cancel.button("❌ إلغاء", key=f"cancel_opt2_{global_idx}", type="secondary", use_container_width=True):
                      st.session_state.edit_beh_idx_2 = None
                      st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                  else:
                    b_str = str(r.get("type", ""))
                    if "-" in b_str or "سلبي" in b_str:
                      color = danger_color
                    elif "(0)" in b_str or "غائب" in b_str or "تنبيه" in b_str:
                      color = warning_color
                    else:
                      color = success_color

                    note_txt = str(r.get("note", "")).strip()
                    note_html = f"<div class='student-card-body' style='color:#94A3B8; font-weight:700;'>📝 {note_txt}</div>" if note_txt else ""

                    st.markdown(
                        f"""
                        <div class="student-list-card" style="border-right: 5px solid {color}; margin-bottom: 6px;">
                            <div class="student-card-header">
                                <div class="student-card-title" style="color: {color};">{b_str}</div>
                                <div class="student-card-date" style="color: #94A3B8;">📅 {r.get('date')}</div>
                            </div>
                            {note_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    lnk = get_professional_msg(s_nm, r.get("type"), r.get("note"), r.get("date"))
                    wa_url = f"https://api.whatsapp.com/send?phone={clp}&text={lnk}"
                    tg_url = f"https://t.me/share/url?url=https://zi-edu.streamlit.app&text={lnk}"

                    st.markdown(
                        f"""
                        <div class="action-bar-grid">
                            <a href="{wa_url}" target="_blank" class="soft-link-btn btn-whatsapp">💬 واتساب</a>
                            <a href="{tg_url}" target="_blank" class="soft-link-btn btn-telegram">✈️ تليجرام</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.session_state.role == "teacher":
                      c_ed, c_dl = st.columns(2)
                      with c_ed:
                        st.markdown('<span class="btn-edit-marker"></span>', unsafe_allow_html=True)
                        if st.button("✏️ تعديل", key=f"ed_beh_opt2_{global_idx}", type="secondary", use_container_width=True):
                          st.session_state.edit_beh_idx_2 = global_idx
                          st.rerun()
                      with c_dl:
                        st.markdown('<span class="btn-del-marker"></span>', unsafe_allow_html=True)
                        st.button(
                            "🗑️ حذف",
                            key=f"dl_beh_opt2_{global_idx}",
                            type="secondary",
                            on_click=delete_behavior_opt2,
                            args=(global_idx, r.get("type")),
                            use_container_width=True,
                        )
            else:
              st.success("✨ سجل الطالب نظيف ولا توجد ملاحظات مسجلة.")
      else:
        st.info("لا توجد بيانات طلاب.")

    # ---------------------------------------------------------
    # 2. السلوك الجماعي (الرصد السريع للفصل)
    # ---------------------------------------------------------
    with eval_tabs[1]:
      if st.session_state.role == "teacher":
        st.markdown("#### 👥 رصد السلوك الجماعي السريع للفصل")
        st.info("💡 اختر الصف، وحدد السلوك أو الغياب للطلاب المعنيين فقط، ثم اضغط حفظ بالأسفل لترصد للجميع دفعة واحدة.")

        bulk_class = st.selectbox("🎯 اختر الصف للسلوك الجماعي:", st.session_state.class_options, key="bulk_class_sel")
        df_st_bulk = st.session_state.df_students.copy()

        if not df_st_bulk.empty:
          df_st_bulk["clean_class"] = df_st_bulk.iloc[:, 2].astype(str).str.strip()
          class_students = df_st_bulk[df_st_bulk["clean_class"] == bulk_class.strip()]

          if not class_students.empty:
            class_students = class_students.sort_values("name")

            with st.form("bulk_behavior_form", clear_on_submit=True):
              beh_options = ["--- بدون ملاحظة ---"] + BEHAVIOR_OPTIONS
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
                c1.markdown(f"<div style='padding-top:12px; font-weight:700;'>{sname_b}</div>", unsafe_allow_html=True)
                b_type = c2.selectbox("السلوك", beh_options, key=f"b_type_{sid_b}", label_visibility="collapsed")
                b_note = c3.text_input("تفاصيل", key=f"b_note_{sid_b}", label_visibility="collapsed", placeholder="أضف تفاصيل...")

                bulk_data[sid_b] = {"type": b_type, "note": b_note}
                st.markdown("<div style='border-bottom: 1px dashed rgba(148,163,184,0.25); margin: 4px 0;'></div>", unsafe_allow_html=True)

              if st.form_submit_button("🚀 حفظ السلوك الجماعي للفصل", type="primary", use_container_width=True):
                behavior_rows_to_add = []
                point_updates = {}

                for sid_key, data in bulk_data.items():
                  if data["type"] != "--- بدون ملاحظة ---":
                    behavior_rows_to_add.append([sid_key, str(datetime.date.today()), data["type"], data["note"]])
                    match = re.search(r"\(([\+\-]?\d+)\)", data["type"])
                    if match:
                      pts_val = int(match.group(1))
                      if pts_val != 0:
                        point_updates[sid_key] = pts_val

                if behavior_rows_to_add:
                  try:
                    with st.spinner("جاري حفظ السلوك الجماعي وتحديث النقاط..."):
                      get_gspread_client().worksheet("behavior").append_rows(behavior_rows_to_add)
                      if point_updates:
                        ws_st = get_gspread_client().worksheet("students")
                        all_st = ws_st.get_all_records()
                        headers = ws_st.row_values(1)

                        if "النقاط" in headers:
                          p_idx = headers.index("النقاط") + 1
                          cells_to_update = []
                          for i, r in enumerate(all_st):
                            st_id = str(r.get("id", "")).split(".")[0].strip()
                            if st_id in point_updates:
                              cur_p = int(pd.to_numeric(r.get("النقاط", 0), errors="coerce") or 0)
                              new_p = cur_p + point_updates[st_id]
                              cells_to_update.append(Cell(row=i + 2, col=p_idx, value=str(new_p)))
                          if cells_to_update:
                            ws_st.update_cells(cells_to_update)

                      st.success(f"✅ تمت المهمة بنجاح! تم رصد ({len(behavior_rows_to_add)}) ملاحظة.")
                      if "db_loaded" in st.session_state:
                        del st.session_state["db_loaded"]
                      fetch_safe.clear()
                      st.rerun()
                  except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
                else:
                  st.warning("⚠️ لم تقم باختيار أي سلوك لأي طالب ليتم حفظه.")
          else:
            st.info("لا يوجد طلاب مسجلين في هذا الصف.")
      else:
        st.info("💡 وضع القراءة فقط.")

    # ---------------------------------------------------------
    # 3. رصد الدرجات (رصد فردي مع المجموع + قائمة سفلية محمية بنموذج للرصد الجماعي)
    # ---------------------------------------------------------
    with eval_tabs[2]:
      cp = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()
      max_t_val = st.session_state.get("max_tasks", 60)
      max_q_val = st.session_state.get("max_quiz", 40)
      max_total_val = max_t_val + max_q_val

      st.markdown(f"#### 📝 رصد وتعديل الدرجات الأكاديمية ({cp})")
      df_ev_g = st.session_state.df_students.copy()

      if not df_ev_g.empty:
        df_ev_g["clean_id"] = df_ev_g.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()

        col_g_cls, col_g_st = st.columns([1, 2.5])
        cls_list_g = ["الكل"] + list(df_ev_g["class"].dropna().unique())
        sel_cls_g = col_g_cls.selectbox("🏫 تصفية بالصف:", cls_list_g, key="grades_cls_filter")

        df_ev_g_filtered = df_ev_g if sel_cls_g == "الكل" else df_ev_g[df_ev_g["class"] == sel_cls_g]
        st_dict_g = {f"{r.iloc[1]} ({r.iloc[0]})": r["clean_id"] for _, r in df_ev_g_filtered.iterrows()}
        sel_g_st = col_g_st.selectbox("🎯 اختر الطالب لرصد أو تعديل درجاته فردياً:", [""] + list(st_dict_g.keys()), key="grades_st_sel")

        df_g = st.session_state.df_grades.copy()
        if not df_g.empty:
          df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
          if "period" not in df_g.columns:
            df_g["period"] = "الفصل الأول - فترة أولى"
          df_g["period"] = df_g["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()

        if sel_g_st:
          sid_g = st_dict_g[sel_g_st]
          s_inf_g = df_ev_g[df_ev_g["clean_id"] == sid_g].iloc[0]
          s_nm_g = s_inf_g["name"]

          cur_p1, cur_p2 = 0, 0
          if not df_g.empty:
            gr_match = df_g[(df_g["clean_id"] == sid_g) & (df_g["period"] == cp)]
            if not gr_match.empty:
              cur_p1 = int(pd.to_numeric(gr_match.iloc[-1]["p1"], errors="coerce") or 0)
              cur_p2 = int(pd.to_numeric(gr_match.iloc[-1]["p2"], errors="coerce") or 0)

          cur_total = cur_p1 + cur_p2
          pct_val = round((cur_total / max_total_val) * 100, 1) if max_total_val > 0 else 0
          tot_color = success_color if pct_val >= 90 else accent_color if pct_val >= 60 else danger_color

          with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:15px; padding-bottom:12px; border-bottom:1px dashed rgba(148,163,184,0.3);">
                    <div>
                        <span style="font-size:1.1rem; font-weight:900; color:var(--text-color);">👤 الطالب: <span style="color:{accent_color};">{s_nm_g}</span></span>
                        <span style="color:#94A3B8; font-size:0.9rem; margin-right:10px;">({s_inf_g.get('class', '')})</span>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <div style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.35); padding:6px 14px; border-radius:10px; font-weight:800; font-size:0.9rem;">
                            مشاركة: <b>{cur_p1}</b>/{max_t_val} | اختبار: <b>{cur_p2}</b>/{max_q_val}
                        </div>
                        <div style="background:{tot_color}20; border:1.5px solid {tot_color}; padding:6px 16px; border-radius:10px; color:{tot_color}; font-weight:900; font-size:1.05rem;">
                            🏆 المجموع: {cur_total} / {max_total_val} ({pct_val}%)
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.role == "teacher":
              with st.form("gr_upd_opt2", clear_on_submit=False):
                g_col1, g_col2 = st.columns(2)
                v1 = g_col1.number_input(f"📝 درجة المشاركة والمهام (من {max_t_val})", 0, max_t_val, cur_p1)
                v2 = g_col2.number_input(f"✍️ درجة الاختبارات القصيرة (من {max_q_val})", 0, max_q_val, cur_p2)

                if st.form_submit_button("💾 حفظ درجات الطالب وتحديث المجموع", type="primary", use_container_width=True):
                  tot = v1 + v2
                  today_s = str(datetime.date.today())
                  ws_g = get_gspread_client().worksheet("grades")

                  all_g_vals = ws_g.get_all_values()
                  headers = all_g_vals[0] if all_g_vals else ["student_id", "p1", "p2", "perf", "date", "period"]
                  if "period" not in headers:
                    ws_g.update_cell(1, len(headers) + 1, "period")
                    headers.append("period")

                  p_col_idx = headers.index("period")
                  row_to_update = None

                  for r_i, r_val in enumerate(all_g_vals[1:], start=2):
                    r_id = str(r_val[0]).strip().split(".")[0] if len(r_val) > 0 else ""
                    r_per = str(r_val[p_col_idx]).strip() if len(r_val) > p_col_idx else "الفصل الأول - فترة أولى"
                    if r_per in ["", "الفترة الأولى"]:
                      r_per = "الفصل الأول - فترة أولى"
                    elif r_per == "الفترة الثانية":
                      r_per = "الفصل الأول - فترة ثانية"
                    if r_id == sid_g and r_per == cp:
                      row_to_update = r_i
                      break

                  row_payload = [sid_g, v1, v2, tot, today_s]
                  while len(row_payload) < len(headers) - 1:
                    row_payload.append("")
                  row_payload.append(cp)

                  if row_to_update:
                    end_cell = rowcol_to_a1(row_to_update, len(row_payload))
                    ws_g.update(range_name=f"A{row_to_update}:{end_cell}", values=[row_payload])
                  else:
                    ws_g.append_row(row_payload)

                  fetch_safe.clear()
                  st.session_state.df_grades = fetch_safe("grades")
                  st.toast(f"✅ تم حفظ درجات {s_nm_g} (المجموع: {tot}) فوراً!", icon="📊")
                  st.rerun()
            else:
              st.info("💡 وضع القراءة فقط.")

        # --- ب) القائمة السفلية الذكية: الرصد الجماعي داخل st.form لمنع إعادة التحميل مع كل رقم ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"📋 الرصد الجماعي السريع لدرجات فصل كامل ({cp}) — اضغط لفتح جدول الرصد الجماعي", expanded=False):
          st.info("💡 اختر الفصل، وعدّل الدرجات لجميع الطلاب بحرية تامة داخل الجدول، ثم اضغط زر الحفظ بالأسفل ليتم رصد الفصل بالكامل دفعة واحدة.")

          bulk_gr_cls = st.selectbox("🏫 اختر الفصل لرصد درجاته جماعياً:", st.session_state.class_options, key="bulk_grades_cls_sel")
          cls_st_df = df_ev_g[df_ev_g["class"].astype(str).str.strip() == bulk_gr_cls.strip()].sort_values("name")

          if not cls_st_df.empty:
            cur_period_grades = pd.DataFrame()
            if not df_g.empty:
              cur_period_grades = df_g[df_g["period"] == cp].drop_duplicates(subset=["clean_id"], keep="last")

            rows_for_editor = []
            for _, st_r in cls_st_df.iterrows():
              c_sid = st_r["clean_id"]
              p1_v, p2_v = 0, 0
              if not cur_period_grades.empty and c_sid in cur_period_grades["clean_id"].values:
                g_row = cur_period_grades[cur_period_grades["clean_id"] == c_sid].iloc[-1]
                p1_v = int(pd.to_numeric(g_row.get("p1", 0), errors="coerce") or 0)
                p2_v = int(pd.to_numeric(g_row.get("p2", 0), errors="coerce") or 0)

              rows_for_editor.append({
                  "الرقم الأكاديمي": c_sid,
                  "اسم الطالب": st_r["name"],
                  "المشاركة والمهام": p1_v,
                  "الاختبارات": p2_v,
                  "المجموع الكلي": p1_v + p2_v,
              })

            df_bulk_editor = pd.DataFrame(rows_for_editor)

            with st.form(f"form_bulk_grades_{bulk_gr_cls}"):
              edited_bulk_grades = st.data_editor(
                  df_bulk_editor,
                  use_container_width=True,
                  hide_index=True,
                  disabled=["الرقم الأكاديمي", "اسم الطالب", "المجموع الكلي"],
                  column_config={
                      "الرقم الأكاديمي": st.column_config.TextColumn("🆔 الرقم الأكاديمي"),
                      "اسم الطالب": st.column_config.TextColumn("👤 اسم الطالب"),
                      "المشاركة والمهام": st.column_config.NumberColumn(
                          f"📝 المشاركة (من {max_t_val})", min_value=0, max_value=max_t_val, step=1, required=True
                      ),
                      "الاختبارات": st.column_config.NumberColumn(
                          f"✍️ الاختبارات (من {max_q_val})", min_value=0, max_value=max_q_val, step=1, required=True
                      ),
                      "المجموع الكلي": st.column_config.NumberColumn("🏆 المجموع المحفوظ"),
                  },
                  key=f"de_bulk_grades_{bulk_gr_cls}_{cp}",
              )

              save_bulk_gr_btn = st.form_submit_button(
                  f"🚀 حفظ درجات فصل ({bulk_gr_cls}) بالكامل دفعة واحدة",
                  type="primary",
                  use_container_width=True,
              )

            if save_bulk_gr_btn and st.session_state.role == "teacher":
              try:
                with st.spinner(f"⏳ جاري حفظ درجات طلاب ({bulk_gr_cls}) وتحديث المجاميع..."):
                  ws_g = get_gspread_client().worksheet("grades")
                  all_g_vals = ws_g.get_all_values()
                  headers = all_g_vals[0] if all_g_vals else ["student_id", "p1", "p2", "perf", "date", "period"]
                  if "period" not in headers:
                    ws_g.update_cell(1, len(headers) + 1, "period")
                    headers.append("period")

                  p_col_idx = headers.index("period")
                  existing_row_map = {}
                  for r_i, r_val in enumerate(all_g_vals[1:], start=2):
                    r_id = str(r_val[0]).strip().split(".")[0] if len(r_val) > 0 else ""
                    r_per = str(r_val[p_col_idx]).strip() if len(r_val) > p_col_idx else "الفصل الأول - فترة أولى"
                    if r_per in ["", "الفترة الأولى"]:
                      r_per = "الفصل الأول - فترة أولى"
                    elif r_per == "الفترة الثانية":
                      r_per = "الفصل الأول - فترة ثانية"
                    if r_id and r_per == cp:
                      existing_row_map[r_id] = r_i

                  today_s = str(datetime.date.today())
                  batch_updates = []
                  new_rows_to_append = []

                  for _, erow in edited_bulk_grades.iterrows():
                    st_id_b = str(erow["الرقم الأكاديمي"]).strip().split(".")[0]
                    v1_b = int(pd.to_numeric(erow["المشاركة والمهام"], errors="coerce") or 0)
                    v2_b = int(pd.to_numeric(erow["الاختبارات"], errors="coerce") or 0)
                    tot_b = v1_b + v2_b

                    row_payload = [st_id_b, v1_b, v2_b, tot_b, today_s]
                    while len(row_payload) < len(headers) - 1:
                      row_payload.append("")
                    row_payload.append(cp)

                    if st_id_b in existing_row_map:
                      target_r = existing_row_map[st_id_b]
                      end_c = rowcol_to_a1(target_r, len(row_payload))
                      batch_updates.append({"range": f"A{target_r}:{end_c}", "values": [row_payload]})
                    else:
                      new_rows_to_append.append(row_payload)

                  if batch_updates:
                    ws_g.batch_update(batch_updates)
                  if new_rows_to_append:
                    ws_g.append_rows(new_rows_to_append)

                  fetch_safe.clear()
                  st.session_state.df_grades = fetch_safe("grades")
                  st.success(f"✅ تم حفظ وتحديث درجات ({len(edited_bulk_grades)}) طالب في فصل ({bulk_gr_cls}) بنجاح!")
                  st.rerun()
              except Exception as e:
                st.error(f"❌ حدث خطأ أثناء الحفظ الجماعي للدرجات: {e}")
          else:
            st.warning("لا يوجد طلاب مسجلين في هذا الفصل.")
      else:
        st.info("لا توجد بيانات طلاب.")

    # ---------------------------------------------------------
    # 4. مدقق رصد الدرجات (كشف النواقص)
    # ---------------------------------------------------------
    with eval_tabs[3]:
      cp_aud = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()
      st.markdown(f"#### 🔍 مدقق رصد الدرجات ({cp_aud})")
      st.info("💡 يعرض هذا المدقق قائمة الطلاب الذين لم تُرصد لهم درجات في الفترة النشطة حالياً.")

      df_st_audit = st.session_state.df_students.copy()
      df_gr_audit = st.session_state.df_grades.copy()

      if not df_st_audit.empty:
        df_st_audit["clean_id"] = df_st_audit.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]

        if not df_gr_audit.empty:
          df_gr_audit["clean_id"] = df_gr_audit.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]
          if "period" not in df_gr_audit.columns:
            df_gr_audit["period"] = "الفصل الأول - فترة أولى"
          df_gr_audit["period"] = df_gr_audit["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()
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
          st.warning(f"⚠️ يوجد ({len(missing_grades)}) طالب لم ترصد لهم درجات في ({cp_aud}).")
          display_missing = missing_grades[["clean_id", "name", "class", "sem"]].rename(
              columns={"clean_id": "الرقم الأكاديمي", "name": "اسم الطالب", "class": "الصف", "sem": "المرحلة"}
          )
          st.dataframe(display_missing, use_container_width=True, hide_index=True)

          st.download_button(
              label="📥 تحميل قائمة نواقص الرصد (Excel)",
              data=build_excel_bytes(display_missing, sheet_name="Missing_Grades"),
              file_name=f"missing_grades_{datetime.date.today()}.xlsx",
              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              type="primary",
              use_container_width=True,
          )
        else:
          st.success(f"✅ ممتاز! جميع الطلاب المسجلين تم رصد درجاتهم في ({cp_aud}) بنجاح.")
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
      df_st_h["clean_id"] = df_st_h.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      df_st_h["النقاط"] = pd.to_numeric(df_st_h["النقاط"], errors="coerce").fillna(0)

    honor_tabs = st.tabs([
        "🌟 لوحة الشرف",
        "🎓 المتفوقون (90%+)",
        "📜 إصدار الشهادات",
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
          top_10 = active_students.sort_values("النقاط", ascending=False).head(10)

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
              rank_text, icon, ribbon_html, badge_class = "المركز الأول", "🏆", '<div class="ribbon gold">الأول</div>', "rank-1"
              med, bg, brd, txt = "🥇", "linear-gradient(135deg, #FFF8DC, #FFFAF0)", "#DAA520", "#8B4513"
            elif rank == 2:
              rank_text, icon, ribbon_html, badge_class = "المركز الثاني", "🥈", '<div class="ribbon silver">الثاني</div>', "rank-2"
              med, bg, brd, txt = "🥈", "linear-gradient(135deg, #F8F9FA, #FFFFFF)", "#94A3B8", "#1E293B"
            elif rank == 3:
              rank_text, icon, ribbon_html, badge_class = "المركز الثالث", "🥉", '<div class="ribbon bronze">الثالث</div>', "rank-3"
              med, bg, brd, txt = "🥉", "linear-gradient(135deg, #FFF1F2, #FFFBFB)", "#CD7F32", "#92400E"
            else:
              rank_text, icon, ribbon_html, badge_class = f"المركز {rank}", "🌟", "", ""
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
              type="secondary",
              use_container_width=True,
          )
        else:
          st.info("لم يحصل أي طالب على نقاط تميز حتى الآن.")

    # --- 2. المتفوقون أكاديمياً (90%+) ---
    with honor_tabs[1]:
      cp = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()
      st.markdown(f"#### 🎓 لوحة المتفوقين أكاديمياً ({cp})")

      if "df_grades" in st.session_state and not st.session_state.df_grades.empty and not df_st_h.empty:
        df_g = st.session_state.df_grades.copy()
        df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0]
        if "period" not in df_g.columns:
          df_g["period"] = "الفصل الأول - فترة أولى"
        df_g["period"] = df_g["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()
        df_g = df_g[df_g["period"] == cp]

        merged_df = pd.merge(df_g, df_st_h[["clean_id", "name", "class", "الجوال"]], on="clean_id", how="inner")

        if not merged_df.empty:
          max_total = st.session_state.get("max_tasks", 60) + st.session_state.get("max_quiz", 40)
          if max_total > 0:
            merged_df["perf_num"] = pd.to_numeric(merged_df["perf"], errors="coerce").fillna(0)
            merged_df["percentage"] = (merged_df["perf_num"] / max_total) * 100
            top_academic = merged_df[merged_df["percentage"] >= 90].sort_values("percentage", ascending=False)

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

    # --- 3. مركز إصدار شهادات المتفوقين والشكر الإلكترونية ---
    with honor_tabs[2]:
      st.markdown("#### 📜 مركز إصدار شهادات التفوق والشكر الإلكترونية (A4 Landscape)")
      st.info("💡 يمكنك تحديد عدة فصول معاً (مثل جميع فصول الخامس) أو اختيار طالب/عدة طلاب بالاسم لاستخراج شهادات شكر وتقدير إلكترونية رسمية ومختومة دفعة واحدة.")

      DEFAULT_CERT_PHRASES = {
          "وسام التميز الأكاديمي": [
              "وذلك نظير تفوقه العلمي وتميزه وحصوله على تقدير ممتاز في مادة اللغة الإنجليزية.",
              "تقديراً لتميزه الأكاديمي وتفوقه الدراسي وحرصه المستمر على تحقيق أعلى مستويات الإنجاز.",
              "إشادةً باجتهاده ومثابرته وتميزه العلمي، وتحقيقه نتائج دراسية متميزة.",
              "تقديراً لإنجازه العلمي المتميز وحرصه على التفوق والارتقاء بمستواه الدراسي.",
          ],
          "وسام التفوق والإبداع": [
              "تقديراً لتفوقه وإبداعه وتميزه في الأداء، وما أظهره من مبادرة وابتكار وروح إيجابية في التعلم.",
              "تقديراً لإبداعه ومبادراته المتميزة وأفكاره الإبداعية التي تعكس شغفه بالتعلم.",
              "نظير تميزه وإبداعه ومشاركته الفاعلة وجهوده المتميزة في الأنشطة التعليمية.",
              "إشادةً بموهبته وإبداعه وقدرته على تقديم أعمال وأفكار متميزة.",
          ],
          "وسام التميز السلوكي والانضباط الصفي": [
              "تقديراً لتميزه في السلوك والانضباط داخل حصة اللغة الإنجليزية، والتزامه بتعليمات المعلم، واحترامه لزملائه، وحرصه على المشاركة الإيجابية.",
              "نظير التزامه بآداب الحوار والانضباط داخل الحصة، وتفاعله الإيجابي واحترامه للمعلم والزملاء.",
              "تقديراً لحسن سلوكه وتعاونه والتزامه بتعليمات حصة اللغة الإنجليزية، وحرصه على توفير بيئة تعليمية إيجابية.",
              "إشادةً بتميزه في الانضباط الصفي، وحسن تعامله، ومشاركته الفاعلة التي تعكس روح المسؤولية والاحترام.",
              "نظير التزامه وهدوئه واحترامه لقواعد الحصة الدراسية، وتميزه في التعامل الإيجابي مع المعلم وزملائه.",
          ],
      }

      if "cert_phrases_config" not in st.session_state:
        s_map_cert = get_cached_settings()
        saved_json = s_map_cert.get("cert_phrases", "")
        if saved_json:
          try:
            loaded_cfg = json.loads(saved_json)
            for k, v in DEFAULT_CERT_PHRASES.items():
              if k not in loaded_cfg or not loaded_cfg[k]:
                loaded_cfg[k] = v
            st.session_state.cert_phrases_config = loaded_cfg
          except Exception:
            st.session_state.cert_phrases_config = DEFAULT_CERT_PHRASES.copy()
        else:
          st.session_state.cert_phrases_config = DEFAULT_CERT_PHRASES.copy()

      phrases_cfg = st.session_state.cert_phrases_config
      badge_titles_list = list(phrases_cfg.keys())

      if "cert_gen_title" not in st.session_state or st.session_state.cert_gen_title not in badge_titles_list:
        st.session_state.cert_gen_title = badge_titles_list[0]
      if "cert_phrase_preset" not in st.session_state:
        st.session_state.cert_phrase_preset = phrases_cfg[st.session_state.cert_gen_title][0]
      if "cert_custom_reason" not in st.session_state:
        st.session_state.cert_custom_reason = phrases_cfg[st.session_state.cert_gen_title][0]

      def on_badge_change():
        chosen_badge = st.session_state.cert_gen_title
        default_phrase = st.session_state.cert_phrases_config.get(chosen_badge, [""])[0]
        st.session_state.cert_phrase_preset = default_phrase
        st.session_state.cert_custom_reason = default_phrase
        st.session_state.ready_certs_pdf = None

      def on_preset_change():
        st.session_state.cert_custom_reason = st.session_state.cert_phrase_preset
        st.session_state.ready_certs_pdf = None

      if not df_st_h.empty:
        c_cert1, c_cert2, c_cert3 = st.columns(3)
        cert_mode = c_cert1.selectbox(
            "1️⃣ نظام الإصدار:",
            [
                "🌟 جميع المتفوقين (90%+) في الفصول",
                "👤 طالب محدد (أو عدة طلاب بالاسم)",
                "🏆 أبطال لوحة الشرف (أعلى النقاط)",
            ],
            key="cert_gen_mode",
        )
        cert_period = c_cert2.selectbox(
            "2️⃣ الفترة الدراسية:",
            [
                "الفصل الأول - فترة أولى",
                "الفصل الأول - فترة ثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
            ],
            index=0,
            key="cert_gen_period",
        )
        cert_title_opt = c_cert3.selectbox(
            "3️⃣ عنوان الوسام:",
            badge_titles_list,
            key="cert_gen_title",
            on_change=on_badge_change,
        )

        avail_cert_classes = list(df_st_h["class"].dropna().unique())
        target_students_cert = pd.DataFrame()

        if cert_mode == "🌟 جميع المتفوقين (90%+) في الفصول":
          sel_cls_cert_list = st.multiselect(
              "🏫 اختر الفصول المستهدفة (يمكنك تحديد أكثر من فصل معاً أو الكل):",
              options=["الكل"] + avail_cert_classes,
              default=["الكل"],
              key="cert_cls_sel_multi",
          )

          df_g_c = st.session_state.df_grades.copy()
          if not df_g_c.empty and sel_cls_cert_list:
            df_g_c["clean_id"] = df_g_c.iloc[:, 0].astype(str).str.split(".").str[0]
            if "period" not in df_g_c.columns:
              df_g_c["period"] = "الفصل الأول - فترة أولى"
            df_g_c["period"] = df_g_c["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()
            df_g_c = df_g_c[df_g_c["period"] == cert_period]

            m_cert = pd.merge(df_st_h, df_g_c[["clean_id", "perf"]], on="clean_id", how="inner")
            if "الكل" not in sel_cls_cert_list:
              m_cert = m_cert[m_cert["class"].isin(sel_cls_cert_list)]

            max_t = st.session_state.get("max_tasks", 60) + st.session_state.get("max_quiz", 40)
            if max_t > 0 and not m_cert.empty:
              m_cert["perf_num"] = pd.to_numeric(m_cert["perf"], errors="coerce").fillna(0)
              m_cert["pct"] = (m_cert["perf_num"] / max_t) * 100
              target_students_cert = m_cert[m_cert["pct"] >= 90].sort_values(["class", "pct"], ascending=[True, False])

        elif cert_mode == "👤 طالب محدد (أو عدة طلاب بالاسم)":
          col_f_c1, col_f_c2 = st.columns([1.3, 2])
          sel_cls_filter_c = col_f_c1.multiselect(
              "🏫 تصفية بالفصول:",
              options=["الكل"] + avail_cert_classes,
              default=["الكل"],
              key="cert_single_cls_f_multi",
          )
          if not sel_cls_filter_c:
            df_st_c_filtered = df_st_h.iloc[0:0]
          elif "الكل" in sel_cls_filter_c:
            df_st_c_filtered = df_st_h
          else:
            df_st_c_filtered = df_st_h[df_st_h["class"].isin(sel_cls_filter_c)]

          st_cert_dict = {f"{r['name']} - ({r.get('class', '')})": r["clean_id"] for _, r in df_st_c_filtered.iterrows()}
          sel_st_cert_list = col_f_c2.multiselect(
              "🎯 ابحث واختر طالباً أو أكثر:",
              options=list(st_cert_dict.keys()),
              default=[list(st_cert_dict.keys())[0]] if st_cert_dict else [],
              key="cert_st_sel_multi",
          )
          if sel_st_cert_list:
            chosen_ids = [st_cert_dict[k] for k in sel_st_cert_list if k in st_cert_dict]
            target_students_cert = df_st_h[df_st_h["clean_id"].isin(chosen_ids)]

        elif cert_mode == "🏆 أبطال لوحة الشرف (أعلى النقاط)":
          sel_cls_honor_list = st.multiselect(
              "🏫 اختر الفصول (اتركه 'الكل' لأفضل 10 على مستوى المدرسة أو حدد فصولاً معينة):",
              options=["الكل"] + avail_cert_classes,
              default=["الكل"],
              key="cert_honor_cls_multi",
          )
          df_h_pool = df_st_h[df_st_h["النقاط"] > 0].copy()
          if sel_cls_honor_list and "الكل" not in sel_cls_honor_list:
            df_h_pool = df_h_pool[df_h_pool["class"].isin(sel_cls_honor_list)]
          elif not sel_cls_honor_list:
            df_h_pool = df_h_pool.iloc[0:0]
          target_students_cert = df_h_pool.sort_values("النقاط", ascending=False).head(10)

        available_phrases_for_badge = phrases_cfg.get(cert_title_opt, [""])
        if st.session_state.cert_phrase_preset not in available_phrases_for_badge:
          st.session_state.cert_phrase_preset = available_phrases_for_badge[0]

        st.selectbox(
            "📋 اختر صيغة جاهزة للعبارة (تتحدث تلقائياً حسب نوع الوسام):",
            available_phrases_for_badge,
            key="cert_phrase_preset",
            on_change=on_preset_change,
            format_func=lambda x: f"⭐ (الافتراضية) {x}" if x == available_phrases_for_badge[0] else f"🔹 {x}",
        )

        custom_reason = st.text_area(
            "✍️ عبارة التكريم في الشهادة (يمكنك التعديل اليدوي بحرية):",
            key="cert_custom_reason",
            height=85,
        )

        if not target_students_cert.empty:
          st.success(f"✅ تم تجهيز ({len(target_students_cert)}) شهادة إلكترونية جاهزة للإصدار والطباعة.")

          star_svg = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDE1LjA5IDguMjYgMjIgOS4yNyAxNyAxNC4xNCAxOC4xOCAyMS4wMiAxMiAxNy43NyA1LjgyIDIxLjAyIDcgMTQuMTQgMiA5LjI3IDguOTEgOC4yNiAxMiAyIiBmaWxsPSIjYjY4YTM2IiAvPjwvc3ZnPg=="
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

                        <table class="top-table">
                            <tr>
                                <td style="text-align: right; width: 50%; line-height: 1.5;">المملكة العربية السعودية - وزارة التعليم<br>{school_c}</td>
                                <td style="text-align: left; width: 50%; line-height: 1.5;">العام الدراسي: {st.session_state.get('current_year', '1447هـ')}<br>{cert_period}</td>
                            </tr>
                        </table>

                        <h1>شهادة شكر وتقدير</h1>
                        <h2>
                            <img src="{star_svg}" class="star-icon">
                            {cert_title_opt}
                            <img src="{star_svg}" class="star-icon">
                        </h2>

                        <p class="intro">يتقدم معلم المادة الأستاذ/ <strong>زياد المعمري</strong> وإدارة المدرسة بوافر الشكر والتقدير للطالب المبدع:</p>
                        <div class="student-name">{st_name_c} <span style="font-size:22px; color:#193b68;">({st_cls_c})</span></div>

                        <div class="reason-container">
                            <p class="reason">{custom_reason}</p>
                            <p class="reason">متمنين له دوام التوفيق ومزيداً من التألق والنجاح.</p>
                        </div>

                        <table class="footer-table">
                            <tr>
                                <td>
                                    <span class="sig-title">مدير المدرسة</span>
                                    <span class="sig-line"></span>
                                    <span class="date-val">أ. عبدالمجيد الحربي</span>
                                </td>
                                <td>
                                    <div class="stamp-circle">
                                        <div class="stamp-inner"></div>
                                        <div style="font-size: 14px; font-weight: 900; line-height: 1.1;">منصة زياد الذكية</div>
                                        <div style="font-family: 'Aref Ruqaa', serif; font-size: 28px; font-weight: bold; line-height: 1.2;">ختم التميز</div>
                                        <div style="font-size: 12px; font-weight: 800; line-height: 1.1;">{datetime.date.today().strftime('%Y-%m-%d')}</div>
                                    </div>
                                </td>
                                <td>
                                    <span class="sig-title">معلم المادة</span>
                                    <span class="sig-line"></span>
                                    <span class="sig-name">زياد المعمري</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            """

          master_certs_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>شهادات التفوق الإلكترونية</title>
          <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
          <style>
              @page {{ size: 297mm 210mm; margin: 0mm !important; }}
              * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
              html, body {{ margin: 0 !important; padding: 0 !important; background-color: #ffffff; font-family: 'Cairo', sans-serif; }}
              .cert-page {{ width: 297mm; height: 210mm; padding: 8mm; background: #ffffff; position: relative; page-break-after: always; page-break-inside: avoid; overflow: hidden; }}
              .cert-page:last-of-type {{ page-break-after: auto; }}
              .border-outer {{ border: 12px solid #193b68; width: 100%; height: 100%; padding: 5px; position: relative; }}
              .border-inner {{ border: 3px solid #b68a36; width: 100%; height: 100%; padding: 18px 35px; text-align: center; position: relative; background-color: #ffffff; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 22px 22px; }}
              .corner {{ position: absolute; width: 28px; height: 28px; border: 4px solid #b68a36; }}
              .tl {{ top: -7px; left: -7px; border-right: none; border-bottom: none; }}
              .tr {{ top: -7px; right: -7px; border-left: none; border-bottom: none; }}
              .bl {{ bottom: -7px; left: -7px; border-right: none; border-top: none; }}
              .br {{ bottom: -7px; right: -7px; border-left: none; border-top: none; }}
              .top-table {{ width: 100%; border-collapse: collapse; margin-bottom: 4px; font-size: 14px; font-weight: 700; color: #193b68; }}
              h1 {{ font-family: 'Aref Ruqaa', serif; font-size: 58px; color: #b68a36; margin: 0 0 4px 0; font-weight: bold; line-height: 1.15; }}
              h2 {{ font-family: 'Cairo', sans-serif; font-size: 27px; color: #193b68; margin: 0 0 12px 0; font-weight: 900; }}
              .star-icon {{ width: 25px; height: 25px; vertical-align: middle; margin: 0 8px; }}
              p.intro {{ font-size: 20px; color: #193b68; margin: 0 0 6px 0; font-weight: 700; }}
              .student-name {{ font-size: 44px; font-weight: 900; color: #d32f2f; margin: 4px auto 12px auto; display: inline-block; border-bottom: 3px solid #b68a36; padding: 0 35px 5px 35px; line-height: 1.2; }}
              .reason-container {{ margin: 6px 0 14px 0; }}
              p.reason {{ font-size: 20px; font-weight: 700; color: #334155; line-height: 1.6; margin: 0; }}
              .footer-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 10px; direction: rtl; }}
              .footer-table td {{ width: 33.33%; vertical-align: middle; text-align: center !important; color: #193b68; padding: 0 10px; }}
              .sig-title {{ font-size: 19px; font-weight: 800; display: block; text-align: center; }}
              .sig-line {{ display: inline-block !important; width: 160px; height: 0px; border-bottom: 2px solid #b68a36; margin: 8px 0; }}
              .sig-name {{ font-family: 'Aref Ruqaa', serif; font-size: 30px; color: #193b68; font-weight: bold; display: block; text-align: center; line-height: 1.1; }}
              .date-val {{ font-size: 19px; font-weight: 800; color: #193b68; display: block; text-align: center; margin-top: 4px; }}
              .stamp-circle {{ display: inline-block !important; width: 126px; height: 126px; border: 3px dashed #d32f2f; border-radius: 50%; transform: rotate(-14deg); color: #d32f2f; text-align: center; opacity: 0.88; padding-top: 18px; position: relative; background-color: rgba(255, 255, 255, 0.85); }}
              .stamp-inner {{ position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px; border: 1px solid #d32f2f; border-radius: 50%; }}
          </style></head><body>
          {all_certs_pages_html}
          <script>window.onload = function() {{ window.print(); }}</script>
          </body></html>
          """

          btn_c1, btn_c2 = st.columns(2)
          with btn_c1:
            st.download_button(
                label=f"🖨️ فتح وطباعة الشهادات فوراً ({len(target_students_cert)} شهادة - سريع)",
                data=master_certs_html,
                file_name=f"Print_Certificates_{datetime.date.today()}.html",
                mime="text/html",
                type="primary",
                use_container_width=True,
            )
          with btn_c2:
            if st.button(
                f"⚙️ تجهيز ملف PDF مباشر ({len(target_students_cert)} شهادة)",
                type="secondary",
                use_container_width=True,
                key="btn_build_certs_pdf",
            ):
              try:
                with st.spinner("⏳ جاري رسم الشهادات وتحويلها إلى PDF..."):
                  st.session_state.ready_certs_pdf = generate_pdf_bytes_cached(master_certs_html)
              except Exception as e:
                st.error(f"تعذر توليد الـ PDF المباشر، استخدم زر الطباعة الفوري: {e}")

            if st.session_state.get("ready_certs_pdf"):
              st.download_button(
                  label=f"📥 اضغط لتنزيل ملف الـ PDF الجاهز ({len(target_students_cert)} شهادة)",
                  data=st.session_state.ready_certs_pdf,
                  file_name=f"Certificates_{datetime.date.today()}.pdf",
                  mime="application/pdf",
                  type="primary",
                  use_container_width=True,
              )

          with st.expander("📲 إرسال تهنئة سريعة لأولياء أمور المكرمين عبر واتساب"):
            for _, s_row in target_students_cert.iterrows():
              s_n = s_row.get("name", "")
              s_p = clean_phone_number(s_row.get("الجوال", ""))
              congrats_msg = urllib.parse.quote(
                  f"🌟 *تهنئة تفوق وتميز من منصة الأستاذ زياد المعمري* 🌟\n\n"
                  f"يسرنا تهنئتكم بحصول الابن المبدع: *{s_n}*\n"
                  f"على *{cert_title_opt}* في مادة اللغة الإنجليزية ({cert_period}).\n"
                  f"📝 *{custom_reason}*\n"
                  f"مع خالص تمنياتنا له بدوام التوفيق والنجاح! 🎉"
              )
              col_w1, col_w2 = st.columns([3, 1])
              col_w1.markdown(f"<div style='padding-top:10px; font-weight:bold;'>🎓 {s_n} ({s_row.get('class', '')})</div>", unsafe_allow_html=True)
              col_w2.link_button("📲 إرسال تهنئة واتساب", f"https://api.whatsapp.com/send?phone={s_p}&text={congrats_msg}", use_container_width=True)
        else:
          st.warning("⚠️ لا يوجد طلاب يطابقون معيار الشهادات المحدد حالياً.")

        if st.session_state.role == "teacher":
          st.markdown("---")
          with st.expander("⚙️ إعدادات قوالب العبارات (إضافة أو تعديل عبارات الأوسمة مستقبلاً دون تعديل الكود)"):
            st.caption("يمكنك إضافة عبارات جديدة لأي وسام أو تعديل العبارات الحالية، وسيتم حفظها في قاعدة البيانات المركزية (`settings`).")
            edit_badge_target = st.selectbox("اختر الوسام لتحرير عباراته:", badge_titles_list, key="cfg_badge_sel")
            current_lines = "\n".join(phrases_cfg.get(edit_badge_target, []))
            updated_lines_text = st.text_area(
                "عبارات الوسام (كل سطر يمثل عبارة مستقلة، والسطر الأول هو العبارة الافتراضية):",
                value=current_lines,
                height=150,
                key=f"cfg_lines_{edit_badge_target}",
            )
            col_sv1, col_sv2 = st.columns([2, 1])
            if col_sv1.button("💾 حفظ عبارات هذا الوسام في قاعدة البيانات", type="primary", use_container_width=True):
              new_list = [line.strip() for line in updated_lines_text.split("\n") if line.strip()]
              if new_list:
                phrases_cfg[edit_badge_target] = new_list
                st.session_state.cert_phrases_config = phrases_cfg
                try:
                  ws_sett = get_gspread_client().worksheet("settings")
                  records_s = ws_sett.get_all_records()
                  row_found = None
                  for idx_s, r_s in enumerate(records_s):
                    if str(r_s.get("key", "")).strip() == "cert_phrases":
                      row_found = idx_s + 2
                      break
                  json_str = json.dumps(phrases_cfg, ensure_ascii=False)
                  if row_found:
                    ws_sett.update_cell(row_found, 2, json_str)
                  else:
                    ws_sett.append_row(["cert_phrases", json_str])
                  get_cached_settings.clear()
                  on_badge_change()
                  st.success(f"✅ تم حفظ عبارات ({edit_badge_target}) بنجاح!")
                  st.rerun()
                except Exception as e:
                  st.error(f"❌ خطأ أثناء الحفظ في السيرفر: {e}")
              else:
                st.warning("⚠️ يجب إدخال عبارة واحدة على الأقل.")

            if col_sv2.button("🔄 استعادة العبارات الافتراضية", type="secondary", use_container_width=True):
              st.session_state.cert_phrases_config = DEFAULT_CERT_PHRASES.copy()
              try:
                ws_sett = get_gspread_client().worksheet("settings")
                records_s = ws_sett.get_all_records()
                for idx_s, r_s in enumerate(records_s):
                  if str(r_s.get("key", "")).strip() == "cert_phrases":
                    ws_sett.update_cell(idx_s + 2, 2, json.dumps(DEFAULT_CERT_PHRASES, ensure_ascii=False))
                    break
                get_cached_settings.clear()
              except Exception:
                pass
              on_badge_change()
              st.rerun()
# ==========================================
# 🖨️ 8. التبويب الرابع: مركز التقارير والطباعة الشامل (يدعم اختيار عدة فصول معاً)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_reports:
    st.subheader("🖨️ مركز التقارير والطباعة والاستخراج")
    st.caption("جميع تقارير الطباعة، شواهد الأداء، الكشوفات المرنة، وتصدير ملفات Excel في مكان واحد مع دعم تحديد عدة فصول دفعة واحدة")

    df_s_rep = st.session_state.df_students.copy()
    if not df_s_rep.empty:
      df_s_rep["clean_id"] = df_s_rep.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
      df_s_rep["النقاط"] = pd.to_numeric(df_s_rep["النقاط"], errors="coerce").fillna(0)

    def resolve_multi_classes(selected_list, all_available_classes):
      if not selected_list:
        return [], "ابتدائية عبادة بن قيس الأنصاري", ""
      if "الكل" in selected_list:
        target_cls = list(all_available_classes)
        label_str = "الكل"
      else:
        target_cls = list(selected_list)
        label_str = " ، ".join(target_cls)

      cs_map = st.session_state.get("class_stage_map", {})
      stages_found = set()
      for c_name in target_cls:
        st_g = cs_map.get(str(c_name).strip(), "")
        if st_g == "متوسط" or "متوسط" in str(c_name):
          stages_found.add("متوسط")
        else:
          stages_found.add("ابتدائي")

      if stages_found == {"متوسط"}:
        sch_name = "متوسطة عبدالرحمن الناصر"
      elif stages_found == {"ابتدائي"}:
        sch_name = "ابتدائية عبادة بن قيس الأنصاري"
      else:
        sch_name = "ابتدائية عبادة بن قيس الأنصاري<br>متوسطة عبدالرحمن الناصر"

      return target_cls, sch_name, label_str

    all_cls_in_db = (
        list(df_s_rep["class"].dropna().unique())
        if not df_s_rep.empty and "class" in df_s_rep.columns
        else st.session_state.get("class_options", [])
    )

    rep_tabs = st.tabs([
        "📑 تقرير طالب",
        "📊 كشف الدرجات",
        "📝 كشف متابعة",
        "🖨️ التفريغ الورقي",
        "📈 فرز المستويات",
        "🧠 أنماط التعلم",
        "📱 أرقام التواصل",
    ])

    # ---------------------------------------------------------
    # 1. تقرير الطالب الشامل المفصل
    # ---------------------------------------------------------
    with rep_tabs[0]:
      st.markdown("#### 📑 التقرير الشامل المفصل للطالب")
      if not df_s_rep.empty:
        col_r_cls, col_r_st = st.columns([1.3, 2.2])
        sel_r_cls = col_r_cls.multiselect(
            "🏫 تصفية بالفصول:",
            ["الكل"] + all_cls_in_db,
            default=["الكل"],
            key="rep_single_cls_filter",
        )

        target_r_cls, _, _ = resolve_multi_classes(sel_r_cls, all_cls_in_db)
        df_s_rep_f = df_s_rep[df_s_rep["class"].isin(target_r_cls)] if target_r_cls else df_s_rep

        st_dict = {f"{r['name']} - ({r.get('class', '')})": r["clean_id"] for _, r in df_s_rep_f.iterrows()}
        sel_rep = col_r_st.selectbox("🔍 ابحث عن الطالب لاستخراج التقرير:", [""] + list(st_dict.keys()), key="rep_sel")

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
              "#3B82F6" if "بصري" in l_style
              else "#10B981" if "سمعي" in l_style
              else "#F59E0B" if "حركي" in l_style
              else "#8B5CF6" if "متعدد" in l_style
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

          grades_html_table = "<div style='text-align:center; padding:20px; color:#64748B;'>لا توجد درجات مرصودة لهذا الطالب في هذه الفترة.</div>"
          behavior_html_table = "<div style='text-align:center; padding:20px; color:#64748B;'>✨ سجل السلوك نظيف.</div>"

          st.markdown("##### 📊 الدرجات الأكاديمية")
          df_g = st.session_state.df_grades.copy()
          cp_report = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()

          if not df_g.empty:
            df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0]
            if "period" not in df_g.columns:
              df_g["period"] = "الفصل الأول - فترة أولى"
            df_g["period"] = df_g["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()
            my_g = df_g[(df_g["clean_id"] == sid) & (df_g["period"] == cp_report)]

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
              st.info(f"لم يتم رصد درجات أكاديمية لهذا الطالب في ({cp_report}) بعد.")

          st.markdown("<br>", unsafe_allow_html=True)
          st.markdown("##### 📜 سجل السلوك والملاحظات")
          df_b = st.session_state.df_behavior.copy()
          if not df_b.empty:
            df_b["clean_id"] = df_b.iloc[:, 0].astype(str).str.split(".").str[0]
            my_b = df_b[df_b["clean_id"] == sid].copy()

            if not my_b.empty:
              my_b["date_parsed"] = pd.to_datetime(my_b["date"], errors="coerce")
              my_b = my_b.sort_values(by="date_parsed", ascending=False)

              display_df = my_b[["date", "type", "note"]].rename(
                  columns={"date": "📅 التاريخ", "type": "🎯 نوع السلوك", "note": "📝 التفاصيل"}
              )
              st.dataframe(display_df, use_container_width=True, hide_index=True)

              rows_html = ""
              for _, r_b in display_df.iterrows():
                rows_html += f"<tr><td>{r_b['📅 التاريخ']}</td><td>{r_b['🎯 نوع السلوك']}</td><td>{r_b['📝 التفاصيل']}</td></tr>"

              behavior_html_table = f"<table><tr><th>التاريخ</th><th>نوع السلوك</th><th>التفاصيل</th></tr>{rows_html}</table>"
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
    # 2. كشف الدرجات المرصودة (يدعم عدة فصول في ملف طباعة واحد أو Excel)
    # ---------------------------------------------------------
    with rep_tabs[1]:
      st.markdown("#### 📊 استخراج كشف الدرجات المرصودة للطباعة")
      st.info("💡 يمكنك اختيار عدة فصول معاً (مثل جميع فصول الخامس) ليتم توليد كشف مستقل لكل فصل في ملف طباعة واحد جاهز للطباعة دفعة واحدة.")

      if not df_s_rep.empty:
        col_g1, col_g2 = st.columns([2, 1.2])
        avail_g_cls = st.session_state.get("class_options", all_cls_in_db)
        grades_print_cls_list = col_g1.multiselect(
            "1️⃣ اختر الفصول (يمكنك تحديد أكثر من فصل أو الكل):",
            options=["الكل"] + avail_g_cls,
            default=[avail_g_cls[0]] if avail_g_cls else ["الكل"],
            key="grades_print_cls_multi",
        )
        grades_print_period = col_g2.selectbox(
            "2️⃣ اختر الفترة:",
            [
                "الفصل الأول - فترة أولى",
                "الفصل الأول - فترة ثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
            ],
            key="grades_print_period",
        )

        if st.button("🖨️ توليد كشف الدرجات للفصول المحددة", type="primary", use_container_width=True):
          target_g_cls, _, label_g_cls = resolve_multi_classes(grades_print_cls_list, avail_g_cls)
          if not target_g_cls:
            st.warning("⚠️ الرجاء اختيار فصل واحد على الأقل.")
          else:
            df_g = st.session_state.get("df_grades", pd.DataFrame()).copy()
            if not df_g.empty:
              df_g["clean_id"] = df_g.iloc[:, 0].astype(str).str.split(".").str[0]
              if "period" not in df_g.columns:
                df_g["period"] = "الفصل الأول - فترة أولى"
              df_g["period"] = df_g["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()
              df_g_period = df_g[df_g["period"] == grades_print_period].drop_duplicates(subset=["clean_id"], keep="last")
            else:
              df_g_period = pd.DataFrame(columns=["clean_id", "p1", "p2", "perf"])

            all_pages_html = ""
            excel_rows_list = []

            for c_name in target_g_cls:
              df_cls_st = df_s_rep[df_s_rep["class"] == c_name].sort_values("name")
              if df_cls_st.empty:
                continue

              df_merged = pd.merge(df_cls_st, df_g_period, on="clean_id", how="left")
              rows_html = ""
              for i, (_, row) in enumerate(df_merged.iterrows(), 1):
                p1 = str(row.get("p1", "")) if pd.notna(row.get("p1")) else ""
                p2 = str(row.get("p2", "")) if pd.notna(row.get("p2")) else ""
                perf = str(row.get("perf", "")) if pd.notna(row.get("perf")) else ""
                rows_html += f"<tr><td>{i}</td><td class='name-col'>{row['name']}</td><td>{p1}</td><td>{p2}</td><td style='font-weight:bold; color:#174A5B; font-size:14px; background-color:#f5f5f5;'>{perf}</td></tr>"
                excel_rows_list.append({
                    "الرقم الأكاديمي": row["clean_id"],
                    "اسم الطالب": row["name"],
                    "الصف": c_name,
                    "المشاركة والمهام": p1,
                    "الاختبارات القصيرة": p2,
                    "المجموع الكلي": perf,
                })

              school_name = get_school_name_dynamic(c_name)
              all_pages_html += f"""
              <div class="page-sheet">
                  <div class="header-box">
                      <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                      <div class="header-text" style="font-size: 18px;">وزارة التعليم<br><span style="font-size: 9px; font-weight:normal;">Ministry of Education</span></div>
                      <div class="header-text">العام الدراسي {st.session_state.current_year}<br>{grades_print_period}</div>
                  </div>
                  <div class="title-box">كشف الدرجات الأكاديمية المرصودة - مادة اللغة الإنجليزية - ({c_name})</div>
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
              </div>
              """

            if not all_pages_html:
              st.warning("⚠️ لا يوجد طلاب مسجلين في الفصول المحددة.")
            else:
              grades_sheet_html = f"""
              <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>كشف الدرجات - {label_g_cls}</title>
              <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
              <style>
                  body {{ font-family: 'Cairo', sans-serif; background: #fff; margin: 0; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                  .page-sheet {{ page-break-after: always; padding-bottom: 15px; }}
                  .page-sheet:last-of-type {{ page-break-after: auto; }}
                  .header-box {{ background-color: #174A5B; color: white; border-radius: 10px; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                  .header-text {{ text-align: center; font-weight: bold; line-height: 1.3; font-size: 11px; }}
                  .title-box {{ background-color: #174A5B; color: white; text-align: center; padding: 4px; font-weight: bold; width: 65%; margin: -20px auto 5px auto; border-radius: 6px; border: 2px solid white; position: relative; z-index: 2; font-size: 13px; }}
                  table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; margin-top: 10px; }}
                  th, td {{ border: 1px solid #b0bec5; padding: 3px 5px; height: 22px; }}
                  th {{ background-color: #e0e0e0; font-weight: bold; color: #333; font-size: 12px; }}
                  .name-col {{ width: 40%; background-color: #f8fafc; text-align: right; padding-right: 10px !important; font-weight: bold; }}
                  .footer {{ display: flex; justify-content: space-between; margin-top: 20px; font-weight: bold; padding: 0 50px; font-size: 12px; }}
                  @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} body {{ padding: 0; }} thead {{ display: table-header-group; }} tr {{ page-break-inside: avoid; }} }}
              </style></head><body>
                  {all_pages_html}
                  <script>window.onload = function() {{ window.print(); }}</script>
              </body></html>
              """
              dl_g1, dl_g2 = st.columns(2)
              dl_g1.download_button(
                  label=f"🖨️ تحميل للطباعة المباشرة ({len(target_g_cls)} فصول)",
                  data=grades_sheet_html,
                  file_name=f"Filled_Grades_{datetime.date.today()}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )
              if excel_rows_list:
                df_ex_g = pd.DataFrame(excel_rows_list)
                dl_g2.download_button(
                    label=f"📥 تصدير الدرجات (Excel - {len(target_g_cls)} فصول)",
                    data=build_excel_bytes(df_ex_g, sheet_name="الدرجات"),
                    file_name=f"Grades_Export_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True,
                )

    # ---------------------------------------------------------
    # 3. كشف متابعة فارغ مرن (يدعم طباعة عدة فصول في ملف واحد)
    # ---------------------------------------------------------
    with rep_tabs[2]:
      st.markdown("#### 📝 استخراج كشف متابعة مرن (فارغ للرصد اليدوي)")
      st.info("💡 اختر عدة فصول معاً ليتم توليد كشف مستقل لكل فصل في ملف طباعة واحد دون الحاجة لتكرار الطباعة لكل فصل.")

      if not df_s_rep.empty:
        col_opt1, col_opt2 = st.columns([2, 1])
        all_classes = st.session_state.get("class_options", all_cls_in_db)
        print_cls_choices = col_opt1.multiselect(
            "1️⃣ اختر الفصول المطلوبة:",
            options=["الكل"] + all_classes,
            default=[all_classes[0]] if all_classes else ["الكل"],
            key="print_cls_flex_multi",
        )
        page_orientation = col_opt2.radio("2️⃣ اتجاه الطباعة:", ["أفقي (Landscape)", "عمودي (Portrait)"])
        css_orientation = "landscape" if "أفقي" in page_orientation else "portrait"

        available_fields = {
            "الحضور والغياب": 10,
            "المشاركة والتفاعل": 5,
            "الواجبات والمهام": 5,
            "الاختبارات القصيرة": 2,
            "المشاريع والبحوث": 5,
            "السلوك والانضباط": 5,
        }

        selected_fields = st.multiselect(
            "3️⃣ اختر الحقول المطلوبة في الكشف:",
            list(available_fields.keys()),
            default=["المشاركة والتفاعل", "الواجبات والمهام", "الاختبارات القصيرة"],
        )

        if st.button("🖨️ توليد الكشف المرن للفصول المحددة", type="primary", use_container_width=True):
          target_flx_cls, _, label_flx = resolve_multi_classes(print_cls_choices, all_classes)
          if not target_flx_cls:
            st.warning("⚠️ الرجاء اختيار فصل واحد على الأقل.")
          elif not selected_fields:
            st.warning("⚠️ الرجاء اختيار حقل واحد على الأقل ليتم رسم الكشف.")
          else:
            main_th_html, sub_th_html = "", ""
            total_empty_cells = 0
            for field in selected_fields:
              colspan = available_fields[field]
              main_th_html += f'<th colspan="{colspan}" class="main-th">{field}</th>'
              for i in range(1, colspan + 1):
                sub_th_html += f"<th>{i}</th>"
              total_empty_cells += colspan

            empty_cells_str = "<td></td>" * total_empty_cells
            all_flex_pages = ""

            for c_name in target_flx_cls:
              df_print = df_s_rep[df_s_rep["class"] == c_name].sort_values("name")
              if df_print.empty:
                continue

              rows_html = ""
              for i, (_, row) in enumerate(df_print.iterrows(), 1):
                rows_html += f"<tr><td>{i}</td><td style='text-align: right; padding-right: 5px; font-weight: bold; white-space: nowrap;'>{row['name']}</td>{empty_cells_str}<td class='total-col'></td></tr>"

              school_name = get_school_name_dynamic(c_name)
              all_flex_pages += f"""
              <div class="page-sheet">
                  <div class="header-box">
                      <div class="header-text">المملكة العربية السعودية<br>وزارة التعليم<br>{school_name}</div>
                      <div class="header-text" style="font-size: 20px;">وزارة التعليم<br><span style="font-size: 10px; font-weight:normal;">Ministry of Education</span></div>
                      <div class="header-text">العام الدراسي {st.session_state.current_year}<br>{st.session_state.current_period}</div>
                  </div>
                  <div class="title-box">كشف متابعة - مادة اللغة الإنجليزية - ({c_name})</div>
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
              </div>
              """

            if not all_flex_pages:
              st.warning("لا يوجد طلاب مسجلين في الفصول المحددة.")
            else:
              sheet_html = f"""
              <!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>كشف متابعة مخصص - {label_flx}</title>
              <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
              <style>
                  body {{ font-family: 'Cairo', sans-serif; background: #fff; margin: 0; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                  .page-sheet {{ page-break-after: always; padding-bottom: 10px; }}
                  .page-sheet:last-of-type {{ page-break-after: auto; }}
                  .header-box {{ background-color: #174A5B; color: white; border-radius: 10px; padding: 8px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
                  .header-text {{ text-align: center; font-weight: bold; line-height: 1.3; font-size: 12px; }}
                  .title-box {{ background-color: #174A5B; color: white; text-align: center; padding: 4px; font-weight: bold; width: 55%; margin: -25px auto 10px auto; border-radius: 6px; border: 2px solid white; position: relative; z-index: 2; font-size: 13px; }}
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
                  {all_flex_pages}
                  <script>window.onload = function() {{ window.print(); }}</script>
              </body></html>
              """
              st.download_button(
                  label=f"📥 تحميل الكشوفات المخصصة للطباعة ({len(target_flx_cls)} فصول في ملف واحد)",
                  data=sheet_html,
                  file_name=f"Custom_Sheets_{datetime.date.today()}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )

    # ---------------------------------------------------------
    # 4. مساعد التفريغ للسجلات الورقية (يدعم عدة فصول معاً)
    # ---------------------------------------------------------
    with rep_tabs[3]:
      st.markdown("#### 🖨️ مساعد التفريغ للسجلات الورقية (حصر الملاحظات)")
      st.info("💡 اختر فصلاً واحداً أو عدة فصول معاً لحصر وتجميع جميع المشاركات والملاحظات وتصديرها إلى Excel.")

      df_b = st.session_state.df_behavior.copy()
      if not df_b.empty and not df_s_rep.empty:
        df_b["clean_id"] = df_b.iloc[:, 0].astype(str).str.strip().str.split(".").str[0]
        merged_df = pd.merge(df_b, df_s_rep[["clean_id", "name", "class"]], on="clean_id", how="inner")
        beh_col = "type" if "type" in merged_df.columns else merged_df.columns[1]

        col1, col2 = st.columns([2, 1.5])
        available_classes = st.session_state.get("class_options", all_cls_in_db)
        cls_choices_p = col1.multiselect(
            "1️⃣ اختر الفصول لفرز بياناتها:",
            options=["الكل"] + available_classes,
            default=[available_classes[0]] if available_classes else ["الكل"],
            key="paper_helper_cls_multi",
        )
        target_p_cls, _, label_p_cls = resolve_multi_classes(cls_choices_p, available_classes)
        class_data = merged_df[merged_df["class"].isin(target_p_cls)]

        if not class_data.empty:
          unique_notes = list(class_data[beh_col].unique())
          type_choice = col2.selectbox(
              "2️⃣ نوع الملاحظة المطلوبة:",
              ["الكل (جدول تجميعي لكشف المتابعة)"] + unique_notes,
              key="paper_helper_type",
          )
          st.divider()

          if type_choice == "الكل (جدول تجميعي لكشف المتابعة)":
            st.markdown(f"##### 📊 حصر شامل لجميع ملاحظات ({label_p_cls})")
            pivot_table = pd.crosstab([class_data["class"], class_data["name"]], class_data[beh_col])
            pivot_table.index.names = ["الصف", "اسم الطالب"]

            if "note" in class_data.columns:
              def combine_notes(group):
                valid = group[group["note"].astype(str).str.strip() != ""]
                if valid.empty:
                  return ""
                return " ، ".join(valid["note"].astype(str).str.strip())

              notes_series = class_data.groupby(["class", "name"]).apply(combine_notes)
              pivot_table["الملاحظات النصية التفصيلية"] = notes_series

            all_st_multi = df_s_rep[df_s_rep["class"].isin(target_p_cls)].sort_values(["class", "name"])[["class", "name"]]
            multi_idx = pd.MultiIndex.from_frame(all_st_multi, names=["الصف", "اسم الطالب"])
            pivot_table = pivot_table.reindex(multi_idx)

            for col in pivot_table.columns:
              if col == "الملاحظات النصية التفصيلية":
                pivot_table[col] = pivot_table[col].fillna("")
              else:
                pivot_table[col] = pd.to_numeric(pivot_table[col], errors="coerce").fillna(0).astype(int).astype(str)

            pivot_display = pivot_table.reset_index()
            st.dataframe(pivot_display, use_container_width=True, hide_index=True)

            st.download_button(
                f"📥 تحميل كشف التفريغ الورقي (Excel - {len(target_p_cls)} فصول)",
                data=build_excel_bytes(pivot_display, sheet_name="التفريغ الورقي"),
                file_name=f"Behavior_Summary_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
          else:
            st.markdown(f"##### 📌 حصر الطلاب الذين لديهم ({type_choice}) في ({label_p_cls})")
            specific_data = class_data[class_data[beh_col] == type_choice]
            if not specific_data.empty:
              summary = specific_data.groupby(["class", "name", "note"]).size().reset_index(name="عدد المرات")
              summary.rename(columns={"class": "الصف", "name": "اسم الطالب", "note": "التفاصيل المكتوبة"}, inplace=True)
              summary = summary.sort_values(["الصف", "عدد المرات"], ascending=[True, False])
              st.dataframe(summary, use_container_width=True, hide_index=True)
            else:
              st.info("لا يوجد أي طالب مسجل عليه هذه الملاحظة.")
        else:
          st.info(f"لا توجد أي ملاحظات مسجلة لطلاب ({label_p_cls}) حتى الآن.")
      else:
        st.warning("لا توجد بيانات سلوكية كافية لإنشاء التقرير.")

    # ---------------------------------------------------------
    # 5. تقرير حصر المتفوقين ومتدني المستوى (يدعم اختيار عدة فصول معاً)
    # ---------------------------------------------------------
    with rep_tabs[4]:
      st.markdown("#### 📈 تقرير حصر المتفوقين ومتدني المستوى (للخطط العلاجية والتعزيز)")
      st.info("💡 يمكنك تحديد عدة فصول معاً (مثل فصول الخامس الأربعة) لاستخراج كشف موحد للخطط العلاجية أو المتفوقين بترويسة المدرسة المناسبة.")

      if not df_s_rep.empty:
        c1, c2 = st.columns([2.2, 1.3])
        avail_lvl_cls = st.session_state.get("class_options", all_cls_in_db)
        rep_cls_list = c1.multiselect(
            "🏫 اختر الفصول المستهدفة (يمكنك اختيار أكثر من فصل أو الكل):",
            options=["الكل"] + avail_lvl_cls,
            default=["الكل"],
            key="rep_lvl_cls_multi",
        )
        rep_per = c2.selectbox(
            "📅 الفترة:",
            [
                "الفصل الأول - فترة أولى",
                "الفصل الأول - فترة ثانية",
                "الفصل الثاني - فترة أولى",
                "الفصل الثاني - فترة ثانية",
            ],
            key="rep_lvl_per",
        )

        c3, c4 = st.columns(2)
        rep_type = c3.selectbox("🎯 الفئة:", ["المتفوقين 🌟", "متدني المستوى 📉"], key="rep_lvl_type")
        default_thresh = 54 if "المتفوقين" in rep_type else 36
        threshold = c4.number_input("الدرجة الفاصلة:", value=default_thresh, step=1, key=f"thresh_{rep_type}")

        if st.button("🖨️ توليد تقرير الحصر للفصول المحددة", type="primary", use_container_width=True):
          target_lvl_cls, school_name, label_lvl_cls = resolve_multi_classes(rep_cls_list, avail_lvl_cls)
          if not target_lvl_cls:
            st.warning("⚠️ الرجاء اختيار فصل واحد على الأقل.")
          else:
            df_g_all = st.session_state.get("df_grades", pd.DataFrame()).copy()
            if df_g_all.empty:
              st.warning("⚠️ لا توجد درجات مرصودة في قاعدة البيانات بعد.")
            else:
              df_st_copy = df_s_rep[df_s_rep["class"].isin(target_lvl_cls)].copy()
              df_g_all["clean_id"] = df_g_all.iloc[:, 0].astype(str).str.split(".").str[0]
              if "period" not in df_g_all.columns:
                df_g_all["period"] = "الفصل الأول - فترة أولى"
              df_g_all["period"] = df_g_all["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()

              df_g_filtered = df_g_all[df_g_all["period"] == rep_per]
              df_merged_lvl = pd.merge(df_st_copy, df_g_filtered, on="clean_id", how="inner")
              df_merged_lvl["perf_num"] = pd.to_numeric(df_merged_lvl["perf"], errors="coerce").fillna(0)

              if "المتفوقين" in rep_type:
                final_df = df_merged_lvl[df_merged_lvl["perf_num"] >= threshold].sort_values(by=["class", "perf_num"], ascending=[True, False])
                report_title = "حصر الطلاب المتفوقين"
                action_text = "تكريم في لوحة الشرف / تعزيز إيجابي"
                color_theme = "#10B981"
              else:
                final_df = df_merged_lvl[df_merged_lvl["perf_num"] < threshold].sort_values(by=["class", "perf_num"], ascending=[True, True])
                report_title = "حصر الطلاب متدني المستوى"
                action_text = "إشعار ولي الأمر / إدراج في الخطة العلاجية"
                color_theme = "#EF4444"

              if final_df.empty:
                st.success(f"✅ لا يوجد طلاب يطابقون معيار ({report_title}) في الفصول المحددة.")
              else:
                rows_lvl = ""
                excel_lvl_rows = []
                for i, (_, row) in enumerate(final_df.iterrows(), 1):
                  rows_lvl += f"<tr><td>{i}</td><td style='text-align:right; font-weight:bold;'>{row['name']}</td><td>{row.get('class', '')}</td><td style='font-weight:900; color:{color_theme};'>{row['perf_num']}</td><td style='color:#64748B; font-size:11px;'>{action_text}</td></tr>"
                  excel_lvl_rows.append({
                      "م": i,
                      "اسم الطالب": row["name"],
                      "الصف": row.get("class", ""),
                      f"المجموع ({rep_per})": row["perf_num"],
                      "الإجراء المقترح": action_text,
                  })

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
                        <div class="header-text">العام الدراسي: {st.session_state.get('current_year', '')}<br>{rep_per}<br>المعلم: زياد المعمري</div>
                    </div>
                    <div class="title-container">
                        <div class="main-title">{report_title}</div>
                        <div class="sub-title">مبني على الدرجات المرصودة في المنصة واستخراج آلي لدعم خطط الرعاية والتعزيز</div>
                        <div style="margin-top: 8px; font-size: 12px; font-weight: bold; color: {color_theme}; background:#f8fafc; display:inline-block; padding:4px 15px; border-radius:8px; border:1px dashed {color_theme};">
                            (الفصول: {label_lvl_cls}) | (معيار الفرز: {threshold} درجة) | (العدد: {len(final_df)} طالب)
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
                dl_l1, dl_l2 = st.columns(2)
                dl_l1.download_button(
                    label="🖨️ تحميل التقرير للطباعة المباشرة",
                    data=lvl_report_html,
                    file_name=f"Performance_Report_{datetime.date.today()}.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True,
                )
                df_ex_lvl = pd.DataFrame(excel_lvl_rows)
                dl_l2.download_button(
                    label="📥 تصدير التقرير (Excel)",
                    data=build_excel_bytes(df_ex_lvl, sheet_name=report_title),
                    file_name=f"Performance_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True,
                )

    # ---------------------------------------------------------
    # 6. تقرير حصر أنماط التعلم (VARK) - يدعم تحديد عدة فصول معاً + طباعة وExcel
    # ---------------------------------------------------------
    with rep_tabs[5]:
      st.markdown("#### 🧠 استخراج تقرير أنماط التعلم (للإدارة والتوثيق)")
      st.info("💡 يمكنك تحديد عدة فصول معاً (مثلاً: الخامس/1، الخامس/2، الخامس/3، الخامس/4) أو اختيار 'الكل' لاستخراج تقرير واحد مجمع جاهز للطباعة أو التصدير لملف Excel.")

      if not df_s_rep.empty:
        c1, c2 = st.columns([2.2, 1.3])
        avail_ls_cls = list(df_s_rep["class"].dropna().unique())
        sel_classes_ls = c1.multiselect(
            "🏫 اختر الفصول (يمكنك تحديد عدة فصول معاً أو الكل):",
            options=["الكل"] + avail_ls_cls,
            default=["الكل"],
            key="ls_class_multi",
        )

        style_opts = [
            "الكل",
            "تم الاختبار ✅",
            "بصري 👀",
            "سمعي 👂",
            "حركي ✋",
            "متعدد الأنماط 🌟",
            "لم يختبر ⏳",
        ]
        sel_style = c2.selectbox("🎯 اختر النمط المستهدف:", style_opts, key="ls_style")

        if st.button("🖨️ توليد تقرير الأنماط للفصول المحددة", type="primary", use_container_width=True):
          target_ls_cls, school_name, label_ls_cls = resolve_multi_classes(sel_classes_ls, avail_ls_cls)
          if not target_ls_cls:
            st.warning("⚠️ الرجاء اختيار فصل واحد على الأقل.")
          else:
            df_filtered = df_s_rep[df_s_rep["class"].isin(target_ls_cls)].copy()

            if "نمط التعلم" not in df_filtered.columns:
              df_filtered["نمط التعلم"] = ""

            if sel_style == "لم يختبر ⏳":
              df_filtered = df_filtered[
                  df_filtered["نمط التعلم"].isna()
                  | (df_filtered["نمط التعلم"].astype(str).str.strip().isin(["", "nan", "None"]))
              ]
            elif sel_style == "تم الاختبار ✅":
              df_filtered = df_filtered[
                  df_filtered["نمط التعلم"].notna()
                  & (~df_filtered["نمط التعلم"].astype(str).str.strip().isin(["", "nan", "None", "لم يختبر ⏳"]))
              ]
            elif sel_style != "الكل":
              keyword = sel_style.split()[0]
              df_filtered = df_filtered[df_filtered["نمط التعلم"].astype(str).str.contains(keyword, na=False)]

            if df_filtered.empty:
              st.warning("⚠️ لا يوجد طلاب يطابقون خياراتك الحالية.")
            else:
              df_sorted = df_filtered.sort_values(by=["class", "name"])
              rows_html = ""
              excel_ls_rows = []

              for i, (_, r) in enumerate(df_sorted.iterrows(), 1):
                s_val = r.get("نمط التعلم", "")
                if pd.isna(s_val) or str(s_val).strip() in ["", "nan", "None"]:
                  s_val = "لم يختبر ⏳"

                clr = (
                    "#3B82F6" if "بصري" in s_val
                    else "#10B981" if "سمعي" in s_val
                    else "#F59E0B" if "حركي" in s_val
                    else "#8B5CF6" if "متعدد" in s_val
                    else "#94A3B8"
                )
                rows_html += f"<tr><td>{i}</td><td style='text-align:right; font-weight:bold;'>{r['name']}</td><td>{r.get('class', '')}</td><td style='color:{clr}; font-weight:bold;'>{s_val}</td></tr>"
                excel_ls_rows.append({
                    "م": i,
                    "الرقم الأكاديمي": r.get("clean_id", ""),
                    "اسم الطالب": r["name"],
                    "الصف": r.get("class", ""),
                    "نمط التعلم": s_val,
                })

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
                          الفئة المستهدفة: (الفصول: {label_ls_cls}) | (النمط: {sel_style}) | (العدد: {len(df_filtered)} طالب)
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
              st.success(f"✅ تم تجهيز التقرير لعدد ({len(df_filtered)}) طالب من الفصول: ({label_ls_cls}).")
              dl_ls1, dl_ls2 = st.columns(2)
              dl_ls1.download_button(
                  label="🖨️ تحميل التقرير للطباعة المباشرة (HTML)",
                  data=ls_report_html,
                  file_name=f"Learning_Styles_Report_{datetime.date.today()}.html",
                  mime="text/html",
                  type="primary",
                  use_container_width=True,
              )
              df_ex_ls = pd.DataFrame(excel_ls_rows)
              dl_ls2.download_button(
                  label="📥 تصدير تقرير الأنماط (Excel)",
                  data=build_excel_bytes(df_ex_ls, sheet_name="أنماط التعلم"),
                  file_name=f"Learning_Styles_{datetime.date.today()}.xlsx",
                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                  type="secondary",
                  use_container_width=True,
              )

    # ---------------------------------------------------------
    # 7. استخراج كشف أسماء وأرقام تواصل الطلاب (يدعم عدة فصول معاً)
    # ---------------------------------------------------------
    with rep_tabs[6]:
      st.markdown("#### 📱 استخراج كشف أرقام تواصل الطلاب (واتساب)")
      st.info("💡 يمكنك تحديد عدة فصول معاً (مثل جميع فصول الخامس) لتحميل أرقام تواصلهم في ملف Excel واحد مرتب.")

      if not df_s_rep.empty:
        all_classes = st.session_state.get("class_options", all_cls_in_db)
        contact_cls_choices = st.multiselect(
            "🏫 اختر الفصول المطلوبة:",
            options=["الكل"] + all_classes,
            default=[all_classes[0]] if all_classes else ["الكل"],
            key="contact_cls_multi",
        )

        target_cnt_cls, _, label_cnt_cls = resolve_multi_classes(contact_cls_choices, all_classes)
        if not target_cnt_cls:
          st.warning("⚠️ الرجاء اختيار فصل واحد على الأقل.")
        else:
          df_contact = df_s_rep[df_s_rep["class"].isin(target_cnt_cls)].sort_values(["class", "name"])
          if not df_contact.empty:
            df_export = df_contact[["name", "class", "الجوال"]].copy()
            df_export = df_export.rename(columns={"name": "اسم الطالب", "class": "الصف", "الجوال": "رقم الجوال (واتساب)"})

            st.download_button(
                label=f"📥 تحميل كشف أرقام الجوال (Excel) - ({label_cnt_cls}) - ({len(df_export)} طالب)",
                data=build_excel_bytes(df_export, sheet_name="أرقام التواصل"),
                file_name=f"Contacts_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

            with st.expander("👁️ معاينة الأسماء والأرقام قبل التحميل"):
              st.dataframe(df_export, use_container_width=True, hide_index=True)
          else:
            st.warning("لا يوجد طلاب مسجلين في الفصول المحددة.")

# ==========================================
# 📢 9. التبويب الخامس: لوحة الإعلانات والتعاميم (يدعم اختيار عدة فصول معاً)
# ==========================================
if st.session_state.role in ["teacher", "viewer"]:
  with tab_alerts:
    st.subheader("📢 لوحة الإعلانات والتعاميم")

    def perform_delete(row_index):
      try:
        get_gspread_client().worksheet("exams").delete_rows(int(row_index) + 2)
        fetch_safe.clear()
        st.toast("✅ تم حذف التنبيه بنجاح")
      except Exception as e:
        st.toast(f"❌ حدث خطأ: {e}")

    if st.session_state.role == "teacher":
      with st.form("ann_add", clear_on_submit=True):
        c1, c2 = st.columns([2, 2])
        at = c1.text_input("📌 عنوان الإعلان أو التعميم")
        atg_list = c2.multiselect(
            "🎯 الفصول المستهدفة (يمكنك اختيار أكثر من فصل معاً):",
            options=["الكل"] + st.session_state.class_options,
            default=["الكل"],
        )
        ad = st.text_area("📄 تفاصيل الإعلان أو الرابط")
        au = st.checkbox("🔥 تعميم عاجل (يظهر بوميض أحمر أعلى حساب الطالب)")

        if st.form_submit_button("📣 نشر التعميم للفصول المحددة", type="primary", use_container_width=True):
          if not at:
            st.warning("⚠️ يرجى كتابة عنوان الإعلان.")
          elif not atg_list:
            st.warning("⚠️ يرجى اختيار فصل واحد على الأقل أو اختيار 'الكل'.")
          else:
            target_str = "الكل" if "الكل" in atg_list else " ، ".join(atg_list)
            safe_append_row(
                "exams",
                {
                    "الصف": target_str,
                    "عاجل": "نعم" if au else "لا",
                    "العنوان": at,
                    "التاريخ": str(datetime.date.today()),
                    "الرابط": ad,
                },
            )
            st.success(f"✅ تم نشر التعميم بنجاح إلى: ({target_str})!")
            fetch_safe.clear()
            st.rerun()

    st.divider()
    df_a = fetch_safe("exams")
    if not df_a.empty:
      for i, r in df_a.iloc[::-1].iterrows():
        with st.container():
          is_urgent = str(r.get("عاجل")).strip() == "نعم"
          anim_class = "urgent-box" if is_urgent else ""
          border_style = f"2px solid {danger_color}" if is_urgent else "1.5px solid rgba(148, 163, 184, 0.28)"
          bg_style = "rgba(239, 68, 68, 0.12)" if is_urgent else "var(--secondary-background-color)"
          st.markdown(
              f"""
              <div class="{anim_class}" style="background:{bg_style}; border:{border_style}; border-radius:14px; padding:16px; margin-bottom:10px; text-align:right; direction:rtl;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                      <h4 style="margin:0; color:var(--text-color); font-weight:900;">{r.get('العنوان')}</h4>
                      <span style="background:var(--background-color); padding:3px 10px; border-radius:8px; font-size:0.82rem; color:#94A3B8; font-weight:bold; direction:ltr;">{r.get('التاريخ')}</span>
                  </div>
                  <p style="margin:8px 0; color:#94A3B8; font-weight:600;">{r.get('الرابط')}</p>
                  <small style="color:{accent_color}; font-weight:800;">🎯 الفصول المستهدفة: {r.get('الصف')}</small>
              </div>
              """,
              unsafe_allow_html=True,
          )
          kc1, kc2 = st.columns([1, 4])
          msg_text = (
              "📢 *تعميم هام من منصة الأستاذ زياد*\n━━━━━━━━━━━━\n📌 *العنوان:*"
              f" {r.get('العنوان')}\n🎯 *الفصل:* {r.get('الصف')}\n📄 *التفاصيل:* {r.get('الرابط')}\n📅"
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

    # --- 1. الصيانة والنسخ الاحتياطي (بأزرار مميزة وحماية تأكيد قبل التصفير) ---
    with set_tabs[0]:
      st.markdown("#### 🛠️ أدوات الصيانة ومزامنة الأرصدة")

      c1, c2 = st.columns(2)
      with c1:
        if st.button("🔄 تحديث البيانات ومزامنة السيرفر (Refresh)", type="secondary", use_container_width=True):
          st.cache_data.clear()
          if "db_loaded" in st.session_state:
            del st.session_state["db_loaded"]
          st.session_state["show_refresh_success"] = True
          st.rerun()

      with c2:
        if st.button("🧮 إعادة احتساب النقاط من السجل (تصحيح شامل)", type="primary", use_container_width=True):
          try:
            with st.spinner("جاري مراجعة السجلات وتصحيح أرصدة الطلاب..."):
              df_beh = fetch_safe("behavior")
              ws_st = get_gspread_client().worksheet("students")
              students_data = ws_st.get_all_records()
              true_scores = {}

              if not df_beh.empty:
                beh_id_col = df_beh.columns[0]
                beh_type_col = "type" if "type" in df_beh.columns else df_beh.columns[2]

                for _, row in df_beh.iterrows():
                  raw_id = str(row.get(beh_id_col, "")).strip().split(".")[0]
                  if not raw_id:
                    continue
                  match = re.search(r"\(([\+\-]?\d+)\)", str(row.get(beh_type_col, "")))
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

                ws_st.update(
                    f"{rowcol_to_a1(2, col_idx)}:{rowcol_to_a1(len(new_values) + 1, col_idx)}",
                    new_values,
                )

                st.cache_data.clear()
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                st.success("✅ تم تصحيح جميع الأرصدة بنجاح وفق السجلات الفعلية!")
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
        b_col1.download_button(
            label="📂 تنزيل بيانات الطلاب (Excel)",
            data=build_excel_bytes(df_st_full, sheet_name="Students"),
            file_name=f"students_backup_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
        )

      df_gr_full = st.session_state.df_grades.copy()
      if not df_gr_full.empty:
        b_col2.download_button(
            label="📊 تنزيل سجل الدرجات (Excel)",
            data=build_excel_bytes(df_gr_full, sheet_name="Grades"),
            file_name=f"grades_backup_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
        )

      st.divider()
      st.markdown(
          """
          <div style="background: rgba(239, 68, 68, 0.08); border: 1.5px dashed #EF4444; border-radius: 14px; padding: 15px; margin-bottom: 10px;">
              <h5 style="color: #EF4444; margin: 0 0 5px 0; font-weight: 900;">🚨 منطقة إجراءات حساسة (تصفير النقاط)</h5>
              <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">تصفير النقاط يقوم بإرجاع رصيد نقاط جميع الطلاب في الجدول إلى (0). هذا الإجراء يتطلب تأكيداً إضافياً لمنع الضغط بالخطأ.</p>
          </div>
          """,
          unsafe_allow_html=True,
      )

      if "confirm_reset_points" not in st.session_state:
        st.session_state.confirm_reset_points = False

      if not st.session_state.confirm_reset_points:
        if st.button("⚠️ طلب تصفير جميع النقاط (يتطلب تأكيداً)", type="secondary", use_container_width=True, key="btn_ask_reset_pts"):
          st.session_state.confirm_reset_points = True
          st.rerun()
      else:
        st.error("🚨 **تأكيد نهائي:** هل أنت متأكد تماماً من رغبتك في تصفير نقاط جميع الطلاب إلى (0)؟ لا يمكن التراجع عن هذا الإجراء إلا بإعادة الاحتساب من السجل.")
        conf_c1, conf_c2 = st.columns(2)
        if conf_c1.button("🧹 نعم، أؤكد تصفير جميع النقاط الآن", type="primary", use_container_width=True, key="btn_confirm_reset_yes"):
          try:
            ws = get_gspread_client().worksheet("students")
            d = ws.get_all_values()
            if len(d) > 1:
              headers = d[0]
              if "النقاط" in headers:
                col_idx = headers.index("النقاط") + 1
                ws.update(
                    range_name=f"{rowcol_to_a1(2, col_idx)}:{rowcol_to_a1(len(d), col_idx)}",
                    values=[[0]] * (len(d) - 1),
                )
                st.session_state.confirm_reset_points = False
                st.success("✅ تم تصفير جميع النقاط بنجاح")
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                st.cache_data.clear()
                st.rerun()
          except Exception as e:
            st.error(f"خطأ: {e}")

        if conf_c2.button("❌ إلغاء التصفير", type="secondary", use_container_width=True, key="btn_confirm_reset_no"):
          st.session_state.confirm_reset_points = False
          st.rerun()

    # --- 2. الهوية البصرية والإعدادات الأكاديمية (بدون شريط جانبي) ---
    with set_tabs[1]:
      s_map_academic = get_cached_settings()
      current_yr_init = str(st.session_state.get("current_year", "1448هـ")).strip()

      if "years_list" not in st.session_state:
        raw_years = s_map_academic.get("years_list", "")
        if raw_years:
          yrs = [y.strip() for y in str(raw_years).split(",") if y.strip()]
        else:
          yrs = ["1447هـ", "1448هـ"]
        if current_yr_init not in yrs:
          yrs.append(current_yr_init)
        st.session_state.years_list = sorted(list(set(yrs)))

      if "year_classes_map" not in st.session_state:
        raw_yc_json = s_map_academic.get("year_classes_map", "")
        loaded_yc = {}
        if raw_yc_json:
          try:
            loaded_yc = json.loads(raw_yc_json)
          except Exception:
            loaded_yc = {}
        if current_yr_init not in loaded_yc:
          loaded_yc[current_yr_init] = list(st.session_state.get("class_options", ["الأول"]))
        st.session_state.year_classes_map = loaded_yc

      if "class_stage_map" not in st.session_state:
        raw_cs_json = s_map_academic.get("class_stage_map", "")
        loaded_cs = {}
        if raw_cs_json:
          try:
            loaded_cs = json.loads(raw_cs_json)
          except Exception:
            loaded_cs = {}
        if not loaded_cs:
          for c_item in st.session_state.get("class_options", ["الأول"]):
            loaded_cs[c_item] = "متوسط" if "متوسط" in str(c_item) else "ابتدائي"
        st.session_state.class_stage_map = loaded_cs

      for c_curr in st.session_state.get("class_options", []):
        if c_curr not in st.session_state.class_stage_map:
          st.session_state.class_stage_map[c_curr] = "متوسط" if "متوسط" in str(c_curr) else "ابتدائي"

      def sync_academic_settings_to_db(target_year, target_period, target_theme, cs_map_dict, max_t, max_q):
        classes_list = list(cs_map_dict.keys())
        stages_list = list(dict.fromkeys(cs_map_dict.values()))
        cls_str = ",".join([c.strip() for c in classes_list if c.strip()])
        stg_str = ",".join([s.strip() for s in stages_list if s.strip()])
        yrs_str = ",".join(st.session_state.years_list)

        st.session_state.year_classes_map[target_year] = classes_list
        yc_json_str = json.dumps(st.session_state.year_classes_map, ensure_ascii=False)
        cs_json_str = json.dumps(cs_map_dict, ensure_ascii=False)

        ws_s = get_gspread_client().worksheet("settings")
        ws_s.batch_update([
            {"range": "A2:B2", "values": [["max_tasks", max_t]]},
            {"range": "A3:B3", "values": [["max_quiz", max_q]]},
            {"range": "A4:B4", "values": [["current_year", target_year]]},
            {"range": "A5:B5", "values": [["class_list", cls_str]]},
            {"range": "A6:B6", "values": [["stage_list", stg_str]]},
            {"range": "A7:B7", "values": [["current_period", target_period]]},
            {"range": "A8:B8", "values": [["app_theme", target_theme]]},
        ])

        all_s_recs = ws_s.get_all_records()
        keys_row_map = {str(r.get("key", "")).strip(): idx + 2 for idx, r in enumerate(all_s_recs)}

        for k_name, k_val in [("years_list", yrs_str), ("year_classes_map", yc_json_str), ("class_stage_map", cs_json_str)]:
          if k_name in keys_row_map:
            ws_s.update_cell(keys_row_map[k_name], 2, k_val)
          else:
            ws_s.append_row([k_name, k_val])

        st.session_state.max_tasks = max_t
        st.session_state.max_quiz = max_q
        st.session_state.current_year = target_year
        st.session_state.current_period = target_period
        st.session_state.class_options = classes_list
        st.session_state.stage_options = stages_list
        st.session_state.class_stage_map = cs_map_dict
        st.session_state.app_theme = target_theme
        get_cached_settings.clear()

      st.markdown("#### 🎨 المظهر والهوية البصرية")
      theme_options = list(themes.keys())
      current_theme_val = st.session_state.get("app_theme", "الرئيسي (الافتراضي)")
      th_index = theme_options.index(current_theme_val) if current_theme_val in theme_options else 0
      selected_theme = st.selectbox("اختر هوية المنصة (تطبق فوراً للجميع):", theme_options, index=th_index)

      st.markdown("---")
      st.markdown("#### ⚙️ العام الدراسي والفترة النشطة")

      col_yr_sel, col_yr_btns, col_per_sel = st.columns([2, 1.3, 2.2])

      with col_yr_sel:
        if st.session_state.current_year not in st.session_state.years_list:
          st.session_state.years_list.append(st.session_state.current_year)
        cy_idx = st.session_state.years_list.index(st.session_state.current_year)
        cy = st.selectbox("📅 العام الدراسي النشط:", st.session_state.years_list, index=cy_idx, key="main_tab_year_sel")

      with col_yr_btns:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        b_y1, b_y2 = st.columns(2)
        if b_y1.button("➕ عام", help="إضافة عام دراسي جديد", type="secondary", use_container_width=True, key="btn_open_new_yr"):
          st.session_state.show_add_year_inline = not st.session_state.get("show_add_year_inline", False)

        prev_yrs = [y for y in st.session_state.years_list if y != cy]
        if b_y2.button("📋 نسخ", help="نسخ صفوف العام السابق", type="secondary", disabled=(len(prev_yrs) == 0), use_container_width=True, key="btn_clone_inline"):
          last_yr = prev_yrs[-1]
          copied_cls = st.session_state.year_classes_map.get(last_yr, [])
          if copied_cls:
            for c_item in copied_cls:
              if c_item not in st.session_state.class_stage_map:
                st.session_state.class_stage_map[c_item] = "متوسط" if "متوسط" in str(c_item) else "ابتدائي"
            st.toast(f"✅ تم نسخ ({len(copied_cls)}) صفوف من عام {last_yr}!", icon="📋")
            st.rerun()

      with col_per_sel:
        current_period_val = st.session_state.get("current_period", "الفصل الأول - فترة أولى")
        period_options = [
            "الفصل الأول - فترة أولى",
            "الفصل الأول - فترة ثانية",
            "الفصل الثاني - فترة أولى",
            "الفصل الثاني - فترة ثانية",
        ]
        if current_period_val not in period_options:
          period_options.insert(0, current_period_val)
        cp_index = period_options.index(current_period_val)
        cp = st.selectbox("🗓️ الفترة الدراسية النشطة:", period_options, index=cp_index)

      if st.session_state.get("show_add_year_inline", False):
        with st.container(border=True):
          st.markdown("###### ➕ إنشاء عام دراسي جديد بصيغة موحدة")
          nums_in_years = [int(re.sub(r"\D", "", y)) for y in st.session_state.years_list if re.sub(r"\D", "", y)]
          next_hijri = (max(nums_in_years) + 1) if nums_in_years else 1449
          suggested_years = [f"{next_hijri}هـ", f"{next_hijri+1}هـ", f"{next_hijri-1}هـ"]

          ny_c1, ny_c2, ny_c3 = st.columns([2, 2, 1.2])
          new_yr_input = ny_c1.selectbox("اختر العام الجديد:", suggested_years, label_visibility="collapsed", key="new_yr_inline_sel")
          clone_prev = ny_c2.checkbox("📋 نسخ صفوف العام السابق تلقائياً", value=True, key="chk_clone_inline")

          if ny_c3.button("✅ تفعيل العام", type="primary", use_container_width=True, key="confirm_new_yr_inline"):
            if new_yr_input not in st.session_state.years_list:
              st.session_state.years_list.append(new_yr_input)
              st.session_state.years_list = sorted(list(set(st.session_state.years_list)))

            if not clone_prev:
              st.session_state.class_stage_map = {"الخامس/1": "ابتدائي"}

            st.session_state.show_add_year_inline = False
            sync_academic_settings_to_db(
                new_yr_input,
                cp,
                selected_theme,
                st.session_state.class_stage_map,
                st.session_state.get("max_tasks", 60),
                st.session_state.get("max_quiz", 40),
            )
            st.toast(f"✅ تم إنشاء وتفعيل العام الدراسي {new_yr_input} بنجاح!", icon="🎉")
            st.rerun()

      st.markdown("---")
      st.markdown("#### 🏫 إدارة الصفوف وربطها بالمراحل الدراسية")
      st.info("💡 كل صف يرتبط بمرحلته الدراسية مباشرة (ابتدائي / متوسط) ليقوم النظام بتحديد المرحلة وترويسة المدرسة تلقائياً.")

      STAGE_CHOICES = ["ابتدائي", "متوسط", "ثانوي", "عام"]

      ui_mode = st.radio(
          "طريقة عرض وتحرير الصفوف:",
          ["📊 الجدول التفاعلي الموحد (الصف + المرحلة)", "🏷️ نظام البطاقات والوسوم السريعة (Tags)"],
          horizontal=True,
          key="cls_editor_mode",
      )

      if ui_mode == "📊 الجدول التفاعلي الموحد (الصف + المرحلة)":
        df_unified = pd.DataFrame([
            {"اسم الصف": k, "المرحلة": v if v in STAGE_CHOICES else "ابتدائي"}
            for k, v in st.session_state.class_stage_map.items()
            if str(k).strip() not in ["", "nan", "None"]
        ])
        if df_unified.empty:
          df_unified = pd.DataFrame([{"اسم الصف": "الخامس/1", "المرحلة": "ابتدائي"}])

        edited_unified_df = st.data_editor(
            df_unified,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "اسم الصف": st.column_config.TextColumn(
                    "🏫 اسم الصف",
                    help="اكتب اسم الصف مثل: الخامس/1 أو أول متوسط/1",
                    required=True,
                ),
                "المرحلة": st.column_config.SelectboxColumn(
                    "🎓 المرحلة الدراسية (قائمة منسدلة)",
                    help="اختر المرحلة التي يتبع لها هذا الصف",
                    options=STAGE_CHOICES,
                    required=True,
                    default="ابتدائي",
                ),
            },
            key="de_unified_cls_stage_table",
        )

        # ✳️ فلترة محمية تمنع دخول أي صفوف فارغة أو None عند الضغط على +
        new_cs_map = {}
        for _, r_u in edited_unified_df.iterrows():
          raw_c = r_u.get("اسم الصف", "")
          raw_s = r_u.get("المرحلة", "ابتدائي")
          if pd.notna(raw_c):
            c_val = str(raw_c).strip().replace(",", "")
            if c_val and c_val.lower() not in ["nan", "none"]:
              s_val = str(raw_s).strip() if pd.notna(raw_s) and str(raw_s).strip().lower() not in ["", "nan", "none"] else "ابتدائي"
              new_cs_map[c_val] = s_val
        st.session_state.class_stage_map = new_cs_map

      else:
        with st.container(border=True):
          st.markdown("##### ➕ إضافة صف جديد مربوط بمرحلته")
          add_c1, add_c2, add_c3 = st.columns([2.2, 1.3, 1])
          new_cls_name = add_c1.text_input("اسم الصف الجديد:", placeholder="مثال: الخامس/1 أو أول متوسط/1", label_visibility="collapsed", key="inp_new_cls_tag")
          new_cls_stage = add_c2.selectbox("المرحلة:", STAGE_CHOICES, label_visibility="collapsed", key="sel_new_cls_stage")
          if add_c3.button("➕ ربط وإضافة", key="btn_add_cls_tag", use_container_width=True):
            clean_c = new_cls_name.strip().replace(",", "")
            if clean_c:
              st.session_state.class_stage_map[clean_c] = new_cls_stage
              st.rerun()

          st.markdown("---")
          curr_keys = [k for k in st.session_state.class_stage_map.keys() if str(k).strip().lower() not in ["", "nan", "none"]]
          selected_keys = st.multiselect(
              "الصفوف المعتمدة ومراحلها (احذف أي صف بالضغط على ×):",
              options=curr_keys,
              default=curr_keys,
              format_func=lambda k: f"{k} ⬅️ ({st.session_state.class_stage_map.get(k, 'ابتدائي')})",
              key="ms_unified_tags",
          )
          st.session_state.class_stage_map = {k: st.session_state.class_stage_map[k] for k in selected_keys}

      st.markdown("---")
      st.markdown("#### 📊 توزيع الدرجات العظمى")
      c1, c2 = st.columns(2)
      mt = c1.number_input("الدرجة العظمى (مشاركة ومهام)", 0, 100, st.session_state.get("max_tasks", 60))
      mq = c2.number_input("الدرجة العظمى (اختبارات)", 0, 100, st.session_state.get("max_quiz", 40))

      if st.button("💾 حفظ الإعدادات وتطبيق التغييرات", type="primary", use_container_width=True):
        if not st.session_state.class_stage_map:
          st.warning("⚠️ يجب إبقاء صف دراسي واحد على الأقل.")
        else:
          sync_academic_settings_to_db(cy, cp, selected_theme, st.session_state.class_stage_map, mt, mq)
          st.success(f"✅ تم الحفظ بنجاح! العام النشط: ({cy}) | الفترة: ({cp}) | عدد الصفوف: ({len(st.session_state.class_stage_map)})")
          st.rerun()

    # --- 3. استيراد البيانات + رفع بيانات أنماط التعلم ---
    with set_tabs[2]:
      import_sub = st.tabs([
          "🧠 رفع وتحديث بيانات أنماط التعلم",
          "📂 استيراد الطلاب أو الدرجات (Excel)",
      ])

      with import_sub[0]:
        st.markdown("#### 🧠 رفع وتحديث بيانات أنماط التعلم (VARK) دفعة واحدة")
        st.info("💡 يمكنك رفع ملف Excel يحتوي على نتائج استبيان أنماط التعلم (سواء من نماذج جوجل أو القالب الجاهز). سيقوم النظام بمطابقة الطلاب تلقائياً عبر **الرقم الأكاديمي (`id`)** أو **اسم الطالب (`name`)** وتحديث ملفاتهم.")

        df_curr_st = st.session_state.df_students.copy()
        if not df_curr_st.empty:
          template_ls_df = pd.DataFrame({
              "id": df_curr_st.iloc[:, 0].astype(str).str.split(".").str[0].str.strip(),
              "name": df_curr_st.get("name", ""),
              "class": df_curr_st.get("class", ""),
              "نمط التعلم": df_curr_st.get("نمط التعلم", ""),
          })
        else:
          template_ls_df = pd.DataFrame(columns=["id", "name", "class", "نمط التعلم"])

        st.download_button(
            label="📥 تحميل قالب أنماط التعلم بأسماء طلابك الحاليين (Excel)",
            data=build_excel_bytes(template_ls_df, sheet_name="Learning_Styles"),
            file_name=f"Learning_Styles_Template_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
        )

        st.markdown("---")
        up_ls = st.file_uploader("📤 ارفع ملف أنماط التعلم (Excel أو CSV):", type=["xlsx", "csv"], key="ls_file_uploader")

        if st.button("🚀 بدء مزامنة وتحديث أنماط التعلم", type="primary", use_container_width=True) and up_ls:
          try:
            with st.spinner("⏳ جاري تحليل الملف وتحديث أنماط تعلم الطلاب..."):
              if up_ls.name.endswith(".csv"):
                df_up_ls = pd.read_csv(up_ls).fillna("")
              else:
                df_up_ls = pd.read_excel(up_ls).fillna("")

              ws_st = get_gspread_client().worksheet("students")
              headers = ws_st.row_values(1)

              if "نمط التعلم" not in headers:
                ws_st.update_cell(1, len(headers) + 1, "نمط التعلم")
                headers.append("نمط التعلم")

              style_col_idx = headers.index("نمط التعلم") + 1
              all_st_records = ws_st.get_all_records()

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

              id_col_candidates = [
                  c for c in df_up_ls.columns
                  if str(c).strip().lower() in ["id", "student_id", "الرقم الأكاديمي", "رقم الهوية", "السجل المدني"]
              ]
              name_col_candidates = [
                  c for c in df_up_ls.columns
                  if "اسم" in str(c) or str(c).strip().lower() == "name"
              ]
              style_col_candidates = [
                  c for c in df_up_ls.columns
                  if "نمط" in str(c) or "style" in str(c).lower()
              ]

              id_col_ls = id_col_candidates[0] if id_col_candidates else None
              name_col_ls = name_col_candidates[0] if name_col_candidates else None
              style_col_ls = style_col_candidates[0] if style_col_candidates else df_up_ls.columns[-1]

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
                  cells_to_update.append(Cell(row=target_row, col=style_col_idx, value=raw_style))
                  updated_count += 1

              if cells_to_update:
                ws_st.update_cells(cells_to_update)
                st.success(f"✅ تم تحديث أنماط التعلم لـ ({updated_count}) طالب بنجاح!")
                if "db_loaded" in st.session_state:
                  del st.session_state["db_loaded"]
                fetch_safe.clear()
                st.rerun()
              else:
                st.warning("⚠️ لم يتم العثور على طلاب مطابقين أو أن حقل 'نمط التعلم' فارغ في الملف المرفوع.")
          except Exception as e:
            st.error(f"❌ حدث خطأ أثناء رفع أنماط التعلم: {e}")

      with import_sub[1]:
        st.info("📌 **دليل رصد ورفع الدرجات في المنصة:** \n\n* **عمود (p1):** مخصص لـ **المشاركة والمهام**.\n* **عمود (p2):** مخصص لـ **الاختبارات القصيرة**.")
        up = st.file_uploader("رفع ملف Excel للطلاب أو الدرجات", type=["xlsx"], key="std_gr_up")
        ts = st.radio(
            "نوع البيانات المرفوعة",
            ["students", "grades"],
            horizontal=True,
            format_func=lambda x: "بيانات الطلاب" if x == "students" else "الدرجات الأكاديمية",
        )
        if st.button("🚀 بدء المزامنة السريعة", type="primary", use_container_width=True) and up:
          try:
            with st.spinner("جاري معالجة ورفع البيانات دفعة واحدة..."):
              df = pd.read_excel(up).fillna("").dropna(how="all")
              ws = get_gspread_client().worksheet(ts)

              hd = ws.row_values(1)
              if ts == "grades" and "period" not in hd:
                ws.update_cell(1, len(hd) + 1, "period")
                hd.append("period")

              records = ws.get_all_records()
              if ts == "grades":
                existing_keys = set(
                    f"{str(r.get('student_id', '')).strip().split('.')[0]}_{str(r.get('period', 'الفصل الأول - فترة أولى')).strip()}"
                    for r in records
                )
              else:
                existing_keys = set(str(r.get("id", "")).strip().split(".")[0] for r in records)

              new_rows_to_append = []
              progress_bar = st.progress(0)
              cp = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()

              for idx, row in df.iterrows():
                d = row.to_dict()
                raw_id = str(d.get("student_id", d.get("id", ""))).strip().split(".")[0]
                if not raw_id or raw_id == "0" or raw_id.lower() == "nan":
                  continue

                if ts == "grades":
                  p1_in = int(pd.to_numeric(d.get("p1", 0), errors="coerce") or 0)
                  p2_in = int(pd.to_numeric(d.get("p2", 0), errors="coerce") or 0)
                  d.update({
                      "student_id": raw_id,
                      "p1": p1_in,
                      "p2": p2_in,
                      "perf": p1_in + p2_in,
                      "date": str(datetime.date.today()),
                      "period": str(d.get("period", cp)).strip() or cp,
                  })
                  if "id" in d:
                    del d["id"]
                  check_key = f"{raw_id}_{d['period']}"
                else:
                  d["id"] = raw_id
                  d["الجوال"] = clean_phone_number(d.get("الجوال", ""))
                  if "النقاط" not in d or str(d.get("النقاط", "")).strip() == "":
                    d["النقاط"] = 0
                  check_key = raw_id

                if check_key not in existing_keys:
                  new_rows_to_append.append([str(d.get(k, "")) for k in hd])

                progress_bar.progress(min((idx + 1) / len(df), 1.0))

              if new_rows_to_append:
                ws.append_rows(new_rows_to_append)
                st.success(f"✅ تم إضافة {len(new_rows_to_append)} سجل جديد بنجاح لـ ({cp})!")
              else:
                st.info(f"💡 جميع البيانات المرفوعة موجودة مسبقاً في ({cp})، لم يتم إضافة جديد.")

              if "db_loaded" in st.session_state:
                del st.session_state["db_loaded"]
              fetch_safe.clear()
              st.rerun()
          except Exception as e:
            st.error(f"حدث خطأ أثناء المزامنة: {e}")

        st.divider()
        c1, c2 = st.columns(2)
        empty_st_tmpl = pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط", "نمط التعلم"])
        c1.download_button(
            "📥 قالب فارغ (طلاب)",
            data=build_excel_bytes(empty_st_tmpl, sheet_name="Students_Template"),
            file_name="students_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
        )
        empty_gr_tmpl = pd.DataFrame(columns=["student_id", "p1", "p2"])
        c2.download_button(
            "📥 قالب فارغ (درجات)",
            data=build_excel_bytes(empty_gr_tmpl, sheet_name="Grades_Template"),
            file_name="grades_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
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
          nrole_label = st.selectbox("نوع الحساب والصلاحية", ["👨‍🏫 معلم (صلاحيات كاملة)", "👁️ إدارة (مشاهد وقراءة فقط)"])
          if st.form_submit_button("إضافة المستخدم", type="primary", use_container_width=True):
            if nu and np:
              role_val = "teacher" if "معلم" in nrole_label else "viewer"
              safe_append_row(
                  "users",
                  {
                      "username": nu.strip(),
                      "password_hash": hashlib.sha256(np.encode()).hexdigest(),
                      "role": role_val,
                  },
              )
              st.success(f"✅ تمت إضافة الحساب ({nu}) بنجاح كـ {role_val}.")
              fetch_safe.clear()
            else:
              st.warning("الرجاء إكمال البيانات.")

      with u_tabs[1]:
        with st.form("chg_pass"):
          df_u_edit = fetch_safe("users")
          if not df_u_edit.empty:
            target_u = st.selectbox("اختر المستخدم لتعديل رقمه السري:", df_u_edit["username"].tolist())
            npwd = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("تحديث كلمة المرور", type="primary", use_container_width=True):
              if npwd:
                idx = df_u_edit[df_u_edit["username"] == target_u].index[0] + 2
                get_gspread_client().worksheet("users").update_cell(idx, 2, hashlib.sha256(npwd.encode()).hexdigest())
                st.success(f"✅ تم تحديث كلمة المرور لـ ({target_u}).")
                fetch_safe.clear()
              else:
                st.warning("الرجاء إدخال كلمة المرور الجديدة.")
          else:
            st.info("لا يوجد مستخدمين بعد.")

      with u_tabs[2]:
        df_u_del = fetch_safe("users")
        if not df_u_del.empty:
          del_u = st.selectbox("اختر المستخدم المراد حذفه:", [""] + df_u_del["username"].tolist())
          if st.button("🗑️ حذف المستخدم نهائياً", type="primary", use_container_width=True):
            if del_u:
              if del_u == st.session_state.username:
                st.error("⚠️ لا يمكنك حذف حسابك الحالي!")
              else:
                idx = df_u_del[df_u_del["username"] == del_u].index[0] + 2
                get_gspread_client().worksheet("users").delete_rows(int(idx))
                st.success(f"✅ تم حذف المستخدم ({del_u}).")
                fetch_safe.clear()
                st.rerun()
            else:
              st.warning("الرجاء اختيار مستخدم للحذف.")

      with u_tabs[3]:
        df_users_log = fetch_safe("users")
        if not df_users_log.empty:
          if "last_login" in df_users_log.columns:
            disp_df = df_users_log[["username", "role", "last_login"]].rename(
                columns={"username": "المستخدم", "role": "الصلاحية", "last_login": "آخر تسجيل دخول"}
            )
            disp_df["الصلاحية"] = disp_df["الصلاحية"].replace({"teacher": "👨‍🏫 معلم", "viewer": "👁️ إدارة"})
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
    if st.button("🚪 تأكيد تسجيل الخروج", type="primary", use_container_width=True):
      st.session_state.role = None
      if "db_loaded" in st.session_state:
        del st.session_state["db_loaded"]
      st.rerun()

  show_footer()

# ==========================================
# 👨‍🎓 12. واجهة الطالب الكاملة (محدثة ومضبوطة المحاذاة والـ PDF المخبأ في الكاش)
# ==========================================
if st.session_state.role == "student":
  sid = str(st.session_state.get("username", "")).strip()
  df_st = st.session_state.df_students.copy()
  df_gr = st.session_state.df_grades.copy()
  df_beh = st.session_state.df_behavior.copy()
  df_ann = fetch_safe("exams")

  if not df_st.empty:
    df_st["clean_id"] = df_st.iloc[:, 0].astype(str).str.split(".").str[0].str.strip()
    info = df_st[df_st["clean_id"] == sid]
  else:
    info = pd.DataFrame()

  if not info.empty:
    s_dat = info.iloc[0]
    s_nm = s_dat.get("name", "طالب")
    s_cls = str(s_dat.get("class", "")).strip()
    pts = int(pd.to_numeric(s_dat.get("النقاط", 0), errors="coerce") or 0)

    # 1. إشعار التعاميم العاجلة (يدعم الفصول المتعددة)
    if not df_ann.empty:
      df_ann["عاجل"] = df_ann["عاجل"].astype(str).str.strip()
      def is_cls_targeted(cell_val):
        targets = [x.strip() for x in str(cell_val).replace("،", ",").split(",") if x.strip()]
        return "الكل" in targets or s_cls in targets
      urg = df_ann[(df_ann["عاجل"] == "نعم") & (df_ann["الصف"].apply(is_cls_targeted))]
      if not urg.empty:
        u = urg.tail(1).iloc[0]
        link_text = str(u.get("الرابط", ""))
        link_display = (
            f"<a href='{link_text}' target='_blank' style='color:{danger_color}; text-decoration:underline;'>اضغط هنا</a>"
            if link_text.startswith("http")
            else link_text
            if link_text.lower() != "none"
            else ""
        )
        st.markdown(
            f"<div class='urgent-box'>🚨 {u.get('العنوان')}<br><small style='color:{danger_color}'>{link_display}</small></div>",
            unsafe_allow_html=True,
        )

    # 2. إشعار المخالفات السلوكية والغياب لولي الأمر
    if not df_beh.empty:
      df_beh["clean_id"] = df_beh.iloc[:, 0].astype(str).str.split(".").str[0]
      my_beh_alerts = df_beh[df_beh["clean_id"] == sid]

      if not my_beh_alerts.empty:
        last_record = my_beh_alerts.iloc[-1]
        b_type = str(last_record.get("type", ""))
        if any(k in b_type for k in ["-", "سلبي", "تنبيه", "غائب", "عدم", "نقص", "تأخر"]):
          st.markdown(
              f"""
              <div class="urgent-box" style="margin-bottom: 15px; padding-bottom: 10px;">
                  <div style="font-size: 1.1rem; font-weight: 900; margin-bottom: 5px;">⚠️ إشعار سلوكي لولي الأمر</div>
                  <div style="color: var(--text-color); margin: 0; font-weight: bold; font-size: 1.05rem;">{b_type}</div>
                  <span style="color: #94A3B8; font-size: 0.9rem; display:block; margin: 6px 0 10px 0;">التفاصيل: {last_record.get('note', 'لا توجد تفاصيل')} | التاريخ: {last_record.get('date', '')}</span>
                  <div style="background-color: rgba(239, 68, 68, 0.15); padding: 6px; border-radius: 8px; font-size: 0.85rem; color: #EF4444;">
                      👇 <b>فضلاً:</b> نرجو الانتقال إلى تبويب <b>(📝 السلوك)</b> بالأسفل للاطلاع على السجل التفصيلي.
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )

    # 3. بطاقة الطالب المنسقة وبطاقة النقاط
    st.markdown(
        f"""
        <div class="welcome-card" style="text-align: right; direction: rtl; padding: 22px 20px;">
            <div style="color: #FFFFFF; font-size: 1.45rem; font-weight: 900; line-height: 1.4; margin-bottom: 14px; text-align: right;">
                👋 أهلاً بك، {s_nm}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: flex-start; direction: rtl;">
                <div style="background: rgba(255, 255, 255, 0.2); padding: 6px 14px; border-radius: 10px; color: #FFFFFF; font-weight: 800; font-size: 0.92rem; white-space: nowrap;">
                    🏫 الصف: {s_cls}
                </div>
                <div style="background: rgba(15, 23, 42, 0.28); border: 1px solid rgba(255, 255, 255, 0.25); padding: 6px 14px; border-radius: 10px; color: #FFFFFF; font-weight: 800; font-size: 0.92rem; white-space: nowrap; direction: ltr;">
                    🆔 ID: {sid}
                </div>
            </div>
        </div>
        <div class="points-banner">
            <div style="margin:0; opacity:0.95; font-size:1rem; font-weight:800;">رصيد النقاط الحالي</div>
            <div style="margin:4px 0; font-size:3.6rem; font-weight:900; line-height:1.1; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">{pts}</div>
            <div style="margin:0; font-size:0.9rem; font-weight:800;">استمر في التفوق!</div>
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

    # --- تبويب 1: التنبيهات ---
    with tabs[0]:
      st.caption("التعاميم والتنبيهات الموجهة لصفك")
      if not df_ann.empty:
        def match_student_class(val):
          targets = [x.strip() for x in str(val).replace("،", ",").split(",") if x.strip()]
          return "الكل" in targets or s_cls in targets

        anns = df_ann[df_ann["الصف"].apply(match_student_class)]
        if not anns.empty:
          for _, r in anns.iloc[::-1].iterrows():
            row_link = str(r.get("الرابط", ""))
            row_link_display = (
                f"<a href='{row_link}' target='_blank' style='color:{accent_color}; text-decoration:underline; font-weight:bold;'>اضغط هنا للفتح 🔗</a>"
                if row_link.startswith("http")
                else row_link
                if row_link.lower() != "none"
                else ""
            )
            st.markdown(
                f"""
                <div class="student-list-card">
                    <div class="student-card-header">
                        <div class="student-card-title" style="color: var(--text-color);">📢 {r.get('العنوان')}</div>
                        <div class="student-card-date" style="color: {accent_color};">{r.get('التاريخ')}</div>
                    </div>
                    <div class="student-card-body" style="color: #94A3B8; font-weight: 600;">{row_link_display}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
          st.info("لا توجد تنبيهات حالياً.")
      else:
        st.info("لا توجد تنبيهات حالياً.")

    # --- تبويب 2: السلوك ---
    with tabs[1]:
      st.caption("سجل السلوك والملاحظات")
      if not df_beh.empty:
        df_beh["clean_id"] = df_beh.iloc[:, 0].astype(str).str.split(".").str[0]
        nts = df_beh[df_beh["clean_id"] == sid].copy()

        if not nts.empty:
          nts = nts.iloc[::-1]
          nts["date_parsed"] = pd.to_datetime(nts["date"], errors="coerce")
          nts = nts.sort_values(by="date_parsed", ascending=False, kind="mergesort")

          for _, n in nts.iterrows():
            b_t_str = str(n.get("type", ""))
            if "-" in b_t_str or "سلبي" in b_t_str:
              color = danger_color
            elif "(0)" in b_t_str or "غائب" in b_t_str or "تنبيه" in b_t_str:
              color = warning_color
            else:
              color = success_color
            note_txt = str(n.get("note", "")).strip()
            note_html = f"<div class='student-card-body' style='color: var(--text-color); font-weight: 700;'>{note_txt}</div>" if note_txt else ""
            st.markdown(
                f"""
                <div class="student-list-card" style="border-right: 5px solid {color};">
                    <div class="student-card-header">
                        <div class="student-card-title" style="color: {color};">{n.get('type')}</div>
                        <div class="student-card-date" style="color: #94A3B8;">{n.get('date')}</div>
                    </div>
                    {note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
          st.success("🌟 سجلك نظيف تماماً!")
      else:
        st.success("🌟 سجلك نظيف تماماً!")

    # --- تبويب 3: الدرجات والشهادة (محمية بالكاش السريع) ---
    with tabs[2]:
      cp = st.session_state.get("current_period", "الفصل الأول - فترة أولى").strip()
      st.caption(f"درجاتي الأكاديمية - {cp}")

      if not df_gr.empty:
        df_gr["clean_id"] = df_gr.iloc[:, 0].astype(str).str.split(".").str[0]
        if "period" not in df_gr.columns:
          df_gr["period"] = "الفصل الأول - فترة أولى"
        df_gr["period"] = df_gr["period"].replace(["", None, "nan", "NaN"], "الفصل الأول - فترة أولى").astype(str).str.strip()

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
              <div class='mobile-list-item' style="direction: rtl;">
                  <span style="font-weight:800;">📝 المشاركة والواجبات</span>
                  <div style="direction: ltr;">
                      <span style='font-size:1.4rem; font-weight:900; color:{accent_color};'>{g.get('p1')}</span> 
                      <span style='color:#94A3B8; font-size:0.9rem; font-weight:bold;'>/ {st.session_state.max_tasks}</span>
                  </div>
              </div>
              <div class='mobile-list-item' style="direction: rtl;">
                  <span style="font-weight:800;">✍️ الاختبارات القصيرة</span>
                  <div style="direction: ltr;">
                      <span style='font-size:1.4rem; font-weight:900; color:{accent_color};'>{g.get('p2')}</span> 
                      <span style='color:#94A3B8; font-size:0.9rem; font-weight:bold;'>/ {st.session_state.max_quiz}</span>
                  </div>
              </div>
              <div class='mobile-list-item' style='background:var(--secondary-background-color); border-color:{accent_color}; display:flex; flex-direction:column; align-items:flex-start; direction: rtl;'>
                  <div style="width:100%; display:flex; justify-content:space-between; align-items:center;">
                      <span style="color:{accent_color}; font-weight:900;">🏆 المجموع النهائي ({cp})</span>
                      <div style="direction: ltr;">
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
            st.success("🎉 مبروك! لتفوقك وحصولك على درجة الامتياز، يمكنك الآن تنزيل شهادة التفوق بصيغة PDF جاهزة للطباعة.")
            school_st = get_school_name_dynamic(s_cls).replace("<br>", " - ")
            star_svg = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDE1LjA5IDguMjYgMjIgOS4yNyAxNyAxNC4xNCAxOC4xOCAyMS4wMiAxMiAxNy43NyA1LjgyIDIxLjAyIDcgMTQuMTQgMiA5LjI3IDguOTEgOC4yNiAxMiAyIiBmaWxsPSIjYjY4YTM2IiAvPjwvc3ZnPg=="

            certificate_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>شهادة تفوق - {s_nm}</title>
    <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        @page {{ size: 297mm 210mm; margin: 0mm !important; }}
        * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        html, body {{ margin: 0 !important; padding: 0 !important; width: 297mm; height: 210mm; background-color: #ffffff; font-family: 'Cairo', sans-serif; overflow: hidden; }}
        .cert-page {{ width: 297mm; height: 210mm; padding: 8mm; background: #ffffff; position: relative; page-break-after: avoid; page-break-before: avoid; page-break-inside: avoid; }}
        .border-outer {{ border: 12px solid #193b68; width: 100%; height: 100%; padding: 5px; position: relative; }}
        .border-inner {{ border: 3px solid #b68a36; width: 100%; height: 100%; padding: 18px 35px; text-align: center; position: relative; background-color: #ffffff; background-image: radial-gradient(#e2e8f0 1px, transparent 1px); background-size: 22px 22px; }}
        .corner {{ position: absolute; width: 28px; height: 28px; border: 4px solid #b68a36; }}
        .tl {{ top: -7px; left: -7px; border-right: none; border-bottom: none; }}
        .tr {{ top: -7px; right: -7px; border-left: none; border-bottom: none; }}
        .bl {{ bottom: -7px; left: -7px; border-right: none; border-top: none; }}
        .br {{ bottom: -7px; right: -7px; border-left: none; border-top: none; }}
        .top-table {{ width: 100%; border-collapse: collapse; margin-bottom: 4px; font-size: 14px; font-weight: 700; color: #193b68; }}
        h1 {{ font-family: 'Aref Ruqaa', serif; font-size: 60px; color: #b68a36; margin: 0 0 4px 0; font-weight: bold; line-height: 1.15; }}
        h2 {{ font-family: 'Cairo', sans-serif; font-size: 28px; color: #193b68; margin: 0 0 14px 0; font-weight: 900; }}
        .star-icon {{ width: 26px; height: 26px; vertical-align: middle; margin: 0 8px; }}
        p.intro {{ font-size: 21px; color: #193b68; margin: 0 0 8px 0; font-weight: 700; }}
        .student-name {{ font-size: 46px; font-weight: 900; color: #d32f2f; margin: 6px auto 14px auto; display: inline-block; border-bottom: 3px solid #b68a36; padding: 0 35px 6px 35px; line-height: 1.2; }}
        .reason-container {{ margin: 8px 0 18px 0; }}
        p.reason {{ font-size: 22px; font-weight: 700; color: #334155; line-height: 1.65; margin: 0; }}
        .footer-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 12px; direction: rtl; }}
        .footer-table td {{ width: 33.33%; vertical-align: middle; text-align: center !important; color: #193b68; padding: 0 10px; }}
        .sig-title {{ font-size: 20px; font-weight: 800; display: block; text-align: center; }}
        .sig-line {{ display: inline-block !important; width: 160px; height: 0px; border-bottom: 2px solid #b68a36; margin: 8px 0; }}
        .sig-name {{ font-family: 'Aref Ruqaa', serif; font-size: 32px; color: #193b68; font-weight: bold; display: block; text-align: center; line-height: 1.1; }}
        .date-val {{ font-size: 20px; font-weight: 800; color: #1e293b; display: block; text-align: center; margin-top: 4px; }}
        .stamp-circle {{ display: inline-block !important; width: 128px; height: 128px; border: 3px dashed #d32f2f; border-radius: 50%; transform: rotate(-14deg); color: #d32f2f; text-align: center; opacity: 0.88; padding-top: 18px; position: relative; background-color: rgba(255, 255, 255, 0.85); }}
        .stamp-inner {{ position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px; border: 1px solid #d32f2f; border-radius: 50%; }}
    </style>
</head>
<body>
    <div class="cert-page">
        <div class="border-outer">
            <div class="border-inner">
                <div class="corner tl"></div><div class="corner tr"></div>
                <div class="corner bl"></div><div class="corner br"></div>

                <table class="top-table">
                    <tr>
                        <td style="text-align: right; width: 50%; line-height: 1.5;">المملكة العربية السعودية - وزارة التعليم<br>{school_st}</td>
                        <td style="text-align: left; width: 50%; line-height: 1.5;">العام الدراسي: {st.session_state.get('current_year', '1447هـ')}<br>{cp}</td>
                    </tr>
                </table>

                <h1>شهادة شكر وتقدير</h1>
                <h2>
                    <img src="{star_svg}" class="star-icon">
                    وسام التميز الأكاديمي
                    <img src="{star_svg}" class="star-icon">
                </h2>

                <p class="intro">يتقدم الأستاذ/ <strong>زياد المعمري</strong> بوافر الشكر والتقدير للطالب المبدع والمتألق:</p>
                <div class="student-name">{s_nm}</div>

                <div class="reason-container">
                    <p class="reason">وذلك نظير تفوقه العلمي وحصوله على تقدير <b style="color:#d32f2f;">ممتاز</b> في مادة اللغة الإنجليزية.</p>
                    <p class="reason">متمنين له دوام التوفيق ومزيداً من التألق والنجاح.</p>
                </div>

                <table class="footer-table">
                    <tr>
                        <td>
                            <span class="sig-title">تاريخ الإصدار</span>
                            <span class="sig-line"></span>
                            <span class="date-val">{datetime.date.today().strftime('%Y-%m-%d')}</span>
                        </td>
                        <td>
                            <div class="stamp-circle">
                                <div class="stamp-inner"></div>
                                <div style="font-size: 15px; font-weight: 900; line-height: 1.1;">وسام</div>
                                <div style="font-family: 'Aref Ruqaa', serif; font-size: 30px; font-weight: bold; line-height: 1.2;">ختم التميز</div>
                                <div style="font-size: 13px; font-weight: 800; line-height: 1.1;">الأكاديمي</div>
                            </div>
                        </td>
                        <td>
                            <span class="sig-title">توقيع المعلم</span>
                            <span class="sig-line"></span>
                            <span class="sig-name">زياد المعمري</span>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

            try:
              pdf_bytes = generate_pdf_bytes_cached(certificate_html)
              st.download_button(
                  label="📥 تنزيل شهادة التفوق (PDF جاهز للطباعة)",
                  data=pdf_bytes,
                  file_name=f"Certificate_{sid}_{s_nm}.pdf",
                  mime="application/pdf",
                  type="primary",
                  use_container_width=True,
              )
            except Exception:
              st.download_button(
                  label="📜 تنزيل شهادة التفوق (جاهزة للطباعة A4)",
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

    # --- تبويب 4: لوحة الشرف ---
    with tabs[3]:
      st.caption("لوحة الشرف (أفضل 10 طلاب في المنصة)")
      df_st["p_num"] = pd.to_numeric(df_st["النقاط"], errors="coerce").fillna(0)
      active_students = df_st[df_st["p_num"] > 0]

      if not active_students.empty:
        for i, (_, r) in enumerate(active_students.sort_values("p_num", ascending=False).head(10).iterrows(), 1):
          ic = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
          sty = f"border:2px solid {warning_color}; background:rgba(245, 158, 11, 0.1);" if str(r["clean_id"]) == sid else ""
          st.markdown(
              f"""
              <div class='mobile-list-item' style='{sty} direction: rtl;'>
                  <div style='display:flex; align-items:center; gap:10px;'>
                      <span style='font-weight:900; font-size:1.2rem; min-width:40px; display:inline-block; text-align:center; white-space:nowrap;'>{ic}</span>
                      <span style='font-weight:bold; text-align:right;'>{r['name']}</span>
                  </div>
                  <span style='color:{warning_color}; font-weight:900; font-size:1.1rem; white-space:nowrap;'>{int(r['p_num'])} نقطة</span>
              </div>
              """,
              unsafe_allow_html=True,
          )
      else:
        st.info("لوحة الشرف فارغة حالياً. كن أنت أول المبادرين وتصدر القائمة! 🚀")

    # --- تبويب 5: نمط التعلم ---
    with tabs[4]:
      st.subheader("🧠 اكتشف نمط تعلمك")
      st.caption("أجب عن هذه المواقف السبعة لنعرف الطريقة التي تفضلها وتتفوق بها في التعلم!")

      current_style = ""
      if "نمط التعلم" in df_st.columns:
        val = df_st.loc[df_st["clean_id"] == sid, "نمط التعلم"].values
        if len(val) > 0 and pd.notna(val[0]) and str(val[0]).strip() not in ["", "nan", "None"]:
          current_style = str(val[0]).strip()

      if current_style:
        color = (
            "#3B82F6" if "بصري" in current_style
            else "#10B981" if "سمعي" in current_style
            else "#F59E0B" if "حركي" in current_style
            else "#8B5CF6"
        )
        st.markdown(
            f"""
            <div style='background-color:{color}20; border:2px solid {color}; padding:25px; border-radius:16px; text-align:center; margin-top:15px;'>
                <div style='font-size:45px; margin-bottom:10px;'>{current_style.split()[-1] if len(current_style.split())>1 else '🎯'}</div>
                <div style='color:{color}; font-size:1.4rem; margin-bottom:8px; font-weight:900;'>أنت متعلم {current_style.replace('👀', '').replace('👂', '').replace('✋', '').replace('🌟', '').strip()}</div>
                <p style='color:#94A3B8; font-size:14px; margin:0; font-weight:bold;'>تم حفظ نمط تعلمك في ملفك الأكاديمي بنجاح.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
      else:
        with st.form("learning_style_quiz"):
          st.info("تخيل نفسك في هذه المواقف، واختر الإجابة التي تشبهك أكثر:")

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

          if st.form_submit_button("🚀 إرسال الإجابات واكتشاف نمطي", type="primary", use_container_width=True):
            answers = [q1, q2, q3, q4, q5, q6, q7]
            if None in answers:
              st.warning("⚠️ عذراً يا بطل، يجب عليك اختيار إجابة لجميع المواقف السبعة قبل إرسال النتيجة.")
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
                ws = get_gspread_client().worksheet("students")
                headers = ws.row_values(1)
                if "نمط التعلم" not in headers:
                  ws.update_cell(1, len(headers) + 1, "نمط التعلم")
                  headers.append("نمط التعلم")

                style_col_idx = headers.index("نمط التعلم") + 1
                cell = ws.find(sid)
                if cell:
                  ws.update_cell(cell.row, style_col_idx, final_style)
                  st.success(f"🎉 رائع! تم حفظ النتيجة. نمط تعلمك هو: {final_style}")
                  if "db_loaded" in st.session_state:
                    del st.session_state["db_loaded"]
                  fetch_safe.clear()
                  st.rerun()
              except Exception as e:
                st.error(f"❌ حدث خطأ أثناء حفظ النتيجة، حاول مرة أخرى. ({e})")

    # --- تبويب 6: حسابي والخروج ---
    with tabs[5]:
      st.caption("إدارة الملف الشخصي وتسجيل الخروج")
      with st.form("my_profile"):
        nm = st.text_input("📧 البريد الإلكتروني", s_dat.get("الإيميل", ""))
        np = st.text_input("📱 رقم الجوال", s_dat.get("الجوال", ""))
        if st.form_submit_button("💾 تحديث بياناتي", type="primary", use_container_width=True):
          try:
            fp = clean_phone_number(np) if np else ""
            ws = get_gspread_client().worksheet("students")
            c = ws.find(sid)
            if c:
              h = ws.row_values(1)
              if "الإيميل" in h and "الجوال" in h:
                ws.update_cell(c.row, h.index("الإيميل") + 1, nm)
                ws.update_cell(c.row, h.index("الجوال") + 1, fp)
                st.success("✅ تم تحديث بيانات التواصل بنجاح")
                fetch_safe.clear()
              else:
                st.error("خطأ هيكلي في الأعمدة")
          except Exception as e:
            st.error(f"خطأ: {e}")

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("🚪 تسجيل الخروج من حسابي", type="secondary", use_container_width=True):
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
