import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. إعداد الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة جلب بيانات آمنة تتخطى أخطاء العناوين المكررة
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            # تنظيف الصفوف الفارغة (البحث عن أول عمود)
            df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# إدارة حالة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المزدوجة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col_t, col_s = st.columns(2)
    
    with col_t:
        st.markdown("### 🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور خاطئة")
            
    with col_s:
        st.markdown("### 👨‍🎓 منطقة الطالب")
        s_id = st.text_input("أدخل الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            # التحقق من وجود الرقم في العمود الأول
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id)
                st.rerun()
            else:
                st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إدارة + درجات + سلوك + اختبارات)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])
    
    # --- 1. إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.header("إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.form("add_student"):
                st.subheader("➕ إضافة طالب جديد")
                n_id = st.text_input("الرقم الأكاديمي")
                n_name = st.text_input("الاسم الثلاثي")
                n_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([n_id, n_name, n_class, "1447هـ", "1", "إنجليزي", "ابتدائي", "", "", 0])
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
        with c2:
            st.subheader("🗑️ حذف طالب")
            if not df_st.empty:
                target = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("تأكيد الحذف") and target:
                    ws = sh.worksheet("students"); cell = ws.find(target)
                    ws.delete_rows(cell.row); st.warning("تم الحذف"); st.rerun()

    # --- 2. رصد الدرجات ---
    elif menu == "📝 رصد الدرجات":
        st.header("رصد وتحديث الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_name:
                with st.form("grades_form"):
                    p1 = st.number_input("درجة الفترة 1", 0, 100)
                    p2 = st.number_input("درجة الفترة 2", 0, 100)
                    if st.form_submit_button("حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_name)
                            ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                        except:
                            ws_g.append_row([sel_name, p1, p2, 0])
                        st.success("تم الرصد"); time.sleep(1); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- 3. رصد السلوك ---
    elif menu == "🎭 رصد السلوك":
        st.header("سجل الملاحظات السلوكية")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_b:
                with st.form("behavior_form"):
                    b_type = st.selectbox("نوع السلوك", ["تميز", "مشاركة", "تنبيه", "غياب"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note])
                        st.success("تم الرصد"); st.rerun()
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    # --- 4. إعلان الاختبارات ---
    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 جدول الاختبارات")
        with st.form("exam_form"):
            ex_sub = st.text_input("المادة")
            ex_day = st.selectbox("اليوم", ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            ex_date = st.date_input("التاريخ")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_date), ex_day, ex_sub])
                st.success("تم النشر"); st.rerun()
        st.table(fetch_safe("exams"))

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    # جلب بيانات الطالب بناءً على الرقم الأكاديمي
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]

    st.title(f"👋 مرحباً بك: {s_name}")
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📢 الاختبارات", "🎭 سلوكي"])
    
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        st.table(my_g) if not my_g.empty else st.info("لا توجد درجات مرصودة")
        
    with t2:
        df_ex = fetch_safe("exams")
        st.table(df_ex) if not df_ex.empty else st.info("لا توجد اختبارات معلنة")
        
    with tab3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_name]
        st.table(my_b) if not my_b.empty else st.info("السجل نظيف")
