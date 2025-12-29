import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. الإعدادات وتحسين الرؤية للجوال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stMetricLabel"] { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; opacity: 1 !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.5rem !important; font-weight: 800 !important; }
    .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 10px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; }
    .main { direction: rtl; text-align: right; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
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

# --- 2. نظام الدخول والخروج (حل مشكلة الاختفاء) ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align:center; color:#1e3a8a;'>🏛️ منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("تسجيل دخول الطالب"):
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
    st.write(f"👤 المستخدم: **{st.session_state.role}**")
    if st.button("🚪 خروج"):
        st.session_state.role = None
        st.rerun()
    st.divider()
    st.info("إشراف: الأستاذ زياد المعمري")

# --- 3. واجهة المعلم (حل زر الحذف وشاشة الدرجات) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة:", ["👥 الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        # زر الحذف الشامل
        st.divider()
        st.subheader("🗑️ الحذف النهائي")
        del_name = st.selectbox("اختر الطالب للحذف", [""] + df_st["الاسم"].tolist())
        if st.button("⚠️ تنفيذ الحذف الشامل"):
            if del_name:
                with st.spinner("جاري حذف كافة سجلات الطالب..."):
                    for sn in ["students", "behavior", "grades"]:
                        ws = sh.worksheet(sn)
                        while True:
                            try:
                                cell = ws.find(del_name.strip())
                                ws.delete_rows(cell.row)
                            except: break
                st.success("تم الحذف بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد البيانات")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        
        with t_g:
            with st.form("g_form"):
                s_name = st.selectbox("الطالب", df_st["الاسم"].tolist())
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1")
                f2 = c2.number_input("ف2")
                wrk = c3.number_input("مشاركة")
                if st.form_submit_button("💾 تحديث الدرجة"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(s_name.strip())
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([s_name, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
        
        with t_b:
            with st.form("b_form"):
                sb_name = st.selectbox("الطالب", df_st["الاسم"].tolist())
                b_type = st.radio("النوع", ["✅ إيجابي", "⭐ متميز", "⚠️ تنبيه", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 رصد السلوك"):
                    sh.worksheet("behavior").append_row([sb_name, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الرصد"); time.sleep(1); st.rerun()

# --- 4. واجهة الطالب (حل مشكلة البيانات والسلوك) ---
elif st.session_state.role == "student":
    st.markdown(f"<h3 style='text-align:center; background-color:#1e3a8a; color:white; padding:10px; border-radius:10px;'>🎓 الطالب: {st.session_state.student_name}</h3>", unsafe_allow_html=True)
    
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
    if not my_grades.empty: st.table(my_grades)
    else: st.info("لا توجد درجات حالياً")
    
    st.divider()
    st.subheader("🎭 سجل الملاحظات السلوكية")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            if "إيجابي" in row["النوع"]: st.success(f"📅 {row['التاريخ']} | {row['النوع']}: {row['الملاحظة']}")
            elif "متميز" in row["النوع"]: st.info(f"📅 {row['التاريخ']} | {row['النوع']}: {row['الملاحظة']}")
            elif "تنبيه" in row["النوع"]: st.warning(f"📅 {row['التاريخ']} | {row['النوع']}: {row['الملاحظة']}")
            elif "سلبي" in row["النوع"]: st.error(f"📅 {row['التاريخ']} | {row['النوع']}: {row['الملاحظة']}")
    else: st.success("السجل السلوكي نظيف ومتميز")
