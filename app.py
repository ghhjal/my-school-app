import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- 1. الاتصال المباشر (تأكد من صحة المفتاح) ---
st.set_page_config(page_title="منصة الأستاذ زياد - نسخة مستقرة", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"فشل الاتصال: {e}")
        return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        if st.text_input("Password", type="password") == "1234":
            if st.button("دخول المعلم"): st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- 3. واجهة الطالب (تحديث البيانات + النتائج) ---
if st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    # البحث عن بيانات الطالب بناءً على الـ id
    student_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"مرحباً: {student_data['name']}")
    
    # قسم تحديث البيانات (الإيميل والجوال)
    with st.expander("📧 تحديث بيانات التواصل الخاصة بك"):
        with st.form("up_form"):
            new_mail = st.text_input("بريدك الإلكتروني", value=str(student_data.get('الإيميل', '')))
            new_phone = st.text_input("رقم الجوال", value=str(student_data.get('الجوال', '')))
            if st.form_submit_button("حفظ التغييرات"):
                ws_st = sh.worksheet("students")
                cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 6, new_mail) # عمود الإيميل F
                ws_st.update_cell(cell.row, 7, new_phone) # عمود الجوال G
                st.success("تم التحديث ✅"); st.rerun()

    # عرض الدرجات (p1, p2, perf)
    st.subheader("📊 نتائج الاختبارات")
    df_g = fetch_data("grades")
    my_grades = df_g[df_g['student_id'] == student_data['name']]
    st.dataframe(my_grades, use_container_width=True, hide_index=True)

# --- 4. واجهة المعلم (رصد وإدارة) ---
elif st.session_state.role == "teacher":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📝 رصد الدرجات", "👥 إدارة الطلاب", "📢 الإعلانات"])

    if menu == "📝 رصد الدرجات":
        st.subheader("تحديث درجات p1, p2, perf")
        df_st = fetch_data("students")
        target = st.selectbox("اختر الطالب", df_st['name'].tolist())
        with st.form("g_form"):
            c1, c2, c3 = st.columns(3)
            p1 = c1.number_input("درجة p1")
            p2 = c2.number_input("درجة p2")
            perf = c3.number_input("المشاركة (perf)")
            if st.form_submit_button("تحديث"):
                ws_g = sh.worksheet("grades")
                try:
                    fnd = ws_g.find(target)
                    ws_g.update(f'B{fnd.row}:D{fnd.row}', [[p1, p2, perf]])
                except:
                    ws_g.append_row([target, p1, p2, perf])
                st.success("تم التحديث ✅")

    elif menu == "👥 إدارة الطلاب":
        st.subheader("بيانات الطلاب الحالية")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True)
        
        # إضافة طالب جديد بالحقول المطلوبة
        with st.form("add_st"):
            st.write("📝 إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            id_v = c1.text_input("الرقم (id)")
            name_v = c2.text_input("الاسم")
            cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
            
            c4, c5 = st.columns(2)
            yr_v = c4.text_input("العام", value="1446هـ")
            sem_v = c5.text_input("المادة (sem)", value="اللغة الإنجليزية")
            
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sem_v, "", "", 0])
                st.success("تمت الإضافة ✅"); st.rerun()
