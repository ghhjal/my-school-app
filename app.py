import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- 1. الاتصال بملف English_Grades ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except: return pd.DataFrame()

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        if st.button("دخول كمعلم (Pass: 1234)"): st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- 3. واجهة المعلم الكاملة ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    # قائمة التنقل الجانبية كما في الصورة
    menu = st.sidebar.radio("انتقل إلى:", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "📢 إعلانات الاختبارات":
        st.header("📢 إضافة تنبيه اختبار جديد")
        with st.form("exam_form"):
            # حقول الإضافة مطابقة للصورة
            target_cls = st.selectbox("حدد الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            exam_title = st.text_input("عنوان الاختبار (مثلاً: اختبار الفترة الأولى)")
            exam_date = st.date_input("موعد الاختبار", value=datetime.now())
            
            if st.form_submit_button("إرسال التنبيه للطلاب 🚀"):
                sh.worksheet("exams").append_row([target_cls, exam_title, str(exam_date)])
                st.success("تم إرسال التنبيه بنجاح")
        
        st.divider()
        st.subheader("📋 الاختبارات المعلنة حالياً")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            # عرض الأعمدة: الصف، العنوان، التاريخ
            st.dataframe(df_ex[['الصف', 'العنوان', 'التاريخ']], use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد اختبارات معلنة حالياً")

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with tab1:
            st.subheader("تحديث درجات الطالب (p1, p2, perf)")
            df_st = fetch_safe("students")
            target = st.selectbox("الطالب", df_st['name'].tolist())
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                v_p1 = c1.number_input("ف1 (p1)")
                v_p2 = c2.number_input("ف2 (p2)")
                v_perf = c3.number_input("مشاركة (perf)")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try: 
                        fnd = ws_g.find(target)
                        ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v_p1, v_p2, v_perf]])
                    except: ws_g.append_row([target, v_p1, v_p2, v_perf])
                    st.success("تم التحديث")

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        with st.form("add_st"):
            st.write("📝 إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            id_v = c1.text_input("الرقم (id)")
            name_v = c2.text_input("الاسم")
            cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([id_v, name_v, cls_v, "1446هـ", "اللغة الإنجليزية", "", "", 0])
                st.rerun()

# --- 4. واجهة الطالب (لمن يهمه الأمر) ---
elif st.session_state.role == "student":
    # (كود عرض النتائج والإعلانات للطالب...)
    pass
