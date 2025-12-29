import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

# --- التنسيق الاحترافي لرفع الوضوح في الجوال ---
st.markdown("""
    <style>
    /* جعل نصوص البطاقات (Metrics) سوداء داكنة وواضحة جداً */
    [data-testid="stMetricLabel"] {
        color: #1e3a8a !important; 
        font-weight: bold !important;
        font-size: 1.1rem !important;
        opacity: 1 !important;
    }
    [data-testid="stMetricValue"] {
        color: #000000 !important; /* لون أسود صريح للوضوح العالي */
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
    .stMetric {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        border-top: 5px solid #1e3a8a !important;
    }
    /* تنسيق عام للمنصة */
    .main { background-color: #f8f9fa; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            df = pd.DataFrame(ws.get_all_records())
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام الدخول والخروج ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري التعليمية</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("تسجيل الدخول كمعلم"):
            if pwd == "1234": 
                st.session_state.role = "teacher"
                st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب", key="login_sid")
        if st.button("تسجيل الدخول كطالب"):
            if sid_in:
                df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
                match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.student_id = str(sid_in)
                    st.session_state.student_name = match.iloc[0]["الاسم"]
                    st.rerun()
                else: st.error("عذراً، الرقم الأكاديمي غير مسجل.")
    st.stop()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown(f"👤 مرحباً بك: **{st.session_state.role}**")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    st.divider()
    st.info("**الأستاذ زياد المعمري**")

# --- 3. واجهة المعلم (تشمل الحذف والدرجات والسلوك) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t_reg, t_view = st.tabs(["📝 تسجيل طالب جديد", "📋 قائمة الطلاب والحذف"])
        with t_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("العام الدراسي", ["1446هـ", "1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("💾 حفظ البيانات"):
                    if sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        st.success("✅ تم الحفظ")
                        time.sleep(1); st.rerun()
        with t_view:
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            st.divider()
            del_target = st.selectbox("🗑️ حذف طالب نهائياً", [""] + df_st["الاسم"].tolist())
            if st.button("⚠️ تأكيد الحذف النهائي من كافة السجلات"):
                if del_target:
                    with st.spinner("جاري تنظيف البيانات..."):
                        for sn in ["students", "behavior", "grades"]:
                            ws = sh.worksheet(sn)
                            while True:
                                try:
                                    cell = ws.find(del_target.strip())
                                    ws.delete_rows(cell.row)
                                except: break
                    st.success("🗑️ تم الحذف بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with t_grad:
            with st.form("grade_form"):
                sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                c1, c2, c3 = st.columns(3)
                p1, p2, work = c1.number_input("ف1"), c2.number_input("ف2"), c3.number_input("مشاركة")
                if st.form_submit_button("🔄 تحديث الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_st.strip())
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, work]])
                    except: ws_g.append_row([sel_st.strip(), p1, p2, work])
                    st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
        with t_beh:
            with st.form("beh_form"):
                b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("نوع السلوك", ["✅ إيجابي", "⭐ متميز", "⚠️ تنبيه", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد"):
                    sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                    st.success("✅ تم الرصد"); time.sleep(1); st.rerun()

# --- 4. واجهة الطالب (وضوح عالي جداً) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-text'><h3>🎓 أهلاً بك: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    
    # بطاقات بيانات الطالب (سوداء وواضحة جداً للجوال)
    st.metric("الصف الدراسي", my_info["الصف"])
    st.metric("المرحلة", my_info["المرحلة"])
    st.metric("المادة المسجلة", my_info["المادة"])
    
    st.divider()
    st.subheader("📊 تقرير الدرجات")
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    if not my_grades.empty: 
        st.dataframe(my_grades, use_container_width=True, hide_index=True) # تنسيق احترافي للجوال
    else: st.info("لم ترصد درجاتك حتى الآن.")
        
    st.divider()
    st.subheader("🎭 سجل الملاحظات السلوكية")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            if "إيجابي" in row["النوع"]: st.success(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "متميز" in row["النوع"]: st.info(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "تنبيه" in row["النوع"]: st.warning(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
            elif "سلبي" in row["النوع"]: st.error(f"📅 {row['التاريخ']} | {row['النوع']} : {row['الملاحظة']}")
    else: st.success("سجلك السلوكي متميز!")
