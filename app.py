import streamlit as st
import pandas as pd
import gspread
import urllib.parse
import datetime
import hashlib
import io
import re
from google.oauth2.service_account import Credentials
from weasyprint import HTML
import math

# ==========================================
# ⚙️ 1. إعدادات النظام
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 تعريف الألوان (الثيم المؤسسي الحديث حسب التصميم الجديد) ---
main_bg = "#F8FAFC"
card_bg = "#FFFFFF"
text_color = "#0F172A"
sub_text = "#64748B"
border_color = "#E2E8F0"
primary_color = "#2563EB"
accent_color = "#1E40AF"
success_color = "#10B981"
warning_color = "#F59E0B"
danger_color = "#EF4444"
header_grad = "linear-gradient(135deg, #1E40AF 0%, #2563EB 100%)"
shadow_val = "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)"

# --- [الدوال المساعدة والاتصال الذكي] ---

@st.cache_resource(ttl=2700) 
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e: 
        st.error(f"⚠️ خطأ اتصال بسيرفر جوجل: {e}")
        return None

sh = get_gspread_client()

def normalize_arabic(text):
    if not isinstance(text, str): text = str(text)
    text = re.sub(r'[أإآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    return text.strip()

def clean_phone_number(phone):
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def get_professional_msg(name, b_type, b_desc, date):
    msg = (f"🔔 *إشعار من منصة الأستاذ زياد*\n👤 *الطالب:* {name}\n📍 *الملاحظة:* {b_type}\n📝 *التفاصيل:* {b_desc if b_desc else 'متابعة'}\n📅 *التاريخ:* {date}")
    return urllib.parse.quote(msg)

def show_footer():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: {sub_text}; padding: 20px; border-top: 1px solid {border_color};'>
        <p style='margin-bottom: 10px; font-size: 0.9rem;'>جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية © 2026</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.link_button("📢 تليجرام الإدارة", "https://t.me/@ZiyadAlmoami", use_container_width=True)
    c2.link_button("💬 واتساب المعلم", "https://wa.me/966534900049", use_container_width=True)
    c3.link_button("📧 البريد الإلكتروني", "mailto:ziad.platform.alerts@gmail.com", use_container_width=True)

@st.cache_data(ttl=300)
def fetch_safe(worksheet_name):
    try:
        current_sh = get_gspread_client()
        if not current_sh: return pd.DataFrame()
        ws = current_sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty: df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
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

# --- تحميل الإعدادات ---
# --- تحميل الإعدادات ---
if "class_options" not in st.session_state:
    try:
        sett = sh.worksheet("settings").get_all_records()
        s_map = {row['key']: row['value'] for row in sett}
        st.session_state.max_tasks = int(s_map.get('max_tasks', 60))
        st.session_state.max_quiz = int(s_map.get('max_quiz', 40))
        st.session_state.current_year = str(s_map.get('current_year', '1447هـ'))
        
        # ✳️ السطر الجديد: جلب الفترة النشطة من الإعدادات في جوجل شيت
        st.session_state.current_period = str(s_map.get('current_period', 'الفترة الأولى'))
        
        st.session_state.class_options = [x.strip() for x in str(s_map.get('class_list', 'الأول')).split(',') if x.strip()]
        st.session_state.stage_options = [x.strip() for x in str(s_map.get('stage_list', 'ابتدائي')).split(',') if x.strip()]
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        
        # ✳️ السطر الجديد: القيمة الافتراضية في حال كانت قاعدة البيانات فارغة
        st.session_state.current_period = "الفترة الأولى"
        
        st.session_state.class_options = ["الأول"]; st.session_state.stage_options = ["ابتدائي"]

if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = None

# ==========================================
# 🎨 2. التصميم (CSS)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
    
    section[data-testid="stSidebar"] {{ display: none; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    html, body, [data-testid="stAppViewContainer"] {{ 
        font-family: 'Tajawal', sans-serif !important; 
        direction: RTL; text-align: right; 
        background-color: {main_bg} !important; color: {text_color} !important; 
    }}
    
    .block-container {{ padding-top: 1rem !important; padding-bottom: 5rem; max-width: 1000px; }}
    
    .header-container {{
        background: {header_grad};
        padding: 70px 20px 40px 20px; /* ✳️ تم زيادة المساحة العلوية لتجنب قص القبعة */
        border-radius: 0 0 40px 40px;
        margin: -1rem -5rem 30px -5rem;
        box-shadow: 0 10px 30px -10px rgba(37, 99, 235, 0.4);
        color: white; 
        text-align: center;
    }}
    
    .title-wrapper {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px; 
        margin-bottom: 10px;
    }}
    
    .logo-icon {{ 
        font-size: 3.8rem; 
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
        animation: float 4s ease-in-out infinite;
        line-height: 1;
        margin-top: 12px; /* ✳️ تنزيل القبعة للأسفل لكي تتوازى مع النص تماماً */
    }}
    
    .main-title {{ 
        margin: 0; 
        font-size: 3rem; 
        font-weight: 900; 
        color: #ffffff !important; 
        line-height: 1;
    }}
    
    .sub-title {{ 
        margin: 0; 
        color: #DBEAFE; 
        font-size: 1.2rem; 
        font-weight: 500; 
    }}
    
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] {{ 
        background-color: #F8FAFC !important; border: 2px solid #E2E8F0 !important; border-radius: 12px !important; height: 50px; 
    }}
    input, textarea, select {{ 
        color: #0F172A !important; -webkit-text-fill-color: #0F172A !important; caret-color: {primary_color} !important;
        background-color: transparent !important; font-weight: 700 !important; font-size: 1.05rem !important;
    }}
    ::placeholder {{ color: #94A3B8 !important; opacity: 1 !important; -webkit-text-fill-color: #94A3B8 !important; }}
    div[data-baseweb="select"] div {{ color: #0F172A !important; }}
    
    [data-testid="stFormSubmitButton"] button, 
    [data-testid="baseButton-primary"], 
    div.stButton > button {{
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
        background-color: #2563EB !important;
        color: white !important; border: none !important; font-weight: 800 !important;
        font-size: 1.1rem !important; border-radius: 12px !important; padding: 12px 20px !important;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important; transition: all 0.2s !important; width: 100%; height: 50px;
    }}
    [data-testid="stFormSubmitButton"] button:hover, 
    [data-testid="baseButton-primary"]:hover, 
    div.stButton > button:hover {{ 
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%) !important; 
        box-shadow: 0 6px 12px rgba(30, 64, 175, 0.3) !important; 
    }}
    
    .app-card {{ background: {card_bg}; padding: 20px; border-radius: 16px; box-shadow: {shadow_val}; border: 1px solid {border_color}; margin-bottom: 15px; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: transparent; border: none; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; color: #64748B; font-weight: bold; flex: 1; justify-content: center; transition: 0.3s; }}
    .stTabs [aria-selected="true"] {{ background-color: {primary_color} !important; color: white !important; border: none !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); }}

    .mobile-list-item {{ background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; align-items: center; justify-content: space-between; }}
    
    .medal-flex {{ display: flex; gap: 10px; margin: 20px 0; direction: rtl; }}
    .m-card {{ flex: 1; background: white; padding: 15px 5px; border-radius: 16px; text-align: center; border: 1px solid #E2E8F0; box-shadow: {shadow_val}; }}
    .m-active {{ border: 2px solid {warning_color} !important; background: #FFFBEB !important; }}
    
    .points-banner {{ background: {warning_color}; color: white; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3); }}
    .welcome-card {{ background: {header_grad}; color: white; padding: 20px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3); }}

    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes pulse-red {{ 0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }} 70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }} }}
    .urgent-box {{ background-color: #FEF2F2; border: 2px solid {danger_color}; color: #991B1B; padding: 15px; border-radius: 12px; text-align: center; animation: pulse-red 2s infinite; font-weight: bold; margin-bottom: 25px; }}

    @media (max-width: 768px) {{
        .header-container {{ padding: 60px 20px 30px 20px; }}
        .main-title {{ font-size: 2rem; }}
        .logo-icon {{ font-size: 2.5rem; }}
    }}
    </style>

    <div class="header-container">
        <div class="title-wrapper">
            <div class="logo-icon">🎓</div>
            <h1 class="main-title">منصة زياد الذكية</h1>
        </div>
        <p class="sub-title">بوابة التعليم الذكية 2026</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 3. نظام الدخول
# ==========================================
if st.session_state.role is None:
    c1, c2 = st.columns([1, 10]) 
    t1, t2, t3 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم", "🏫 بوابة الإدارة (مشاهد)"])
    
    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("st_login"):
            st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>تسجيل دخول الطالب</h4>", unsafe_allow_html=True)
            sid = st.text_input("رقم الهوية / الرقم الأكاديمي", placeholder="أدخل الرقم هنا...").strip()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 دخول للمنصة", type="primary", use_container_width=True):
                df = fetch_safe("students")
                if not df.empty:
                    df['clean_id'] = df.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
                    if sid.split('.')[0] in df['clean_id'].values:
                        st.session_state.username = sid.split('.')[0]
                        st.session_state.role = "student"
                        st.rerun()
                    else: st.error("⚠️ الرقم غير مسجل في النظام")
                    
    with t2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("tr_login"):
            st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>تسجيل دخول المعلم</h4>", unsafe_allow_html=True)
            u = st.text_input("اسم المستخدم", placeholder="User")
            p = st.text_input("كلمة المرور", type="password", placeholder="******")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🛠️ دخول لوحة التحكم", type="primary", use_container_width=True):
                df = fetch_safe("users")
                if not df.empty and u in df['username'].values:
                    ud = df[df['username']==u].iloc[0]
                    if hashlib.sha256(p.encode()).hexdigest() == ud['password_hash']:
                        if ud.get('role', 'teacher') in ['teacher', '']:
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
            st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>دخول الإدارة (قراءة واستخراج تقارير)</h4>", unsafe_allow_html=True)
            u_admin = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم للإدارة...")
            p_admin = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور...")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("👁️ دخول الإشراف", type="primary", use_container_width=True):
                df_u = fetch_safe("users")
                if not df_u.empty and u_admin in df_u['username'].values:
                    ud = df_u[df_u['username']==u_admin].iloc[0]
                    if hashlib.sha256(p_admin.encode()).hexdigest() == ud['password_hash']:
                        if ud.get('role', '') == 'viewer':
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

# ==========================================
# 👨‍🏫 4. واجهة المعلم / الإدارة (مشاهد)
# ==========================================
else:
    if 'db_loaded' not in st.session_state:
        with st.spinner("⏳ جاري الاتصال بالمنصة وتحديث البيانات المركزية..."):
            try:
                st.session_state.df_students = fetch_safe("students")
                st.session_state.df_grades = fetch_safe("grades")
                st.session_state.df_behavior = fetch_safe("behavior")
                st.session_state.db_loaded = True
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء الاتصال: {e}")
                st.stop()
                
    if st.session_state.get('show_refresh_success'):
        st.toast("✅ تم تحديث البيانات ومزامنتها بنجاح!", icon="🔄")
        st.session_state['show_refresh_success'] = False 

    if st.session_state.role in ["teacher", "viewer"]:
        
        if st.session_state.role == "teacher":
            menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "⚙️ الإعدادات", "🛑 خروج"])
            tab_students, tab_eval, tab_alerts, tab_settings, tab_logout = menu[0], menu[1], menu[2], menu[3], menu[4]
        else:
            menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "🛑 خروج"])
            tab_students, tab_eval, tab_alerts, tab_logout = menu[0], menu[1], menu[2], menu[3]
            
        # --- 👥 الطلاب ---
        with tab_students:
            st.subheader("👥 إدارة الطلاب والتقارير")
            df_st = st.session_state.df_students
            
            if not df_st.empty:
                df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
                df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
                
                sub_tabs = st.tabs(["📋 قائمة الطلاب", "🏆 لوحة الشرف (نقاط)", "🌟 المتفوقين (90%+)", "📑 تقرير الطالب الشامل"])
                
                # --- 1. قائمة الطلاب ---
                with sub_tabs[0]:
                    if 'toast_msg' in st.session_state:
                        st.toast(st.session_state.toast_msg, icon="🔔")
                        del st.session_state['toast_msg']
        
                    total_students = len(df_st)
                    total_classes = len(df_st['class'].unique()) if 'class' in df_st.columns else 0
                    avg_points = round(df_st['النقاط'].mean(), 1) if 'النقاط' in df_st.columns else 0
                    
                    cards_css = f"""
                    <style>
                    .metric-container {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 20px; direction: rtl; }}
                    .metric-card {{
                        background-color: #ffffff; border: 1px solid {border_color}; border-radius: 12px;
                        padding: 20px; flex: 1; display: flex; justify-content: space-between; align-items: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
                    }}
                    .metric-info {{ text-align: right; }}
                    .metric-title {{ color: {sub_text}; font-size: 14px; font-weight: bold; margin-bottom: 5px; }}
                    .metric-val {{ color: {text_color}; font-size: 28px; font-weight: 900; }}
                    .metric-sub {{ color: #94A3B8; font-size: 13px; }}
                    .metric-icon {{ width: 55px; height: 55px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 26px; }}
                    .ic-green {{ background-color: #D1FAE5; color: {success_color}; }}
                    .ic-blue {{ background-color: #DBEAFE; color: {primary_color}; }}
                    .ic-red {{ background-color: #FEE2E2; color: {danger_color}; }}
                    
                    [data-testid="stDataFrame"] {{ direction: rtl; }}
                    </style>
                    """
                    
                    cards_html = f"""
                    {cards_css}
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
                                <div class="metric-title">الفصول</div>
                                <div class="metric-val">{total_classes}</div>
                                <div class="metric-sub">فصول دراسية</div>
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
                    """
                    st.markdown(cards_html, unsafe_allow_html=True)
        
                    action_tabs = st.tabs(["🔍 عرض الطلاب", "➕ إضافة طالب", "✏️ تعديل بيانات طالب", "🗑️ حذف طالب"])
        
                    # -------------------------------------
                    # 📄 عرض الطلاب
                    # -------------------------------------
                    with action_tabs[0]:
                        
                        if 'current_page' not in st.session_state:
                            st.session_state.current_page = 1
                        
                        col_search, col_rows = st.columns([3, 1])
                        with col_search:
                            sq = st.text_input("🔍 بحث:", placeholder="أدخل اسم الطالب أو رقمه...", label_visibility="collapsed")
                        with col_rows:
                            rows_per_page = st.selectbox("الصفوف:", [10, 20, 50, 100], index=0, label_visibility="collapsed")
                        
                        display_df = df_st.copy()
                        if 'clean_id' in display_df.columns:
                            display_df = display_df.drop(columns=['clean_id'])
                        
                        rename_dict = {
                            'id': 'الرقم الأكاديمي', 'name': 'الاسم', 'class': 'الصف',
                            'year': 'العام', 'sem': 'المرحلة', 'subject': 'المادة'
                        }
                        display_df = display_df.rename(columns=rename_dict)
                        
                        # قلب الترتيب
                        display_df = display_df[display_df.columns[::-1]]
                        
                        if sq: 
                            norm_sq = normalize_arabic(sq)
                            mask = display_df['الرقم الأكاديمي'].astype(str).str.contains(norm_sq) | display_df['الاسم'].astype(str).apply(normalize_arabic).str.contains(norm_sq)
                            display_df = display_df[mask]
                            st.session_state.current_page = 1 
                        
                        total_rows = len(display_df)
                        total_pages = max(1, math.ceil(total_rows / rows_per_page))
                        
                        if st.session_state.current_page > total_pages:
                            st.session_state.current_page = total_pages
                            
                        start_idx = (st.session_state.current_page - 1) * rows_per_page
                        end_idx = start_idx + rows_per_page
                        
                        st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        pc1, pc2, pc3 = st.columns([1, 2, 1])
                        
                        with pc1:
                            if st.button("▶ التالي", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                                st.session_state.current_page += 1
                                st.rerun()
                                
                        with pc2:
                            st.markdown(f"<div style='text-align: center; font-weight: bold; padding-top: 5px; color: #64748b;'>صفحة {st.session_state.current_page} من {total_pages} <br><small>(إجمالي الطلاب: {total_rows})</small></div>", unsafe_allow_html=True)
                            
                        with pc3:
                            if st.button("السابق ◀", disabled=(st.session_state.current_page <= 1), use_container_width=True):
                                st.session_state.current_page -= 1
                                st.rerun()
        
                    # -------------------------------------
                    # 2. إضافة طالب
                    # -------------------------------------
                    with action_tabs[1]:
                        if st.session_state.role == "teacher":
                            with st.form("add_st_v26", clear_on_submit=True):
                                st.markdown("#### 👤 بيانات الطالب الأساسية")
                                c1, c2 = st.columns(2)
                                f_name = c1.text_input("الإسم الكامل", placeholder="أدخل الاسم الكامل")
                                f_id = c2.text_input("الرقم الأكاديمي", placeholder="أدخل الرقم الأكاديمي")
                                
                                c3, c4, c5 = st.columns(3)
                                f_stage = c3.selectbox("المرحلة", st.session_state.stage_options)
                                f_class = c4.selectbox("الصف", st.session_state.class_options)
                                f_year = c5.text_input("العام", st.session_state.current_year)
                                
                                st.markdown("#### 📞 معلومات التواصل")
                                c6, c7 = st.columns(2)
                                f_mail = c6.text_input("الإيميل", placeholder="أدخل البريد الإلكتروني")
                                f_phone = c7.text_input("الجوال", placeholder="أدخل رقم الجوال")
                                
                                submit_btn = st.form_submit_button("✅ حفظ الطالب", type="primary", use_container_width=True)
                                
                                if submit_btn:
                                    if f_id and f_name:
                                        if f_id.strip() in df_st['clean_id'].values:
                                            st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً!")
                                        else:
                                            cl_p = clean_phone_number(f_phone) if f_phone else ""
                                            st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "الجوال": cl_p, "الإيميل": f_mail.strip(), "النقاط": "0"}
                                            if safe_append_row("students", st_map):
                                                st.session_state.toast_msg = f"✅ تم إضافة الطالب '{f_name}' بنجاح!"
                                                if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                                st.cache_data.clear()
                                                st.rerun()
                                    else: st.warning("الرجاء إكمال البيانات الأساسية (الاسم والرقم)!")
                        else:
                            st.info("ليس لديك صلاحية لإضافة طلاب.")
        
                    # -------------------------------------
                    # 3. تعديل بيانات طالب
                    # -------------------------------------
                    with action_tabs[2]:
                        if st.session_state.role == "teacher":
                            if not df_st.empty:
                                edit_options = df_st.index.tolist()
                                selected_idx = st.selectbox(
                                    "✏️ اختر الطالب المطلوب تعديل بياناته (يمكنك البحث بالكتابة هنا):", 
                                    edit_options, 
                                    format_func=lambda x: f"{df_st.loc[x, 'name']} - (الرقم: {df_st.loc[x, 'id']})",
                                    key="edit_select"
                                )
                                
                                with st.form("edit_form_single"):
                                    st.markdown(f"**📝 تعديل بيانات: <span style='color:{primary_color};'>{df_st.loc[selected_idx, 'name']}</span>**", unsafe_allow_html=True)
                                    cols = st.columns(3)
                                    new_vals = []
                                    
                                    valid_columns = [c for c in df_st.columns if c not in ['clean_id'] and not str(c).startswith('Unnamed') and str(c).strip() != ""]
                                    
                                    for col_idx, col_name in enumerate(valid_columns):
                                        with cols[col_idx % 3]:
                                            current_val = "" if pd.isna(df_st.loc[selected_idx, col_name]) else str(df_st.loc[selected_idx, col_name])
                                            val = st.text_input(col_name, current_val, key=f"inp_edit_{selected_idx}_{col_idx}")
                                            new_vals.append(val)
                                    
                                    if st.form_submit_button("💾 حفظ التعديلات", type="primary", use_container_width=True):
                                        row_index = int(selected_idx) + 2
                                        try:
                                            sh.worksheet("students").update(f"A{row_index}", [new_vals])
                                            st.session_state.toast_msg = f"🔄 تم تحديث بيانات '{new_vals[1]}' بنجاح!"
                                            if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ حدث خطأ أثناء التعديل: {e}")
                            else:
                                st.info("لا توجد بيانات للطلاب بعد.")
        
                    # -------------------------------------
                    # 4. حذف طالب
                    # -------------------------------------
                    with action_tabs[3]:
                        if st.session_state.role == "teacher":
                            if not df_st.empty:
                                del_options = df_st.index.tolist()
                                del_idx = st.selectbox(
                                    "🗑️ اختر الطالب المطلوب حذفه نهائياً (يمكنك البحث بالكتابة هنا):", 
                                    del_options, 
                                    format_func=lambda x: f"{df_st.loc[x, 'name']} - (الرقم: {df_st.loc[x, 'id']})",
                                    key="del_select"
                                )
                                
                                student_to_delete = df_st.loc[del_idx, 'name']
                                st.error(f"⚠️ سيتم حذف بيانات ( {student_to_delete} ) نهائياً من قاعدة البيانات. هل أنت متأكد؟")
                                
                                if st.button(f"🚨 نعم، احذف {student_to_delete}", type="primary"):
                                    sh.worksheet("students").delete_rows(int(del_idx)+2)
                                    st.session_state.toast_msg = f"🗑️ تم حذف '{student_to_delete}' بشكل نهائي!"
                                    if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.info("لا توجد بيانات للطلاب بعد.")
                
                # --- 2. لوحة الشرف (النقاط والسلوك) ---
                with sub_tabs[1]:
                    st.markdown("#### 🌟 أفضل 10 طلاب (حسب نقاط التميز)")
                    
                    lux_css = """
                        * { box-sizing: border-box; } 
                        body { margin: 0; padding: 0; background: #F8FAFC; font-family: 'Cairo', sans-serif; text-align: center; direction: rtl; }
                        .page { width: 210mm; padding: 10mm; display: flex; flex-wrap: wrap; justify-content: center; gap: 4%; margin: 0 auto; }
                        
                        .card { 
                            width: 46%; height: 135mm; 
                            border-radius: 15px; position: relative; overflow: hidden;
                            background: #fff;
                            box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
                            page-break-inside: avoid;
                            margin-bottom: 20px;
                        }
                        
                        .ribbon {
                            position: absolute; top: 20px; right: -35px;
                            padding: 5px 40px; font-weight: 900; font-size: 15px;
                            transform: rotate(45deg); z-index: 10;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                            font-family: 'Cairo', sans-serif; letter-spacing: 1px;
                        }
                        .ribbon.gold { background: linear-gradient(45deg, #FFD700, #FFA500); color: #8B4513; }
                        .ribbon.silver { background: linear-gradient(45deg, #E2E8F0, #94A3B8); color: #1E293B; }
                        .ribbon.bronze { background: linear-gradient(45deg, #FDBA74, #D97706); color: #78350F; }
                        
                        .card-inner {
                            position: absolute; top: 12px; bottom: 12px; left: 12px; right: 12px;
                            border: 2px dashed #b68a36; border-radius: 10px; padding: 20px 10px;
                            display: flex; flex-direction: column; justify-content: space-between; align-items: center;
                            background-color: rgba(255,255,255,0.95);
                            background-image: url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23b68a36' fill-opacity='0.05' fill-rule='evenodd'%3E%3Ccircle cx='3' cy='3' r='3'/%3E%3Ccircle cx='13' cy='13' r='3'/%3E%3C/g%3E%3C/svg%3E");
                        }
                        
                        .c-icon { font-size: 45px; line-height: 1; margin-bottom: 5px; width: 100%; text-align: center; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1)); }
                        .c-header { font-family: 'Aref Ruqaa', serif; font-size: 30px; font-weight: bold; width: 100%; text-align: center; margin-bottom: 5px; color: #b68a36; }
                        .c-teacher { font-size: 14px; color: #475569; font-weight: bold; width: 100%; text-align: center; margin-bottom: 10px; }
                        
                        .c-name { 
                            font-size: 26px; font-weight: 900; line-height: 1.4; 
                            width: 100%; text-align: center; 
                            display: flex; align-items: center; justify-content: center; flex-grow: 1;
                            padding: 0 10px; word-wrap: break-word;
                        }
                        
                        .c-badge { 
                            width: 80%; margin: 10px auto; padding: 15px 5px; border-radius: 12px;
                            background: #fff; text-align: center;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.08); border: 1px solid #E2E8F0;
                        }
                        
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
                        
                        @media print { 
                            @page { size: A4 portrait; margin: 5mm; } 
                            body { background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; } 
                            .card { box-shadow: none; margin-bottom: 10mm; border-width: 10px; }
                        }
                    """
        
                    if not df_st.empty:
                        top_10 = df_st.sort_values('النقاط', ascending=False).head(10)
                        
                        for i, (_, r) in enumerate(top_10.iterrows(), 1):
                            ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
                            brd_col = "#F59E0B" if i<=3 else "#E2E8F0"
                            st.markdown(f"""
                                <div style='background:#ffffff; border:1px solid #E2E8F0; border-right:5px solid {brd_col}; padding:15px; border-radius:12px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                                    <div style='display:flex; align-items:center; gap:15px;'>
                                        <span style='font-size:1.5rem; font-weight:bold; width:30px; text-align:center;'>{ic}</span>
                                        <div>
                                            <b style='font-size:1.1rem; color:{accent_color};'>{r.get('name', '')}</b><br>
                                            <small style='color:#64748B;'>🏫 الصف: {r.get('class', '')} | 🆔 ID: {r.get('clean_id', '')}</small>
                                        </div>
                                    </div>
                                    <div style='background:#FEF3C7; padding:5px 15px; border-radius:8px; color:#B45309; font-weight:900; font-size:1.2rem;'>
                                        {int(r.get('النقاط', 0))} نقطة
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.subheader("🖨️ طباعة بطاقات لوحة الشرف")
                        
                        honor_cards_content = ""
                        for rank, (_, row) in enumerate(top_10.iterrows(), 1):
                            student_name = row.get('name', 'اسم غير متوفر')
                            score = int(row.get('النقاط', 0))
                            
                            if rank == 1:
                                rank_text = "المركز الأول"
                                icon = "🏆"
                                ribbon_html = '<div class="ribbon gold">الأول</div>'
                                badge_class = "rank-1"
                            elif rank == 2:
                                rank_text = "المركز الثاني"
                                icon = "🥈"
                                ribbon_html = '<div class="ribbon silver">الثاني</div>'
                                badge_class = "rank-2"
                            elif rank == 3:
                                rank_text = "المركز الثالث"
                                icon = "🥉"
                                ribbon_html = '<div class="ribbon bronze">الثالث</div>'
                                badge_class = "rank-3"
                            else:
                                rank_text = f"المركز {rank}"
                                icon = "🌟"
                                ribbon_html = ""
                                badge_class = ""
                            
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
                        
                        honor_full_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet"><style>{lux_css}</style></head><body><div class="page">{honor_cards_content}</div><script>window.onload = function() {{ window.print(); }}</script></body></html>"""
                        
                        st.download_button(
                            label="🌐 تحميل بطاقات الشرف (تصميم واقعي للطباعة)", 
                            data=honor_full_html, 
                            file_name=f"Honor_Cards_{datetime.date.today()}.html", 
                            mime="text/html", 
                            use_container_width=True,
                            type="primary"
                        )
        
                # --- 3. المتفوقين (أكاديمياً 90% فما فوق) ---
                # --- 3. المتفوقين (أكاديمياً 90% فما فوق) ---
                with sub_tabs[2]:
                    cp = st.session_state.get('current_period', 'الفترة الأولى')
                    st.markdown(f"#### 🎓 لوحة المتفوقين أكاديمياً ({cp})")
                    
                    if 'df_grades' in st.session_state and not st.session_state.df_grades.empty:
                        df_g = st.session_state.df_grades.copy()
                        df_g['clean_id'] = df_g.iloc[:,0].astype(str).str.split('.').str[0]
                        
                        # ✳️ ملء الفراغات لضمان ظهور بيانات الفترة الأولى القديمة
                        if 'period' not in df_g.columns: df_g['period'] = 'الفترة الأولى'
                        df_g['period'] = df_g['period'].replace(['', None, 'nan'], 'الفترة الأولى')
                        
                        df_g = df_g[df_g['period'] == cp]
                        # ... بقية الكود الخاص بـ merged_df و top_academic يكمل كما هو ...
                        
                        merged_df = pd.merge(df_g, df_st[['clean_id', 'name', 'class']], on='clean_id', how='inner')
                        
                        if not merged_df.empty:
                            max_total = st.session_state.get('max_tasks', 0) + st.session_state.get('max_quiz', 0)
                            if max_total > 0:
                                merged_df['perf_num'] = pd.to_numeric(merged_df['perf'], errors='coerce').fillna(0)
                                merged_df['percentage'] = (merged_df['perf_num'] / max_total) * 100
                                top_academic = merged_df[merged_df['percentage'] >= 90].sort_values('percentage', ascending=False)
                                
                                if not top_academic.empty:
                                    for i, (_, r) in enumerate(top_academic.iterrows(), 1):
                                        st.markdown(f"<div style='background:#ffffff; border:1px solid #E2E8F0; border-right:5px solid {success_color}; padding:15px; border-radius:12px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'><div style='display:flex; align-items:center; gap:15px;'><span style='font-size:1.5rem;'>🎓</span><div><b style='font-size:1.1rem; color:{success_color};'>{r.get('name', '')}</b><br><small>🏫 {r.get('class', '')}</small></div></div><div style='background:#D1FAE5; padding:5px 15px; border-radius:8px; color:{success_color}; font-weight:900;'>ممتاز</div></div>", unsafe_allow_html=True)
                                        
                                    st.markdown("---")
                                    st.subheader("🖨️ طباعة بطاقات التفوق")
                                    
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
                                        type="primary"
                                    )
                                else:
                                    st.info(f"لم يصل أحد لنسبة 90% في {cp} حتى الآن.")
                        else:
                            st.info(f"لا توجد درجات مطابقة للطلاب في {cp}.")
                    else:
                        st.info("لم يتم رصد درجات بعد.")
                        
                # --- 4. تقرير الطالب الشامل ---
                with sub_tabs[3]:
                    st.markdown("#### 📑 التقرير الشامل المفصل")
                    st_dict = {f"{r['name']} ({r['clean_id']})": r['clean_id'] for _, r in df_st.iterrows()}
                    sel_rep = st.selectbox("🔍 ابحث عن الطالب لاستخراج التقرير:", [""] + list(st_dict.keys()), key="rep_sel")
                    
                    if sel_rep:
                        sid = st_dict[sel_rep]
                        s_inf = df_st[df_st['clean_id'] == sid].iloc[0]
                        st.markdown("---")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.info(f"👤 الاسم:\n\n**{s_inf['name']}**")
                        c2.success(f"🆔 الرقم الأكاديمي:\n\n**{sid}**")
                        c3.warning(f"🏫 الصف:\n\n**{s_inf.get('class', 'غير محدد')}**")
                        c4.error(f"🌟 إجمالي النقاط:\n\n**{int(s_inf['النقاط'])}**")
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        grades_html_table = "<div style='text-align:center; padding:20px; color:#64748B;'>لا توجد درجات مرصودة لهذا الطالب.</div>"
                        behavior_html_table = "<div style='text-align:center; padding:20px; color:#64748B;'>✨ سجل السلوك نظيف.</div>"

                        st.markdown("##### 📊 الدرجات الأكاديمية")
                        df_g = st.session_state.df_grades
                        if not df_g.empty:
                            df_g['clean_id'] = df_g.iloc[:,0].astype(str).str.split('.').str[0]
                            my_g = df_g[df_g['clean_id'] == sid]
                            if not my_g.empty:
                                g_inf = my_g.iloc[0]
                                k1, k2, k3 = st.columns(3)
                                k1.metric("📝 المشاركة والواجبات", g_inf.get('p1', 0))
                                k2.metric("✍️ الاختبارات", g_inf.get('p2', 0))
                                k3.metric("🏆 المجموع الكلي", g_inf.get('perf', 0))
                                
                                grades_html_table = f"""
                                <table>
                                    <tr><th>المشاركة والواجبات</th><th>الاختبارات</th><th>المجموع الكلي</th></tr>
                                    <tr>
                                        <td style="text-align: center;">{g_inf.get('p1', 0)}</td>
                                        <td style="text-align: center;">{g_inf.get('p2', 0)}</td>
                                        <td style="text-align: center; font-weight:bold; color:{primary_color};">{g_inf.get('perf', 0)}</td>
                                    </tr>
                                </table>
                                """
                            else: st.info("لم يتم رصد درجات أكاديمية لهذا الطالب بعد.")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("##### 📜 سجل الملاحظات والسلوك التفصيلي")
                        df_b = st.session_state.df_behavior
                        if not df_b.empty:
                            df_b['clean_id'] = df_b.iloc[:,0].astype(str).str.split('.').str[0]
                            my_b = df_b[df_b['clean_id'] == sid]
                            if not my_b.empty:
                                display_df = my_b[['date', 'type', 'note']].rename(columns={'date':'📅 التاريخ', 'type':'🎯 نوع السلوك', 'note':'📝 التفاصيل'})
                                st.dataframe(display_df, use_container_width=True, hide_index=True)
                                rows_html = ""
                                for _, r_b in display_df.iterrows():
                                    rows_html += f"<tr><td>{r_b['📅 التاريخ']}</td><td>{r_b['🎯 نوع السلوك']}</td><td>{r_b['📝 التفاصيل']}</td></tr>"
                                behavior_html_table = f"<table><tr><th>التاريخ</th><th>نوع السلوك</th><th>التفاصيل</th></tr>{rows_html}</table>"
                            else: st.success("✨ سجله نظيف، لا توجد ملاحظات مسجلة في السجل.")
                        else: st.info("سجل السلوك فارغ تماماً في المنصة.")

                        st.divider()
                        final_report = f"""
                        <!DOCTYPE html>
                        <html dir="rtl" lang="ar">
                        <head>
                            <meta charset="UTF-8">
                            <title>تقرير الطالب: {s_inf['name']}</title>
                            <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
                            <style>
                                body {{ font-family: 'Cairo', sans-serif; background-color: #F8FAFC; padding: 20px; color: #0F172A; line-height: 1.6; }}
                                .container {{ max-width: 800px; margin: 0 auto; background: #FFFFFF; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                                .banner {{ background: {header_grad}; color: white; text-align: center; padding: 15px; border-radius: 12px; margin-bottom: 30px; font-weight: 800; font-size: 24px; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3); }}
                                .header {{ text-align: center; margin-bottom: 30px; }}
                                .header h1 {{ color: #0F172A; margin-bottom: 5px; font-weight: 800; font-size: 28px; }}
                                .header p {{ color: #64748B; font-size: 14px; margin-top: 0; }}
                                .student-card {{ background: #F8FAFC; border-right: 5px solid {primary_color}; padding: 25px; border-radius: 12px; margin-bottom: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }}
                                .student-card h2 {{ grid-column: 1 / -1; margin-top: 0; color: {accent_color}; border-bottom: 1px dashed {border_color}; padding-bottom: 15px; margin-bottom: 10px; }}
                                .student-card .info-item {{ font-size: 16px; }}
                                .student-card .info-item span {{ font-weight: 800; color: #475569; margin-left: 5px; }}
                                h3 {{ color: {accent_color}; display: flex; align-items: center; gap: 10px; margin-top: 40px; border-bottom: 2px solid {border_color}; padding-bottom: 10px; }}
                                .table-container {{ overflow: hidden; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px; border: 1px solid {border_color}; }}
                                table {{ width: 100%; border-collapse: collapse; background: #fff; text-align: right; }}
                                th {{ background-color: #F8FAFC; color: #0F172A; font-weight: 800; padding: 15px; border-bottom: 2px solid {border_color}; }}
                                td {{ padding: 15px; border-bottom: 1px solid #F1F5F9; color: #475569; font-weight: 600; }}
                                tr:last-child td {{ border-bottom: none; }}
                                tr:nth-child(even) {{ background-color: #F8FAFC; }}
                                .footer-sigs {{ margin-top: 60px; display: flex; justify-content: space-between; align-items: center; padding-top: 30px; border-top: 2px dashed #CBD5E1; color: #0F172A; font-weight: 800; }}
                                .footer-sigs > div {{ text-align: center; flex: 1; }}
                                .sig-line {{ margin-top: 30px; color: #94A3B8; font-weight: normal; }}
                                @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; padding: 0; max-width: 100%; border: none; }} .banner, th, .student-card {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="banner">✨ منصة زياد الذكية ✨</div>
                                <div class="header"><h1>تقرير متابعة طالب</h1><p>تاريخ استخراج التقرير: {pd.Timestamp.now().strftime('%Y-%m-%d')}</p></div>
                                <div class="student-card">
                                    <h2>👤 {s_inf['name']}</h2>
                                    <div class="info-item"><span>🆔 الرقم الأكاديمي:</span> {sid}</div>
                                    <div class="info-item"><span>🏫 الصف:</span> {s_inf.get('class', 'غير محدد')}</div>
                                    <div class="info-item"><span>⭐ نقاط التميز:</span> <span style="color:#d97706; font-size:1.2em;">{int(s_inf['النقاط'])}</span></div>
                                </div>
                                <h3>📊 الأداء الأكاديمي</h3>
                                <div class="table-container">{grades_html_table}</div>
                                <h3>📜 سجل السلوك والملاحظات</h3>
                                <div class="table-container">{behavior_html_table}</div>
                                <div class="footer-sigs">
                                    <div>وكيل شؤون الطلاب<div class="sig-line">.................................</div></div>
                                    <div>المعلم<div style="margin-top: 20px; color: {accent_color}; font-size: 18px;">زياد المعمري</div></div>
                                    <div>الموجه الطلابي<div class="sig-line">.................................</div></div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        col_btn1, col_btn2 = st.columns([1, 4])
                        with col_btn1:
                            st.download_button(label="🖨️ تحميل التقرير", data=final_report, file_name=f"Report_{sid}_{s_inf['name']}.html", mime="text/html", type="primary")
                        with col_btn2: st.caption("👈 التصميم جاهز! حمل الملف واضغط Ctrl+P للطباعة.")
            
                # 📊 التقييم والمتابعة (فردي وجماعي)
                with tab_eval:
                    st.markdown("### 📊 التقييم والمتابعة")
                    # ✳️ تم تعديل السطر التالي ليحتوي على 3 تبويبات
                    eval_tabs = st.tabs(["👤 التقييم الفردي", "👥 الرصد الجماعي السريع", "🖨️ مساعد التفريغ الورقي"])
                    
                    # --- 1. التقييم الفردي ---
                    with eval_tabs[0]:
                        df_ev = st.session_state.df_students
                        
                        if not df_ev.empty:
                            st_dict = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_ev.iterrows()}
                            sel = st.selectbox("🎯 اختر الطالب من القائمة:", [""] + list(st_dict.keys()), key="single_eval_sel")
                            
                            if sel:
                                sid = str(st_dict[sel]).strip().split('.')[0]
                                student_idx = df_ev[df_ev.iloc[:,0].astype(str).str.split('.').str[0] == sid].index[0]
                                s_inf = df_ev.loc[student_idx]
                                
                                s_nm = s_inf['name']
                                clp = clean_phone_number(s_inf.get('الجوال',''))
                                s_eml = s_inf.get('الإيميل', '')
                                current_points = int(pd.to_numeric(s_inf.get('النقاط', 0), errors='coerce') or 0)
                                
                                c1, c2 = st.columns(2)
                                
                                # --- قسم السلوك الفردي ---
                                with c2:
                                    st.container(border=True)
                                    st.markdown(f"##### 🎭 السلوك (الرصيد: {current_points} نقطة)")
                                    if st.session_state.role == "teacher":
                                        with st.form("beh_add", clear_on_submit=True):
                                            bt = st.selectbox("نوع السلوك", [
                                                "🌟 متميز (+10)", "✅ إيجابي (+5)", "📝 حل الواجب (+5)", "🎯 أداء المهمة (+10)", "📂 ملف الإنجاز (+10)", 
                                                "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص أدوات الكتابة (-5)", "💤 النوم داخل الفصل (-3)", 
                                                "🏃 تأخر عن الحصة (-5)", "❌ عدم إحضار ملف الإنجاز (-10)", "🚫 سلبي (-10)"
                                            ])
                                            bn = st.text_area("تفاصيل الملاحظة")
                                            
                                            if st.form_submit_button("💾 تسجيل السلوك", type="primary"):
                                                new_b_row = {"student_id": sid, "date": str(datetime.date.today()), "type": bt, "note": bn}
                                                
                                                safe_append_row("behavior", new_b_row)
                                                
                                                new_b_df = pd.DataFrame([new_b_row])
                                                st.session_state.df_behavior = pd.concat([st.session_state.df_behavior, new_b_df], ignore_index=True)
                                                
                                                match = re.search(r'\(([\+\-]?\d+)\)', bt)
                                                chg = int(match.group(1)) if match else 0
                                                if chg != 0:
                                                    try:
                                                        ws = sh.worksheet("students"); c = ws.find(sid)
                                                        if c:
                                                            h = ws.row_values(1)
                                                            if 'النقاط' in h:
                                                                idx = h.index('النقاط') + 1
                                                                new_val = current_points + chg
                                                                ws.update_cell(c.row, idx, new_val)
                                                                st.session_state.df_students.loc[student_idx, 'النقاط'] = int(new_val)
                                                    except Exception as e: st.error(f"خطأ: {e}")
                                                
                                                st.toast(f"✅ تم إضافة الملاحظة للطالب {s_nm} وتحديث رصيده!", icon="🎉")
                                    else: st.info("💡 وضع القراءة فقط.")
        
                                # --- قسم الدرجات الأكاديمية ---
                                with c1:
                                    st.container(border=True)
                                    cp = st.session_state.get('current_period', 'الفترة الأولى')
                                    st.markdown(f"##### 📝 رصد الدرجات ({cp})")
                                    
                                    df_g = st.session_state.df_grades.copy()
                                    cur_p1, cur_p2 = 0, 0
                                    
                                    if not df_g.empty:
                                        df_g['clean_id'] = df_g.iloc[:,0].astype(str).str.split('.').str[0]
                                        
                                        if 'period' not in df_g.columns: df_g['period'] = 'الفترة الأولى'
                                        df_g['period'] = df_g['period'].replace(['', None, 'nan'], 'الفترة الأولى')
                                            
                                        gr_match = df_g[(df_g['clean_id'] == sid) & (df_g['period'] == cp)]
                                        if not gr_match.empty:
                                            cur_p1 = int(pd.to_numeric(gr_match.iloc[0]['p1'], errors='coerce') or 0)
                                            cur_p2 = int(pd.to_numeric(gr_match.iloc[0]['p2'], errors='coerce') or 0)
                                    
                                    if st.session_state.role == "teacher":
                                        with st.form("gr_upd", clear_on_submit=False):
                                            v1 = st.number_input("درجة المشاركة", 0, st.session_state.get('max_tasks', 60), cur_p1)
                                            v2 = st.number_input("درجة الاختبار", 0, st.session_state.get('max_quiz', 40), cur_p2)
                                            
                                            if st.form_submit_button("💾 حفظ الدرجات", type="primary"):
                                                tot = v1 + v2
                                                ws_g = sh.worksheet("grades")
                                                
                                                headers = ws_g.row_values(1)
                                                if 'period' not in headers:
                                                    ws_g.update_cell(1, len(headers)+1, 'period')
                                                    headers.append('period')
                                                    
                                                records = ws_g.get_all_records()
                                                row_to_update = None
                                                
                                                for i, r in enumerate(records):
                                                    r_id = str(r.get(headers[0], '')).strip().split('.')[0]
                                                    r_period = str(r.get('period', 'الفترة الأولى'))
                                                    if r_id == sid and r_period == cp:
                                                        row_to_update = i + 2 
                                                        break
                                                        
                                                if row_to_update:
                                                    ws_g.update_cell(row_to_update, 2, v1); ws_g.update_cell(row_to_update, 3, v2)
                                                    ws_g.update_cell(row_to_update, 4, tot); ws_g.update_cell(row_to_update, 5, str(datetime.date.today()))
                                                    ws_g.update_cell(row_to_update, headers.index('period')+1, cp)
                                                else: 
                                                    new_row = [sid, v1, v2, tot, str(datetime.date.today())]
                                                    while len(new_row) < len(headers) - 1: new_row.append("") 
                                                    new_row.append(cp)
                                                    ws_g.append_row(new_row)
                                                    
                                                st.session_state['show_refresh_success'] = True
                                                if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                                st.cache_data.clear(); st.rerun()
                                    else: st.info("💡 وضع القراءة فقط.")
                                    st.caption(f"📊 المجموع الحالي لـ {cp}: {cur_p1 + cur_p2}")
        
                                # --- سجل السلوك السفلي ---
                                st.markdown("#### 📜 سجل السلوك الأخير")
                                df_b = st.session_state.df_behavior
                                if not df_b.empty:
                                    cid = 'student_id' if 'student_id' in df_b.columns else df_b.columns[0]
                                    my_b = df_b[df_b[cid].astype(str) == str(sid)]
                                    
                                    def delete_behavior(row_idx, global_idx):
                                        try: 
                                            sh.worksheet("behavior").delete_rows(int(row_idx) + 2)
                                            st.session_state.df_behavior = st.session_state.df_behavior.drop(global_idx).reset_index(drop=True)
                                        except: pass
        
                                    for global_idx, r in my_b.iloc[::-1].iterrows():
                                        with st.container():
                                            color = danger_color if "سلبي" in str(r.get('type')) or "-" in str(r.get('type')) else success_color
                                            st.markdown(f"""
                                            <div class="mobile-list-item" style="border-right: 4px solid {color}">
                                                <div><b>{r.get('type')}</b> | <small>{r.get('date')}</small><br><span style="color:#64748B">{r.get('note')}</span></div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            c_del, c_wa, c_em = st.columns([0.5, 1, 1])
                                            lnk = get_professional_msg(s_nm, r.get('type'), r.get('note'), r.get('date'))
                                            c_wa.link_button("واتساب", f"https://api.whatsapp.com/send?phone={clp}&text={lnk}", use_container_width=True)
                                            c_em.link_button("إيميل", f"mailto:{s_eml}?subject=ملاحظة: {s_nm}&body={lnk}", use_container_width=True)
                                            
                                            if st.session_state.role == "teacher": 
                                                c_del.button("❌", key=f"dl_beh_{global_idx}", on_click=delete_behavior, args=(global_idx, global_idx))
                    
                    # --- 2. الرصد الجماعي السريع ---
                    with eval_tabs[1]:
                        if st.session_state.role == "teacher":
                            st.markdown("#### 🚀 الرصد الجماعي للملاحظات والواجبات")
                            st.info("💡 اختر الصف، وحدد الملاحظات للطلاب المعنيين فقط، ثم اضغط حفظ بالأسفل لترصد للجميع دفعة واحدة.")
                            
                            bulk_class = st.selectbox("🎯 اختر الصف للرصد الجماعي:", st.session_state.class_options, key="bulk_class_sel")
                            df_st_bulk = fetch_safe("students")
                            
                            if not df_st_bulk.empty:
                                df_st_bulk['clean_class'] = df_st_bulk.iloc[:, 2].astype(str).str.strip()
                                class_students = df_st_bulk[df_st_bulk['clean_class'] == bulk_class.strip()]
                                
                                if not class_students.empty:
                                    with st.form("bulk_behavior_form", clear_on_submit=True):
                                        beh_options = [
                                            "--- بدون ملاحظة ---",
                                            "🌟 متميز (+10)", "✅ إيجابي (+5)", "📝 حل الواجب (+5)", "🎯 أداء المهمة (+10)", "📂 ملف الإنجاز (+10)", 
                                            "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص أدوات الكتابة (-5)", "💤 النوم داخل الفصل (-3)", 
                                            "🏃 تأخر عن الحصة (-5)", "❌ عدم إحضار ملف الإنجاز (-10)", "🚫 سلبي (-10)"
                                        ]
                                        
                                        bulk_data = {}
                                        
                                        st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
                                        col_n, col_b, col_t = st.columns([1.5, 2, 2])
                                        col_n.markdown("**👤 اسم الطالب**"); col_b.markdown("**🎭 السلوك**"); col_t.markdown("**📝 ملاحظة (اختياري)**")
                                        st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
        
                                        for _, row in class_students.iterrows():
                                            sid_b = str(row.iloc[0]).split('.')[0].strip()
                                            sname_b = row.iloc[1]
                                            
                                            c1, c2, c3 = st.columns([1.5, 2, 2])
                                            c1.markdown(f"<div style='padding-top:15px;'>{sname_b}</div>", unsafe_allow_html=True)
                                            b_type = c2.selectbox("السلوك", beh_options, key=f"b_type_{sid_b}", label_visibility="collapsed")
                                            b_note = c3.text_input("تفاصيل", key=f"b_note_{sid_b}", label_visibility="collapsed", placeholder="أضف تفاصيل...")
                                            
                                            bulk_data[sid_b] = {"type": b_type, "note": b_note}
                                            st.markdown("<div style='border-bottom: 1px dashed #E2E8F0; margin: 5px 0;'></div>", unsafe_allow_html=True)
        
                                        if st.form_submit_button("🚀 حفظ الرصد الجماعي للجميع", type="primary"):
                                            behavior_rows_to_add = []
                                            point_updates = {}
                                            
                                            for sid_key, data in bulk_data.items():
                                                if data["type"] != "--- بدون ملاحظة ---":
                                                    behavior_rows_to_add.append([sid_key, str(datetime.date.today()), data["type"], data["note"]])
                                                    match = re.search(r'\(([\+\-]?\d+)\)', data["type"])
                                                    if match:
                                                        point_updates[sid_key] = int(match.group(1))
        
                                            if behavior_rows_to_add:
                                                try:
                                                    with st.spinner("جاري حفظ الرصد الجماعي وتحديث النقاط..."):
                                                        sh.worksheet("behavior").append_rows(behavior_rows_to_add)
                                                        
                                                        ws_st = sh.worksheet("students")
                                                        all_st = ws_st.get_all_records()
                                                        headers = ws_st.row_values(1)
                                                        
                                                        if 'النقاط' in headers:
                                                            p_idx = headers.index('النقاط') + 1
                                                            from gspread import Cell
                                                            cells_to_update = []
                                                            
                                                            for i, r in enumerate(all_st):
                                                                st_id = str(r.get('id', '')).split('.')[0].strip()
                                                                if st_id in point_updates:
                                                                    cur_p = int(pd.to_numeric(r.get('النقاط', 0), errors='coerce') or 0)
                                                                    new_p = cur_p + point_updates[st_id]
                                                                    cells_to_update.append(Cell(row=i+2, col=p_idx, value=new_p))
                                                            
                                                            if cells_to_update:
                                                                ws_st.update_cells(cells_to_update)
                                                        
                                                        st.success(f"✅ تمت المهمة بنجاح! تم رصد ({len(behavior_rows_to_add)}) ملاحظة.")
                                                        if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                                        st.cache_data.clear()
                                                        st.rerun()
                                                except Exception as e:
                                                    st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
                                            else:
                                                st.warning("⚠️ لم تقم باختيار أي سلوك لأي طالب ليتم حفظه.")
                                else:
                                    st.info("لا يوجد طلاب مسجلين في هذا الصف.")
                        else:
                            st.info("💡 وضع القراءة فقط.")
        
                    # --- 3. مساعد التفريغ الورقي (الإضافة الجديدة) ---
                    with eval_tabs[2]:
                        st.markdown("#### 🖨️ مساعد التفريغ للسجلات الورقية (حصر الملاحظات)")
                        st.info("هذه الأداة تجمع وتحصي المخالفات والمشاركات لتسهيل نقلها إلى كشف المتابعة الورقي بسرعة.")
                        
                        df_b = fetch_safe("behavior")
                        df_s = fetch_safe("students")
                        
                        if not df_b.empty and not df_s.empty:
                            df_b['clean_id'] = df_b.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                            df_s['clean_id'] = df_s.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                            
                            merged_df = pd.merge(df_b, df_s[['clean_id', 'name', 'class']], on='clean_id', how='inner')
                            beh_col = 'type' if 'type' in merged_df.columns else merged_df.columns[1]
                            
                            col1, col2 = st.columns(2)
                            
                            available_classes = st.session_state.get('class_options', ['الرابع', 'الخامس'])
                            cls_choice = col1.selectbox("1️⃣ اختر الصف لفرز بياناته:", available_classes)
                            class_data = merged_df[merged_df['class'] == cls_choice]
                            
                            if not class_data.empty:
                                unique_notes = list(class_data[beh_col].unique())
                                type_choice = col2.selectbox("2️⃣ نوع الملاحظة المطلوبة:", ["الكل (جدول تجميعي لكشف المتابعة)"] + unique_notes)
                                
                                st.divider()
                                
                                if type_choice == "الكل (جدول تجميعي لكشف المتابعة)":
                                    st.markdown(f"##### 📊 حصر شامل لجميع ملاحظات (الصف {cls_choice})")
                                    
                                    # إنشاء الجدول التجميعي للأرقام
                                    pivot_table = pd.crosstab(class_data['name'], class_data[beh_col])
                                    pivot_table.index.name = "اسم الطالب"
                                    
                                    # تجميع الملاحظات النصية
                                    if 'note' in class_data.columns:
                                        def combine_notes(group):
                                            valid = group[group['note'].astype(str).str.strip() != '']
                                            if valid.empty: return ""
                                            return " ، ".join(valid['note'].astype(str).str.strip())
                                            
                                        notes_series = class_data.groupby('name').apply(combine_notes)
                                        pivot_table['الملاحظات النصية التفصيلية'] = notes_series
                                    
                                    # ✳️ الحل الجذري لمنع اختفاء الجدول: تنظيف وتوحيد نوع البيانات
                                    pivot_table = pivot_table.fillna("") 
                                    pivot_table = pivot_table.astype(str) # إجبار كل الخلايا لتكون نصوصاً لكي لا يتعطل محرك الرسم
                                    
                                    st.dataframe(pivot_table, use_container_width=True)
                                    
                                    b_csv = io.BytesIO()
                                    with pd.ExcelWriter(b_csv, engine='xlsxwriter') as writer:
                                        pivot_table.to_excel(writer, sheet_name='التفريغ الورقي')
                                    st.download_button(f"📥 تحميل كشف (الصف {cls_choice}) للطباعة", b_csv.getvalue(), f"Behavior_Summary_{cls_choice}.xlsx", use_container_width=True)
                                    
                                else:
                                    st.markdown(f"##### 📌 حصر الطلاب الذين لديهم ({type_choice}) في (الصف {cls_choice})")
                                    specific_data = class_data[class_data[beh_col] == type_choice]
                                    if not specific_data.empty:
                                        # عرض الملاحظات النصية حتى في البحث الفردي
                                        summary = specific_data.groupby(['name', 'note']).size().reset_index(name='عدد المرات')
                                        summary.rename(columns={'name': 'اسم الطالب', 'note': 'التفاصيل المكتوبة'}, inplace=True)
                                        summary = summary.sort_values('عدد المرات', ascending=False)
                                        st.dataframe(summary, use_container_width=True, hide_index=True)
                                    else:
                                        st.info("لا يوجد أي طالب مسجل عليه هذه الملاحظة.")
                            else:
                                st.info(f"لا توجد أي ملاحظات مسجلة لطلاب (الصف {cls_choice}) حتى الآن.")
                        else:
                            st.warning("لا توجد بيانات سلوكية كافية لإنشاء التقرير.")
                    
        # 📢 التنبيهات
        with tab_alerts:
            st.markdown("### 📢 لوحة الإعلانات والتعاميم")
            def perform_delete(row_index):
                try: 
                    sh.worksheet("exams").delete_rows(int(row_index) + 2)
                    st.cache_data.clear(); st.toast("✅ تم حذف التنبيه بنجاح")
                except Exception as e: st.toast(f"❌ حدث خطأ: {e}")

            if st.session_state.role == "teacher":
                with st.form("ann_add"):
                    c1, c2 = st.columns([3, 1])
                    at = c1.text_input("عنوان الإعلان")
                    atg = c2.selectbox("الفئة المستهدفة", ["الكل"] + st.session_state.class_options)
                    ad = st.text_area("نص الإعلان أو الرابط")
                    au = c1.checkbox("🔥 تعميم عاجل (يظهر بوميض)")
                    if st.form_submit_button("📣 نشر التعميم", type="primary"):
                        safe_append_row("exams", {"الصف": atg, "عاجل": "نعم" if au else "لا", "العنوان": at, "التاريخ": str(datetime.date.today()), "الرابط": ad})
                        st.success("✅ تم النشر"); st.cache_data.clear(); st.rerun()
            
            st.divider()
            df_a = fetch_safe("exams")
            if not df_a.empty:
                for i, r in df_a.iloc[::-1].iterrows():
                    with st.container():
                        is_urgent = str(r.get('عاجل')).strip() == 'نعم'
                        anim_class = "urgent-box" if is_urgent else ""
                        border_style = f"2px solid {danger_color}" if is_urgent else f"1px solid {border_color}"
                        bg_style = "#FEF2F2" if is_urgent else "#FFFFFF"
                        st.markdown(f"""
                        <div class="{anim_class}" style="background:{bg_style}; border:{border_style}; border-radius:12px; padding:15px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between;"><h4 style="margin:0; color:#0F172A;">{r.get('العنوان')}</h4><span style="background:white; padding:2px 8px; border-radius:8px; font-size:0.8rem; color:#64748B;">{r.get('التاريخ')}</span></div>
                            <p style="margin:5px 0 0 0; color:#475569">{r.get('الرابط')}</p><small style="color:{accent_color}; font-weight:bold;">🎯 الفئة: {r.get('الصف')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        kc1, kc2 = st.columns([1, 4])
                        msg_text = f"📢 *تعميم هام من منصة الأستاذ زياد*\n━━━━━━━━━━━━\n📌 *العنوان:* {r.get('العنوان')}\n📄 *التفاصيل:* {r.get('الرابط')}\n📅 *التاريخ:* {r.get('التاريخ')}\n━━━━━━━━━━━━"
                        grp_msg = urllib.parse.quote(msg_text)
                        kc2.link_button("📲 مشاركة عبر واتساب", f"https://api.whatsapp.com/send?text={grp_msg}", use_container_width=True)
                        if st.session_state.role == "teacher":
                            kc1.button("🗑️ حذف", key=f"del_btn_unique_{i}", type="secondary", on_click=perform_delete, args=(i,), use_container_width=True)
            else: st.info("💡 لا توجد تنبيهات منشورة حالياً.")

        # --- ⚙️ الإعدادات (المعلم فقط) ---
        if st.session_state.role == "teacher":
            with tab_settings:
                st.subheader("⚙️ إعدادات النظام")
                with st.expander("🛠️ أدوات الصيانة والنسخ الاحتياطي", expanded=True):
                    c1, c2 = st.columns(2)
                    
                    if c1.button("🔄 تحديث البيانات (Refresh)", use_container_width=True):
                        st.cache_data.clear()
                        if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                        st.session_state['show_refresh_success'] = True 
                        st.rerun()
                        
                    if c2.button("🧹 تصفير جميع النقاط", use_container_width=True):
                        try:
                            ws = sh.worksheet("students"); d = ws.get_all_values()
                            if len(d) > 1: 
                                ws.update(range_name=f"I2:I{len(d)}", values=[[0]]*(len(d)-1))
                                st.success("✅ تم تصفير جميع النقاط")
                                if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"خطأ: {e}")

                    if st.button("🧮 إعادة احتساب النقاط من السجل (تصحيح شامل)", type="primary", use_container_width=True):
                        try:
                            with st.spinner("جاري مراجعة السجلات وتصحيح أرصدة الطلاب..."):
                                df_beh = fetch_safe("behavior"); ws_st = sh.worksheet("students"); students_data = ws_st.get_all_records()
                                true_scores = {}
                                if not df_beh.empty:
                                    for _, row in df_beh.iterrows():
                                        raw_id = str(row.get('student_id', row.get('id', ''))).strip().split('.')[0]
                                        if not raw_id: continue
                                        match = re.search(r'\(([\+\-]?\d+)\)', str(row.get('type', '')))
                                        if match: true_scores[raw_id] = true_scores.get(raw_id, 0) + int(match.group(1))
                                headers = ws_st.row_values(1)
                                if 'النقاط' in headers:
                                    col_idx = headers.index('النقاط') + 1; new_values = []
                                    for st_row in students_data:
                                        sid_v = str(st_row.get('id', '')).strip().split('.')[0]
                                        new_values.append([true_scores.get(sid_v, 0)])
                                    from gspread.utils import rowcol_to_a1
                                    ws_st.update(f"{rowcol_to_a1(2, col_idx)}:{rowcol_to_a1(len(new_values) + 1, col_idx)}", new_values)
                                    st.success("✅ تم تصحيح جميع الأرصدة بنجاح!")
                                    if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                    st.cache_data.clear(); st.rerun()
                                else: st.error("لم يتم العثور على عمود 'النقاط'")
                        except Exception as e: st.error(f"حدث خطأ: {e}")

                st.divider()
                st.markdown("##### 📥 تنزيل نسخة كاملة من البيانات (Backup)")
                df_st_full = fetch_safe("students")
                if not df_st_full.empty:
                    b_st = io.BytesIO()
                    with pd.ExcelWriter(b_st, engine='xlsxwriter') as writer: df_st_full.to_excel(writer, index=False, sheet_name='Students')
                    st.download_button(label="📂 تنزيل بيانات الطلاب (Excel)", data=b_st.getvalue(), file_name=f"students_backup_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                
                df_gr_full = fetch_safe("grades")
                if not df_gr_full.empty:
                    b_gr = io.BytesIO()
                    with pd.ExcelWriter(b_gr, engine='xlsxwriter') as writer: df_gr_full.to_excel(writer, index=False, sheet_name='Grades')
                    st.download_button(label="📊 تنزيل سجل الدرجات (Excel)", data=b_gr.getvalue(), file_name=f"grades_backup_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

                with st.expander("📝 تهيئة الصفوف والدرجات"):
                    c_y, c_p = st.columns(2)
                    cy = c_y.text_input("العام الدراسي", st.session_state.get('current_year', '1447هـ'))
                    
                    # ✳️ الإضافة الجديدة: قائمة لاختيار الفترة النشطة
                    current_period_val = st.session_state.get('current_period', 'الفترة الأولى')
                    period_options = ["الفترة الأولى", "الفترة الثانية", "الفصل الثاني - فترة أولى", "الفصل الثاني - فترة ثانية"]
                    cp_index = period_options.index(current_period_val) if current_period_val in period_options else 0
                    cp = c_p.selectbox("الفترة الدراسية النشطة", period_options, index=cp_index)

                    cls = st.text_area("قائمة الصفوف (افصل بفاصلة)", ",".join(st.session_state.get('class_options', ['الرابع'])))
                    stg = st.text_area("قائمة المراحل", ",".join(st.session_state.get('stage_options', ['ابتدائي'])))
                    
                    c1, c2 = st.columns(2)
                    mt = c1.number_input("الدرجة العظمى (مشاركة)", 0, 100, st.session_state.get('max_tasks', 60))
                    mq = c2.number_input("الدرجة العظمى (اختبار)", 0, 100, st.session_state.get('max_quiz', 40))
                    
                    if st.button("💾 حفظ الإعدادات", type="primary"):
                        # ✳️ تحديث قاعدة البيانات لتشمل الفترة الجديدة في الخلية A7:B7
                        sh.worksheet("settings").batch_update([
                            {'range': 'A2:B2', 'values': [['max_tasks', mt]]}, 
                            {'range': 'A3:B3', 'values': [['max_quiz', mq]]},
                            {'range': 'A4:B4', 'values': [['current_year', cy]]}, 
                            {'range': 'A5:B5', 'values': [['class_list', cls]]},
                            {'range': 'A6:B6', 'values': [['stage_list', stg]]},
                            {'range': 'A7:B7', 'values': [['current_period', cp]]} # حفظ الفترة
                        ])
                        
                        st.session_state.max_tasks = mt
                        st.session_state.max_quiz = mq
                        st.session_state.current_year = cy
                        st.session_state.current_period = cp # تحديث الذاكرة
                        st.session_state.class_options = [x.strip() for x in cls.split(',') if x.strip()]
                        st.session_state.stage_options = [x.strip() for x in stg.split(',') if x.strip()]
                        
                        st.success(f"✅ تم الحفظ بنجاح! المنصة الآن تعمل على: {cp}")
                        if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                        st.cache_data.clear(); st.rerun()

                with st.expander("📤 استيراد البيانات (Excel) - سريع"):
                    up = st.file_uploader("رفع ملف Excel", type=['xlsx'])
                    ts = st.radio("نوع البيانات", ["students", "grades"], horizontal=True, format_func=lambda x: "بيانات الطلاب" if x == "students" else "الدرجات")
                    if st.button("🚀 بدء المزامنة السريعة", type="primary") and up:
                        try:
                            with st.spinner('جاري معالجة ورفع البيانات دفعة واحدة...'):
                                df = pd.read_excel(up).fillna("").dropna(how='all')
                                ws = sh.worksheet(ts)
                                
                                # ✳️ تحديث الهيدر تلقائياً إذا كنا نرفع درجات ولم يكن عمود period موجوداً
                                hd = ws.row_values(1)
                                if ts == "grades" and 'period' not in hd:
                                    ws.update_cell(1, len(hd)+1, 'period')
                                    hd.append('period')

                                records = ws.get_all_records()
                                
                                # ✳️ منطق ذكي للتحقق من التكرار (للطالب نتحقق من رقمه فقط، وللدرجات نتحقق من رقمه + اسم الفترة)
                                if ts == "grades":
                                    existing_keys = set(f"{str(r.get('student_id', '')).strip().split('.')[0]}_{str(r.get('period', 'الفترة الأولى')).strip()}" for r in records)
                                else:
                                    existing_keys = set(str(r.get('id', '')).strip().split('.')[0] for r in records)

                                new_rows_to_append = []
                                progress_bar = st.progress(0)
                                cp = st.session_state.get('current_period', 'الفترة الأولى') # جلب الفترة النشطة حالياً
                                
                                for idx, row in df.iterrows():
                                    d = row.to_dict()
                                    raw_id = str(d.get('student_id', d.get('id', ''))).strip().split('.')[0]
                                    if not raw_id or raw_id == '0' or raw_id.lower() == 'nan': continue
                                    
                                    if ts == "grades":
                                        d.update({
                                            "student_id": raw_id, 
                                            "p1": int(d.get('p1',0)), 
                                            "p2": int(d.get('p2',0)), 
                                            "perf": int(d.get('p1',0))+int(d.get('p2',0)), 
                                            "date": str(datetime.date.today()),
                                            "period": d.get('period', cp) # ✳️ حقن الفترة الحالية تلقائياً بدون تعب للمعلم
                                        })
                                        if 'id' in d: del d['id']
                                        check_key = f"{raw_id}_{d['period']}"
                                    else:
                                        d['id'] = raw_id; d['الجوال'] = clean_phone_number(d.get('الجوال',''))
                                        if 'النقاط' not in d or str(d.get('النقاط', '')).strip() == "": d['النقاط'] = 0
                                        check_key = raw_id
                                        
                                    if check_key not in existing_keys: 
                                        new_rows_to_append.append([str(d.get(k, "")) for k in hd])
                                        
                                    progress_bar.progress(min((idx + 1) / len(df), 1.0))

                                if new_rows_to_append: 
                                    ws.append_rows(new_rows_to_append)
                                    st.success(f"✅ تم إضافة {len(new_rows_to_append)} سجل جديد بنجاح لـ ({cp})!")
                                else: 
                                    st.info(f"💡 جميع البيانات المرفوعة موجودة مسبقاً في ({cp})، لم يتم إضافة جديد.")
                                    
                                if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                                st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"حدث خطأ أثناء المزامنة: {e}")
                
                    st.divider(); c1, c2 = st.columns(2)
                    b1 = io.BytesIO(); pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط"]).to_excel(b1, index=False)
                    c1.download_button("📥 قالب فارغ (طلاب)", b1.getvalue(), "students_template.xlsx", use_container_width=True)
                    b2 = io.BytesIO(); pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(b2, index=False)
                    c2.download_button("📥 قالب فارغ (درجات)", b2.getvalue(), "grades_template.xlsx", use_container_width=True)

                with st.expander("🔍 مدقق رصد الدرجات (كشف النواقص)", expanded=False):
                    st.markdown("##### قائمة الطلاب الذين لم يتم رصد درجاتهم بعد")
                    
                    df_st_audit = fetch_safe("students")
                    df_gr_audit = fetch_safe("grades")
                    
                    if not df_st_audit.empty:
                        df_st_audit['clean_id'] = df_st_audit.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                        
                        if not df_gr_audit.empty:
                            df_gr_audit['clean_id'] = df_gr_audit.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                            audit_merge = pd.merge(
                                df_st_audit[['clean_id', 'name', 'class', 'sem']], 
                                df_gr_audit[['clean_id', 'perf']], 
                                on='clean_id', 
                                how='left'
                            )
                            missing_grades = audit_merge[audit_merge['perf'].isna()]
                        else:
                            missing_grades = df_st_audit[['clean_id', 'name', 'class', 'sem']]

                        if not missing_grades.empty:
                            st.warning(f"⚠️ يوجد {len(missing_grades)} طالب لم ترصد لهم درجات.")
                            display_missing = missing_grades[['clean_id', 'name', 'class', 'sem']].rename(columns={
                                'clean_id': 'الرقم الأكاديمي',
                                'name': 'اسم الطالب',
                                'class': 'الصف',
                                'sem': 'المرحلة'
                            })
                            
                            st.dataframe(display_missing, use_container_width=True, hide_index=True)
                            
                            b_audit = io.BytesIO()
                            with pd.ExcelWriter(b_audit, engine='xlsxwriter') as writer:
                                display_missing.to_excel(writer, index=False, sheet_name='Missing_Grades')
                            
                            st.download_button(
                                label="📥 تحميل قائمة النواقص للطباعة",
                                data=b_audit.getvalue(),
                                file_name=f"missing_grades_{datetime.date.today()}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        else:
                            st.success("✅ جميع الطلاب المسجلين تم رصد درجاتهم بنجاح!")
                    else:
                        st.info("لا توجد بيانات طلاب للتدقيق.")

                with st.expander("🔐 إدارة المستخدمين (معلمين / إدارة)"):
                    t1, t2, t3 = st.tabs(["➕ إضافة مستخدم", "🔑 تعديل كلمة المرور", "🗑️ حذف مستخدم"])
                    with t1:
                        with st.form("add_u"):
                            nu = st.text_input("اسم المستخدم الجديد"); np = st.text_input("كلمة المرور", type="password")
                            nrole_label = st.selectbox("نوع الحساب والصلاحية", ["👨‍🏫 معلم (صلاحيات كاملة)", "👁️ إدارة (مشاهد وقراءة فقط)"])
                            if st.form_submit_button("إضافة المستخدم", type="primary"):
                                if nu and np:
                                    role_val = "teacher" if "معلم" in nrole_label else "viewer"
                                    safe_append_row("users", {"username": nu, "password_hash": hashlib.sha256(np.encode()).hexdigest(), "role": role_val})
                                    st.success(f"✅ تمت إضافة الحساب ({nu}) بنجاح كـ {role_val}.")
                                    st.cache_data.clear()
                                else: st.warning("الرجاء إكمال البيانات.")
                    with t2:
                        with st.form("chg_pass"):
                            df_u_edit = fetch_safe("users")
                            if not df_u_edit.empty:
                                target_u = st.selectbox("اختر المستخدم لتعديل رقمه السري:", df_u_edit['username'].tolist())
                                npwd = st.text_input("كلمة المرور الجديدة", type="password")
                                if st.form_submit_button("تحديث كلمة المرور", type="primary"):
                                    if npwd:
                                        idx = df_u_edit[df_u_edit['username']==target_u].index[0] + 2
                                        sh.worksheet("users").update_cell(idx, 2, hashlib.sha256(npwd.encode()).hexdigest())
                                        st.success(f"✅ تم تحديث كلمة المرور لـ ({target_u}).")
                                        st.cache_data.clear()
                                    else: st.warning("الرجاء إدخال كلمة المرور الجديدة.")
                            else: st.info("لا يوجد مستخدمين بعد.")
                    with t3:
                        df_u_del = fetch_safe("users")
                        if not df_u_del.empty:
                            del_u = st.selectbox("اختر المستخدم المراد حذفه:", [""] + df_u_del['username'].tolist())
                            if st.button("🗑️ حذف المستخدم نهائياً", type="primary"):
                                if del_u:
                                    if del_u == st.session_state.username: st.error("⚠️ لا يمكنك حذف حسابك الحالي!")
                                    else:
                                        idx = df_u_del[df_u_del['username']==del_u].index[0] + 2
                                        sh.worksheet("users").delete_rows(int(idx)); st.success(f"✅ تم حذف المستخدم ({del_u}).")
                                        st.cache_data.clear(); st.rerun()
                                else: st.warning("الرجاء اختيار مستخدم للحذف.")

        with tab_logout:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("تسجيل الخروج من لوحة التحكم", type="secondary"): 
                st.session_state.role = None
                if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                st.rerun()
                
        show_footer()

    # ==========================================
    # 👨‍🎓 5. واجهة الطالب (مع الألقاب التحفيزية)
    # ==========================================
    elif st.session_state.role == "student":
        sid = str(st.session_state.get('username', '')).strip()
        df_st = fetch_safe("students"); df_gr = fetch_safe("grades"); df_beh = fetch_safe("behavior"); df_ann = fetch_safe("exams")
        
        if not df_st.empty:
            df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
            info = df_st[df_st['clean_id'] == sid]
        else: info = pd.DataFrame()

        if not info.empty:
            s_dat = info.iloc[0]
            s_nm = s_dat.get('name', 'طالب'); s_cls = str(s_dat.get('class', '')).strip()
            pts = int(pd.to_numeric(s_dat.get('النقاط', 0), errors='coerce') or 0)

            if not df_ann.empty:
                df_ann['عاجل'] = df_ann['عاجل'].astype(str).str.strip(); df_ann['الصف'] = df_ann['الصف'].astype(str).str.strip()
                urg = df_ann[(df_ann['عاجل']=='نعم') & (df_ann['الصف'].isin(['الكل', s_cls]))]
                if not urg.empty:
                    u = urg.tail(1).iloc[0]
                    link_text = str(u.get('الرابط', ''))
                    link_display = f"<a href='{link_text}' target='_blank' style='color:{danger_color}; text-decoration:underline;'>اضغط هنا</a>" if link_text.startswith('http') else link_text if link_text.lower() != 'none' else ""
                    st.markdown(f"<div class='urgent-box'>🚨 {u.get('العنوان')}<br><small style='color:{danger_color}'>{link_display}</small></div>", unsafe_allow_html=True)

            st.markdown(f"""
                <div class="welcome-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><h2 style="color:white; margin:0; font-size:1.5rem;">👋 أهلاً بك، {s_nm}</h2><p style="color:#DBEAFE; margin:5px 0 0 0;">{s_cls}</p></div>
                        <div style="background:rgba(255,255,255,0.2); padding:5px 15px; border-radius:12px;"><span style="font-weight:bold; font-size:0.9rem; color:#FFFFFF;">ID: {sid}</span></div>
                    </div>
                </div>
                <div class="points-banner">
                    <p style="margin:0; opacity:0.9; font-size:0.9rem;">رصيد النقاط الحالي</p>
                    <h1 style="margin:0; font-size:3.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{pts}</h1>
                    <p style="margin:0; font-size:0.8rem;">استمر في التفوق!</p>
                </div>
                <div class="medal-flex">
                    <div class="m-card {'m-active' if pts>=100 else ''}" style="color: {warning_color};">🥇<br><b>ذهبي</b></div>
                    <div class="m-card {'m-active' if pts>=50 else ''}" style="color: {sub_text};">🥈<br><b>فضي</b></div>
                    <div class="m-card m-active" style="color: #B45309;">🥉<br><b>برونزي</b></div>
                </div>
            """, unsafe_allow_html=True)

            tabs = st.tabs(["📢 التنبيهات", "📝 السلوك", "📊 الدرجات", "🏆 الشرف", "⚙️ الإعدادات"])

            with tabs[0]: 
                st.caption("التعاميم والتنبيهات")
                if not df_ann.empty:
                    anns = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_cls])]
                    for _, r in anns.iloc[::-1].iterrows():
                        row_link = str(r.get('الرابط', ''))
                        row_link_display = f"<a href='{row_link}' target='_blank' style='color:{primary_color}; text-decoration:underline;'>اضغط هنا للفتح</a>" if row_link.startswith('http') else row_link if row_link.lower() != 'none' else ""
                        st.markdown(f"""
                        <div class='mobile-list-item'>
                            <div style="width:100%">
                                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><b>📢 {r.get('العنوان')}</b><small style="background:#EFF6FF; color:{primary_color}; padding:2px 6px; border-radius:4px;">{r.get('التاريخ')}</small></div>
                                <span style="color:#475569; font-size:0.9rem;">{row_link_display}</span>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else: st.info("لا يوجد تنبيهات حالياً")

            with tabs[1]: 
                st.caption("سجل السلوك والملاحظات")
                if not df_beh.empty:
                    df_beh['clean_id'] = df_beh.iloc[:,0].astype(str).str.split('.').str[0]
                    nts = df_beh[df_beh['clean_id']==sid]
                    if not nts.empty:
                        for _, n in nts.iloc[::-1].iterrows():
                            color = danger_color if "سلبي" in str(n.get('type')) else primary_color
                            st.markdown(f"<div class='mobile-list-item' style='border-right: 4px solid {color};'><div><b style='color:{color}'>{n.get('type')}</b><p style='margin:0; font-size:0.9rem; color:#334155;'>{n.get('note')}</p><small style='color:#94A3B8;'>{n.get('date')}</small></div></div>", unsafe_allow_html=True)
                    else: st.success("🌟 سجلك نظيف تماماً!")

            with tabs[2]: 
                cp = st.session_state.get('current_period', 'الفترة الأولى')
                st.caption(f"درجاتي - {cp}")
                
                if not df_gr.empty:
                    df_gr = df_gr.copy()
                    df_gr['clean_id'] = df_gr.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                    
                    # ✳️ ملء الفراغات لضمان ظهور درجات الطالب في الفترة الأولى
                    if 'period' not in df_gr.columns: df_gr['period'] = 'الفترة الأولى'
                    df_gr['period'] = df_gr['period'].replace(['', None, 'nan'], 'الفترة الأولى')
                    
                    grs = df_gr[(df_gr['clean_id']==sid) & (df_gr['period']==cp)]
                    # ... بقية الكود يكمل كما هو ...
                    
                    if not grs.empty:
                        g = grs.iloc[0]
                        max_total = st.session_state.max_tasks + st.session_state.max_quiz
                        perf_score = int(pd.to_numeric(g.get('perf', 0), errors='coerce') or 0)
                        percentage = (perf_score / max_total) * 100 if max_total > 0 else 0
                        
                        if percentage >= 90: title, title_color = "🌟 أسطورة المنصة", warning_color
                        elif percentage >= 80: title, title_color = "🚀 بطل مبدع", accent_color
                        elif percentage >= 70: title, title_color = "👍 متألق ومجتهد", success_color
                        elif percentage >= 60: title, title_color = "💪 واصل تقدمك", primary_color
                        else: title, title_color = "🌱 أنت قادر على الأفضل", sub_text
    
                        st.markdown(f"""
                        <div class='mobile-list-item'><span>📝 المشاركة والواجبات</span><b>{g.get('p1')} / {st.session_state.max_tasks}</b></div>
                        <div class='mobile-list-item'><span>✍️ الاختبارات القصيرة</span><b>{g.get('p2')} / {st.session_state.max_quiz}</b></div>
                        <div class='mobile-list-item' style='background:#EFF6FF; border-color:{accent_color}; display:flex; flex-direction:column; align-items:flex-start;'>
                            <div style="width:100%; display:flex; justify-content:space-between;">
                                <span style="color:{accent_color}; font-weight:bold;">🏆 المجموع النهائي ({cp})</span><b style="color:{accent_color}; font-size:1.2rem;">{perf_score} / {max_total}</b>
                            </div>
                            <div style="margin-top:8px; width:100%; text-align:center; padding:5px; background:white; border-radius:8px; color:{title_color}; font-weight:bold; font-size:1.1rem; border:1px solid {title_color}33;">
                                {title}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
                        if percentage >= 90:
                            st.divider()
                            st.success("🎉 مبروك! لتفوقك وحصولك على درجة الامتياز، تم تفعيل ميزة استخراج 'شهادة التفوق'.")
                            certificate_html = f"""
                        <!DOCTYPE html>
                        <html dir="rtl" lang="ar">
                        <head>
                            <meta charset="UTF-8">
                            <title>شهادة تفوق - {s_nm}</title>
                            <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
                            <style>
                                * {{ box-sizing: border-box; }}
                                body {{
                                    margin: 0; padding: 0;
                                    background-color: #f0f2f5;
                                    display: flex; justify-content: center; align-items: center;
                                    min-height: 100vh;
                                }}
                                .cert-page {{
                                    width: 297mm; height: 210mm;
                                    padding: 10mm;
                                    background: #ffffff;
                                    position: relative;
                                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                                    overflow: hidden;
                                }}
                                .border-outer {{
                                    border: 14px solid #193b68;
                                    height: 100%; width: 100%;
                                    padding: 6px;
                                    position: relative;
                                }}
                                .border-inner {{
                                    border: 3px solid #b68a36;
                                    height: 100%; width: 100%;
                                    position: relative;
                                    padding: 30px 40px;
                                    text-align: center;
                                    background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
                                    background-size: 25px 25px;
                                    -webkit-print-color-adjust: exact !important;
                                    print-color-adjust: exact !important;
                                }}
                                
                                .corner {{ position: absolute; width: 30px; height: 30px; border: 4px solid #b68a36; }}
                                .tl {{ top: -8px; left: -8px; border-right: none; border-bottom: none; }}
                                .tr {{ top: -8px; right: -8px; border-left: none; border-bottom: none; }}
                                .bl {{ bottom: -8px; left: -8px; border-right: none; border-top: none; }}
                                .br {{ bottom: -8px; right: -8px; border-left: none; border-top: none; }}

                                .top-badge {{ position: absolute; top: 25px; left: 35px; width: 90px; height: 90px; }}

                                h1 {{ 
                                    font-family: 'Aref Ruqaa', serif; font-size: 70px; color: #b68a36; 
                                    margin: 0; font-weight: normal; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                                }}
                                
                                h2 {{ 
                                    font-family: 'Cairo', sans-serif; font-size: 34px; color: #193b68; 
                                    margin: 5px 0 25px 0; font-weight: 900;
                                    display: flex; justify-content: center; align-items: center; gap: 15px;
                                }}
                                
                                p.intro {{ font-family: 'Cairo', sans-serif; font-size: 22px; color: #193b68; margin-bottom: 10px; }}
                                
                                .student-name {{ 
                                    font-family: 'Cairo', sans-serif; font-size: 55px; font-weight: 900; color: #d32f2f; 
                                    margin: 15px auto; display: inline-block;
                                    border-bottom: 3px solid #b68a36; padding-bottom: 5px; padding-left: 30px; padding-right: 30px;
                                    letter-spacing: 1px;
                                }}
                                
                                .reason-container {{ margin-top: 15px; margin-bottom: 25px; }}
                                
                                p.reason {{ 
                                    font-family: 'Cairo', sans-serif; font-size: 24px; font-weight: 600; color: #444; 
                                    line-height: 1.8; margin: 0;
                                }}
                                
                                .footer-section {{ 
                                    display: flex; justify-content: space-between; align-items: flex-end; 
                                    margin-top: 30px; padding: 0 30px; font-family: 'Cairo', sans-serif; 
                                }}
                                
                                .sig-box, .date-box {{ text-align: center; color: #193b68; width: 220px; }}
                                .sig-title {{ font-size: 22px; font-weight: bold; }}
                                .sig-line {{ border-bottom: 1px solid #b68a36; width: 150px; margin: 8px auto; }}
                                .sig-name {{ font-family: 'Aref Ruqaa', serif; font-size: 34px; color: #193b68; line-height: 1; }}
                                .date-val {{ font-size: 22px; font-weight: bold; color: #333; margin-top: 8px; }}

                                .stamp-wrapper {{
                                    display: flex; justify-content: center; align-items: center;
                                    margin-bottom: 10px; width: 150px;
                                }}

                                @media print {{
                                    @page {{ size: A4 landscape; margin: 0mm; }}
                                    body {{ min-height: auto; align-items: flex-start; justify-content: flex-start; background: white; }}
                                    .cert-page {{ padding: 0; box-shadow: none; width: 297mm; height: 210mm; overflow: hidden; page-break-after: avoid; page-break-before: avoid; }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="cert-page">
                                <div class="border-outer">
                                    <div class="border-inner">
                                        <div class="corner tl"></div><div class="corner tr"></div>
                                        <div class="corner bl"></div><div class="corner br"></div>
                                        
                                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgZmlsbD0iIzE5M2I2OCIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjUiLz48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIzMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1kYXNoYXJyYXk9IjQgNCIvPjxwYXRoIGQ9Ik0zNSA2NUw1MCA0MEw2NSA2NVoiIGZpbGw9IiNiNjhhMzYiLz48cGF0aCBkPSJNMzUgMzVMNjUgMzVMMTUgNjVIMzVaIiBmaWxsPSIjYjY4YTM2IiBvcGFjaXR5PSIwLjciLz48L3N2Zz4=" class="top-badge">

                                        <h1>شهادة شكر وتقدير</h1>
                                        
                                        <h2>
                                            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDE1LjA5IDguMjYgMjIgOS4yNyAxNyAxNC4xNCAxOC4xOCAyMS4wMiAxMiAxNy43NyA1LjgyIDIxLjAyIDcgMTQuMTQgMiA5LjI3IDguOTEgOC4yNiAxMiAyIiBmaWxsPSIjYjY4YTM2IiAvPjwvc3ZnPg==" style="width:30px; height:30px;">
                                            وسام التميز الأكاديمي
                                            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjYjY4YTM2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDE1LjA5IDguMjYgMjIgOS4yNyAxNyAxNC4xNCAxOC4xOCAyMS4wMiAxMiAxNy43NyA1LjgyIDIxLjAyIDcgMTQuMTQgMiA5LjI3IDguOTEgOC4yNiAxMiAyIiBmaWxsPSIjYjY4YTM2IiAvPjwvc3ZnPg==" style="width:30px; height:30px;">
                                        </h2>

                                        <p class="intro">يتقدم الأستاذ/ <strong>زياد المعمري</strong> بوافر الشكر والتقدير للطالب المبدع والمتألق:</p>
                                        
                                        <div class="student-name">{s_nm}</div>
                                        
                                        <div class="reason-container">
                                            <p class="reason">وذلك نظير تفوقه العلمي وحصوله على تقدير <b style="color:#d32f2f;">ممتاز</b> في مادة اللغة الإنجليزية.</p>
                                            <p class="reason">متمنين له دوام التوفيق ومزيداً من التألق والنجاح.</p>
                                        </div>

                                        <div class="footer-section">
                                            <div class="date-box">
                                                <div class="sig-title">تاريخ الإصدار</div>
                                                <div class="sig-line"></div>
                                                <div class="date-val">{datetime.date.today().strftime('%Y-%m-%d')}</div>
                                            </div>
                                            
                                            <div class="stamp-wrapper">
                                                <div style="width: 140px; height: 140px; border: 3px dashed #d32f2f; border-radius: 50%; transform: rotate(-15deg); color: #d32f2f; text-align: center; opacity: 0.85; position: relative; padding-top: 25px; margin: 0 auto; background-color: rgba(255, 255, 255, 0.7);">
                                                    <div style="position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px; border: 1px solid #d32f2f; border-radius: 50%;"></div>
                                                    <div style="font-family: 'Cairo', sans-serif; font-size: 16px; font-weight: 900; line-height: 1; margin-top: 5px;">وسام</div>
                                                    <div style="font-family: 'Aref Ruqaa', serif; font-size: 34px; font-weight: bold; line-height: 1.2; margin: 2px 0;">ختم التميز</div>
                                                    <div style="font-family: 'Cairo', sans-serif; font-size: 12px; font-weight: bold; line-height: 1;">الأكاديمي</div>
                                                </div>
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
                        </body>
                        </html>
                        """
                            
                            try:
                                from weasyprint import HTML
                                with st.spinner("⏳ جاري إعداد شهادة التفوق بصيغة PDF..."):
                                    pdf_bytes = HTML(string=certificate_html).write_pdf()
                                    
                                    st.download_button(
                                        label="📥 تحميل شهادة التفوق (PDF مباشر)",
                                        data=pdf_bytes,
                                        file_name=f"Certificate_{sid}_{s_nm}.pdf",
                                        mime="application/pdf",
                                        type="primary",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.error(f"⚠️ فشل توليد الـ PDF بسبب: {e}")
                                st.info("💡 ملاحظة: تم تفعيل تحميل نسخة الويب لسرعة الوصول.")
                                st.download_button(
                                    label="📜 استخراج شهادة التفوق (نسخة ويب)",
                                    data=certificate_html,
                                    file_name=f"Certificate_{sid}.html",
                                    mime="text/html",
                                    type="primary",
                                    use_container_width=True
                                )
    
                    else: st.info(f"لم يتم رصد درجات لك في {cp} حتى الآن.")
            with tabs[3]: 
                st.caption("لوحة الشرف (أفضل 10 طلاب)")
                df_st['p_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
                for i, (_, r) in enumerate(df_st.sort_values('p_num', ascending=False).head(10).iterrows(), 1):
                    ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
                    sty = f"border:2px solid {primary_color}; background:#EFF6FF;" if str(r['clean_id']) == sid else ""
                    st.markdown(f"<div class='mobile-list-item' style='{sty}'><div style='display:flex; align-items:center; gap:10px;'><span style='font-weight:900; font-size:1.2rem; width:30px;'>{ic}</span><span>{r['name']}</span></div><span style='color:{warning_color}; font-weight:900;'>{int(r['p_num'])}</span></div>", unsafe_allow_html=True)

            with tabs[4]:
                st.caption("إدارة الملف الشخصي")
                with st.form("my_profile"):
                    nm = st.text_input("📧 البريد الإلكتروني", s_dat.get('الإيميل',''))
                    np = st.text_input("📱 رقم الجوال", s_dat.get('الجوال',''))
                    if st.form_submit_button("💾 تحديث بياناتي", type="primary", use_container_width=True):
                        try:
                            fp = clean_phone_number(np) if np else ""
                            ws = sh.worksheet("students"); c = ws.find(sid)
                            if c:
                                h = ws.row_values(1)
                                if 'الإيميل' in h and 'الجوال' in h:
                                    ws.update_cell(c.row, h.index('الإيميل')+1, nm); ws.update_cell(c.row, h.index('الجوال')+1, fp); st.success("✅ تم التحديث")
                                else: st.error("خطأ هيكلي")
                        except Exception as e: st.error(f"خطأ: {e}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚪 تسجيل الخروج", type="secondary", use_container_width=True): 
                    st.session_state.role = None
                    if 'db_loaded' in st.session_state: del st.session_state['db_loaded']
                    st.rerun()

        else: st.error("عذراً، لم يتم العثور على بياناتك"); st.button("العودة للقائمة الرئيسية", on_click=st.rerun)
        
        show_footer()
