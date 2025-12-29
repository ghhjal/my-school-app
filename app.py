import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
import urllib.parse

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stMetricLabel"] { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
    .main { background-color: #f8f9fa; direction: rtl; text-align: right; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    
    /* تنسيق الأوسمة */
    .badge-gold { background: linear-gradient(45deg, #ffd700, #ff8c00); color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold; box-shadow: 0 4px 10px rgba(255,215,0,0.4); }
    .badge-silver { background: linear-gradient(45deg, #c0c0c0, #708090); color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold; }
    .badge-bronze { background: linear-gradient(45deg, #cd7f32, #8b4513); color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold; }
    
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

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<div class='header-text'><h1>🏛️ منصة الأستاذ زياد المعمري</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["👨‍🏫 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
            match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
            if not match.empty:
                st.session_state.role = "student"
                st.session_state.student_id = str(sid_in)
                st.session_state.student_name = match.iloc[0]["الاسم"]
                st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم (إضافة النقاط تلقائياً) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 الاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد السلوك والتحفيز")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        
        with st.form("beh_f"):
            b_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
            b_type = st.radio("نوع السلوك (سيؤثر على النقاط)", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
            b_note = st.text_input("الملاحظة")
            if st.form_submit_button("📌 رصد وحساب النقاط"):
                # حساب النقاط بناءً على الاختيار
                pts_change = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                
                # 1. تحديث جدول السلوك
                sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                
                # 2. تحديث نقاط الطالب في جدول students
                ws_st = sh.worksheet("students")
                cell = ws_st.find(b_st)
                current_pts = int(ws_st.cell(cell.row, 9).value or 0)
                ws_st.update_cell(cell.row, 9, current_pts + pts_change)
                
                st.success(f"تم رصد السلوك وإضافة {pts_change} نقطة للطالب {b_st}")
                time.sleep(1); st.rerun()

    elif menu == "👥 إدارة الطلاب":
        st.header("🏆 لوحة التميز (أعلى النقاط)")
        df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
        st.dataframe(df_st.sort_values(by="النقاط", ascending=False), use_container_width=True, hide_index=True)

# --- 4. واجهة الطالب (الأوسمة والتحفيز) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-text'><h3>🎓 الطالب: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"])
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    pts = int(my_info["النقاط"])

    # نظام الأوسمة الذكي
    st.subheader("🏅 وسام التميز الحالي")
    if pts >= 50:
        st.markdown("<div class='badge-gold'>🏆 أنت الآن في المستوى الذهبي (قائد متميز)</div>", unsafe_allow_html=True)
    elif pts >= 20:
        st.markdown("<div class='badge-silver'>🥈 أنت الآن في المستوى الفضي (طالب مجتهد)</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='badge-bronze'>🥉 أنت في المستوى البرونزي (بداية موفقة)</div>", unsafe_allow_html=True)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد نقاطك", f"{pts} نقطة")
    c2.metric("الصف", my_info["الصف"])
    c3.metric("المادة", my_info["المادة"])
    
    st.divider()
    st.subheader("📝 تفاصيل نقاطك وسلوكك")
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    st.dataframe(my_beh, use_container_width=True, hide_index=True)
