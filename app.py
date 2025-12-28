import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال الآمن ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

def get_db():
    try:
        # تصحيح الـ Scopes لحل مشكلة فشل الاتصال
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        # معرف ملفك الخاص الذي استخرجناه سابقاً
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db()

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    l_tab1, l_tab2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    
    with l_tab1:
        pwd = st.text_input("كلمة مرور المعلم", type="password", key="pwd_t")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
            
    with l_tab2:
        std_id = st.text_input("رقم الطالب الأكاديمي", key="std_l")
        if st.button("دخول الطالب"):
            if std_id:
                st.session_state.role = "student"
                st.session_state.student_id = std_id
                st.rerun()
    st.stop()

# زر خروج موحد في الشريط الجانبي
if st.sidebar.button("🚪 تسجيل الخروج", key="logout_global"):
    st.session_state.role = None
    st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    # شاشة إدارة الطلاب (تطابق مع صورتك 91405f)
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t1, t2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with t1:
            with st.form("student_reg", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ", "1448هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ"):
                    if sh and sname:
                        # الحفظ في جدول students
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub])
                        # تحديث ورقة النتائج sheet1 للدخول
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success(f"✅ تم حفظ {sname} بنجاح")

        with t2:
            try:
                df = pd.DataFrame(sh.worksheet("students").get_all_records())
                st.dataframe(df, use_container_width=True)
            except: st.info("القائمة فارغة")

    # شاشة الدرجات والسلوك (تطابق مع مخططك 91b0c3)
    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            std_list = [r[1] for r in sh.worksheet("students").get_all_values()[1:]]
            tab_g, tab_b = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
            
            with tab_g:
                with st.form("g_form"):
                    sel_st = st.selectbox("اختر الطالب", std_list)
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("P1", 0.0)
                    p2 = col2.number_input("P2", 0.0)
                    pf = col3.number_input("Perf", 0.0)
                    if st.form_submit_button("تحديث"):
                        sh.worksheet("grades").append_row([sel_st, p1, p2, pf])
                        st.success("تم الحفظ")

            with tab_b:
                with st.form("b_form"):
                    sel_b = st.selectbox("اختر الطالب", std_list, key="bs")
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    note = st.text_input("وصف السلوك")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, note])
                        st.success("تم الرصد")
        except: st.warning("يرجى إضافة طلاب أولاً")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title(f"🎓 نتائج الطالب: {st.session_state.student_id}")
    try:
        data = sh.worksheet("sheet1").get_all_values()
        res = next((r for r in data if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", res[2])
            c2.metric("الفترة 2", res[3])
            c3.metric("الأداء", res[4])
        else: st.error("رقم أكاديمي غير مسجل")
    except: st.info("🔄 جاري تحميل النتائج...")
