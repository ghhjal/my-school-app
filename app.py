import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide")

def get_db_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # تأكد أن ملف secrets يحتوي على بيانات gcp_service_account
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = gspread.authorize(creds)
        # تم وضع معرف ملفك هنا بناءً على الرابط الذي أرسلته
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db_connection()

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    login_tab1, login_tab2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    
    with login_tab1:
        pwd = st.text_input("كلمة المرور", type="password", key="p_teacher")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
            
    with login_tab2:
        user_id = st.text_input("أدخل رقم الطالب الأكاديمي", key="s_login")
        if st.button("دخول الطالب"):
            if user_id:
                st.session_state.role = "student"
                st.session_state.student_id = user_id
                st.rerun()
    st.stop()

# زر خروج موحد لتجنب خطأ التكرار
if st.sidebar.button("🚪 تسجيل الخروج", key="logout_main"):
    st.session_state.role = None
    st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])
    
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t1, t2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with t1:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ"):
                    if sh and sname:
                        try:
                            # الحفظ في جدول students
                            sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssubject])
                            # تحديث ورقة sheet1 للنتائج
                            sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                            st.success(f"✅ تم تسجيل {sname}")
                        except: st.error("❌ تأكد من وجود ورقة باسم 'students' و 'sheet1'")

        with t2:
            if sh:
                try:
                    data = sh.worksheet("students").get_all_records()
                    if data:
                        df = pd.DataFrame(data)
                        for idx, row in df.iterrows():
                            st.write(f"👤 {row.get('name', '؟؟')} | ID: {row.get('id', '؟؟')}")
                except: st.info("القائمة فارغة")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الأداء والسلوك")
        try:
            # جلب الأسماء من ورقة students
            names = [r[1] for r in sh.worksheet("students").get_all_values()[1:]]
            st1, st2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with st1:
                with st.form("grade_form"):
                    sel_n = st.selectbox("الطالب", names)
                    g1, g2, gp = st.columns(3)
                    v1 = g1.number_input("P1", 0.0)
                    v2 = g2.number_input("P2", 0.0)
                    vperf = gp.number_input("Perf", 0.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        sh.worksheet("grades").append_row([sel_n, v1, v2, vperf])
                        st.success("تم الحفظ")

            with st2:
                with st.form("beh_form"):
                    sel_b = st.selectbox("الطالب", names, key="b_sel_key")
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("ملاحظة السلوك")
                    if st.form_submit_button("رصد"):
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                        st.success("تم الرصد")
        except: st.warning("يجب إضافة طلاب أولاً")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title(f"🎓 نتائج الطالب: {st.session_state.student_id}")
    if sh:
        try:
            data = sh.worksheet("sheet1").get_all_values()
            user_data = next((r for r in data if r[0] == st.session_state.student_id), None)
            if user_data:
                st.success(f"أهلاً بك يا {user_data[1]}")
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة 1", user_data[2])
                c2.metric("الفترة 2", user_data[3])
                c3.metric("الأداء", user_data[4])
            else: st.error("❌ الرقم الأكاديمي غير موجود")
        except: st.info("🔄 جاري تحميل البيانات...")
