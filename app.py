import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials

# إعدادات الاستقرار وتسجيل الأخطاء
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# --- الاتصال بـ Google Sheets ---
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        logging.error(f"فشل الاتصال: {e}")
        return None

sh = get_client()

# --- دالة جلب البيانات مع الحفاظ على أسماء الأعمدة ---
@st.cache_data(ttl=60)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        logging.error(f"خطأ في جلب {worksheet_name}: {e}")
        return pd.DataFrame()

# --- دالة ذكية لإيجاد رقم العمود بناءً على اسمه (الحل لمشكلتك) ---
def get_col_idx(df, col_name):
    try:
        # نعيد رقم العمود (بإضافة 1 لأن شيت يبدأ من 1 وباندا من 0)
        return df.columns.get_loc(col_name) + 1
    except KeyError:
        logging.error(f"العمود '{col_name}' غير موجود في الشيت!")
        return None

# --- التصميم CSS (يبقى كما هو تماماً) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 40px; border-radius: 0 0 40px 40px; color: white; text-align: center; margin: -80px -20px 30px -20px; }
    </style>
    <div class="header-section"><h1>منصة زياد الذكية</h1><p>نظام مستقر يعتمد على أسماء الأعمدة</p></div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# --- نظام الدخول ---
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 الطلاب", "🔐 الإدارة"])
    with t1:
        with st.form("login_st"):
            sid = st.text_input("الرقم الأكاديمي")
            if st.form_submit_button("دخول"):
                df = fetch_safe("students")
                # البحث في العمود الذي اسمه "الرقم الأكاديمي" أينما كان مكانه
                col_id_name = "الرقم الأكاديمي" # تأكد أن هذا هو الاسم في الشيت
                if not df.empty and sid.strip() in df[col_id_name].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip(); st.rerun()
                else: st.error("الرقم غير مسجل")
    with t2:
        with st.form("login_te"):
            u = st.text_input("المستخدم"); p = st.text_input("المرور", type="password")
            if st.form_submit_button("دخول"):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (حل مشكلة ترتيب الأعمدة)
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs(["👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "⚙️ الإعدادات", "🚗 خروج"])

    with tabs[0]: # إدارة الطلاب
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        # عند الإضافة، نرسل البيانات كقاموس أو بترتيب الأعمدة الحالي
        with st.form("add_st"):
            st.write("إضافة طالب جديد")
            # ... مدخلات الطالب (الاسم، الرقم، إلخ)
            btn = st.form_submit_button("حفظ")
            # المنطق: append_row يحفظ بالترتيب، ولكن التحديث هو الأهم

    with tabs[1]: # رصد الدرجات (الاعتماد على الأسماء)
        st.subheader("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            # نستخدم أسماء الأعمدة بدقة
            student_map = dict(zip(df_st["الاسم الثلاثي"], df_st["الرقم الأكاديمي"]))
            with st.form("grade_f"):
                s_name = st.selectbox("اختر الطالب:", list(student_map.keys()))
                v_p1 = st.number_input("المشاركة")
                note = st.text_input("ملاحظة")
                if st.form_submit_button("حفظ"):
                    sid = student_map[s_name]
                    ws_g = sh.worksheet("grades")
                    df_g = fetch_safe("grades")
                    
                    # نجد رقم السطر بناءً على ID الطالب
                    id_col_name = "الرقم الأكاديمي"
                    if not df_g.empty and str(sid) in df_g[id_col_name].astype(str).values:
                        row_idx = df_g[df_g[id_col_name].astype(str) == str(sid)].index[0] + 2
                        # تحديث بناءً على اسم العمود
                        c_idx = get_col_idx(df_g, "المشاركة")
                        ws_g.update_cell(row_idx, c_idx, v_p1)
                        st.success("تم التحديث بناءً على اسم العمود بنجاح")
                    else:
                        ws_g.append_row([sid, v_p1, "", "", str(datetime.date.today()), note])
                    st.cache_data.clear(); st.rerun()

    with tabs[2]: # رصد السلوك (حل مشكلة عمود النقاط)
        st.subheader("🥇 رصد السلوك")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_map = dict(zip(df_st["الاسم الثلاثي"], df_st["الرقم الأكاديمي"]))
            with st.form("beh_f"):
                s_name = st.selectbox("الطالب:", list(st_map.keys()))
                b_type = st.selectbox("السلوك", ["🌟 متميز (+10)", "❌ سلبي (-5)"])
                if st.form_submit_button("رصد"):
                    sid = st_map[s_name]
                    # 1. تحديث شيت السلوك
                    sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                    
                    # 2. تحديث النقاط في شيت الطلاب (ديناميكياً)
                    ws_st = sh.worksheet("students")
                    row_idx = df_st[df_st["الرقم الأكاديمي"].astype(str) == str(sid)].index[0] + 2
                    
                    # العثور على عمود "النقاط" أينما كان
                    points_col_idx = get_col_idx(df_st, "النقاط")
                    if points_col_idx:
                        curr_points = int(df_st.iloc[row_idx-2]["النقاط"] or 0)
                        add = 10 if "+" in b_type else -5
                        ws_st.update_cell(row_idx, points_col_idx, str(curr_points + add))
                        st.success(f"تم تحديث عمود النقاط (رقم {points_col_idx}) بنجاح")
                    st.cache_data.clear(); st.rerun()

    with tabs[4]: # خروج
        if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (مؤمنة بالكامل)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students")
    # البحث بالاسم داخل الداتا فريم لضمان استرجاع البيانات حتى لو تغير ترتيب الأعمدة
    s_id = st.session_state.sid
    student_info = df_st[df_st["الرقم الأكاديمي"].astype(str) == str(s_id)].iloc[0]
    
    st.header(f"مرحباً بك: {student_info['الاسم الثلاثي']}")
    st.metric("رصيدك من النقاط", student_info["النقاط"])
    
    # عرض الدرجات
    df_g = fetch_safe("grades")
    my_grades = df_g[df_g["الرقم الأكاديمي"].astype(str) == str(s_id)]
    if not my_grades.empty:
        st.write("📊 درجاتك الأكاديمية:")
        st.dataframe(my_grades)

    if st.button("خروج"): st.session_state.role = None; st.rerun()
