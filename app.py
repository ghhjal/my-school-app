import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# ==========================================
# 1. إعدادات الصفحة وتهيئة الجلسة
# ==========================================
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="centered")

if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# ==========================================
# 2. دالة الاتصال المحسنة (تعالج أنواع البيانات)
# ==========================================
def fetch_safe(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit") 
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        # تحويل العمود الأول دائماً إلى نص لمنع مشاكل المطابقة
        if not df.empty:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df, sh
    except Exception as e:
        return pd.DataFrame(), None

# جلب البيانات الأساسية
df_st, sh = fetch_safe("students")

# ==========================================
# 🏠 3. الصفحة الرئيسية (التحكم في الدخول)
# ==========================================
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 15px; text-align: center; border-radius: 15px; margin-bottom: 20px; color: white;">
            <h2 style="font-family: 'Cairo', sans-serif; font-size: 1.8rem; margin: 0;">🌟 منصة الأستاذ زياد العمري</h2>
            <p style="font-size: 1rem; opacity: 0.9; margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    # إحصائيات سريعة
    total_students = len(df_st) if not df_st.empty else 0
    st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
            <div style="flex: 1; background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #1e3a8a;">{total_students}</div>
                <div style="color: #64748b; font-size: 0.7rem;">طالباً مسجلاً</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<h4 style='text-align: center; color: #1e3a8a;'>🔐 تسجيل الدخول</h4>", unsafe_allow_html=True)
        login_type = st.radio("نوع الدخول:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", placeholder="مثال: 1001").strip()
        
        if st.button("🚀 دخول للمنصة", use_container_width=True, type="primary"):
            if login_type == "معلم":
                if user_id == "1234":
                    st.session_state.role = "teacher"
                    st.rerun()
                else:
                    st.error("❌ كود المعلم غير صحيح")
            else:
                # التحقق من وجود الكود في قائمة الطلاب
                if not df_st.empty and user_id in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"
                    st.session_state.sid = user_id
                    st.success("✅ جاري التحميل...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ الكود غير مسجل أو الجدول فارغ")

# ==========================================
# 👨‍🏫 4. واجهة المعلم
# ==========================================
elif st.session_state.role == "teacher":
    st.sidebar.markdown(f"### 👨‍🏫 أهلاً أ. زياد")
    menu = st.sidebar.selectbox("الانتقال إلى:", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    
    if st.sidebar.button("🚗 تسجيل خروج"):
        st.session_state.role = None
        st.rerun()

    if menu == "👥 إدارة الطلاب":
        st.title("👥 إدارة الطلاب")
        df_now, _ = fetch_safe("students")
        st.dataframe(df_now, use_container_width=True)
        
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الكود (ID)")
            nname = c2.text_input("الاسم")
            nclass = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("إضافة"):
                sh.worksheet("students").append_row([nid, nname, nclass, "1447", "نشط", "English", "Primary", "", "", "0"])
                st.success("تم الحفظ"); st.rerun()

    elif menu == "📝 رصد الدرجات":
        st.title("📝 رصد الدرجات")
        df_st, _ = fetch_safe("students")
        student_name = st.selectbox("اختر الطالب:", [""] + df_st.iloc[:, 1].tolist())
        if student_name:
            with st.form("grades_form"):
                p1 = st.number_input("الفترة الأولى", 0, 100)
                p2 = st.number_input("الفترة الثانية", 0, 100)
                part = st.number_input("المشاركة", 0, 100)
                if st.form_submit_button("حفظ الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(student_name)
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except:
                        ws_g.append_row([student_name, p1, p2, part])
                    st.success("تم تحديث الدرجات")

    # بقية أقسام المعلم (السلوك والاختبارات) تبقى كما هي في كودك السابق...

# ==========================================
# 👨‍🎓 5. واجهة الطالب (تم إصلاحها بالكامل)
# ==========================================
elif st.session_state.role == "student":
    # إعادة جلب البيانات لضمان الحداثة
    df_st, _ = fetch_safe("students")
    df_grades, _ = fetch_safe("grades")
    
    # تحديد سطر الطالب بناءً على الـ ID
    student_data = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
    s_name = student_data.iloc[1]
    s_class = student_data.iloc[2]
    
    # جلب النقاط
    try: s_points = int(student_data.iloc[8])
    except: s_points = 0

    st.markdown(f"""<div style="background:#1e3a8a; padding:15px; border-radius:10px; color:white; text-align:center;">
        <h3>🎓 مرحباً بك: {s_name}</h3>
        <p>الصف: {s_class}</p>
    </div>""", unsafe_allow_html=True)

    # تبويبات الطالب
    t1, t2, t3 = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📢 تنبيهات"])

    with t1:
        # البحث عن درجات الطالب بالاسم في ورقة grades
        g_data = df_grades[df_grades.iloc[:, 0] == s_name]
        if not g_data.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", g_data.iloc[0, 1])
            c2.metric("الفترة 2", g_data.iloc[0, 2])
            c3.metric("المشاركة", g_data.iloc[0, 3])
        else:
            st.info("لم ترصد درجاتك بعد.")

    with t2:
        df_beh, _ = fetch_safe("behavior")
        st.subheader("سجل السلوك")
        my_beh = df_beh[df_beh.iloc[:, 0] == s_name]
        if not my_beh.empty:
            for _, r in my_beh.iloc[::-1].iterrows():
                st.warning(f"{r.iloc[2]}: {r.iloc[3]} ({r.iloc[1]})")
        else:
            st.success("سجلك السلوكي نظيف وجميل! ✨")

    if st.button("🚗 تسجيل خروج"):
        st.session_state.role = None
        st.rerun()
