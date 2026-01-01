import streamlit as st
import gspread
import pandas as pd
import html, uuid, time
from google.oauth2.service_account import Credentials

# =========================
# ⚙️ إعدادات الصفحة والتنسيق العربي (RTL)
# =========================
st.set_page_config(
    page_title="المنصة التعليمية الذكية",
    layout="wide",
    initial_sidebar_state="expanded"
)

# حقن كود CSS لفرض اتجاه اليمين إلى اليسار وتحسين مظهر الجوال
st.markdown("""
    <style>
    /* اتجاه الصفحة من اليمين لليسار */
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        direction: RTL;
        text-align: right;
    }
    /* تعديل اتجاه القائمة الجانبية */
    [data-testid="stSidebarNav"] {
        direction: RTL;
        text-align: right;
    }
    /* تنسيق البطاقات (Cards) للجوال */
    .mobile-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-right: 8px solid #007bff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        color: #333;
    }
    /* تكبير الأزرار لتناسب اللمس */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
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
        st.error(f"⚠️ خطأ في الاتصال بقاعدة البيانات: {e}")
        st.stop()

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df.astype(str).apply(lambda x: x.str.strip())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# =========================
# 🧠 إدارة الجلسة
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user = None

# =========================
# 🔐 شاشة تسجيل الدخول
# =========================
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    
    tab_std, tab_teach = st.tabs(["👨‍🎓 دخول الطلاب", "👨‍🏫 دخول المعلمين"])
    
    with tab_std:
        st.info("أدخل الرقم الأكاديمي المكتوب في عمود (id) داخل الجدول")
        s_id = st.text_input("الرقم الأكاديمي", placeholder="مثلاً: 26", key="login_sid")
        if st.button("دخول الطالب 🚀"):
            df_std = fetch_data("students")
            if not df_std.empty:
                # البحث في العمود الأول (A) بناءً على صورتك
                match = df_std[df_std.iloc[:, 0] == s_id.strip()]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.role = "student"
                    st.session_state.user = s_id.strip()
                    st.success("تم التوثيق بنجاح...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("الرقم الأكاديمي غير مسجل!")
            else:
                st.error("جدول الطلاب فارغ أو غير موجود.")

    with tab_teach:
        u_t = st.text_input("اسم المعلم", key="login_tu")
        p_t = st.text_input("كلمة المرور", type="password", key="login_tp")
        if st.button("دخول المعلم 🔑"):
            df_users = fetch_data("users")
            # التحقق من حساب المعلم
            match = df_users[(df_users['username'] == u_t) & (df_users['role'] == 'teacher')]
            # ملاحظة: استبدل "1234" بكلمة المرور الفعلية في جدولك أو استخدم نظام الـ Hash
            if not match.empty and p_t == "1234":
                st.session_state.auth = True
                st.session_state.role = "teacher"
                st.session_state.user = u_t
                st.rerun()
            else:
                st.error("بيانات المعلم غير صحيحة")
    st.stop()

# =========================
# 👨‍🏫 شاشات المعلم (Teacher UI)
# =========================
if st.session_state.role == "teacher":
    st.sidebar.header(f"أهلاً أ/ {st.session_state.user}")
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 السلوك", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if menu == "👥 إدارة الطلاب":
        st.header("👥 قائمة الطلاب المسجلين")
        df_students = fetch_data("students")
        st.dataframe(df_students, use_container_width=True)
        
        with st.expander("➕ إضافة طالب جديد"):
            with st.form("new_student_form"):
                n_id = st.text_input("الرقم الأكاديمي (id)")
                n_name = st.text_input("اسم الطالب الكامل")
                n_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس"])
                if st.form_submit_button("إضافة الطالب للجدول"):
                    sh.worksheet("students").append_row([n_id, n_name, n_class, "1447هـ", "اللغة الإنجليزية"])
                    st.success("تمت الإضافة بنجاح!")
                    st.rerun()

    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد درجات الطلاب")
        st.write("سيتم عرض الدرجات المرتبطة بالأرقام الأكاديمية")
        st.dataframe(fetch_data("grades"), use_container_width=True)

# =========================
# 👨‍🎓 شاشات الطالب (Student UI)
# =========================
elif st.session_state.role == "student":
    st.sidebar.header(f"الطالب: {st.session_state.user}")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("انتقل إلى:", ["🏠 صفحتي الشخصية", "📊 درجاتي", "🎭 سجل السلوك"])
    
    if st.sidebar.button("🚪 خروج", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    df_students = fetch_data("students")
    # البحث في العمود الأول (id)
    me = df_students[df_students.iloc[:, 0] == st.session_state.user]
    
    if not me.empty:
        student_info = me.iloc[0]
        
        if menu == "🏠 صفحتي الشخصية":
            st.title("🏠 معلوماتي الدراسية")
            st.markdown(f"""
                <div class="mobile-card">
                    <h2 style='color:#007bff;'>{student_info['name']}</h2>
                    <p><b>🔢 الرقم الأكاديمي:</b> {student_info['id']}</p>
                    <p><b>📚 الصف:</b> {student_info.get('class', 'غير محدد')}</p>
                    <p><b>🏆 مجموع النقاط:</b> {student_info.get('النقاط', '0')}</p>
                </div>
            """, unsafe_allow_html=True)

        elif menu == "📊 درجاتي":
            st.title("📊 كشف الدرجات")
            all_grades = fetch_data("grades")
            # البحث عن درجات الطالب بالرقم في العمود الثاني من ورقة الدرجات
            my_grades = all_grades[all_grades.iloc[:, 1] == st.session_state.user]
            if not my_grades.empty:
                for _, row in my_grades.iterrows():
                    st.markdown(f"""
                        <div class="mobile-card">
                            <b>📖 المادة:</b> {row.iloc[2]} <br>
                            <b>✅ الدرجة:</b> {row.iloc[3]}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("لا توجد درجات مرصودة حالياً.")

        elif menu == "🎭 سجل السلوك":
            st.title("🎭 السلوك والانضباط")
            all_behavior = fetch_data("behavior")
            my_behavior = all_behavior[all_behavior.iloc[:, 1] == st.session_state.user]
            if not my_behavior.empty:
                st.table(my_behavior)
            else:
                st.info("سجلك السلوكي نظيف وممتاز!")
    else:
        st.error("لم يتم العثور على بيانات مرتبطة بهذا الرقم.")
