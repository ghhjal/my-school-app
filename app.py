import streamlit as st
import gspread
import pandas as pd
import hashlib
import datetime
import urllib.parse
import io
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام والاستقرار الأساسية
# ==========================================
# يجب أن يكون أول أمر في السكريبت
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# الاتصال بـ Google Sheets عبر نظام Secrets
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception:
        st.error("⚠️ فشل الاتصال. تحقق من إعدادات Secrets.")
        return None

sh = get_gspread_client()

# تهيئة الذاكرة المؤقتة (Session State) لضمان استقرار التنقل
if "role" not in st.session_state: st.session_state.role = None
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

# تحميل الإعدادات الدائمة فور تشغيل المنصة
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40

# ==========================================
# 🧠 2. دوال البيانات الاحترافية
# ==========================================
@st.cache_data(ttl=30)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # تحويل المعرف (ID) لنص لضمان البحث الدقيق
        if not df.empty: df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def get_col_idx(df, col_name):
    try: return df.columns.get_loc(col_name) + 1
    except: return None

# ==========================================
# 🎨 3. التصميم البصري الاحترافي (CSS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin: -80px -20px 25px -20px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .stMetric { background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    </style>
    <div class="header-section">
        <h1>🏛️ منصة زياد الذكية</h1>
        <p>نظام الإدارة الشامل - إصدار 2026 المستقر</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 4. نظام الدخول والحماية
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    with t1:
        with st.form("st_login"):
            sid_in = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول الطلاب"):
                df_s = fetch_safe("students")
                if not df_s.empty and sid_in in df_s.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid_in; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل.")
    with t2:
        with st.form("admin_login"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    u_data = df_u[df_u['username']==u.strip()].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == u_data['password_hash']:
                        st.session_state.role = "teacher"; st.session_state.username = u.strip(); st.rerun()
                st.error("بيانات الدخول غير صحيحة.")
    st.stop()

# ==========================================
# 👨‍🏫 5. واجهة المعلم (الضبط الإداري المكتمل)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التواصل", "⚙️ الإعدادات", "🚗 خروج"])

    with menu[0]: # تبويب الطلاب: إحصائيات + بحث ذكي
        st.subheader("👥 إدارة قاعدة الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            c2.metric("🏫 الصفوف", len(df_st.iloc[:, 4].unique()) if len(df_st.columns) > 4 else 1)
            c3.metric("⭐ متوسط النقاط", round(pd.to_numeric(df_st['النقاط'], errors='coerce').mean(), 1))
            st.divider()
            q = st.text_input("🔍 ابحث عن طالب (الاسم أو الرقم):")
            df_disp = df_st[df_st.iloc[:, 0].str.contains(q) | df_st.iloc[:, 1].str.contains(q)] if q else df_st
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

    with menu[1]: # تبويب التقييم: رصد الدرجات مع صمام أمان
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_list = {f"{row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected = st.selectbox("🎯 اختر الطالب:", [""] + list(st_list.keys()))
            if selected:
                sid = st_list[selected]
                c_grades, c_beh = st.columns(2)
                with c_grades:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_form"):
                        v_t = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0)
                        v_q = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0)
                        if st.form_submit_button("💾 حفظ"):
                            if v_t <= st.session_state.max_tasks and v_q <= st.session_state.max_quiz:
                                sh.worksheet("grades").append_row([sid, v_t, v_q, v_t+v_q, str(datetime.date.today())])
                                st.success("✅ تم الحفظ بنجاح"); st.cache_data.clear()
                            else: st.error("تنبيه: الدرجة تتجاوز الحد المسموح به.")
                with c_beh: # سجل السلوك والواتساب
                    st.markdown("##### 🎭 سجل السلوك")
                    with st.form("beh_form", clear_on_submit=True):
                        b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "🚫 سلبي (-10)"])
                        b_desc = st.text_input("ملاحظات")
                        if st.form_submit_button("💾 حفظ"):
                            sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, b_desc])
                            st.success("تم الحفظ وتحديث النقاط"); st.cache_data.clear()

    with menu[3]: # تبويب الإعدادات: الحفظ الدائم + الرفع
        st.subheader("⚙️ أدوات التحكم المتقدمة")
        with st.expander("⚖️ تعديل توزيع الدرجات (حفظ دائم)", expanded=True):
            col1, col2 = st.columns(2)
            nt = col1.number_input("الحد الأقصى للمشاركة", 1, 100, st.session_state.max_tasks)
            nq = col2.number_input("الحد الأقصى للاختبار", 1, 100, st.session_state.max_quiz)
            if st.button("💾 اعتماد وحفظ نهائي"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, nt); ws_s.update_cell(3, 2, nq)
                st.session_state.max_tasks, st.session_state.max_quiz = nt, nq
                st.success("✅ تم الحفظ في قاعدة البيانات"); st.rerun()

        with st.expander("📤 رفع البيانات من Excel"):
            up_f = st.file_uploader("اختر ملف (طلاب أو درجات)", type=["xlsx"])
            if up_f and st.button("🚀 بدء الرفع"):
                df_up = pd.read_excel(up_f).fillna("")
                sh.worksheet("students").append_rows(df_up.values.tolist())
                st.success("✅ تمت العملية بنجاح"); st.cache_data.clear()

    with menu[4]:
        if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 6. واجهة الطالب (الترتيب والنقاط المكتملة)
# ==========================================
if st.session_state.role == "student":
    df_s = fetch_safe("students"); df_g = fetch_safe("grades")
    df_ex = fetch_safe("exams"); s_id = st.session_state.sid
    
    # جلب بيانات الطالب بدقة لضمان عرض النقاط الصحيحة
    s_row = df_s[df_s.iloc[:, 0] == s_id].iloc[0]
    s_name = s_row.iloc[1]; s_points = s_row['النقاط']
    
    st.markdown(f"""<div style='background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 20px; color: white; text-align: center;'>
        <h2>🎯 مرحباً: {s_name}</h2><div>🏆 نقاط تفاعلك الحالية: {s_points}</div></div>""", unsafe_allow_html=True)

    t_ex, t_grade, t_beh = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سجل السلوك"])

    with t_grade: # الترتيب الأكاديمي اللحظي
        my_g = df_g[df_g.iloc[:, 0] == s_id]
        if not my_g.empty:
            df_rank = df_g.copy(); df_rank.iloc[:, 3] = pd.to_numeric(df_rank.iloc[:, 3], errors='coerce').fillna(0)
            df_sorted = df_rank.sort_values(by=df_rank.columns[3], ascending=False).reset_index(drop=True)
            rank = df_sorted[df_sorted.iloc[:, 0] == s_id].index[0] + 1
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📚 المشاركة", f"{my_g.iloc[0, 1]} / {st.session_state.max_tasks}")
            c2.metric("📝 الاختبار", f"{my_g.iloc[0, 2]} / {st.session_state.max_quiz}")
            c3.metric("🏆 المجموع", f"{my_g.iloc[0, 3]} / 100")
            st.markdown(f"<div style='text-align: center; background: #1e3a8a; color: white; padding: 10px; border-radius: 10px; margin-top: 15px;'>🥇 ترتيبك الحالي: {rank} من {len(df_sorted)}</div>", unsafe_allow_html=True)
        else: st.info("لم ترصد درجاتك بعد.")

    if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()
