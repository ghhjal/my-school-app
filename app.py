import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    """جلب البيانات مع تنظيف أسماء الأعمدة لمنع الأخطاء"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        # تنظيف أسماء الأعمدة من المسافات الزائدة
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"تنبيه: لم يتم العثور على ورقة العمل '{worksheet_name}' أو هي فارغة.")
        return pd.DataFrame()

# --- 2. التصميم الاحترافي ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .stButton>button { border-radius: 12px; width: 100%; height: 3em; font-weight: bold; }
    .main-header { background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. منطق الدخول والحماية من الانهيار ---
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown('<div class="main-header"><h1>منصة زياد الذكية</h1><p>نظام إدارة المدرسة المتطور</p></div>', unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🎓 بوابة الطالب", "🔐 بوابة الإدارة"])
    
    with t1:
        with st.form("login_student"):
            sid = st.text_input("🆔 أدخل الرقم الأكاديمي للمتابعة")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df_st = fetch_safe("students")
                
                # التحقق من وجود العمود المطلوب بأمان
                target_col = 'الالرقم الأكاديمي' if 'الالرقم الأكاديمي' in df_st.columns else df_st.columns[0]
                
                if not df_st.empty:
                    if str(sid).strip() in df_st[target_col].astype(str).values:
                        st.session_state.role = "student"
                        st.session_state.sid = str(sid).strip()
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ الرقم غير مسجل. تأكد من صحة الرقم أو تواصل مع الإدارة.")
                else:
                    st.error("⚠️ قاعدة بيانات الطلاب فارغة حالياً.")

    with t2:
        with st.form("login_admin"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = fetch_safe("users")
                if not df_u.empty and 'username' in df_u.columns:
                    row = df_u[df_u['username'] == u.strip()]
                    if not row.empty:
                        hashed = hashlib.sha256(str.encode(p)).hexdigest()
                        # التحقق من العمود الصحيح لكلمة المرور
                        pass_col = 'password_hash' if 'password_hash' in df_u.columns else df_u.columns[1]
                        if hashed == str(row.iloc[0][pass_col]):
                            st.session_state.role = "teacher"
                            st.rerun()
                        else: st.error("🔑 كلمة المرور خاطئة")
                    else: st.error("👤 المستخدم غير موجود")

    # زر تشخيصي يظهر فقط عند وجود مشكلة (يساعدك في معرفة أسماء الأعمدة الحقيقية)
    with st.expander("🛠️ وضع تشخيص الأخطاء (للمطور فقط)"):
        df_debug = fetch_safe("students")
        st.write("الأعمدة المتوفرة في شيت الطلاب حالياً:")
        st.write(list(df_debug.columns))

    st.stop()

# --- 4. واجهة المعلم (Teacher) ---
if st.session_state.role == "teacher":
    st.sidebar.title("👨‍🏫 لوحة المعلم")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    
    st.success("مرحباً بك يا أستاذ زياد. النظام مستقر الآن.")
    # أضف هنا بقية دوال المعلم الخاصة بك

# --- 5. واجهة الطالب (Student) ---
if st.session_state.role == "student":
    st.sidebar.title("🎓 لوحة الطالب")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    
    df_st = fetch_safe("students")
    # جلب بيانات الطالب بأمان باستخدام العمود الأول كمعرف
    target_col = df_st.columns[0]
    s_data = df_st[df_st[target_col].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"### مرحباً بك يا {s_data.get('الاسم الثلاثي', 'أيها الطالب')}")
    st.info(f"رصيدك الحالي من النقاط: {s_data.get('النقاط', 0)}")
