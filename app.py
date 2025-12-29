import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والتنسيق الاحترافي للجوال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

# تنسيق CSS احترافي لحل مشكلة بهتان الألوان ووضوح الجوال
st.markdown("""
    <style>
    /* تحسين الخلفية العامة واتجاه النص */
    .main { background-color: #f0f2f6; direction: rtl; text-align: right; }
    
    /* جعل نصوص البطاقات سوداء داكنة وواضحة جداً */
    [data-testid="stMetricLabel"] {
        color: #1e3a8a !important; 
        font-weight: bold !important;
        font-size: 1.1rem !important;
        opacity: 1 !important;
    }
    [data-testid="stMetricValue"] {
        color: #000000 !important; /* أسود داكن للوضوح العالي */
        font-size: 1.7rem !important;
        font-weight: 800 !important;
    }
    .stMetric {
        background-color: white !important;
        border-radius: 15px !important;
        padding: 15px !important;
        border-right: 10px solid #1e3a8a !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }

    /* تحسين وضوح تقرير الدرجات والجداول */
    .stDataFrame, .stTable {
        background-color: white !important;
        border-radius: 12px !important;
        padding: 5px !important;
    }
    
    /* تصميم العنوان العلوي */
    .header-box {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. الاتصال بجدول البيانات ---
@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-box'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    
    with tab1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرor خاطئة")
            
    with tab2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
            if not match.empty:
                st.session_state.role = "student"
                st.session_state.student_id = str(sid_in)
                st.session_state.student_name = match.iloc[0]["الاسم"]
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown(f"### أهلاً بك\n**{st.session_state.role}**")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    st.divider()
    st.info("إشراف: الأستاذ زياد المعمري")

# --- 4. واجهة المعلم (إدارة الدرجات والسلوك) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 الطلاب", "📊 الدرجات والسلوك"])
    
    if menu == "👥 الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        t1, t2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        
        with t1:
            with st.form("grade_form"):
                sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("ف1")
                p2 = c2.number_input("ف2")
                work = c3.number_input("مشاركة")
                if st.form_submit_button("💾 حفظ"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_st.strip())
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, work]])
                    except: ws_g.append_row([sel_st, p1, p2, work])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        
        with t2:
            with st.form("beh_form"):
                b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("النوع", ["✅ إيجابي", "⭐ متميز", "⚠️ تنبيه", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد"):
                    sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الرصد"); time.sleep(1); st.rerun()

# --- 5. واجهة الطالب (تنسيق احترافي ووضوح عالي) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-box'><h3>🎓 أهلاً بك الطالب: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    
    # بطاقات واضحة جداً
    st.metric("الصف الدراسي", my_info["الصف"])
    st.metric("المرحلة", my_info["المرحلة"])
    st.metric("المادة المسجلة", my_info["المادة"])
    
    st.divider()
    st.subheader("📊 تقرير الدرجات")
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    if not my_grades.empty:
        st.dataframe(my_grades, use_container_width=True, hide_index=True) # وضوح ممتاز للجداول
    else: st.info("لا يوجد درجات مرصودة حالياً")
    
    st.divider()
    st.subheader("🎭 سجل الملاحظات السلوكية")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            if "إيجابي" in row["النوع"] or "متميز" in row["النوع"]:
                st.success(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            else:
                st.warning(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
    else: st.success("سجلك السلوكي متميز!")
