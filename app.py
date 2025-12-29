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
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة الطالب (إعلانات مخصصة + تحديث بيانات) ---
if st.session_state.role == "student":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    student_data = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.title(f"مرحباً بك: {student_data['name']}")
    
    # 1. عرض الإعلانات المخصصة لصف الطالب فقط
    st.markdown(f"### 📢 تعاميم الصف: {student_data['class']}")
    try:
        ann_df = fetch_safe("announcements")
        # فلترة الإعلانات بناءً على صف الطالب
        my_ann = ann_df[ann_df['target_class'] == student_data['class']]
        if not my_ann.empty:
            for msg in my_ann['message']: st.info(msg)
        else: st.write("لا توجد إعلانات مخصصة لصفك حالياً.")
    except: st.info("لا توجد إعلانات.")

    st.divider()
    t1, t2, t3 = st.tabs(["📊 نتيجتي", "📝 تحديث بياناتي", "✍️ الاختبارات"])
    
    with t1:
        df_g = fetch_safe("grades")
        st.dataframe(df_g[df_g.iloc[:,0] == student_data['name']], use_container_width=True)
    
    with t2: # 2. إدخال الإيميل والجوال من شاشة الطالب
        st.subheader("📧 تحديث معلومات التواصل")
        with st.form("update_contact"):
            new_mail = st.text_input("البريد الإلكتروني الجديد", value=student_data.get('الإيميل', ''))
            new_phone = st.text_input("رقم الجوال الجديد", value=student_data.get('الجوال', ''))
            if st.form_submit_button("حفظ التغييرات"):
                ws_st = sh.worksheet("students")
                cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 7, new_mail) # تحديث عمود الإيميل
                ws_st.update_cell(cell.row, 8, new_phone) # تحديث عمود الجوال
                st.success("✅ تم تحديث بياناتك بنجاح"); time.sleep(1); st.rerun()

# --- 4. واجهة المعلم (نشر إعلانات مخصصة) ---
elif st.session_state.role == "teacher":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 نشر إعلان مخصص"])
    
    if menu == "📢 نشر إعلان مخصص":
        st.header("📢 نشر إعلان لصف محدد")
        with st.form("ann_form"):
            target_cls = st.selectbox("اختر الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            msg_text = st.text_area("نص الإعلان")
            if st.form_submit_button("نشر الإعلان"):
                try:
                    sh.worksheet("announcements").append_row([target_cls, msg_text, str(datetime.now())])
                    st.success(f"✅ تم إرسال الإعلان لطلاب الصف {target_cls}")
                except: st.error("تأكد من وجود ورقة باسم announcements")

    elif menu == "📊 الدرجات والسلوك":
        # (نفس كود رصد الدرجات والسلوك السابق)
        st.subheader("📝 رصد الدرجات والتحفيز")
        df_st = fetch_safe("students")
        sel_st = st.selectbox("الطالب", df_st['name'].tolist())
        # ... بقية الكود ...

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 قائمة الطلاب والبيانات")
        st.dataframe(fetch_safe("students"), use_container_width=True)
