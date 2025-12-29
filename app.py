import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والربط (English_Grades) ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except: return pd.DataFrame()

# --- 2. نظام الدخول (المعلم والطالب) ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم الأكاديمي غير صحيح")
    st.stop()

# --- 3. واجهة المعلم (إدارة شاملة) ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    # القائمة الجانبية كما في الصورة
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "📢 إعلانات الاختبارات":
        st.header("📢 إضافة تنبيه اختبار جديد")
        with st.form("exam_form"):
            t_cls = st.selectbox("حدد الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            t_title = st.text_input("عنوان الاختبار (مثلاً: اختبار الفترة الأولى)")
            t_date = st.date_input("موعد الاختبار", value=datetime.now())
            if st.form_submit_button("إرسال التنبيه للطلاب 🚀"):
                sh.worksheet("exams").append_row([t_cls, t_title, str(t_date)])
                st.success("تم إرسال التنبيه بنجاح ✅")
        
        st.divider()
        st.subheader("📋 الاختبارات المعلنة حالياً")
        df_ex = fetch_data("exams")
        st.dataframe(df_ex, use_container_width=True, hide_index=True)

    elif menu == "📊 الدرجات والسلوك":
        tab_g, tab_b = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        with tab_g:
            st.subheader("تحديث درجات الطالب (p1, p2, perf)")
            df_st = fetch_data("students")
            target = st.selectbox("اختر الطالب لتعديل درجته", df_st['name'].tolist())
            with st.form("g_update"):
                c1, c2, c3 = st.columns(3)
                v1 = c1.number_input("ف1 (p1)")
                v2 = c2.number_input("ف2 (p2)")
                v3 = c3.number_input("مشاركة (perf)")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        fnd = ws_g.find(target)
                        ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                    except: ws_g.append_row([target, v1, v2, v3])
                    st.success("تم تحديث الدرجات ✅")
            st.divider()
            st.subheader("📋 كشف الدرجات العام")
            st.dataframe(fetch_data("grades"), use_container_width=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True)
        
        c_del, c_add = st.columns([1, 2])
        with c_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                for s in ["students", "grades", "behavior"]:
                    try: ws = sh.worksheet(s); ws.delete_rows(ws.find(to_del).row)
                    except: pass
                st.error("تم حذف الطالب نهائياً"); st.rerun()
        with c_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_st"):
                id_v = st.text_input("الرقم (id)")
                name_v = st.text_input("الاسم")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
                sub_v = st.text_input("المادة (sem)", value="اللغة الإنجليزية")
                if st.form_submit_button("إضافة الطالب"):
                    # id, name, class, year, sem, الإيميل, الجوال, النقاط
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, "1446هـ", sub_v, "", "", 0])
                    st.success("تمت الإضافة ✅"); st.rerun()

# --- 4. واجهة الطالب (تحديث الإيميل + النتائج) ---
elif st.session_state.role == "student":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"مرحباً بك: {s_data['name']}")
    
    # 📢 عرض تنبيهات الاختبارات الخاصة بصف الطالب
    df_ex = fetch_data("exams")
    my_exams = df_ex[df_ex['الصف'] == s_data['class']]
    if not my_exams.empty:
        for index, row in my_exams.iterrows():
            st.warning(f"📢 اختبار جديد: {row['العنوان']} - الموعد: {row['التاريخ']}")

    t1, t2 = st.tabs(["📊 نتيجتي", "📧 تحديث بياناتي"])
    with t1:
        df_g = fetch_data("grades")
        st.table(df_g[df_g['student_id'] == s_data['name']])
        st.metric("نقاطي ⭐", s_data['النقاط'])
    
    with t2:
        st.subheader("تحديث البريد الإلكتروني والجوال")
        with st.form("st_up"):
            mail = st.text_input("الإيميل", value=s_data['الإيميل'])
            phone = st.text_input("الجوال", value=s_data['الجوال'])
            if st.form_submit_button("حفظ"):
                ws_st = sh.worksheet("students"); cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 6, mail) # عمود الإيميل F
                ws_st.update_cell(cell.row, 7, phone) # عمود الجوال G
                st.success("تم التحديث ✅"); st.rerun()
