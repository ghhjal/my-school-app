import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials
import urllib.parse
import io

# ==========================================
# ⚙️ 1. إعدادات النظام والاستقرار (إصدار 2026)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# الاتصال بـ Google Sheets
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من Secrets.")
        return None

sh = get_gspread_client()

# --- تحميل الإعدادات الدائمة من شيت settings لضمان ثبات التوزيع ---
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40

if "active_tab" not in st.session_state: st.session_state.active_tab = 0
if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🧠 2. دوال معالجة البيانات الاحترافية
# ==========================================
@st.cache_data(ttl=30)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def get_col_idx(df, col_name):
    try: return df.columns.get_loc(col_name) + 1
    except: return None

# ==========================================
# 🎨 3. التصميم البصري (CSS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin: -80px -20px 20px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .stMetric { background: #f8fafc; padding: 15px; border-radius: 15px; border: 1px solid #e2e8f0; }
    </style>
    <div class="header-section"><h1>منصة زياد الذكية</h1><p>نظام الإدارة والتقييم المتكامل 2026</p></div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 4. نظام الدخول الموحد
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    with t1:
        with st.form("st_log"):
            sid_input = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid_input in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid_input; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("te_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    user_data = df_u[df_u['username']==u.strip()].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role = "teacher"; st.session_state.username = u.strip(); st.rerun()
                st.error("بيانات الدخول خاطئة")
    st.stop()

# ==========================================
# 👨‍🏫 5. واجهة المعلم (إحصائيات + بحث + رصد + إعدادات)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التواصل", "⚙️ الإعدادات", "🚗 خروج"])

    with menu[0]: # تبويب الطلاب المطور
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

    with menu[1]: # تبويب التقييم والرصد
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_list = {f"{row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected = st.selectbox("🎯 اختر الطالب:", [""] + list(st_list.keys()))
            if selected:
                sid = st_list[selected]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    v_t = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0)
                    v_q = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0)
                    if st.button("💾 حفظ الدرجات"):
                        if v_t <= st.session_state.max_tasks and v_q <= st.session_state.max_quiz:
                            sh.worksheet("grades").append_row([sid, v_t, v_q, v_t+v_q, str(datetime.date.today())])
                            st.success("تم الحفظ"); st.cache_data.clear()
                with col_b:
                    st.markdown("##### 🎭 سجل السلوك")
                    # (كود السلوك والواتساب المنسق الخاص بك)

    with menu[3]: # تبويب الإعدادات والرفع
        st.subheader("⚙️ التحكم الإداري")
        with st.expander("⚖️ تعديل توزيع الدرجات (حفظ دائم)"):
            c1, c2 = st.columns(2)
            nt = c1.number_input("الحد الأقصى للمشاركة", 1, 100, st.session_state.max_tasks)
            nq = c2.number_input("الحد الأقصى للاختبار", 1, 100, st.session_state.max_quiz)
            if st.button("💾 اعتماد"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, nt); ws_s.update_cell(3, 2, nq)
                st.session_state.max_tasks, st.session_state.max_quiz = nt, nq
                st.success("تم الحفظ الدائم"); st.rerun()
        with st.expander("📤 رفع ملفات Excel"):
            f_up = st.file_uploader("اختر ملف الطلاب/الدرجات", type=["xlsx"])
            if f_up and st.button("🚀 رفع"):
                df_up = pd.read_excel(f_up).fillna("")
                sh.worksheet("students").append_rows(df_up.values.tolist())
                st.success("تم الرفع"); st.cache_data.clear()

    with menu[4]:
        if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 6. واجهة الطالب (النسخة الذهبية المكتملة)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students"); df_grades = fetch_safe("grades")
    df_beh = fetch_safe("behavior"); df_ex = fetch_safe("exams")
    s_id = str(st.session_state.sid)
    
    # جلب معلومات الطالب الحالية لضمان الاستقرار
    s_row = df_st[df_st.iloc[:, 0] == s_id].iloc[0]
    s_name = s_row['name'] if 'name' in s_row else s_row.iloc[1]
    s_class = s_row['class'] if 'class' in s_row else s_row.iloc[4]
    s_points = int(float(s_row['النقاط'])) if 'النقاط' in s_row else 0

    st.markdown(f"""<div style='background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 20px; color: white; text-align: center;'>
        <h2 style='color: white;'>مرحباً بك: {s_name}</h2><div>🏫 {s_class} | 🏆 النقاط: {s_points}</div></div>""", unsafe_allow_html=True)

    t_ex, t_grade, t_beh, t_lead = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال"])

    with t_ex: # التنبيهات (الفلترة حسب الصف)
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
        if not f_ex.empty:
            for _, r in f_ex.iloc[::-1].iterrows():
                with st.container(border=True):
                    st.markdown(f"### 📍 {r[1]}"); st.caption(f"📅 {r[2]}")
                    st.markdown(r[3])
        else: st.info("لا توجد تعميمات حالياً.")

    with t_grade: # الدرجات مع الترتيب الذكي
        my_g = df_grades[df_grades.iloc[:, 0] == s_id]
        if not my_g.empty:
            # حساب الترتيب اللحظي
            df_rank = df_grades.copy()
            df_rank.iloc[:, 3] = pd.to_numeric(df_rank.iloc[:, 3], errors='coerce').fillna(0)
            df_sorted = df_rank.sort_values(by=df_rank.columns[3], ascending=False).reset_index(drop=True)
            rank = df_sorted[df_sorted.iloc[:, 0] == s_id].index[0] + 1
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📚 المشاركة", f"{my_g.iloc[0, 1]} / {st.session_state.max_tasks}")
            c2.metric("📝 الاختبار", f"{my_g.iloc[0, 2]} / {st.session_state.max_quiz}")
            c3.metric("🏆 المجموع", f"{my_g.iloc[0, 3]} / 100")
            st.markdown(f"<div style='text-align: center; background: green; color: white; padding: 10px; border-radius: 10px; margin-top: 15px;'>🥇 ترتيبك في الفصل: {rank} من {len(df_sorted)}</div>", unsafe_allow_html=True)
        else: st.info("لم تُرصد درجاتك بعد.")

    with t_beh: # السلوك
        my_b = df_beh[df_beh.iloc[:, 0] == s_id]
        if not my_b.empty:
            for _, r in my_b.iloc[::-1].iterrows(): st.warning(f"🏷️ {r[2]} | {r[3]} (📅 {r[1]})")
        else: st.success("سجلك متميز ونظيف! ✨")

    with t_lead: # لوحة الأبطال
        top_10 = df_st.sort_values(by='النقاط', ascending=False).head(10)
        for i, row in top_10.iterrows():
            st.markdown(f"<div style='padding:5px; border-bottom:1px solid #eee;'>👤 {row.iloc[1]} - <b>{row['النقاط']} نقطة</b></div>", unsafe_allow_html=True)

    if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()
