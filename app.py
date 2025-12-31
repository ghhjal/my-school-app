import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse  # تم نقلها للأعلى لضمان السرعة

# --- 1. الإعدادات الأساسية وتنسيق الجوال (CSS) ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stButton>button {
        width: 100%;
        height: 60px;
        border-radius: 15px;
        font-size: 18px !important;
        font-weight: bold;
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    .stTextInput>div>div>input {
        height: 55px;
        border-radius: 12px;
        text-align: center;
        font-size: 20px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. دالة الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=300) # تحديث كل 5 دقائق لضمان السرعة مع 400 طالب
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 35px 20px; border-radius: 20px; text-align: center; color: white; margin-bottom: 25px;">
            <h1 style="font-size: 1.8rem; margin: 0;">🌟 منصة الأستاذ زياد العمري</h1>
            <p style="opacity: 0.9; margin-top: 10px;">نحو تميز إبداعي في اللغة الإنجليزية</p>
        </div>
    """, unsafe_allow_html=True)

    tab_st, tab_tea = st.tabs(["🎓 دخول الطالب", "👨‍🏫 منطقة المعلم"])

    with tab_st:
        st.markdown("<br>", unsafe_allow_html=True)
        sid_in = st.text_input("أدخل الرقم الأكاديمي", placeholder="مثال: 1001", key="st_login_id")
        if st.button("🚀 دخول الطالب", type="primary"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(sid_in)
                st.success("تم الدخول بنجاح")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("عذراً، الرقم غير مسجل")

    with tab_tea:
        st.markdown("<br>", unsafe_allow_html=True)
        t_pwd = st.text_input("كلمة مرور المعلم", type="password", placeholder="****", key="tea_login_pwd")
        if st.button("🔓 دخول المعلم"):
            if t_pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    if st.sidebar.button("🚗 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()

    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        with st.container(border=True):
            st.subheader("📋 السجل الحالي")
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        with st.form("add_student_pro", clear_on_submit=True):
            st.markdown("### ➕ تأسيس طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nyear = c5.text_input("🗓️ العام", value="1447هـ")
            nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
            if st.form_submit_button("✅ اعتماد التأسيس"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"])
                    st.success("تم التأسيس بنجاح"); st.rerun()

    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("grade_pro_form"):
                st.markdown(f"**تحديث درجات الطالب: {target}**")
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("📉 الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                if st.form_submit_button("💾 حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except:
                        ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ"); st.rerun()
        st.divider()
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        df_st = fetch_safe("students")
        search = st.text_input("🔍 ابحث عن الاسم")
        filtered = [n for n in df_st.iloc[:,1].tolist() if search in n]
        b_name = st.selectbox("🎯 الطالب:", [""] + filtered)
        
        if b_name:
            s_info = df_st[df_st.iloc[:,1] == b_name].iloc[0]
            s_phone = str(s_info[7]).split('.')[0]
            with st.form("beh_form"):
                b_type = st.selectbox("النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_note = st.text_area("الملاحظة")
                btn_wa = st.form_submit_button("💬 حفظ وإرسال واتساب")
                
                if btn_wa and b_note:
                    sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note])
                    # التنسيق الذي طلبته للواتساب
                    wa_msg = (
                        f"📢 *تنبيه من منصة الأستاذ زياد الذكية*\n"
                        f"----------------------------------\n"
                        f"🏫 *الطالب:* {b_name}\n"
                        f"📝 *السلوك:* {b_type}\n"
                        f"💬 *الملاحظة:* {b_note}\n"
                        f"📅 *التاريخ:* {datetime.now().date()}\n"
                        f"----------------------------------\n"
                        f"يرجى العلم والمتابعة. مع تمنياتي لكم بالتوفيق 🌟"
                    )
                    wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(wa_msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank">✅ اضغط هنا لإرسال الرسالة</a>', unsafe_allow_html=True)
                    st.success("تم الحفظ")

            st.divider()
            st.subheader("📋 سجل سلوك الطالب")
            df_beh = fetch_safe("behavior")
            if not df_beh.empty:
                st.dataframe(df_beh[df_beh.iloc[:,0] == b_name].iloc[::-1], use_container_width=True, hide_index=True)

    elif menu == "📢 شاشة الاختبارات":
        st.markdown('<div style="background:linear-gradient(90deg, #4F46E5 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;"><h1>📢 شاشة الاختبارات</h1></div>', unsafe_allow_html=True)
        with st.form("exam_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            e_class = c1.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = c2.text_input("العنوان")
            e_date = c3.date_input("الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (نفس هيكلك الأصلي تماماً)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name, s_class = s_row[1], s_row[2]
    
    # حساب النقاط والأوسمة
    try: s_points = int(s_row[8]) if s_row[8] else 0
    except: s_points = 0

    st.markdown(f"""<div style="background:#1e3a8a; padding:15px; color:white; text-align:center; border-radius:10px;"><h3>🎯 الطالب: {s_name} | النقاط: {s_points}</h3></div>""", unsafe_allow_html=True)
    
    t_ex, t_grade, t_beh, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "⚙️ الإعدادات"])
    
    with t_ex:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.info(f"📢 {r[1]} - 📅 {r[2]}")

    with t_grade:
        try:
            g_row = df_grades[df_grades.iloc[:, 0] == s_name].iloc[0]
            st.metric("المشاركة (p1)", g_row[1])
            st.metric("الواجبات (p2)", g_row[2])
            st.metric("الاختبارات (perf)", g_row[3])
        except: st.warning("لا توجد درجات مرصودة")

    with t_beh:
        df_beh = fetch_safe("behavior")
        if not df_beh.empty:
            st.dataframe(df_beh[df_beh.iloc[:, 0] == s_name].iloc[::-1], use_container_width=True, hide_index=True)

    with t_set:
        with st.form("st_settings"):
            new_mail = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            new_phone = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ البيانات"):
                ws = sh.worksheet("students")
                cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, new_mail)
                ws.update_cell(cell.row, 8, new_phone)
                st.success("تم التحديث بنجاح")

    if st.button("🚗 تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
