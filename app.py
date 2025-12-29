import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

@st.cache_resource(ttl=300)
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
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with col_r:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة الطالب (الإعلانات والنتائج) ---
if st.session_state.role == "student":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    student_data = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"مرحباً بك: {student_data['name']}")
    
    # شاشة الإعلان (استعادة)
    st.markdown("### 📢 إعلان المعلم")
    try:
        ann_ws = sh.worksheet("announcements")
        ann_text = ann_ws.cell(1, 1).value
        st.info(ann_text if ann_text else "لا توجد إعلانات جديدة حالياً")
    except: st.info("لا توجد إعلانات جديدة")

    st.divider()
    t1, t2 = st.tabs(["📊 نتيجتي", "📝 الاختبارات"])
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:,0] == student_data['name']]
        st.dataframe(my_g, use_container_width=True, hide_index=True)
        st.metric("رصيد التميز ⭐", student_data['النقاط'] if 'النقاط' in student_data else 0)

# --- 4. واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 نشر إعلان"])
    
    if menu == "📢 نشر إعلان":
        st.header("📢 إدارة إعلانات الطلاب")
        current_ann = ""
        try:
            ann_ws = sh.worksheet("announcements")
            current_ann = ann_ws.cell(1, 1).value
        except: sh.add_worksheet(title="announcements", rows="10", cols="2")
        
        new_ann = st.text_area("اكتب الإعلان هنا ليظهر لجميع الطلاب", value=current_ann)
        if st.button("نشر الإعلان"):
            sh.worksheet("announcements").update('A1', [[new_ann]])
            st.success("تم النشر بنجاح ✅")

    elif menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        tab1, tab2 = st.tabs(["🎭 السلوك والفلترة", "📝 رصد الدرجات"])
        with tab2:
            st.subheader("📝 رصد الدرجات (بما فيها المشاركة)")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب", df_st['name'].tolist())
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1"); f2 = c2.number_input("ف2"); part = c3.number_input("المشاركة")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try: fnd = ws_g.find(target); ws_g.update(f'B{fnd.row}:D{fnd.row}', [[f1, f2, part]])
                    except: ws_g.append_row([target, f1, f2, part])
                    st.success("✅ تم التحديث"); st.rerun()
            st.dataframe(df_g, use_container_width=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True) # عرض الجدول بما فيه الإيميل
        
        st.divider()
        with st.form("add_full"):
            st.subheader("📝 إضافة طالب (البيانات كاملة)")
            c1, c2 = st.columns(2)
            id_v = c1.text_input("الرقم")
            name_v = c2.text_input("الاسم")
            
            c3, c4, c5, c6 = st.columns(4)
            cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            yr_v = c4.text_input("العام", value="1446هـ")
            lev_v = c5.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            sub_v = c6.text_input("المادة", value="اللغة الإنجليزية")
            
            # استعادة حقول الإيميل والجوال
            email_v = st.text_input("البريد الإلكتروني (الإيميل)")
            phone_v = st.text_input("رقم الجوال")
            
            if st.form_submit_button("إضافة الطالب"):
                sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, email_v, phone_v, 0])
                st.success("✅ تمت الإضافة"); st.rerun()
