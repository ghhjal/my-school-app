import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
import urllib.parse

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide", initial_sidebar_state="expanded")

# تنسيق CSS احترافي للوضوح العالي في الجوال
st.markdown("""
    <style>
    [data-testid="stMetricLabel"] { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; opacity: 1 !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; border-top: 5px solid #1e3a8a !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
    .main { background-color: #f8f9fa; direction: rtl; text-align: right; }
    .header-text { color: white; background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .exam-alert { background-color: #fee2e2; border-right: 10px solid #dc2626; padding: 15px; border-radius: 10px; color: #991b1b; font-weight: bold; margin-bottom: 20px; }
    .instruction-box { background-color: #e0f2fe; border: 1px dashed #0369a1; padding: 10px; border-radius: 8px; color: #0369a1; font-size: 0.9rem; margin-bottom: 10px; }
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
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال"])
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
    st.markdown(f"👤 مرحباً بك: **{st.session_state.role}**")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

# --- 3. واجهة المعلم (بزر الواتساب) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد السلوك والدرجات")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال"])
        t1, t2 = st.tabs(["🎭 رصد السلوك", "📝 رصد الدرجات"])
        
        with t1:
            with st.form("beh_f"):
                b_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                b_type = st.radio("نوع السلوك", ["✅ إيجابي", "⭐ متميز", "⚠️ تنبيه", "❌ سلبي"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("📌 حفظ في السجل"):
                    sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الرصد بنجاح")
            
            # ميزة الواتساب للمعلم
            st.markdown("### 📱 إرسال إشعار لولي الأمر")
            current_st = df_all[df_all["الاسم"] == b_st].iloc[0]
            phone = str(current_st["الجوال"])
            if phone and len(phone) > 5:
                msg = f"تحية طيبة، إشعار من منصة الأستاذ زياد المعمري.\nالطالب: {b_st}\nنوع السلوك: {b_type}\nالملاحظة: {b_note}"
                encoded_msg = urllib.parse.quote(msg)
                st.markdown(f'<a href="https://wa.me/{phone}?text={encoded_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer;">💬 إرسال عبر واتساب الآن</button></a>', unsafe_allow_html=True)
            else: st.warning("رقم الجوال غير صحيح أو لم يقم الطالب بتحديثه بعد.")

    # (بقية كود المعلم لإدارة الطلاب والإعلانات تظل كما هي)
    elif menu == "👥 إدارة الطلاب":
        st.info("واجهة إدارة الطلاب")
    elif menu == "📢 إعلانات الاختبارات":
        st.info("واجهة الاختبارات")

# --- 4. واجهة الطالب (مع التنبيهات وصيغة الجوال) ---
elif st.session_state.role == "student":
    st.markdown(f"<div class='header-text'><h3>🎓 أهلاً بك: {st.session_state.student_name}</h3></div>", unsafe_allow_html=True)
    
    ws_st = sh.worksheet("students")
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة", "الإيميل", "الجوال"])
    my_row_idx = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].index[0]
    my_info = df_st.iloc[my_row_idx]

    # تحديث البيانات ذاتياً مع التعليمات
    with st.expander("📝 تحديث بيانات التواصل (هام جداً لاستلام الإشعارات)"):
        st.markdown("""
            <div class='instruction-box'>
            ⚠️ <b>طريقة كتابة رقم الجوال الصحيحة:</b><br>
            يجب كتابة الرقم بالصيغة الدولية بدون الصفر الأول وبدءاً بـ <b>966</b>.<br>
            ✅ مثال صحيح: <b>966501234567</b><br>
            ❌ مثال خاطئ: 0501234567
            </div>
        """, unsafe_allow_html=True)
        
        new_mail = st.text_input("البريد الإلكتروني", value=str(my_info["الإيميل"]))
        new_phone = st.text_input("رقم جوال ولي الأمر (بصيغة 966...)", value=str(my_info["الجوال"]))
        
        if st.button("حفظ وتحديث البيانات"):
            if new_phone.startswith("0"):
                st.error("خطأ: يرجى حذف الصفر الأول وكتابة الرقم بدءاً بـ 966")
            else:
                ws_st.update_cell(my_row_idx + 2, 7, new_mail) # عمود G
                ws_st.update_cell(my_row_idx + 2, 8, new_phone) # عمود H
                st.success("✅ تم تحديث بياناتك بنجاح")
                time.sleep(1); st.rerun()

    # عرض البيانات والبطاقات
    c1, c2, c3 = st.columns(3)
    c1.metric("الصف", my_info["الصف"])
    c2.metric("المرحلة", my_info["المرحلة"])
    c3.metric("المادة", my_info["المادة"])

    st.divider()
    st.subheader("📊 سجل الدرجات والملاحظات")
    # (تكملة عرض جداول الدرجات والسلوك...)
