import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# CSS لتحسين المظهر على الجوال
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1e3a8a; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 10px; border-right: 5px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            raw_headers = data[0]
            clean_headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(raw_headers)]
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول (تصميم البطاقات للجوال)
# ==========================================
if st.session_state.role is None:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a; padding: 20px;'>🎓 منصة الأستاذ زياد التعليمية</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطلاب", "🔐 دخول المعلم"])
    
    with tab1:
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            sid_in = st.text_input("أدخل الرقم الأكاديمي", placeholder="مثال: 12345")
            if st.button("دخول الطالب 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid_in)
                    st.rerun()
                else: st.error("❌ الرقم غير مسجل")
            st.markdown("</div>", unsafe_allow_html=True)
            
    with tab2:
        with st.container():
            st.markdown("<div class='card' style='border-right-color: #ef4444;'>", unsafe_allow_html=True)
            t_pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول المعلم 🔐"):
                if t_pwd == "1234":
                    st.session_state.role = "teacher"
                    st.rerun()
                else: st.error("❌ كلمة المرور خطأ")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (تصميم القوائم للجوال)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.markdown("### 📱 لوحة التحكم")
    menu = st.sidebar.selectbox("اختر الشاشة", ["👥 الطلاب", "📝 الدرجات", "🎭 السلوك", "📢 الاختبارات"])
    
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()

    if menu == "🎭 السلوك":
        st.markdown("### 🎭 رصد السلوك والتواصل")
        df_st = fetch_safe("students")
        search_term = st.text_input("🔍 ابحث عن اسم الطالب")
        filtered_names = [n for n in df_st.iloc[:, 1].tolist() if search_term in n] if search_term else df_st.iloc[:, 1].tolist()
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + filtered_names)
        
        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_phone = str(student_info[7]).split('.')[0]
            with st.container(border=True):
                b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_note = st.text_area("الملاحظة")
                if st.button("💾 حفظ السلوك"):
                    sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الحفظ!")
                
                # أزرار الواتساب (كبيرة للجوال)
                wa_msg = f"ولي أمر الطالب: {b_name}\nتم رصد: {b_type}\nالملاحظة: {b_note}"
                wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">💬 إرسال عبر واتساب</div></a>', unsafe_allow_html=True)

    elif menu == "📢 الاختبارات":
        st.markdown("### 📢 إضافة تنبيه/اختبار")
        with st.form("exam_form"):
            a_class = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = st.text_input("عنوان التنبيه")
            a_date = st.date_input("الموعد")
            if st.form_submit_button("🚀 نشر وإرسال للمجموعات"):
                sh.worksheet("exams").append_row([a_class, a_title, str(a_date)])
                wa_msg = f"📢 تنبيه لطلاب صف {a_class}:\nالموضوع: {a_title}\nالموعد: {a_date}"
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank">📲 اضغط هنا لنشر التنبيه في واتساب</a>', unsafe_allow_html=True)
                st.rerun()

    # (بقية أقسام المعلم تبقى بنفس المنطق مع أزرار عريضة)

# ==========================================
# 👨‍🎓 واجهة الطالب (تصميم البطاقات الحديثة)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin:-1rem -1rem 1rem -1rem;">
            <h3>مرحباً، {s_row[1]} 👋</h3>
            <p>صف: {s_row[2]}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("🌟 نقاطك", f"{s_row[8]} ن")
    col2.metric("📚 المادة", s_row[5])

    st.markdown("#### 📢 التنبيهات الجديدة")
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_row[2]) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.markdown(f"""
                <div class="card">
                    <small style='color:#3b82f6;'>📅 {r[2]}</small>
                    <div style='font-weight:bold; font-size:1.1em;'>📍 {r[1]}</div>
                </div>
            """, unsafe_allow_html=True)
    
    if st.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
