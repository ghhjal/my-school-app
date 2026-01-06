import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات النظام والاستقرار ---
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ خطأ في الاتصال بالبيانات")
        return None

sh = get_gspread_client()

# --- 2. دوال التعامل مع البيانات (الاعتماد على الأسماء وليس الترتيب) ---
@st.cache_data(ttl=60)
def fetch_data(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """البحث عن رقم العمود بناءً على اسمه لضمان المرونة"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

# --- 3. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 40px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>الإصدار المطور - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_log"):
            sid = st.text_input("🆔 الرقم الأكاديمي")
            if st.form_submit_button("دخول الطلاب"):
                df = fetch_data("students")
                if not df.empty and sid.strip() in df.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip(); st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("te_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_data("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (الهيكلية المدمجة الجديدة)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📧 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1️⃣ تبويب: الطلاب (إدارة + بحث) ---
    with menu[0]:
        c_add, c_search = st.columns([2, 1])
        with c_add:
            with st.expander("➕ إضافة طالب جديد", expanded=False):
                with st.form("add_st"):
                    nid = st.text_input("الرقم الأكاديمي")
                    nname = st.text_input("الاسم الثلاثي")
                    nclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    if st.form_submit_button("اعتماد الطالب"):
                        sh.worksheet("students").append_row([nid, nname, nclass, "1447", "ابتدائي", "لغة إنجليزية", "", "", "0"])
                        st.success("تم الإضافة"); st.cache_data.clear(); st.rerun()
        
        with c_search:
            query = st.text_input("🔍 بحث سريع (اسم/رقم)")
            
        df_st = fetch_data("students")
        if query:
            df_st = df_st[df_st.iloc[:, 0].astype(str).str.contains(query) | df_st.iloc[:, 1].str.contains(query)]
        st.dataframe(df_st, use_container_width=True, hide_index=True)

    # --- 2️⃣ تبويب: التقييم والمتابعة (درجات + سلوك) ---
    with menu[1]:
        st.subheader("📈 التقييم الأكاديمي والسلوكي")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            selected_st = st.selectbox("🎯 اختر الطالب للتقييم:", [""] + list(st_map.keys()))
            
            if selected_st:
                sid = st_map[selected_st]
                col_g, col_b = st.columns(2)
                
                with col_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                    if st.button("حفظ الدرجات"):
                        ws_g = sh.worksheet("grades"); df_g = fetch_data("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].astype(str).values:
                            idx = df_g[df_g.iloc[:, 0].astype(str) == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v1); ws_g.update_cell(idx, 3, v2)
                        else: ws_g.append_row([sid, v1, v2, "0", str(datetime.date.today()), ""])
                        st.success("تم رصد الدرجة")

                with col_b:
                    st.markdown("##### 🥇 رصد السلوك")
                    b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                    if st.button("رصد السلوك وتحديث النقاط"):
                        sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                        # تحديث النقاط ديناميكياً
                        p_idx = get_col_idx(df_st, "النقاط")
                        row_idx = df_st[df_st.iloc[:,0] == sid].index[0] + 2
                        points = 10 if "متميز" in b_type else (5 if "إيجابي" in b_type else -5)
                        old_p = int(df_st[df_st.iloc[:,0] == sid].iloc[0]["النقاط"] or 0)
                        sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + points))
                        st.success("تم تحديث النقاط")

    # --- 3️⃣ تبويب: التواصل والتنبيهات ---
    with menu[2]:
        st.subheader("📢 الإعلانات وقنوات التواصل")
        with st.form("ann_f"):
            c1, c2 = st.columns(2)
            e_title = c1.text_input("عنوان التنبيه")
            e_class = c2.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث"])
            if st.form_submit_button("🚀 نشر الإعلان"):
                sh.worksheet("exams").append_row([e_class, e_title, str(datetime.date.today()), ""])
                st.success("تم النشر")

    # --- 4️⃣ تبويب: الإعدادات ---
    with menu[3]:
        st.subheader("⚙️ إعدادات المنصة")
        with st.expander("📥 استيراد بيانات الطلاب من Excel"):
            up = st.file_uploader("ارفع الملف هنا", type="xlsx")
            if up and st.button("تأكيد الرفع"):
                new_df = pd.read_excel(up)
                sh.worksheet("students").update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم استيراد البيانات")

    with menu[4]:
        if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الكاملة المستقرة)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_data("students")
    s_info = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #3b82f6;">
            <h2>أهلاً بك: {s_info.iloc[1]}</h2>
            <p style="font-size: 20px;">النقاط الحالية: <b>{s_info['النقاط']}</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    t_st = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📢 تنبيهات"])
    # (الأكواد هنا تتبع نفس منطق البحث بالـ ID)
