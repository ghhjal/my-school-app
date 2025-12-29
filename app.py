import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
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

# --- 2. إدارة نظام الدخول (Login System) ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
                
    with col_r:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(sid)
                st.rerun()
            else: st.error("عفواً، الرقم غير مسجل")
    st.stop()

# --- 3. واجهة الطالب (إعلانات + اختبارات + نتائج) ---
if st.session_state.role == "student":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة", ["📢 الإعلانات", "📝 الاختبارات", "📊 نتيجتي"])
    
    df_st = fetch_safe("students")
    student_data = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.title(f"مرحباً بك: {student_data['name']}")

    if menu == "📢 الإعلانات":
        st.info("📢 إعلان هام: بدأ رصد درجات الفصل الدراسي الحالي، يرجى الاجتهاد!")
        
    elif menu == "📝 الاختبارات":
        st.warning("🚀 لا توجد اختبارات متاحة حالياً. سيتم إشعارك فور تفعيلها.")

    elif menu == "📊 نتيجتي":
        # عرض الدرجات والسلوك للطالب
        df_g = fetch_safe("grades")
        my_grade = df_g[df_g.iloc[:,0] == student_data['name']]
        st.subheader("📈 تقرير درجاتك")
        st.dataframe(my_grade, use_container_width=True, hide_index=True)
        st.metric("رصيد نقاط التميز ⭐", student_data['النقاط'] if 'النقاط' in student_data else 0)

# --- 4. واجهة المعلم (كل الشاشات) ---
elif st.session_state.role == "teacher":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        tab1, tab2 = st.tabs(["🎭 السلوك والفلترة", "📝 رصد الدرجات"])
        
        with tab1: # شاشة السلوك مع الفلترة
            with st.form("b_form"):
                sel_st = st.selectbox("اختر الطالب", df_st['name'].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                if st.form_submit_button("حفظ"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, ""])
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old = int(ws_st.cell(c.row, 9).value or 0); ws_st.update_cell(c.row, 9, old + pts)
                    st.success("تم الحفظ"); st.rerun()
            
            st.divider()
            st.subheader(f"📋 سجل سلوك: {sel_st}")
            df_b = fetch_safe("behavior")
            st.dataframe(df_b[df_b.iloc[:,0] == sel_st], use_container_width=True)

        with tab2: # شاشة الدرجات مع الجدول السفلي
            df_g = fetch_safe("grades")
            target = st.selectbox("اختر الطالب لتعديل درجته", df_st['name'].tolist())
            with st.form("g_form"):
                f1 = st.number_input("ف1"); f2 = st.number_input("ف2")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try: fnd = ws_g.find(target); ws_g.update(f'B{fnd.row}:C{fnd.row}', [[f1, f2]])
                    except: ws_g.append_row([target, f1, f2])
                    st.success("تم التحديث"); st.rerun()
            st.divider()
            st.subheader("📋 كشف الدرجات العام")
            st.dataframe(df_g, use_container_width=True)

    elif menu == "👥 إدارة الطلاب": # شاشة الإدارة بكافة الحقول
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        st.divider()
        c_del, c_add = st.columns([1, 2])
        with c_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("الطالب للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                for s in ["students", "grades", "behavior"]:
                    try: ws = sh.worksheet(s); ws.delete_rows(ws.find(to_del).row)
                    except: pass
                st.success("تم الحذف"); st.rerun()
        with c_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_st"):
                id_v = st.text_input("الرقم")
                name_v = st.text_input("الاسم")
                col_a, col_b, col_c = st.columns(3)
                cls_v = col_a.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = col_b.text_input("العام", value="1446هـ")
                lev_v = col_c.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, "اللغة الإنجليزية", lev_v, "", "", 0])
                    st.success("تمت الإضافة"); st.rerun()
