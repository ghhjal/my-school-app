import streamlit as st
import pandas as pd
import gspread
import urllib.parse
import datetime
import hashlib
import io
import re
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 تعريف الألوان (ثيم البنفسجي مع حقول محايدة) ---
main_bg = "#f5f3ff"
card_bg = "#ffffff"
text_color = "#1e1b4b"
sub_text = "#6b7280"
border_color = "#e0e7ff"
primary_color = "#4f46e5"
accent_color = "#818cf8"
header_grad = "linear-gradient(135deg, #4338ca 0%, #7c3aed 100%)"
shadow_val = "0 4px 6px -1px rgba(67, 56, 202, 0.1), 0 2px 4px -1px rgba(67, 56, 202, 0.06)"

# --- [الدوال المساعدة والاتصال الذكي] ---

# 🚀 تجديد الاتصال تلقائياً كل 45 دقيقة لمنع الانقطاع
@st.cache_resource(ttl=2700) 
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e: 
        st.error(f"⚠️ خطأ اتصال بسيرفر جوجل: {e}")
        return None

sh = get_gspread_client()

# 🚀 دالة تسوية النصوص العربية لتسهيل البحث
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

# 🚀 جلب البيانات مع معالجة الانقطاع
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
if "class_options" not in st.session_state:
    try:
        sett = sh.worksheet("settings").get_all_records()
        s_map = {row['key']: row['value'] for row in sett}
        st.session_state.max_tasks = int(s_map.get('max_tasks', 60))
        st.session_state.max_quiz = int(s_map.get('max_quiz', 40))
        st.session_state.current_year = str(s_map.get('current_year', '1447هـ'))
        st.session_state.class_options = [x.strip() for x in str(s_map.get('class_list', 'الأول')).split(',') if x.strip()]
        st.session_state.stage_options = [x.strip() for x in str(s_map.get('stage_list', 'ابتدائي')).split(',') if x.strip()]
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
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
    
    .block-container {{ padding-top: 0rem; padding-bottom: 5rem; max-width: 1000px; }}
    
    .header-container {{
        background: {header_grad};
        padding: 80px 20px 40px 20px;
        border-radius: 0 0 40px 40px;
        margin: -60px -5rem 30px -5rem;
        box-shadow: 0 10px 30px -10px rgba(67, 56, 202, 0.5);
        color: white; text-align: center;
        position: relative; overflow: visible;
    }}
    
    .logo-icon {{ 
        font-size: 5rem; margin-bottom: 15px; display: inline-block;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
        animation: float 4s ease-in-out infinite;
    }}
    
    .header-text h1 {{ margin: 0; font-size: 2.5rem; font-weight: 900; color: #fff !important; }}
    .header-text p {{ margin: 5px 0 0 0; color: #e0e7ff; font-size: 1.1rem; font-weight: 500; }}
    
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] {{ 
        background-color: #f1f5f9 !important; border: 2px solid #cbd5e1 !important; border-radius: 16px !important; height: 55px; 
    }}
    input, textarea, select {{ 
        color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: {primary_color} !important;
        background-color: transparent !important; font-weight: 700 !important; font-size: 1.1rem !important;
    }}
    ::placeholder {{ color: #64748b !important; opacity: 1 !important; -webkit-text-fill-color: #64748b !important; }}
    div[data-baseweb="select"] div {{ color: #0f172a !important; }}
    
    div.stButton > button {{
        background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%) !important;
        color: white !important; border: none !important; font-weight: 800 !important;
        font-size: 1.1rem !important; border-radius: 16px !important; padding: 12px 20px !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); transition: transform 0.2s; width: 100%; height: 55px;
    }}
    div.stButton > button:active {{ transform: scale(0.98); }}
    
    .app-card {{ background: {card_bg}; padding: 20px; border-radius: 24px; box-shadow: {shadow_val}; border: 1px solid #e0e7ff; margin-bottom: 15px; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; background-color: transparent; border: none; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; background-color: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; color: #64748b; font-weight: bold; flex: 1; justify-content: center; }}
    .stTabs [aria-selected="true"] {{ background-color: {primary_color} !important; color: white !important; border: none !important; box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3); }}

    .mobile-list-item {{ background: white; border-radius: 16px; padding: 16px; margin-bottom: 12px; border: 1px solid #e0e7ff; box-shadow: 0 2px 4px rgba(0,0,0,0.03); display: flex; align-items: center; justify-content: space-between; }}
    
    .medal-flex {{ display: flex; gap: 10px; margin: 20px 0; direction: rtl; }}
    .m-card {{ flex: 1; background: white; padding: 15px 5px; border-radius: 20px; text-align: center; border: 1px solid #e0e7ff; box-shadow: {shadow_val}; }}
    .m-active {{ border: 2px solid #f59e0b !important; background: linear-gradient(to bottom right, #fffbeb, #fef3c7) !important; }}
    
    .points-banner {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 25px; border-radius: 24px; text-align: center; margin-bottom: 25px; }}
    .welcome-card {{ background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%); color: white; padding: 20px; border-radius: 24px; margin-bottom: 15px; }}

    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes pulse-red {{ 0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }} 70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }} }}
    .urgent-box {{ background-color: #fef2f2; border: 2px solid #ef4444; color: #b91c1c; padding: 15px; border-radius: 16px; text-align: center; animation: pulse-red 2s infinite; font-weight: bold; margin-bottom: 25px; }}

    @media (max-width: 768px) {{
        .header-container {{ padding: 70px 20px 30px 20px; }}
        .header-text h1 {{ font-size: 1.8rem; }}
        .logo-icon {{ font-size: 4rem; }}
    }}
    </style>

    <div class="header-container">
        <div class="header-content">
            <div class="logo-icon">🎓</div>
            <div class="header-text">
                <h1>منصة زياد الذكية</h1>
                <p>بوابة التعليم الذكية 2026</p>
            </div>
        </div>
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
# --- 🏗️ تأسيس المخزن المحلي (يُنفذ مرة واحدة فقط) ---
if 'db_loaded' not in st.session_state:
    with st.spinner("⏳ جاري تحميل قاعدة البيانات المركزية... (يرجى الانتظار لمرة واحدة فقط)"):
        st.session_state.df_students = fetch_safe("students")
        st.session_state.df_grades = fetch_safe("grades")
        st.session_state.df_behavior = fetch_safe("behavior")
        st.session_state.db_loaded = True
# ==========================================
# 👨‍🏫 4. واجهة المعلم / الإدارة (مشاهد)
# ==========================================
elif st.session_state.role in ["teacher", "viewer"]:
    
    if st.session_state.role == "teacher":
        menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "⚙️ الإعدادات", "🛑 خروج"])
        tab_students, tab_eval, tab_alerts, tab_settings, tab_logout = menu[0], menu[1], menu[2], menu[3], menu[4]
    else:
        menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التنبيهات", "🛑 خروج"])
        tab_students, tab_eval, tab_alerts, tab_logout = menu[0], menu[1], menu[2], menu[3]
        
    # --- 👥 الطلاب ---
    with tab_students:
        st.subheader("👥 إدارة الطلاب والتقارير")
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            df_st['clean_id'] = df_st.iloc[:,0].astype(str).str.split('.').str[0].str.strip()
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            
            # 🚀 تم إضافة التبويب الجديد "المتفوقين" هنا
            sub_tabs = st.tabs(["📋 قائمة الطلاب", "🏆 لوحة الشرف (نقاط)", "🌟 المتفوقين (90%+)", "📑 تقرير الطالب الشامل"])
            
            # --- 1. قائمة الطلاب ---
            with sub_tabs[0]:
                c1, c2, c3 = st.columns(3)
                c1.metric("العدد الإجمالي", len(df_st))
                c2.metric("الفصول", len(df_st.iloc[:,2].unique()) if len(df_st.columns)>2 else 0)
                c3.metric("متوسط النقاط", round(df_st['النقاط'].mean(), 1))
                st.divider()

                if st.session_state.role == "teacher":
                    with st.expander("➕ إضافة طالب جديد", expanded=False):
                        with st.form("add_st_v26", clear_on_submit=True):
                            c1, c2 = st.columns(2)
                            f_id = c1.text_input("🔢 الرقم الأكاديمي")
                            f_name = c2.text_input("👤 الاسم")
                            c3, c4, c5 = st.columns(3)
                            f_class = c3.selectbox("الصف", st.session_state.class_options)
                            f_stage = c4.selectbox("المرحلة", st.session_state.stage_options)
                            f_year = c5.text_input("العام", st.session_state.current_year)
                            c6, c7 = st.columns(2)
                            f_phone = c6.text_input("📱 الجوال")
                            f_mail = c7.text_input("📧 الإيميل")
                            
                            if st.form_submit_button("✅ حفظ", type="primary"):
                                if f_id and f_name:
                                    if f_id.strip() in df_st['clean_id'].values:
                                        st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً!")
                                    else:
                                        cl_p = clean_phone_number(f_phone) if f_phone else ""
                                        st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "الجوال": cl_p, "الإيميل": f_mail.strip(), "النقاط": "0"}
                                        if safe_append_row("students", st_map):
                                            st.success("✅ تم الحفظ"); st.cache_data.clear(); st.rerun()
                                else: st.warning("أكمل البيانات")
                
                st.write("---")
                
                sq = st.text_input("🔍 بحث في القائمة:")
                if sq: 
                    norm_sq = normalize_arabic(sq)
                    mask = df_st.iloc[:,0].astype(str).str.contains(norm_sq) | df_st.iloc[:,1].astype(str).apply(normalize_arabic).str.contains(norm_sq)
                    st.dataframe(df_st[mask], use_container_width=True, hide_index=True)
                else: 
                    st.dataframe(df_st, use_container_width=True, hide_index=True)

                if st.session_state.role == "teacher":
                    with st.expander("🗑️ حذف طالب"):
                        dq = st.text_input("بحث للحذف:", key="dq")
                        if dq:
                            norm_dq = normalize_arabic(dq)
                            mask = df_st.iloc[:,0].astype(str).str.contains(norm_dq) | df_st.iloc[:,1].astype(str).apply(normalize_arabic).str.contains(norm_dq)
                            for i, r in df_st[mask].iterrows():
                                if st.button(f"حذف {r.iloc[1]}", key=f"d{i}"):
                                    sh.worksheet("students").delete_rows(int(i)+2); st.success("تم"); st.cache_data.clear(); st.rerun()
            
            # --- 2. لوحة الشرف (النقاط والسلوك) ---
            with sub_tabs[1]:
                st.markdown("#### 🌟 أفضل 10 طلاب (حسب نقاط التميز)")
                top_10 = df_st.sort_values('النقاط', ascending=False).head(10)
                for i, (_, r) in enumerate(top_10.iterrows(), 1):
                    ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
                    border_color = "#f59e0b" if i<=3 else "#cbd5e1"
                    st.markdown(f"""
                        <div style='background:#ffffff; border:1px solid #e2e8f0; border-right:5px solid {border_color}; padding:15px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                            <div style='display:flex; align-items:center; gap:15px;'>
                                <span style='font-size:1.5rem; font-weight:bold; width:30px; text-align:center;'>{ic}</span>
                                <div>
                                    <b style='font-size:1.1rem; color:#1e3a8a;'>{r['name']}</b><br>
                                    <small style='color:#64748b;'>🏫 الصف: {r.get('class', '')} | 🆔 ID: {r['clean_id']}</small>
                                </div>
                            </div>
                            <div style='background:#fef3c7; padding:5px 15px; border-radius:8px; color:#b45309; font-weight:900; font-size:1.2rem;'>
                                {int(r['النقاط'])} نقطة
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            # --- 3. المتفوقين (أكاديمياً 90% فما فوق) ---
            with sub_tabs[2]:
                st.markdown("#### 🎓 لوحة المتفوقين أكاديمياً (نسبة 90% فما فوق)")
                df_g = fetch_safe("grades")
                
                if not df_g.empty and not df_st.empty:
                    df_g['clean_id'] = df_g.iloc[:,0].astype(str).str.split('.').str[0]
                    # دمج جدول الدرجات مع جدول الطلاب لجلب الأسماء
                    merged_df = pd.merge(df_g, df_st[['clean_id', 'name', 'class']], on='clean_id', how='inner')
                    
                    if not merged_df.empty:
                        max_total = st.session_state.max_tasks + st.session_state.max_quiz
                        if max_total > 0:
                            merged_df['perf_num'] = pd.to_numeric(merged_df['perf'], errors='coerce').fillna(0)
                            merged_df['percentage'] = (merged_df['perf_num'] / max_total) * 100
                            
                            # فلترة من حصل على 90% فأكثر وترتيبهم
                            top_academic = merged_df[merged_df['percentage'] >= 90].sort_values('percentage', ascending=False)
                            
                            if not top_academic.empty:
                                for i, (_, r) in enumerate(top_academic.iterrows(), 1):
                                    st.markdown(f"""
                                        <div style='background:#ffffff; border:1px solid #e2e8f0; border-right:5px solid #059669; padding:15px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                                            <div style='display:flex; align-items:center; gap:15px;'>
                                                <span style='font-size:1.5rem; font-weight:bold; width:30px; text-align:center;'>🎓</span>
                                                <div>
                                                    <b style='font-size:1.1rem; color:#064e3b;'>{r['name']}</b><br>
                                                    <small style='color:#64748b;'>🏫 الصف: {r.get('class', '')} | 🆔 ID: {r['clean_id']}</small>
                                                </div>
                                            </div>
                                            <div style='background:#dcfce7; padding:5px 15px; border-radius:8px; color:#047857; font-weight:900; font-size:1.2rem;'>
                                                {int(r['percentage'])}%
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("لم يصل أحد لنسبة 90% حتى الآن. بانتظار إبداعات الأبطال!")
                    else:
                        st.info("لا توجد درجات مطابقة للطلاب.")
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
                    
                    grades_html_table = "<div style='text-align:center; padding:20px; color:#64748b;'>لا توجد درجات مرصودة لهذا الطالب.</div>"
                    behavior_html_table = "<div style='text-align:center; padding:20px; color:#64748b;'>✨ سجل السلوك نظيف.</div>"

                    st.markdown("##### 📊 الدرجات الأكاديمية")
                    df_g = fetch_safe("grades")
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
                                    <td style="text-align: center; font-weight:bold; color:#1e40af;">{g_inf.get('perf', 0)}</td>
                                </tr>
                            </table>
                            """
                        else: st.info("لم يتم رصد درجات أكاديمية لهذا الطالب بعد.")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### 📜 سجل الملاحظات والسلوك التفصيلي")
                    df_b = fetch_safe("behavior")
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
                            body {{ font-family: 'Cairo', sans-serif; background-color: #f8fafc; padding: 20px; color: #334155; line-height: 1.6; }}
                            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                            .banner {{ background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; text-align: center; padding: 15px; border-radius: 12px; margin-bottom: 30px; font-weight: 800; font-size: 24px; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3); }}
                            .header {{ text-align: center; margin-bottom: 30px; }}
                            .header h1 {{ color: #0f172a; margin-bottom: 5px; font-weight: 800; font-size: 28px; }}
                            .header p {{ color: #64748b; font-size: 14px; margin-top: 0; }}
                            .student-card {{ background: linear-gradient(to left, #eff6ff, #ffffff); border-right: 5px solid #3b82f6; padding: 25px; border-radius: 12px; margin-bottom: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }}
                            .student-card h2 {{ grid-column: 1 / -1; margin-top: 0; color: #1e40af; border-bottom: 1px dashed #bfdbfe; padding-bottom: 15px; margin-bottom: 10px; }}
                            .student-card .info-item {{ font-size: 16px; }}
                            .student-card .info-item span {{ font-weight: 800; color: #475569; margin-left: 5px; }}
                            h3 {{ color: #4338ca; display: flex; align-items: center; gap: 10px; margin-top: 40px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
                            .table-container {{ overflow: hidden; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px; border: 1px solid #e2e8f0; }}
                            table {{ width: 100%; border-collapse: collapse; background: #fff; text-align: right; }}
                            th {{ background-color: #f8fafc; color: #334155; font-weight: 800; padding: 15px; border-bottom: 2px solid #e2e8f0; }}
                            td {{ padding: 15px; border-bottom: 1px solid #f1f5f9; color: #475569; font-weight: 600; }}
                            tr:last-child td {{ border-bottom: none; }}
                            tr:nth-child(even) {{ background-color: #f8fafc; }}
                            .footer-sigs {{ margin-top: 60px; display: flex; justify-content: space-between; align-items: center; padding-top: 30px; border-top: 2px dashed #cbd5e1; color: #334155; font-weight: 800; }}
                            .footer-sigs > div {{ text-align: center; flex: 1; }}
                            .sig-line {{ margin-top: 30px; color: #94a3b8; font-weight: normal; }}
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
                                <div>المعلم<div style="margin-top: 20px; color: #1e40af; font-size: 18px;">زياد المعمري</div></div>
                                <div>الموجه الطلابي<div class="sig-line">.................................</div></div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        st.download_button(label="🖨️ تحميل التقرير (عصري)", data=final_report, file_name=f"Report_{sid}_{s_inf['name']}.html", mime="text/html", type="primary")
                    with col_btn2: st.caption("👈 التصميم الجديد جاهز! حمل الملف واضغط Ctrl+P للطباعة.")
            
    # 📊 التقييم
    # 📊 التقييم والمتابعة (فردي وجماعي)
    with tab_eval:
        st.markdown("### 📊 التقييم والمتابعة")
        
        # 🚀 تقسيم التقييم إلى فردي وجماعي
        eval_tabs = st.tabs(["👤 التقييم الفردي", "👥 الرصد الجماعي السريع"])
        
        # --- 1. التقييم الفردي (محدث بنظام الذاكرة المؤقتة لتسريع الأداء) ---
        with eval_tabs[0]:
            # تهيئة سلة المهملات (Buffer) في الذاكرة المؤقتة إذا لم تكن موجودة
            if 'pending_behaviors' not in st.session_state:
                st.session_state.pending_behaviors = []
            
            df_ev = fetch_safe("students")
            if not df_ev.empty:
                st_dict = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_ev.iterrows()}
                sel = st.selectbox("🎯 اختر الطالب من القائمة:", [""] + list(st_dict.keys()), key="single_eval_sel")
                
                if sel:
                    sid = str(st_dict[sel]).strip().split('.')[0]
                    s_inf = df_ev[df_ev.iloc[:,0].astype(str).str.split('.').str[0] == sid].iloc[0]
                    s_nm = s_inf['name']; clp = clean_phone_number(s_inf.get('الجوال','')); s_eml = s_inf.get('الإيميل', '')
                    
                    c1, c2 = st.columns(2)
                    
                    # --- قسم السلوك الفردي (يعمل بنظام الـ Buffer السريع) ---
                    with c2:
                        st.container(border=True)
                        st.markdown("##### 🎭 السلوك والملاحظات (سريع)")
                        if st.session_state.role == "teacher":
                            with st.form("beh_add", clear_on_submit=True):
                                bt = st.selectbox("نوع السلوك", [
                                    "🌟 متميز (+10)", "✅ إيجابي (+5)", "📝 حل الواجب (+5)", "🎯 أداء المهمة (+10)", "📂 ملف الإنجاز (+10)", 
                                    "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص أدوات الكتابة (-5)", "💤 النوم داخل الفصل (-3)", 
                                    "🏃 تأخر عن الحصة (-5)", "❌ عدم إحضار ملف الإنجاز (-10)", "🚫 سلبي (-10)"
                                ])
                                bn = st.text_area("تفاصيل الملاحظة")
                                
                                if st.form_submit_button("💾 تسجيل (في الذاكرة المؤقتة)", type="primary"):
                                    # إضافة السلوك للسلة بدون الاتصال بجوجل!
                                    st.session_state.pending_behaviors.append({
                                        "student_id": sid, "name": s_nm, "date": str(datetime.date.today()), 
                                        "type": bt, "note": bn
                                    })
                                    # استخدام التنبيه اللطيف بدل إعادة تحميل الصفحة
                                    st.toast(f"✅ تم إضافة ملاحظة ({bt}) للطالب {s_nm} في الذاكرة المؤقتة.", icon="🛒")
                        else: st.info("💡 وضع القراءة فقط.")

                    # --- قسم الدرجات الأكاديمية ---
                    with c1:
                        st.container(border=True)
                        st.markdown("##### 📝 رصد الدرجات الأكاديمية")
                        df_g = fetch_safe("grades")
                        cur_p1 = 0; cur_p2 = 0
                        if not df_g.empty:
                            df_g['clean_id'] = df_g.iloc[:,0].astype(str).str.split('.').str[0]
                            gr = df_g[df_g['clean_id'] == sid]
                            if not gr.empty:
                                cur_p1 = int(pd.to_numeric(gr.iloc[0]['p1'], errors='coerce') or 0)
                                cur_p2 = int(pd.to_numeric(gr.iloc[0]['p2'], errors='coerce') or 0)
                        
                        if st.session_state.role == "teacher":
                            with st.form("gr_upd", clear_on_submit=False):
                                v1 = st.number_input("درجة المشاركة", 0, st.session_state.max_tasks, cur_p1)
                                v2 = st.number_input("درجة الاختبار", 0, st.session_state.max_quiz, cur_p2)
                                if st.form_submit_button("💾 رفع الدرجة مباشرة", type="primary"):
                                    with st.spinner("جاري الحفظ..."):
                                        ws_g = sh.worksheet("grades")
                                        cell = ws_g.find(sid) # هنا Find مقبولة لأنها لمرة واحدة فقط لدرجة الطالب
                                        tot = v1 + v2
                                        if cell:
                                            ws_g.update_cell(cell.row, 2, v1); ws_g.update_cell(cell.row, 3, v2)
                                            ws_g.update_cell(cell.row, 4, tot); ws_g.update_cell(cell.row, 5, str(datetime.date.today()))
                                        else: ws_g.append_row([sid, v1, v2, tot, str(datetime.date.today())])
                                        st.cache_data.clear(); st.rerun()
                        else: st.info("💡 وضع القراءة فقط.")
                        st.caption(f"📊 المجموع الحالي للدرجات: {cur_p1 + cur_p2}")

            # --- مركز الرفع الجماعي (Sync Center) ---
            if st.session_state.role == "teacher" and st.session_state.pending_behaviors:
                st.markdown("---")
                st.warning(f"⚠️ لديك ({len(st.session_state.pending_behaviors)}) ملاحظات سلوكية معلقة في الذاكرة المؤقتة لم يتم رفعها للمنصة!")
                
                with st.expander("👀 عرض الملاحظات المعلقة", expanded=True):
                    for idx, pb in enumerate(st.session_state.pending_behaviors):
                        st.write(f"**{pb['name']}**: {pb['type']} - *{pb['note']}*")
                        
                    if st.button("🚀 رفع جميع الملاحظات دفعة واحدة", type="primary", use_container_width=True):
                        try:
                            with st.spinner("جاري رفع الملاحظات وتحديث النقاط..."):
                                behavior_rows = []
                                point_updates = {}
                                
                                # تجهيز البيانات من الـ Buffer
                                for pb in st.session_state.pending_behaviors:
                                    behavior_rows.append([pb['student_id'], pb['date'], pb['type'], pb['note']])
                                    match = re.search(r'\(([\+\-]?\d+)\)', pb['type'])
                                    if match:
                                        point_updates[pb['student_id']] = point_updates.get(pb['student_id'], 0) + int(match.group(1))

                                # 1. رفع الملاحظات دفعة واحدة
                                if behavior_rows:
                                    sh.worksheet("behavior").append_rows(behavior_rows)
                                
                                # 2. تحديث النقاط دفعة واحدة بدون دالة find
                                if point_updates:
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
                                
                                # تنظيف السلة والكاش أخيراً
                                st.session_state.pending_behaviors = []
                                st.cache_data.clear()
                                st.success("✅ تم مزامنة جميع الملاحظات مع قاعدة البيانات بنجاح!")
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الرفع: {e}")
                    
                    if st.button("🗑️ إفراغ الذاكرة وإلغاء المعلقات"):
                        st.session_state.pending_behaviors = []
                        st.rerun()

        # --- 2. الرصد الجماعي السريع (الميزة الجديدة) ---
        with eval_tabs[1]:
            if st.session_state.role == "teacher":
                st.markdown("#### 🚀 الرصد الجماعي للملاحظات والواجبات")
                st.info("💡 اختر الصف، وحدد الملاحظات للطلاب المعنيين فقط، ثم اضغط حفظ بالأسفل لترصد للجميع دفعة واحدة.")
                
                bulk_class = st.selectbox("🎯 اختر الصف للرصد الجماعي:", st.session_state.class_options, key="bulk_class_sel")
                df_st_bulk = fetch_safe("students")
                
                if not df_st_bulk.empty:
                    # جلب طلاب الصف المحدد فقط
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
                            
                            # عرض الطلاب بشكل مرتب
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
                                st.markdown("<div style='border-bottom: 1px dashed #e0e7ff; margin: 5px 0;'></div>", unsafe_allow_html=True)

                            if st.form_submit_button("🚀 حفظ الرصد الجماعي للجميع", type="primary"):
                                behavior_rows_to_add = []
                                point_updates = {}
                                
                                # تجميع البيانات
                                for sid_key, data in bulk_data.items():
                                    if data["type"] != "--- بدون ملاحظة ---":
                                        behavior_rows_to_add.append([sid_key, str(datetime.date.today()), data["type"], data["note"]])
                                        match = re.search(r'\(([\+\-]?\d+)\)', data["type"])
                                        if match:
                                            point_updates[sid_key] = int(match.group(1))

                                if behavior_rows_to_add:
                                    try:
                                        with st.spinner("جاري حفظ الرصد الجماعي وتحديث النقاط..."):
                                            # 1. إضافة الملاحظات دفعة واحدة (API سريع)
                                            sh.worksheet("behavior").append_rows(behavior_rows_to_add)
                                            
                                            # 2. تحديث النقاط دفعة واحدة باستخدام update_cells (API صاروخي)
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
                                            
                                        st.success(f"✅ تمت المهمة بنجاح! تم رصد ({len(behavior_rows_to_add)}) ملاحظة وتحديث نقاط الطلاب.")
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
    # 📢 التنبيهات
    with tab_alerts:
        st.markdown("### 📢 لوحة الإعلانات والتعاميم")
        def perform_delete(row_index):
            try: sh.worksheet("exams").delete_rows(int(row_index) + 2); st.cache_data.clear(); st.toast("✅ تم حذف التنبيه بنجاح")
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
                    anim_class = "urgent-anim" if is_urgent else ""
                    border_style = "2px solid #ef4444" if is_urgent else "1px solid #e0e7ff"
                    bg_style = "#fef2f2" if is_urgent else "#ffffff"
                    st.markdown(f"""
                    <div class="{anim_class}" style="background:{bg_style}; border:{border_style}; border-radius:12px; padding:15px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between;"><h4 style="margin:0; color:#000;">{r.get('العنوان')}</h4><span style="background:white; padding:2px 8px; border-radius:8px; font-size:0.8rem; color:#555;">{r.get('التاريخ')}</span></div>
                        <p style="margin:5px 0 0 0; color:#475569">{r.get('الرابط')}</p><small style="color:#1e3a8a; font-weight:bold;">🎯 الفئة: {r.get('الصف')}</small>
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
                if c1.button("🔄 تحديث البيانات (Refresh)", use_container_width=True): st.cache_data.clear(); st.rerun()
                if c2.button("🧹 تصفير جميع النقاط", use_container_width=True):
                    try:
                        ws = sh.worksheet("students"); d = ws.get_all_values()
                        if len(d) > 1: ws.update(range_name=f"I2:I{len(d)}", values=[[0]]*(len(d)-1)); st.success("✅ تم تصفير جميع النقاط")
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
                                st.success("✅ تم تصحيح جميع الأرصدة بنجاح!"); st.cache_data.clear()
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
                cy = st.text_input("العام الدراسي", st.session_state.current_year)
                cls = st.text_area("قائمة الصفوف (افصل بفاصلة)", ",".join(st.session_state.class_options))
                stg = st.text_area("قائمة المراحل", ",".join(st.session_state.stage_options))
                c1, c2 = st.columns(2)
                mt = c1.number_input("الدرجة العظمى (مشاركة)", 0, 100, st.session_state.max_tasks)
                mq = c2.number_input("الدرجة العظمى (اختبار)", 0, 100, st.session_state.max_quiz)
                if st.button("💾 حفظ الإعدادات", type="primary"):
                    sh.worksheet("settings").batch_update([
                        {'range': 'A2:B2', 'values': [['max_tasks', mt]]}, {'range': 'A3:B3', 'values': [['max_quiz', mq]]},
                        {'range': 'A4:B4', 'values': [['current_year', cy]]}, {'range': 'A5:B5', 'values': [['class_list', cls]]},
                        {'range': 'A6:B6', 'values': [['stage_list', stg]]} 
                    ])
                    st.session_state.max_tasks = mt; st.session_state.max_quiz = mq; st.session_state.current_year = cy
                    st.session_state.class_options = [x.strip() for x in cls.split(',') if x.strip()]
                    st.session_state.stage_options = [x.strip() for x in stg.split(',') if x.strip()]
                    st.success("✅ تم الحفظ بنجاح"); st.cache_data.clear(); st.rerun()

            with st.expander("📤 استيراد البيانات (Excel) - سريع"):
                up = st.file_uploader("رفع ملف Excel", type=['xlsx'])
                ts = st.radio("نوع البيانات", ["students", "grades"], horizontal=True, format_func=lambda x: "بيانات الطلاب" if x == "students" else "الدرجات")
                if st.button("🚀 بدء المزامنة السريعة", type="primary") and up:
                    try:
                        with st.spinner('جاري معالجة ورفع البيانات دفعة واحدة...'):
                            df = pd.read_excel(up).fillna("").dropna(how='all'); ws = sh.worksheet(ts)
                            existing_ids = set(str(r.get('id', r.get('student_id', ''))).strip().split('.')[0] for r in ws.get_all_records())
                            hd = ws.row_values(1); new_rows_to_append = []; progress_bar = st.progress(0)
                            
                            for idx, row in df.iterrows():
                                d = row.to_dict()
                                raw_id = str(d.get('student_id', d.get('id', ''))).strip().split('.')[0]
                                if not raw_id or raw_id == '0' or raw_id.lower() == 'nan': continue
                                if ts == "grades":
                                    d.update({"student_id": raw_id, "p1": int(d.get('p1',0)), "p2": int(d.get('p2',0)), "perf": int(d.get('p1',0))+int(d.get('p2',0)), "date": str(datetime.date.today())})
                                    if 'id' in d: del d['id']
                                else:
                                    d['id'] = raw_id; d['الجوال'] = clean_phone_number(d.get('الجوال',''))
                                    if 'النقاط' not in d or str(d.get('النقاط', '')).strip() == "": d['النقاط'] = 0
                                if raw_id not in existing_ids: new_rows_to_append.append([str(d.get(k, "")) for k in hd])
                                progress_bar.progress(min((idx + 1) / len(df), 1.0))

                            if new_rows_to_append: ws.append_rows(new_rows_to_append); st.success(f"✅ تم إضافة {len(new_rows_to_append)} سجل جديد بنجاح!")
                            else: st.info("💡 جميع البيانات موجودة مسبقاً، لم يتم إضافة جديد.")
                            st.cache_data.clear()
                    except Exception as e: st.error(f"حدث خطأ أثناء المزامنة: {e}")
            
                st.divider(); c1, c2 = st.columns(2)
                b1 = io.BytesIO(); pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط"]).to_excel(b1, index=False)
                c1.download_button("📥 قالب فارغ (طلاب)", b1.getvalue(), "students_template.xlsx", use_container_width=True)
                b2 = io.BytesIO(); pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(b2, index=False)
                c2.download_button("📥 قالب فارغ (درجات)", b2.getvalue(), "grades_template.xlsx", use_container_width=True)

            # 👇👇 تم دمج كود مدقق البيانات هنا بنجاح 👇👇
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
            # 👆👆 نهاية كود مدقق البيانات 👆👆

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
                                st.success(f"✅ تمت إضافة الحساب ({nu}) بنجاح كـ {role_val}."); st.cache_data.clear()
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
                                    st.success(f"✅ تم تحديث كلمة المرور لـ ({target_u})."); st.cache_data.clear()
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
                                    sh.worksheet("users").delete_rows(int(idx)); st.success(f"✅ تم حذف المستخدم ({del_u})."); st.cache_data.clear(); st.rerun()
                            else: st.warning("الرجاء اختيار مستخدم للحذف.")

    with tab_logout:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("تسجيل الخروج من لوحة التحكم", type="secondary"): st.session_state.role = None; st.rerun()
            
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
                link_display = f"<a href='{link_text}' target='_blank' style='color:#7f1d1d; text-decoration:underline;'>اضغط هنا</a>" if link_text.startswith('http') else link_text if link_text.lower() != 'none' else ""
                st.markdown(f"<div class='urgent-box'>🚨 {u.get('العنوان')}<br><small style='color:#7f1d1d'>{link_display}</small></div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class="welcome-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><h2 style="color:white; margin:0; font-size:1.5rem;">👋 أهلاً بك، {s_nm}</h2><p style="color:#e0e7ff; margin:5px 0 0 0;">{s_cls}</p></div>
                    <div style="background:rgba(255,255,255,0.2); padding:5px 15px; border-radius:12px;"><span style="font-weight:bold; font-size:0.9rem;">ID: {sid}</span></div>
                </div>
            </div>
            <div class="points-banner">
                <p style="margin:0; opacity:0.9; font-size:0.9rem;">رصيد النقاط الحالي</p>
                <h1 style="margin:0; font-size:3.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{pts}</h1>
                <p style="margin:0; font-size:0.8rem;">استمر في التفوق!</p>
            </div>
            <div class="medal-flex">
                <div class="m-card {'m-active' if pts>=100 else ''}" style="color: #d97706;">🥇<br><b>ذهبي</b></div>
                <div class="m-card {'m-active' if pts>=50 else ''}" style="color: #64748b;">🥈<br><b>فضي</b></div>
                <div class="m-card m-active" style="color: #b45309;">🥉<br><b>برونزي</b></div>
            </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["📢", "📝", "📊", "🏆", "⚙️"])

        with tabs[0]: 
            st.caption("التعاميم والتنبيهات")
            if not df_ann.empty:
                anns = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_cls])]
                for _, r in anns.iloc[::-1].iterrows():
                    row_link = str(r.get('الرابط', ''))
                    row_link_display = f"<a href='{row_link}' target='_blank' style='color:#4b5563; text-decoration:underline;'>اضغط هنا للفتح</a>" if row_link.startswith('http') else row_link if row_link.lower() != 'none' else ""
                    st.markdown(f"""
                    <div class='mobile-list-item'>
                        <div style="width:100%">
                            <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><b>📢 {r.get('العنوان')}</b><small style="background:#f5f3ff; color:#4338ca; padding:2px 6px; border-radius:4px;">{r.get('التاريخ')}</small></div>
                            <span style="color:#4b5563; font-size:0.9rem;">{row_link_display}</span>
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
                        color = "#ef4444" if "سلبي" in str(n.get('type')) else "#4f46e5"
                        st.markdown(f"<div class='mobile-list-item' style='border-right: 4px solid {color};'><div><b style='color:{color}'>{n.get('type')}</b><p style='margin:0; font-size:0.9rem; color:#374151;'>{n.get('note')}</p><small style='color:#9ca3af;'>{n.get('date')}</small></div></div>", unsafe_allow_html=True)
                else: st.success("🌟 سجلك نظيف تماماً!")

        with tabs[2]: 
            st.caption("درجاتي")
            if not df_gr.empty:
                df_gr['clean_id'] = df_gr.iloc[:,0].astype(str).str.strip().str.split('.').str[0]
                grs = df_gr[df_gr['clean_id']==sid]
                if not grs.empty:
                    g = grs.iloc[0]
                    # حساب النسبة واختيار اللقب التحفيزي
                    max_total = st.session_state.max_tasks + st.session_state.max_quiz
                    perf_score = int(pd.to_numeric(g.get('perf', 0), errors='coerce') or 0)
                    percentage = (perf_score / max_total) * 100 if max_total > 0 else 0
                    
                    if percentage >= 90: title, title_color = "🌟 أسطورة المنصة", "#d97706"
                    elif percentage >= 80: title, title_color = "🚀 بطل مبدع", "#4338ca"
                    elif percentage >= 70: title, title_color = "👍 متألق ومجتهد", "#059669"
                    elif percentage >= 60: title, title_color = "💪 واصل تقدمك", "#2563eb"
                    else: title, title_color = "🌱 أنت قادر على الأفضل", "#64748b"

                    st.markdown(f"""
                    <div class='mobile-list-item'><span>📝 المشاركة والواجبات</span><b>{g.get('p1')} / {st.session_state.max_tasks}</b></div>
                    <div class='mobile-list-item'><span>✍️ الاختبارات القصيرة</span><b>{g.get('p2')} / {st.session_state.max_quiz}</b></div>
                    <div class='mobile-list-item' style='background:#eef2ff; border-color:#818cf8; display:flex; flex-direction:column; align-items:flex-start;'>
                        <div style="width:100%; display:flex; justify-content:space-between;">
                            <span style="color:#4338ca; font-weight:bold;">🏆 المجموع النهائي</span><b style="color:#4338ca; font-size:1.2rem;">{perf_score} / {max_total}</b>
                        </div>
                        <div style="margin-top:8px; width:100%; text-align:center; padding:5px; background:white; border-radius:8px; color:{title_color}; font-weight:bold; font-size:1.1rem; border:1px solid {title_color}33;">
                            {title}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 🚀 الميزة الجديدة: إظهار شهادة التفوق فقط لمن حصل على 90% فما فوق
                    if percentage >= 90:
                        st.divider()
                        st.success("🎉 مبروك! لتفوقك وحصولك على درجة الامتياز، تم تفعيل ميزة استخراج 'شهادة التفوق'.")
                        
                        # تصميم الشهادة الاحترافي (HTML/CSS)
                        # تصميم الشهادة الاحترافي (محدث ليطابق الطباعة 100%)
                        certificate_html = f"""
                        <!DOCTYPE html>
                        <html dir="rtl" lang="ar">
                        <head>
                            <meta charset="UTF-8">
                            <title>شهادة تفوق - {s_nm}</title>
                            <link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
                            <style>
                                * {{ box-sizing: border-box; }}
                                body {{
                                    font-family: 'Cairo', sans-serif;
                                    background-color: #f8fafc;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    min-height: 100vh;
                                    margin: 0;
                                }}
                                .cert-wrapper {{
                                    width: 297mm;
                                    height: 210mm;
                                    background-color: white;
                                    padding: 15mm;
                                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                                }}
                                .cert-border {{
                                    border: 15px solid #1e3a8a;
                                    height: 100%;
                                    width: 100%;
                                    padding: 10px;
                                    background-image: radial-gradient(#e0e7ff 1px, transparent 1px);
                                    background-size: 20px 20px;
                                    -webkit-print-color-adjust: exact !important;
                                    print-color-adjust: exact !important;
                                }}
                                .cert-inner-border {{
                                    border: 3px double #d97706;
                                    height: 100%;
                                    width: 100%;
                                    padding: 30px;
                                    text-align: center;
                                    display: flex;
                                    flex-direction: column;
                                    justify-content: space-between;
                                }}
                                .cert-content {{ flex-grow: 1; }}
                                h1 {{ font-family: 'Aref Ruqaa', serif; font-size: 60px; color: #d97706; margin: 0 0 15px 0; }}
                                h2 {{ font-size: 35px; color: #1e3a8a; margin: 0 0 20px 0; }}
                                p {{ font-size: 26px; color: #334155; line-height: 1.8; margin: 0 50px; }}
                                .student-name {{ font-size: 45px; font-weight: 900; color: #ef4444; text-decoration: underline; text-decoration-color: #d97706; display: inline-block; margin: 15px 0; }}
                                .footer-section {{ display: flex; justify-content: space-between; align-items: flex-end; padding: 0 40px; margin-bottom: 10px; }}
                                .signature {{ font-size: 24px; font-weight: bold; color: #1e3a8a; text-align: center; line-height: 1.5; }}
                                .seal {{ width: 120px; height: 120px; border: 4px dashed #ef4444; border-radius: 50%; line-height: 110px; color: #ef4444; font-weight: 900; font-size: 20px; transform: rotate(-15deg); opacity: 0.8; text-align: center; }}
                                
                                /* 🚀 إعدادات الطباعة الدقيقة */
                                @media print {{
                                    @page {{ size: A4 landscape; margin: 0mm; }}
                                    body {{ min-height: auto; background-color: white; align-items: flex-start; justify-content: flex-start; }}
                                    .cert-wrapper {{ box-shadow: none; width: 297mm; height: 210mm; padding: 10mm; page-break-after: avoid; }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="cert-wrapper">
                                <div class="cert-border">
                                    <div class="cert-inner-border">
                                        <div class="cert-content">
                                            <h1>شهادة شكر وتقدير</h1>
                                            <h2>🌟 وسام التميز الأكاديمي 🌟</h2>
                                            <p>
                                                يتقدم الأستاذ/ <b>زياد المعمري</b> بوافر الشكر والتقدير للطالب المبدع والمتألق:
                                                <br><span class="student-name">{s_nm}</span><br>
                                                وذلك نظير تفوقه العلمي وحصوله على نسبة <b>{int(percentage)}%</b> في المادة.
                                                <br>متمنين له دوام التوفيق ومزيداً من التألق والنجاح.
                                            </p>
                                        </div>
                                        <div class="footer-section">
                                            <div class="signature">
                                                تاريخ الإصدار<br>
                                                <span style="color:#475569;">{datetime.date.today().strftime('%Y-%m-%d')}</span>
                                            </div>
                                            <div class="seal">ختم التميز</div>
                                            <div class="signature">
                                                توقيع المعلم<br>
                                                <span style="font-family: 'Aref Ruqaa', serif; font-size: 35px; color:#475569;">زياد المعمري</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        st.download_button(
                            label="📜 استخراج وطباعة شهادة التفوق",
                            data=certificate_html,
                            file_name=f"Certificate_{sid}.html",
                            mime="text/html",
                            type="primary",
                            use_container_width=True
                        )

                else: st.info("لم يتم رصد درجات بعد")

        with tabs[3]: 
            st.caption("لوحة الشرف (أفضل 10 طلاب)")
            df_st['p_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            for i, (_, r) in enumerate(df_st.sort_values('p_num', ascending=False).head(10).iterrows(), 1):
                ic = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
                sty = "border:2px solid #818cf8; background:#eef2ff;" if str(r['clean_id']) == sid else ""
                st.markdown(f"<div class='mobile-list-item' style='{sty}'><div style='display:flex; align-items:center; gap:10px;'><span style='font-weight:900; font-size:1.2rem; width:30px;'>{ic}</span><span>{r['name']}</span></div><span style='color:#f59e0b; font-weight:900;'>{int(r['p_num'])}</span></div>", unsafe_allow_html=True)

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
            if st.button("🚪 تسجيل الخروج", type="secondary", use_container_width=True): st.session_state.role = None; st.rerun()

    else: st.error("عذراً، لم يتم العثور على بياناتك"); st.button("العودة للقائمة الرئيسية", on_click=st.rerun)
    
    show_footer()
