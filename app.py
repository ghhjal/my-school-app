import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# ==========================================
# 1. إعدادات الصفحة والتنسيق الاحترافي (CSS)
# ==========================================
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

# تصميم مخصص لجعل الواجهة متجاوبة مع الجوال
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    /* تنسيق الحاويات على الجوال */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8fafc;
        border-radius: 10px 10px 0 0;
        padding: 5px 15px;
    }

    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        transition: all 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. تهيئة حالة الجلسة والاتصال
# ==========================================
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

def fetch_safe(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # استخدام البيانات من Secrets في Streamlit
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # استبدل الرابط برابط ملفك الفعلي
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit")
        worksheet = sh.worksheet(sheet_name)
        return pd.DataFrame(worksheet.get_all_records()), sh
    except Exception as e:
        # st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame(), None

# ==========================================
# 🏠 3. الصفحة الرئيسية وتسجيل الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 15px; text-align: center; border-radius: 15px; margin-bottom: 20px; color: white;">
            <h2 style="margin: 0;">🌟 منصة الأستاذ زياد العمري</h2>
            <p style="font-size: 1rem; opacity: 0.9; margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    df_st, _ = fetch_safe("students")
    
    with st.container():
        st.markdown("<h4 style='text-align: center; color: #1e3a8a;'>🔐 تسجيل الدخول</h4>", unsafe_allow_html=True)
        login_type = st.radio("الدخول كـ:", ["طالب", "معلم"], horizontal=True)
        user_id = st.text_input("أدخل الكود الخاص بك (ID)", placeholder="مثال: 1001")
        
        if st.button("🚀 دخول للمنصة", type="primary"):
            if login_type == "معلم":
                if user_id == "1234": # كود المعلم
                    st.session_state.role = "teacher"
                    st.rerun()
                else:
                    st.error("كود المعلم غير صحيح")
            else:
                if not df_st.empty and str(user_id) in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(user_id)
                    st.rerun()
                else:
                    st.error("الكود غير مسجل")

# ==========================================
# 👨‍🏫 4. واجهة المعلم (إدارة شاملة)
# ==========================================
elif st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة تحكم المعلم")
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    
    if st.sidebar.button("🚗 خروج"):
        st.session_state.role = None
        st.rerun()

    df_st, sh = fetch_safe("students")

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        with st.form("add_student"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nclass = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("✅ إضافة الطالب"):
                sh.worksheet("students").append_row([nid, nname, nclass, "1447هـ", "نشط", "English", "ابتدائي", "", "", "0"])
                st.success("تمت الإضافة بنجاح"); st.rerun()
        st.dataframe(df_st, use_container_width=True)

    elif menu == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات")
        target = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g, _ = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            with st.form("grades_form"):
                p1 = st.number_input("الفترة الأولى", 0, 100, value=v1)
                p2 = st.number_input("الفترة الثانية", 0, 100)
                if st.form_submit_button("💾 حفظ"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, 0]])
                    except:
                        ws.append_row([target, p1, p2, 0])
                    st.success("تم الحفظ")

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والتواصل")
        b_name = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if b_name:
            with st.form("behavior_form"):
                b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("💾 حفظ وإرسال"):
                    sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note])
                    st.success("تم الرصد")

# ==========================================
# 👨‍🎓 5. واجهة الطالب (تجربة جوال احترافية)
# ==========================================
elif st.session_state.role == "student":
    df_st, _ = fetch_safe("students")
    df_grades, _ = fetch_safe("grades")
    
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row[1]
    s_class = s_row[2]
    try: s_points = int(s_row[8])
    except: s_points = 0

    # هيدر الطالب
    st.markdown(f"""
        <div style="background: #1e3a8a; padding: 15px; margin: -1rem; border-bottom: 5px solid #f59e0b; text-align: center; color: white;">
            <h3 style="margin: 0;">🎓 الطالب: {s_name}</h3>
            <small>الصف: {s_class}</small>
        </div>
        <div style="margin-top: 20px; background: white; border-radius: 15px; padding: 20px; border: 1px solid #e2e8f0; text-align: center;">
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 10px; border-radius: 10px;">
                <small>رصيد النقاط</small><br><b style="font-size: 2rem;">{s_points}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # التبويبات المتجاوبة
    t_ex, t_grade, t_beh = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي"])

    with t_ex:
        df_ex, _ = fetch_safe("exams")
        if not df_ex.empty:
            for _, r in df_ex.iloc[::-1].iterrows():
                st.info(f"📢 {r[1]} \n\n 📅 الموعد: {r[2]}")

    with t_grade:
        try:
            g_row = df_grades[df_grades.iloc[:, 0] == s_name].iloc[0]
            st.metric("الفترة الأولى", g_row[1])
            st.metric("الفترة الثانية", g_row[2])
        except:
            st.warning("لم ترصد درجات بعد")

    with t_beh:
        df_b, _ = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for _, r in my_b.iloc[::-1].iterrows():
                color = "green" if "+" in str(r[2]) else "red"
                st.markdown(f"""<div style="border-right: 5px solid {color}; background: #f8fafc; padding: 10px; margin-bottom: 5px;">
                    <b>{r[2]}</b><br><small>{r[1]}</small><br>{r[3]}</div>""", unsafe_allow_html=True)

    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
