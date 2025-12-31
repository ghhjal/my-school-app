import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# --- 1. تهيئة حالة الجلسة أولاً (لحل مشكلة AttributeError) ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# --- 2. إعدادات التصميم (لجعل التطبيق احترافي على الجوال) ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. دالة الاتصال (محصنة ضد خطأ 404) ---
def get_google_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # تأكد من إضافة gcp_service_account في Secrets على Streamlit Cloud
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # ⚠️ تأكد أن هذا الرابط هو رابط ملفك الفعلي ⚠️
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        
        return client.open_by_url(SHEET_URL)
    except Exception as e:
        st.error(f"❌ لم نتمكن من الوصول للملف. تأكد من الرابط ومن إضافة ايميل الخدمة للملف. نوع الخطأ: {e}")
        return None

sh = get_google_sheet()

# --- 4. واجهة تسجيل الدخول ---
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; text-align: center; color: white; margin-bottom: 25px;">
            <h1 style="font-size: 2rem; margin: 0;">🌟 منصة الأستاذ زياد العمري</h1>
            <p style="opacity: 0.9; margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", placeholder="مثال: 1001").strip()
        
        if st.button("🚀 دخول للمنصة", type="primary"):
            if login_type == "معلم":
                if user_id == "1234": # كود المعلم الافتراضي
                    st.session_state.role = "teacher"
                    st.rerun()
                else:
                    st.error("❌ كود المعلم غير صحيح")
            else:
                if sh:
                    try:
                        ws = sh.worksheet("students")
                        df = pd.DataFrame(ws.get_all_records())
                        # تنظيف الأكواد للمطابقة الدقيقة
                        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                        
                        if user_id in df.iloc[:, 0].values:
                            st.session_state.role = "student"
                            st.session_state.sid = user_id
                            st.rerun()
                        else:
                            st.error(f"❌ الكود ({user_id}) غير موجود في سجلات الطلاب")
                    except Exception as e:
                        st.error(f"⚠️ خطأ في قراءة بيانات الطلاب: {e}")
                else:
                    st.error("❌ لا يوجد اتصال بقاعدة البيانات حالياً")

# --- 5. واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.sidebar.title("👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك"])
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        if sh:
            ws = sh.worksheet("students")
            df = pd.DataFrame(ws.get_all_records())
            st.dataframe(df, use_container_width=True)
            
            with st.expander("➕ إضافة طالب جديد"):
                with st.form("add_st"):
                    c1, c2, c3 = st.columns(3)
                    nid = c1.text_input("الكود")
                    nname = c2.text_input("الاسم")
                    nclass = c3.selectbox("الصف", ["الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    if st.form_submit_button("اعتماد الإضافة"):
                        ws.append_row([nid, nname, nclass, "1447", "نشط", "English", "ابتدائي", "", "", "0"])
                        st.success("تم الحفظ بنجاح"); time.sleep(1); st.rerun()

# --- 6. واجهة الطالب ---
elif st.session_state.role == "student":
    if sh:
        ws = sh.worksheet("students")
        df = pd.DataFrame(ws.get_all_records())
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        s_data = df[df.iloc[:, 0] == st.session_state.sid].iloc[0]
        
        st.markdown(f"""
            <div style="background: #1e3a8a; padding: 20px; border-radius: 15px; color: white; text-align: center;">
                <h2>🎓 أهلاً بك: {s_data.iloc[1]}</h2>
                <p>الصف: {s_data.iloc[2]} | الحالة: {s_data.iloc[4]}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # عرض النقاط بشكل مميز
        points = s_data.iloc[8] if len(s_data) > 8 else 0
        st.markdown(f"""
            <div style="text-align: center; margin-top: 20px; padding: 20px; border: 2px solid #f59e0b; border-radius: 15px;">
                <span style="font-size: 1.2rem; color: #64748b;">رصيد نقاطك السلوكية</span><br>
                <span style="font-size: 3rem; color: #f59e0b; font-weight: bold;">{points} 🌟</span>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚗 تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()
