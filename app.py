import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="نظام الإدارة المدرسية", layout="wide")

def get_gspread_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return gspread.authorize(creds)
    except: return None

gc = get_gspread_client()
sh = None
if gc:
    try: sh = gc.open_by_key("1Xf_B-YOUR_ACTUAL_ID_HERE") # ضع معرف ملفك هنا
    except: pass

# --- 2. إدارة الجلسة والدخول ---
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if st.session_state.user_role is None:
    st.title("🔐 نظام المدرسة الرقمي")
    choice = st.radio("اختر نوع المستخدم", ["👨‍🏫 معلم", "🎓 طالب"], horizontal=True)
    
    if choice == "👨‍🏫 معلم":
        pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.user_role = "teacher"
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    else:
        std_id = st.text_input("أدخل رقم الطالب")
        if st.button("دخول الطالب"):
            if std_id:
                st.session_state.user_role = "student"
                st.session_state.student_id = std_id
                st.rerun()
    st.stop()

# --- زر خروج موحد (تم إصلاح خطأ التكرار هنا) ---
if st.sidebar.button("🚪 تسجيل الخروج", key="global_logout"):
    st.session_state.user_role = None
    st.rerun()

# --- 3. واجهة المعلم (رصد وإدارة) ---
if st.session_state.user_role == "teacher":
    st.title("👨‍🏫 لوحة تحكم المعلم")
    tab1, tab2, tab3 = st.tabs(["🎭 رصد السلوك", "📊 لوحة الدرجات", "👥 إدارة الطلاب"])
    
    # جلب الأسماء لجميع التبويبات
    names = []
    if sh:
        try:
            ws_gr = sh.worksheet("sheet1")
            names = ws_gr.col_values(2)[1:] # العمود B الأسماء
        except: names = []

    with tab1:
        with st.form("behavior_form"):
            s_name = st.selectbox("اسم الطالب", names if names else ["لا توجد أسماء"])
            b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
            b_desc = st.selectbox("الوصف", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
            if st.form_submit_button("🚀 حفظ الرصد"):
                if sh and s_name != "لا توجد أسماء":
                    try:
                        sh.worksheet("behavior").append_row([s_name, str(datetime.now().date()), b_type, b_desc])
                        st.success(f"تم الحفظ لـ {s_name}")
                    except: st.error("خطأ في الاتصال")

    with tab3: # شاشة إدارة الطلاب (الكود الخاص بك)
        st.markdown("### 👥 إدارة شؤون الطلاب")
        t_sub1, t_sub2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        with t_sub1:
            with st.form("add_student", clear_on_submit=True):
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
                    if sh:
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0", sphase, sclass])
                        st.success("✅ تم الحفظ")
                        st.rerun()

        with t_sub2:
            if sh:
                data = sh.worksheet("sheet1").get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    for i, r in df.iterrows():
                        st.info(f"👤 {r.get('الاسم', '؟')} | ID: {r.get('رقم الطالب', '؟')}")
                        if st.button(f"🗑️ حذف {r.get('الاسم')}", key=f"del_{i}"):
                            sh.worksheet("sheet1").delete_rows(i + 2)
                            st.rerun()

# --- 4. واجهة الطالب (مستقلة) ---
elif st.session_state.user_role == "student":
    st.title("🎓 بوابة الطالب")
    if sh:
        try:
            ws_gr = sh.worksheet("sheet1")
            row = next((r for r in ws_gr.get_all_values() if r[0] == st.session_state.student_id), None)
            if row:
                st.success(f"👋 أهلاً {row[1]}")
                st.metric("📊 مجموع درجاتك", row[4]) # الأداء
            else: st.error("❌ الرقم غير مسجل")
        except: st.info("🔄 جاري التحديث...")
