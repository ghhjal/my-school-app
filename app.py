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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# إعداد تسجيل الأخطاء للاستقرار الاحترافي
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# --- دالة الاتصال المحمية ---
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        logging.error(f"فشل الاتصال بـ Google Sheets: {e}")
        return None

sh = get_client()

# --- جلب البيانات مع التخزين المؤقت لتقليل الـ API Calls ---
@st.cache_data(ttl=60)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        logging.error(f"خطأ في جلب {worksheet_name}: {e}")
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) - النسخة الأصلية كاملة ---
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 45px 20px; border-radius: 0 0 40px 40px; color: white; text-align: center;
        margin: -80px -20px 30px -20px; box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1); width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .welcome-card { background: rgba(30, 64, 175, 0.05); border-right: 5px solid #1e40af; padding: 20px; border-radius: 12px; margin: 25px 0; }
    .stButton>button { background: #2563eb !important; color: white !important; border-radius: 15px !important; font-weight: bold; width: 100%; height: 3.5em; }
    .stTextInput input { border: 2px solid #3b82f6 !important; border-radius: 12px !important; }
    [data-testid="stSidebar"] { display: none !important; }
    .ann-card { padding: 15px; border-radius: 10px; margin-bottom: 5px; border-right: 5px solid #4F46E5; background-color: #F8FAFC; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="color:white; font-size:26px;">منصة زياد الذكية</h1>
        <p style="color:white; opacity:0.9;">نظام متابعة الطلاب المتكامل</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 نظام تسجيل الدخول
# ==========================================
if st.session_state.role is None:
    tab_log1, tab_log2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab_log1:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid.strip() in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip(); st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with tab_log2:
        with st.form("te_login"):
            u = st.text_input("👤 اسم المستخدم"); p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = fetch_safe("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("كلمة المرور خاطئة")
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم الكاملة (كل التبويبات)
# ==========================================
if st.session_state.role == "teacher":
    t_tabs = st.tabs(["👥 الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    with t_tabs[0]: # إدارة الطلاب
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        with st.form("add_st_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            c4, c5, c6 = st.columns(3)
            nyear = c4.text_input("🗓️ العام الدراسي", value="1447هـ")
            nstage = c5.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
            c7, c8 = st.columns(2)
            nmail = c7.text_input("📧 البريد الإلكتروني")
            nphone = c8.text_input("📱 جوال ولي الأمر (بدون 966)")
            if st.form_submit_button("✅ اعتماد وإضافة الطالب"):
                if nid and nname:
                    cp = nphone.strip()
                    if cp.startswith("0"): cp = cp[1:]
                    if not cp.startswith("966"): cp = "966" + cp
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"])
                    st.success(f"تم إضافة {nname} بنجاح"); st.cache_data.clear(); st.rerun()

        with st.expander("🗑️ منطقة الحذف النهائي (بالـ ID الطالب)"):
            if not df_st.empty:
                st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
                del_name = st.selectbox("🎯 اختر الطالب للحذف:", [""] + list(st_map.keys()))
                if st.button("🚨 تنفيذ الحذف النهائي الآن"):
                    if del_name:
                        target_id = st_map[del_name]
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s); df_tmp = fetch_safe(s)
                                if not df_tmp.empty and str(target_id) in df_tmp.iloc[:,0].astype(str).values:
                                    idx = df_tmp[df_tmp.iloc[:,0].astype(str) == str(target_id)].index[0]
                                    ws.delete_rows(int(idx)+2)
                            except Exception as e: logging.error(e)
                        st.success("💥 تم المسح الشامل"); st.cache_data.clear(); st.rerun()

    with t_tabs[1]: # شاشة الدرجات
        st.markdown("### 📝 رصد درجات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("grade_entry_form"):
                sel_name = st.selectbox("👤 اختر الطالب:", list(st_map.keys()))
                c1, c2, c3 = st.columns(3)
                v1 = c1.number_input("⭐ المشاركة", 0.0, 20.0); v2 = c2.number_input("📚 الواجبات", 0.0, 20.0); v3 = c3.number_input("📝 اختبار", 0.0, 20.0)
                note = st.text_input("💬 ملاحظة المعلم")
                if st.form_submit_button("✅ حفظ الدرجات"):
                    sid = st_map[sel_name]; ws = sh.worksheet("grades"); df_g = fetch_safe("grades")
                    curr_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    row = [sid, v1, v2, v3, curr_date, note]
                    if not df_g.empty and str(sid) in df_g.iloc[:, 0].astype(str).values:
                        idx = df_g[df_g.iloc[:, 0].astype(str) == str(sid)].index[0]
                        ws.update(f"B{idx+2}:F{idx+2}", [[v1, v2, v3, curr_date, note]])
                    else: ws.append_row(row)
                    st.success("✅ تم التحديث"); st.cache_data.clear(); st.rerun()

    with t_tabs[2]: # البحث المطور
        st.markdown("### 🔍 محرك البحث الذكي")
        query = st.text_input("🔎 ابحث باسم الطالب أو الرقم الأكاديمي:")
        if query:
            df_st = fetch_safe("students")
            res = df_st[df_st.iloc[:, 0].astype(str).str.contains(query) | df_st.iloc[:, 1].str.contains(query)]
            for i, r in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"**👤 {r[1]}** | 🔢 {r[0]} | 🏫 {r[2]}")
                    st.markdown(f'<a href="https://wa.me/{r[7]}" target="_blank">💬 واتساب</a>', unsafe_allow_html=True)

    with t_tabs[3]: # رصد السلوك
        st.markdown("### 🎭 رصد السلوك والتواصل الفوري")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("beh_form"):
                b_name = st.selectbox("🎯 اختر الطالب:", list(st_map.keys()))
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 نص الملاحظة")
                if st.form_submit_button("💾 رصد وحفظ"):
                    sid = st_map[b_name]; sh.worksheet("behavior").append_row([sid, str(b_date), b_type, b_note])
                    ws_st = sh.worksheet("students"); idx = df_st[df_st.iloc[:,0]==sid].index[0]
                    p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5}
                    curr = int(df_st.iloc[idx, 8] if df_st.iloc[idx, 8] else 0)
                    ws_st.update_cell(int(idx)+2, 9, str(curr + p_map[b_type]))
                    st.success("✅ تم تحديث النقاط"); st.cache_data.clear(); st.rerun()

    with t_tabs[4]: # الاختبارات
        st.markdown("### 📢 إدارة الاختبارات والتنبيهات")
        with st.form("exam_form"):
            e_class = st.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("📝 عنوان التنبيه"); e_date = st.date_input("📅 التاريخ"); e_link = st.text_input("🔗 رابط")
            if st.form_submit_button("🚀 نشر الآن"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date), e_link])
                st.success("✅ تم النشر"); st.cache_data.clear(); st.rerun()

    with t_tabs[5]: # الإعدادات
        st.markdown("### ⚙️ الإعدادات المتقدمة")
        with st.expander("🔐 تغيير بيانات الدخول"):
            with st.form("pass_upd"):
                nu = st.text_input("المستخدم الجديد"); np = st.text_input("المرور الجديدة", type="password")
                if st.form_submit_button("💾 حفظ"):
                    h = hashlib.sha256(str.encode(np)).hexdigest()
                    sh.worksheet("users").update("A2:B2", [[nu, h]])
                    st.success("تم التحديث")
        
        # إضافة ميزة رفع الملفات Excel التي كانت لديك
        st.markdown("### 📥 استيراد بيانات الطلاب")
        up_file = st.file_uploader("اختر ملف Excel", type=["xlsx"])
        if up_file:
            if st.button("🚀 تأكيد الرفع والاستبدال"):
                new_df = pd.read_excel(up_file)
                ws = sh.worksheet("students"); ws.clear()
                ws.update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم التحديث بنجاح"); st.cache_data.clear(); st.rerun()

    with t_tabs[6]:
        if st.button("🚗 خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب الكاملة (بكل المزايا)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students"); df_g = fetch_safe("grades"); df_b = fetch_safe("behavior"); df_ex = fetch_safe("exams")
    s_id = st.session_state.sid
    s_row = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].iloc[0]
    s_name, s_class, s_points = s_row[1], s_row[2], int(float(s_row[8] if s_row[8] else 0))

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 20px; color: white; text-align: center;">
            <h2 style="color:white; margin:0;">🎯 الطالب: {s_name}</h2>
            <p style="color:white; font-size:18px; margin:5px 0;">🏫 الصف: {s_class}</p>
        </div>
    """, unsafe_allow_html=True)

    # نظام الأوسمة الأصلي
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="opacity: {'1' if s_points >= 10 else '0.2'}">🥉<br><b>برونزي</b></div>
                <div style="opacity: {'1' if s_points >= 50 else '0.2'}">🥈<br><b>فضي</b></div>
                <div style="opacity: {'1' if s_points >= 100 else '0.2'}">🥇<br><b>ذهبي</b></div>
            </div>
            <div style="background: #f59e0b; color: white; padding: 15px; border-radius: 15px; font-size: 24px; font-weight: bold;">
                رصيد النقاط: {s_points}
            </div>
        </div>
    """, unsafe_allow_html=True)

    s_tabs = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال", "⚙️ الإعدادات"])
    
    with s_tabs[0]: # تنبيهات
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.info(f"📢 {r[1]} | 📅 {r[2]}")

    with s_tabs[1]: # درجاتي
        st.markdown("#### 📊 السجل الأكاديمي")
        my_g = df_g[df_g.iloc[:, 0].astype(str) == str(s_id)]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("⭐ المشاركة", my_g.iloc[0, 1])
            c2.metric("📚 الواجبات", my_g.iloc[0, 2])
            c3.metric("📝 الاختبارات", my_g.iloc[0, 3])
            st.success(f"💬 ملاحظة المعلم: {my_g.iloc[0, 5]}")
        else: st.info("لا توجد درجات مرصودة")

    with s_tabs[2]: # سلوكي
        st.markdown("#### 🎭 سجل الانضباط")
        my_b = df_b[df_b.iloc[:, 0].astype(str) == str(s_id)]
        for _, r in my_b.iloc[::-1].iterrows():
            st.warning(f"🏷️ {r[2]} | {r[3]} (📅 {r[1]})")

    with s_tabs[3]: # الأبطال
        st.markdown("#### 🏆 متصدرو المنصة")
        df_st.iloc[:, 8] = pd.to_numeric(df_st.iloc[:, 8], errors='coerce').fillna(0)
        top = df_st.sort_values(by=df_st.columns[8], ascending=False).head(10)
        for i, row in top.iterrows():
            is_me = (str(row[0]) == str(s_id))
            st.markdown(f'<div style="padding:10px; border:{"2px solid blue" if is_me else "1px solid #ddd"}; border-radius:10px; margin-bottom:5px;">👤 {row[1]} | 🏅 {int(row[8])} نقطة {"(أنت)" if is_me else ""}</div>', unsafe_allow_html=True)

    with s_tabs[4]: # إعدادات الطالب
        with st.form("st_up"):
            m = st.text_input("📧 البريد الإلكتروني", value=s_row[6])
            p = st.text_input("📱 الجوال", value=s_row[7])
            if st.form_submit_button("✅ حفظ التعديلات"):
                ws = sh.worksheet("students"); idx = df_st[df_st.iloc[:,0].astype(str)==str(s_id)].index[0]
                ws.update_cell(int(idx)+2, 7, m); ws.update_cell(int(idx)+2, 8, p)
                st.success("تم التحديث"); st.cache_data.clear(); st.rerun()

    if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()
