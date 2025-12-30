import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. إعداد الصفحة والاتصال الآمن ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=2)
def get_db():
    try:
        # استخدام ملف الاعتماد من Secrets
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة جلب البيانات مع تنظيف الصفوف الفارغة لتجنب أخطاء العناوين المكررة
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            # نأخذ العناوين من الصف الأول والبيانات من الباقي
            df = pd.DataFrame(data[1:], columns=data[0])
            # حذف أي صفوف فارغة تماماً قد توجد في نهاية الجدول
            df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. إدارة حالة الدخول والجلسة ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول الرئيسية
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    col_t, col_s = st.columns(2)
    
    with col_t:
        st.markdown("### 🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة مرور المعلم", type="password", key="t_pwd")
        if st.button("دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
            
    with col_s:
        st.markdown("### 👨‍🎓 منطقة الطالب")
        s_id_input = st.text_input("أدخل الرقم الأكاديمي", key="s_id_input")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            # التحقق من الرقم الأكاديمي في العمود الأول (ID)
            if not df_st.empty and str(s_id_input) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id_input)
                st.rerun()
            else:
                st.error("⚠️ الرقم الأكاديمي غير مسجل حالياً")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إدارة كاملة للمنصة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])
    
    # --- 1. إدارة الطلاب ---
    if menu == "👥 إدارة الطلاب":
        st.header("إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.form("add_student_form"):
                st.subheader("➕ إضافة طالب")
                new_id = st.text_input("الرقم الأكاديمي")
                new_name = st.text_input("الاسم الثلاثي")
                new_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                if st.form_submit_button("حفظ"):
                    if new_id and new_name:
                        sh.worksheet("students").append_row([new_id, new_name, new_class, "1447هـ", "1", "إنجليزي", "ابتدائي", "", "", 0])
                        st.success("✅ تم الحفظ"); time.sleep(0.5); st.rerun()
        with c2:
            st.subheader("🗑️ حذف طالب")
            if not df_st.empty:
                del_target = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("❌ حذف نهائي") and del_target:
                    ws = sh.worksheet("students")
                    cell = ws.find(del_target)
                    ws.delete_rows(cell.row)
                    st.warning("تم الحذف"); st.rerun()

    # --- 2. رصد الدرجات ---
    elif menu == "📝 رصد الدرجات":
        st.header("رصد وتحديث درجات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_student = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            if sel_student:
                with st.form("grades_form"):
                    p1 = st.number_input("درجة الفترة 1", 0, 100)
                    p2 = st.number_input("درجة الفترة 2", 0, 100)
                    pf = st.number_input("درجة المشاركة", 0, 100)
                    if st.form_submit_button("💾 حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_student)
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                        except:
                            ws_g.append_row([sel_student, p1, p2, pf])
                        st.success("✅ تمت العملية"); time.sleep(0.5); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- 3. إعلان الاختبارات (المطلوبة) ---
    elif menu == "📢 إعلان الاختبارات":
        st.header("إدارة إعلانات الاختبارات")
        with st.form("exams_form"):
            ex_subject = st.text_input("المادة")
            ex_date = st.date_input("التاريخ")
            ex_day = st.selectbox("اليوم", ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            if st.form_submit_button("📢 نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_date), ex_day, ex_subject])
                st.success("✅ تم النشر"); time.sleep(0.5); st.rerun()
        st.subheader("الجدول الحالي")
        st.table(fetch_safe("exams"))

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    # البحث عن بيانات الطالب بالرقم الأكاديمي
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 جدول الاختبارات", "🎭 سجل السلوك"])
    
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        if not my_g.empty: st.table(my_g)
        else: st.info("لم يتم رصد درجاتك بعد")
        
    with t2:
        df_ex = fetch_safe("exams")
        if not df_ex.empty: st.table(df_ex)
        else: st.info("لا توجد اختبارات معلنة حالياً")
        
    with t3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_name]
        if not my_b.empty: st.table(my_b)
        else: st.success("سجلك السلوكي نظيف ومتميز! استمر")
