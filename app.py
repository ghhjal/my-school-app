import streamlit as st
import gspread
import pandas as pd
import hashlib
from google.oauth2.service_account import Credentials

# 1. إعداد الصفحة والتصميم مع الشعار (Header & Logo)
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 40px 20px; border-radius: 0 0 35px 35px; color: white; text-align: center;
        margin: -65px -20px 25px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .logo-box {
        background: rgba(255, 255, 255, 0.2); width: 70px; height: 70px; border-radius: 20px;
        margin: 0 auto 15px auto; display: flex; justify-content: center; align-items: center;
        border: 2px solid rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px);
    }
    .logo-box i { font-size: 35px; color: white; }
    .stTextInput input { border-radius: 12px !important; padding: 12px !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 12px !important; width: 100%; height: 55px; font-weight: bold; border: none; }
    </style>

    <div class="header-box">
        <div class="logo-box"><i class="bi bi-graph-up-arrow"></i></div>
        <h1 style="margin:0; font-size: 28px;">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.9; font-size: 15px;">بوابتك نحو التميز والنجاح</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظيفة الاتصال ببيانات جوجل
@st.cache_resource
def get_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

client = get_db()

if "login_state" not in st.session_state:
    st.session_state.login_state = None

# 3. واجهة تسجيل الدخول
if st.session_state.login_state is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        st.write("")
        student_id = st.text_input("الرقم الأكاديمي الموحد", placeholder="ادخل رقم الهوية", key="std_id")
        if st.button("دخول آمن للمنصة 🚀"):
            if client:
                try:
                    # جلب البيانات الخام من ورقة students
                    ws = client.worksheet("students")
                    data = ws.get_all_values()
                    
                    # تحويل البيانات لجدول مع التأكد من أسماء الأعمدة
                    df = pd.DataFrame(data[1:], columns=data[0])
                    
                    # تنظيف البحث (إزالة المسافات وتحويل لنص)
                    df['id'] = df['id'].astype(str).str.strip()
                    input_val = str(student_id).strip()
                    
                    # البحث عن الطالب
                    student_row = df[df['id'] == input_val]
                    
                    if not student_row.empty:
                        st.session_state.login_state = "student"
                        st.session_state.user_data = student_row.iloc[0].to_dict()
                        st.rerun()
                    else:
                        # الرسالة الدقيقة التي طلبتها
                        st.error("❌ عذراً، رقم الهوية الذي أدخلته غير مسجل لدينا.")
                except Exception as e:
                    st.error(f"⚠️ خطأ في قراءة الجدول: يرجى التأكد من وجود عمود باسم 'id' في الشيت.")
            else: st.error("⚠️ لا يوجد اتصال بقاعدة البيانات.")

    with tab2:
        st.write("")
        t_user = st.text_input("اسم المستخدم", key="teach_u")
        t_pass = st.text_input("كلمة المرور", type="password", key="teach_p")
        if st.button("دخول المعلم 🔐"):
            if client:
                try:
                    # جلب ورقة users
                    ws_u = client.worksheet("users")
                    u_data = ws_u.get_all_values()
                    u_df = pd.DataFrame(u_data[1:], columns=u_data[0])
                    
                    # البحث عن المعلم
                    user_match = u_df[u_df['username'].str.strip() == t_user.strip()]
                    if not user_match.empty:
                        # تشفير SHA256 والمقارنة بعمود password_hash
                        hashed = hashlib.sha256(str.encode(t_pass)).hexdigest()
                        if hashed == user_match.iloc[0]['password_hash'].strip():
                            st.session_state.login_state = "teacher"
                            st.rerun()
                        else: st.error("❌ كلمة المرور غير صحيحة")
                    else: st.error("❌ اسم المستخدم غير موجود")
                except: st.error("⚠️ فشل في التحقق من صلاحيات المعلم.")
    st.stop()

# 4. لوحات التحكم
if st.session_state.login_state == "student":
    u = st.session_state.user_data
    st.success(f"مرحباً بك يا {u['name']}")
    st.markdown(f"**نقاطك التعليمية:** {u.get('النقاط', 0)}")
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.login_state == "teacher":
    st.success("أهلاً بك يا أستاذ زياد في لوحة التحكم الإدارية")
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()
