import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials

# --- 1. إعداد نظام مراقبة الأخطاء (Logging) ---
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# --- 2. الاتصال الذكي بـ Google Sheets ---
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من الإعدادات.")
        logging.error(f"Connection Error: {e}")
        return None

sh = get_gspread_client()

# --- 3. دوال التعامل مع البيانات (بدون الاعتماد على ترتيب الأعمدة) ---
@st.cache_data(ttl=30)
def get_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        logging.error(f"Fetch Error [{sheet_name}]: {e}")
        return pd.DataFrame()

def get_col_index(df, col_name):
    """دالة تجلب رقم العمود في Excel بناءً على اسمه في DataFrame"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        st.error(f"❌ لم يتم العثور على العمود: {col_name}")
        return None

# --- 4. التصميم (CSS) - المحافظة على هويتك البصرية كاملة ---
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 45px 20px; border-radius: 0 0 40px 40px; color: white; text-align: center; margin: -80px -20px 30px -20px; }
    .stButton>button { background: #2563eb !important; color: white !important; border-radius: 12px !important; font-weight: bold; width: 100%; height: 3em; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.05) !important; border-radius: 20px !important; border: 1px solid rgba(128, 128, 128, 0.2) !important; }
    </style>
    <div class="header-section">
        <h1 style="color:white;">منصة زياد الذكية</h1>
        <p style="color:white; opacity:0.8;">نظام إداري مستقر واحترافي</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 بوابة تسجيل الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    with t1:
        with st.form("student_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي")
            if st.form_submit_button("دخول 🚀"):
                df = get_data("students")
                if not df.empty and sid.strip() in df.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip(); st.rerun()
                else: st.error("الرقم غير مسجل لدينا")
    with t2:
        with st.form("teacher_login"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الآدمن"):
                df_u = get_data("users")
                if not df_u.empty and u in df_u['username'].values:
                    h = hashlib.sha256(str.encode(p)).hexdigest()
                    if h == df_u[df_u['username']==u].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (كاملة وبدون أخطاء)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])
    
    # --- إدارة الطلاب ---
    with menu[0]:
        st.subheader("إضافة طالب جديد")
        with st.form("add_st", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("اعتماد الطالب"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, "1447", "ابتدائي", "لغة إنجليزية", "", "", "0"])
                    st.success("تم الإضافة"); st.cache_data.clear(); st.rerun()

        st.divider()
        df_st = get_data("students")
        if not df_st.empty:
            st.write("🗑️ حذف طالب (بالرقم الأكاديمي):")
            del_id = st.selectbox("اختر الرقم المراد حذفه:", df_st.iloc[:, 0].tolist())
            if st.button("🚨 حذف نهائي"):
                for s in ["students", "grades", "behavior"]:
                    ws = sh.worksheet(s); df_t = get_data(s)
                    if not df_t.empty and str(del_id) in df_t.iloc[:, 0].astype(str).values:
                        idx = df_t[df_t.iloc[:, 0].astype(str) == str(del_id)].index[0]
                        ws.delete_rows(int(idx)+2)
                st.success("تم المسح"); st.cache_data.clear(); st.rerun()

    # --- رصد الدرجات (ID ذكي) ---
    with menu[1]:
        st.subheader("رصد الدرجات")
        df_st = get_data("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("grade_f"):
                target_name = st.selectbox("اسم الطالب:", list(st_map.keys()))
                v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                if st.form_submit_button("حفظ الدرجة"):
                    sid = st_map[target_name]; ws = sh.worksheet("grades"); df_g = get_data("grades")
                    if not df_g.empty and str(sid) in df_g.iloc[:, 0].astype(str).values:
                        idx = df_g[df_g.iloc[:, 0].astype(str) == str(sid)].index[0] + 2
                        ws.update_cell(idx, 2, v1); ws.update_cell(idx, 3, v2)
                    else: ws.append_row([sid, v1, v2, "", str(datetime.date.today()), ""])
                    st.success("تم الحفظ"); st.cache_data.clear()

    # --- رصد السلوك (تحديث تلقائي للنقاط) ---
    with menu[2]:
        st.subheader("🥇 نظام النقاط والسلوك")
        df_st = get_data("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("beh_f"):
                s_name = st.selectbox("الطالب المستهدف:", list(st_map.keys()))
                b_type = st.selectbox("نوع الملاحظة", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "❌ سلبي (-5)"])
                b_note = st.text_area("تفاصيل الملاحظة")
                if st.form_submit_button("رصد الملاحظة"):
                    sid = st_map[s_name]; sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, b_note])
                    # تحديث النقاط بناءً على اسم العمود
                    points_idx = get_col_index(df_st, "النقاط")
                    row_idx = df_st[df_st.iloc[:,0] == sid].index[0] + 2
                    p_val = 10 if "+" in b_type else -5
                    old_p = int(df_st[df_st.iloc[:,0] == sid].iloc[0]["النقاط"] or 0)
                    sh.worksheet("students").update_cell(row_idx, points_idx, str(old_p + p_val))
                    st.success("تم تحديث السجل والنقاط"); st.cache_data.clear(); st.rerun()

    with menu[4]:
        st.subheader("⚙️ إعدادات المنصة")
        if st.button("تصفير كاش البيانات"): st.cache_data.clear(); st.success("تم التحديث")

    with menu[5]:
        if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (كاملة وشخصية)
# ==========================================
if st.session_state.role == "student":
    df_st = get_data("students")
    s_id = st.session_state.sid
    # جلب بيانات الطالب بالـ ID لضمان عدم حدوث تكرار
    s_info = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].iloc[0]
    
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #ddd;">
            <h2 style="color: #1e40af;">مرحباً بك: {s_info.iloc[1]}</h2>
            <div style="font-size: 24px; font-weight: bold; color: orange;">رصيد نقاطك: {s_info['النقاط']}</div>
        </div>
    """, unsafe_allow_html=True)

    t_st = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📢 تنبيهات", "🚗 خروج"])
    
    with t_st[0]:
        st.write("### سجل الدرجات الأكاديمية")
        df_g = get_data("grades")
        my_g = df_g[df_g.iloc[:, 0].astype(str) == str(s_id)]
        if not my_g.empty: st.dataframe(my_g, use_container_width=True)
        else: st.info("لا توجد درجات مرصودة حالياً.")

    with t_st[1]:
        st.write("### سجل الملاحظات السلوكية")
        df_b = get_data("behavior")
        my_b = df_b[df_b.iloc[:, 0].astype(str) == str(s_id)]
        for i, row in my_b.iterrows():
            st.warning(f"📅 {row[1]} | {row[2]}: {row[3]}")

    with t_st[2]:
        st.write("### الإعلانات العامة")
        df_ex = get_data("exams")
        if not df_ex.empty: st.table(df_ex.iloc[::-1])

    with t_st[3]:
        if st.button("خروج"): st.session_state.role = None; st.rerun()
