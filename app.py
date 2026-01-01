import streamlit as st
import gspread
import pandas as pd
import hashlib
from google.oauth2.service_account import Credentials

# 1. التنسيق الجمالي للمنصة
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-box { background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); padding: 35px; border-radius: 0 0 35px 35px; color: white; text-align: center; margin: -60px -20px 25px -20px; }
    .stButton>button { width: 100%; border-radius: 12px !important; background-color: #2563eb !important; color: white !important; font-weight: bold; height: 3.2em; }
    </style>
    <div class="header-box">
        <h1>منصة الأستاذ زياد</h1>
        <p>نحو مستقبل تعليمي مشرق وآمن</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الربط (محمية من أخطاء التنسيق)
@st.cache_resource
def get_db_connection():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

client = get_db_connection()

if "auth_role" not in st.session_state:
    st.session_state.auth_role = None

# 3. شاشة تسجيل الدخول
if st.session_state.auth_role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        student_id_input = st.text_input("الرقم الأكاديمي", placeholder="مثلاً: 26", key="s_login")
        if st.button("دخول الطالب 🚀"):
            if client:
                try:
                    # جلب ورقة الطلاب
                    ws = client.worksheet("students")
                    # قراءة البيانات كقيم نصية خام لتجنب انهيار الكود
                    all_data = ws.get_all_values()
                    df = pd.DataFrame(all_data[1:], columns=all_data[0])
                    
                    # تنظيف وتجهيز البحث
                    df['id'] = df['id'].astype(str).str.strip()
                    search_id = str(student_id_input).strip()
                    
                    user = df[df['id'] == search_id]
                    
                    if not user.empty:
                        st.session_state.auth_role = "student"
                        st.session_state.user_info = user.iloc[0].to_dict()
                        st.rerun()
                    else:
                        # الرسالة المطلوبة عند الخطأ
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except: st.error("⚠️ يرجى التأكد من تسمية عمود الـ (id) في الجدول بشكل صحيح.")
            else: st.error("⚠️ فشل الاتصال بقاعدة البيانات.")

    with tab2:
        username = st.text_input("اسم المستخدم", key="t_user")
        password = st.text_input("كلمة المرور", type="password", key="t_pass")
        if st.button("دخول المعلم 🔐"):
            if client:
                try:
                    # جلب ورقة المعلمين
                    ws_u = client.worksheet("users")
                    u_data = ws_u.get_all_values()
                    u_df = pd.DataFrame(u_data[1:], columns=u_data[0])
                    
                    user_row = u_df[u_df['username'].str.strip() == username.strip()]
                    if not user_row.empty:
                        # التشفير المطابق لجدولك
                        h = hashlib.sha256(str.encode(password)).hexdigest()
                        if h == user_row.iloc[0]['password_hash'].strip():
                            st.session_state.auth_role = "teacher"
                            st.rerun()
                        else: st.error("❌ كلمة المرور غير صحيحة")
                    else: st.error("❌ اسم المستخدم غير موجود")
                except: st.error("⚠️ فشل الوصول لجدول الصلاحيات.")
    st.stop()

# 4. لوحات التحكم
if st.session_state.auth_role == "student":
    st.success(f"مرحباً بك يا {st.session_state.user_info['name']}")
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.auth_role == "teacher":
    st.success("أهلاً بك يا أستاذ زياد")
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()
