import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال الآمن ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

def get_db():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        # معرف ملفك الخاص
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

# زر خروج موحد لتجنب خطأ DuplicateElementId
if st.sidebar.button("🚪 تسجيل الخروج", key="logout_global"):
    st.session_state.role = None
    st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

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
                        st.rerun()

        with t2:
            st.subheader("📋 كشف الطلاب المسجلين")
            if sh:
                try:
                    ws_students = sh.worksheet("students")
                    data = ws_students.get_all_records()
                    if data:
                        df_display = pd.DataFrame(data)
                        for index, row in df_display.iterrows():
                            col_info, col_del = st.columns([4, 1])
                            with col_info:
                                st.markdown(f"👤 **{row.get('name', 'بدون اسم')}** | الرقم: `{row.get('id', '؟')}` | الصف: {row.get('class', '؟')}")
                            with col_del:
                                # مفتاح فريد لكل زر حذف لتجنب الأخطاء
                                if st.button("🗑️ حذف", key=f"del_{row.get('id')}_{index}"):
                                    ws_students.delete_rows(index + 2)
                                    # حذف التزامن من sheet1
                                    try:
                                        ws_sheet1 = sh.worksheet("sheet1")
                                        cell = ws_sheet1.find(str(row.get('id')))
                                        ws_sheet1.delete_rows(cell.row)
                                    except: pass
                                    st.success(f"تم حذف الطالب بنجاح")
                                    st.rerun()
                    else: st.info("القائمة فارغة")
                except: st.error("خطأ في تحميل البيانات")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            # جلب أسماء الطلاب للرصد
            ws_st = sh.worksheet("students")
            std_list = [r[1] for r in ws_st.get_all_values()[1:]]
            tab_g, tab_b = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
            
            with tab_g:
                with st.form("g_form"):
                    sel_st = st.selectbox("اختر الطالب", std_list)
                    col1, col2, col3 = st.columns(3)
                    p1 = col1.number_input("P1", 0.0)
                    p2 = col2.number_input("P2", 0.0)
                    pf = col3.number_input("Perf", 0.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        sh.worksheet("grades").append_row([sel_st, p1, p2, pf])
                        st.success("✅ تم حفظ الدرجات")

            with tab_b:
                with st.form("b_form"):
                    sel_b = st.selectbox("اسم الطالب", std_list, key="bs_select")
                    b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    note = st.selectbox("وصف السلوك", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
                    if st.form_submit_button("حفظ الرصد"):
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, note])
                        st.success("✅ تم رصد السلوك")
        except: st.warning("يرجى إضافة طلاب أولاً من تبويب الإدارة")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title(f"🎓 ملف الطالب الأكاديمي")
    try:
        data = sh.worksheet("sheet1").get_all_values()
        res = next((r for r in data if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً بك: {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", res[2])
            c2.metric("الفترة 2", res[3])
            c3.metric("الأداء", res[4])
        else: st.error("عذراً، الرقم الأكاديمي غير مسجل")
    except: st.info("🔄 جاري تحميل النتائج...")
