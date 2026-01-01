import streamlit as st
import gspread
import pandas as pd
import html, time
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ إعدادات الصفحة والتنسيق الاحترافي (RTL)
# ==========================================
st.set_page_config(
    page_title="منصة التميز التعليمية",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# حقن كود CSS مخصص لتصميم يشبه تطبيقات الموبايل
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
        background-color: #f0f2f5;
    }

    /* هيدر التطبيق الاحترافي */
    .app-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 25px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin: -60px -20px 20px -20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* تنسيق الحقول الإرشادية */
    .stTextInput label {
        font-weight: bold !important;
        color: #1e3a8a !important;
    }
    
    .stTextInput input {
        border-radius: 12px !important;
        border: 1px solid #d1d5db !important;
        padding: 12px !important;
    }

    /* تنسيق الأزرار كأنها تطبيق */
    .stButton>button {
        width: 100%;
        border-radius: 15px !important;
        background-color: #1e3a8a !important;
        color: white !important;
        font-weight: bold !important;
        height: 50px !important;
        border: none !important;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #3b82f6 !important;
        transform: translateY(-2px);
    }

    /* بطاقة المعلومات للطالب */
    .student-info-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        border-right: 10px solid #3b82f6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-top: 10px;
    }

    /* إخفاء القوائم غير الضرورية في الجوال */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =========================
# 🔒 الاتصال بقاعدة البيانات
# =========================
@st.cache_resource
def get_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ خطأ في الاتصال بالخادم")
        st.stop()

sh = get_db()

def fetch_data(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df.astype(str).apply(lambda x: x.str.strip())
        return pd.DataFrame()
    except: return pd.DataFrame()

# =========================
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 شاشة الدخول الاحترافية
# =========================
if not st.session_state.auth:
    # هيدر علوي جذاب
    st.markdown('<div class="app-header"><h1>منصة التميز التعليمية</h1><p>مرحباً بك في بوابتك الذكية</p></div>', unsafe_allow_html=True)
    
    # استخدام حاوية (Container) لتنظيم العناصر في منتصف الشاشة
    with st.container():
        tab_std, tab_teach = st.tabs(["👨‍🎓 دخول الطلاب", "👨‍🏫 بوابة المعلمين"])
        
        with tab_std:
            st.write("") # مسافة
            student_id = st.text_input("رقم الهوية / الرقم الأكاديمي", placeholder="أدخل رقمك هنا...", key="s_id")
            
            if st.button("تسجيل الدخول للمنصة"):
                if student_id:
                    df_std = fetch_data("students")
                    # البحث في العمود الأول (A) بناءً على صورتك
                    match = df_std[df_std.iloc[:, 0] == student_id]
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.role = "student"
                        st.session_state.user = student_id
                        st.success("✅ تم التحقق، مرحباً بك!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ الرقم غير مسجل، يرجى التواصل مع المعلم.")
                else:
                    st.warning("⚠️ يرجى كتابة الرقم أولاً.")

        with tab_teach:
            u_t = st.text_input("اسم المستخدم", key="t_u")
            p_t = st.text_input("كلمة المرور", type="password", key="t_p")
            if st.button("دخول هيئة التدريس"):
                df_users = fetch_data("users")
                match = df_users[(df_users['username'] == u_t) & (df_users['role'] == 'teacher')]
                if not match.empty and p_t == "1234": # يفضل تغيير الباسوورد في الجدول
                    st.session_state.auth = True
                    st.session_state.role = "teacher"
                    st.session_state.user = u_t
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة.")
    st.stop()

# =========================
# 👨‍🎓 لوحة الطالب (واجهة الجوال)
# =========================
if st.session_state.role == "student":
    st.markdown('<div class="app-header"><h3>لوحة بيانات الطالب</h3></div>', unsafe_allow_html=True)
    
    df_students = fetch_data("students")
    me = df_students[df_students.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        s = me.iloc[0]
        # بطاقة تعريف الطالب
        st.markdown(f"""
            <div class="student-info-card">
                <h2 style='color: #1e3a8a; margin-bottom:5px;'>{s['name']}</h2>
                <p><b>🆔 الرقم الأكاديمي:</b> {s['id']}</p>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <span><b>📚 الصف:</b> {s.get('class', 'غير محدد')}</span>
                    <span><b>🏆 النقاط:</b> <span style="color:green; font-weight:bold;">{s.get('النقاط', '0')}</span></span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # قائمة الخيارات السفلية (كأنها أزرار تطبيق)
        st.write("")
        menu = st.radio("القائمة السريعة:", ["🏠 الرئيسية", "📊 نتائجي", "📞 التواصل"], horizontal=True)
        
        if menu == "📊 نتائجي":
            st.subheader("📝 درجات المواد")
            # هنا يمكنك عرض الدرجات من جدول grades
            st.info("سيتم عرض درجاتك التفصيلية هنا قريباً.")
            
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

# =========================
# 👨‍🏫 لوحة المعلم (واجهة متكاملة)
# =========================
elif st.session_state.role == "teacher":
    st.sidebar.title(f"مرحباً أ/ {st.session_state.user}")
    st.header("إدارة بيانات الطلاب")
    
    df_all = fetch_data("students")
    st.dataframe(df_all, use_container_width=True)
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()
