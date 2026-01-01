import streamlit as st
import gspread
import pandas as pd
import html, uuid, time
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات الصفحة (متجاوبة)
# =========================
st.set_page_config(
    page_title="منصتي التعليمية", 
    layout="wide", 
    initial_sidebar_state="collapsed" # إخفاء القائمة الجانبية تلقائياً في الجوال
)

# تنسيق CSS مخصص لتحسين المظهر على الجوال
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    .stTextInput>div>div>input { border-radius: 10px; }
    /* تنسيق بطاقة المعلومات */
    .student-card {
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;
        border-right: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 🔒 اتصال Google Sheets
# =========================
@st.cache_resource
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        st.stop()

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
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
# 🔐 تسجيل الدخول (تصميم جوال)
# =========================
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 10, 1]) # موازنة المحتوى في منتصف الشاشة
    with col2:
        st.title("🔐 دخول المنصة")
        
        tab_std, tab_teach = st.tabs(["👨‍🎓 الطالب", "👨‍🏫 المعلم"])
        
        with tab_std:
            st.write("استخدم رقمك الأكاديمي للدخول")
            student_id = st.text_input("الرقم الأكاديمي (ID)", placeholder="مثلاً: 26", key="mob_s_id")
            if st.button("دخول الطالب 🚀"):
                df_std = fetch("students")
                if not df_std.empty:
                    # البحث في العمود الأول (A) كما في صورتك
                    match = df_std[df_std.iloc[:, 0] == student_id.strip()]
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.role = "student"
                        st.session_state.user = student_id.strip()
                        st.success("تم الدخول بنجاح")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("الرقم غير مسجل")

        with tab_teach:
            u_t = st.text_input("اسم المستخدم", key="mob_t_u")
            p_t = st.text_input("كلمة المرور", type="password", key="mob_t_p")
            if st.button("دخول المعلم 🔑"):
                df_users = fetch("users")
                match = df_users[(df_users['username'] == u_t) & (df_users['role'] == 'teacher')]
                if not match.empty and p_t == "1234":
                    st.session_state.auth = True
                    st.session_state.role = "teacher"
                    st.session_state.user = u_t
                    st.rerun()
                else:
                    st.error("بيانات خاطئة")
    st.stop()

# =========================
# 👨‍🎓 لوحة الطالب (تصميم بطاقات الجوال)
# =========================
if st.session_state.role == "student":
    st.markdown(f"### 👋 أهلاً بك")
    
    df_students = fetch("students")
    me = df_students[df_students.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        student_data = me.iloc[0]
        # عرض البيانات على شكل بطاقة جذابة
        st.markdown(f"""
            <div class="student-card">
                <h4>{student_data['name']}</h4>
                <p><b>🔢 الرقم:</b> {student_data['id']}</p>
                <p><b>📚 الصف:</b> {student_data.get('class', 'غير محدد')}</p>
                <p><b>🏆 النقاط:</b> {student_data.get('النقاط', '0')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        menu = st.segmented_control("اختر العرض", ["📊 الدرجات", "🎭 السلوك"], default="📊 الدرجات")
        
        if menu == "📊 الدرجات":
            all_grades = fetch("grades")
            my_grades = all_grades[all_grades.iloc[:, 1] == st.session_state.user]
            if not my_grades.empty:
                for _, row in my_grades.iterrows():
                    st.info(f"📖 {row.iloc[2]}: {row.iloc[3]} درجة")
            else:
                st.write("لا توجد درجات حالياً")
                
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

# =========================
# 👨‍🏫 لوحة المعلم (تصميم بسيط)
# =========================
elif st.session_state.role == "teacher":
    st.title("👨‍🏫 إدارة المنصة")
    
    with st.expander("➕ إضافة طالب جديد"):
        with st.form("add_mob"):
            new_id = st.text_input("الرقم (ID)")
            new_name = st.text_input("الاسم")
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([new_id, new_name])
                st.rerun()

    st.write("👥 قائمة الطلاب:")
    st.dataframe(fetch("students"), use_container_width=True)
    
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()
