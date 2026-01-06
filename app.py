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

# 1- إعداد تسجيل الأخطاء (للمراقبة والاستقرار)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2- تحسين الاتصال بـ Google Sheets وتقليل الضغط (Caching)
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

@st.cache_data(ttl=60)
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        logging.error(f"خطأ في جلب بيانات {worksheet_name}: {e}")
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) - النسخة الأصلية كاملة بدون تعديل ---
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 45px 20px; border-radius: 0 0 40px 40px;
        color: white; text-align: center; margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1); width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .welcome-card {
        background: rgba(30, 64, 175, 0.05); border-right: 5px solid #1e40af;
        padding: 20px; border-radius: 12px; margin: 25px 0;
    }
    .stButton>button { background: #2563eb !important; color: white !important; border-radius: 15px !important; font-weight: bold; width: 100%; }
    .stTextInput input { border: 2px solid #3b82f6 !important; border-radius: 12px !important; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="color:white; font-size:26px;">منصة زياد الذكية</h1>
        <p style="color:white; opacity:0.9;">نظام متابعة الطلاب والتواصل الفعال</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# --- نظام الدخول الموحد ---
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid.strip() in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid.strip(); st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with tab2:
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
# 👨‍🏫 واجهة المعلم (لوحة التحكم)
# ==========================================
if st.session_state.role == "teacher":
    t_tabs = st.tabs(["👥 الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    with t_tabs[0]: # إدارة الطلاب
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        with st.form("add_student_form", clear_on_submit=True):
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
            nphone = c8.text_input("📱 جوال ولي الأمر")
            if st.form_submit_button("✅ إضافة الطالب"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, nstage, nsub, nmail, nphone, "0"])
                    st.success("تمت الإضافة بنجاح"); st.cache_data.clear(); st.rerun()

        with st.expander("🗑️ منطقة الحذف النهائي (بالرقم الأكاديمي)"):
            if not df_st.empty:
                del_id = st.selectbox("اختر الطالب للحذف:", df_st.iloc[:, 0].tolist())
                if st.button("🚨 حذف الطالب نهائياً من كافة الجداول"):
                    for s in ["students", "grades", "behavior"]:
                        ws = sh.worksheet(s); df_tmp = fetch_safe(s)
                        if not df_tmp.empty and str(del_id) in df_tmp.iloc[:,0].astype(str).values:
                            idx = df_tmp[df_tmp.iloc[:,0].astype(str) == str(del_id)].index[0]
                            ws.delete_rows(int(idx)+2)
                    st.success("تم المسح الشامل"); st.cache_data.clear(); st.rerun()

    with t_tabs[1]: # شاشة الدرجات
        st.markdown("### 📝 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("grade_entry"):
                s_name = st.selectbox("👤 اختر الطالب:", list(st_dict.keys()))
                c1, c2, c3 = st.columns(3)
                v1 = c1.number_input("⭐ المشاركة", 0.0, 20.0); v2 = c2.number_input("📚 الواجبات", 0.0, 20.0); v3 = c3.number_input("📝 اختبار", 0.0, 20.0)
                note = st.text_input("💬 ملاحظة")
                if st.form_submit_button("✅ حفظ"):
                    sid = st_dict[s_name]; ws = sh.worksheet("grades"); df_g = fetch_safe("grades")
                    row = [sid, v1, v2, v3, str(datetime.date.today()), note]
                    if not df_g.empty and str(sid) in df_g.iloc[:,0].astype(str).values:
                        idx = df_g[df_g.iloc[:,0].astype(str) == str(sid)].index[0]
                        ws.update(f"B{idx+2}:F{idx+2}", [[v1, v2, v3, str(datetime.date.today()), note]])
                    else: ws.append_row(row)
                    st.success("تم الحفظ"); st.cache_data.clear(); st.rerun()

    with t_tabs[2]: # البحث المطور
        st.markdown("### 🔍 محرك البحث")
        query = st.text_input("🔎 ابحث بالاسم أو الرقم:")
        if query:
            df_st = fetch_safe("students")
            res = df_st[df_st.iloc[:,0].astype(str).str.contains(query) | df_st.iloc[:,1].str.contains(query)]
            st.dataframe(res, use_container_width=True)

    with t_tabs[3]: # رصد السلوك
        st.markdown("### 🥇 رصد السلوك")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("beh_entry"):
                s_name = st.selectbox("🎯 الطالب:", list(st_dict.keys()))
                b_type = st.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "❌ سلبي (-5)"])
                b_note = st.text_area("📝 الملاحظة")
                if st.form_submit_button("💾 رصد"):
                    sid = st_dict[s_name]; sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, b_note])
                    ws_st = sh.worksheet("students"); idx = df_st[df_st.iloc[:,0]==sid].index[0]
                    p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "❌ سلبي (-5)": -5}
                    curr = int(df_st.iloc[idx, 8] if df_st.iloc[idx, 8] else 0)
                    ws_st.update_cell(int(idx)+2, 9, str(curr + p_map[b_type]))
                    st.success("تم تحديث النقاط"); st.cache_data.clear(); st.rerun()

    with t_tabs[4]: # الاختبارات
        st.markdown("### 📢 نشر التنبيهات")
        with st.form("exam_pub"):
            e_class = st.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("📝 العنوان"); e_date = st.date_input("📅 التاريخ"); e_link = st.text_input("🔗 رابط")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date), e_link])
                st.success("تم النشر"); st.cache_data.clear(); st.rerun()

    with t_tabs[5]: # الإعدادات
        st.markdown("### ⚙️ الإعدادات")
        with st.form("settings_form"):
            nu = st.text_input("اسم المستخدم الجديد"); np = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("حفظ التغييرات"):
                if nu and np:
                    h = hashlib.sha256(str.encode(np)).hexdigest()
                    sh.worksheet("users").update("A2:B2", [[nu, h]])
                    st.success("تم التحديث")

    with t_tabs[6]: # الخروج
        if st.button("🚪 تأكيد تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الملف الشخصي)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students"); df_g = fetch_safe("grades"); df_b = fetch_safe("behavior"); df_ex = fetch_safe("exams")
    s_id = st.session_state.sid
    s_row = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].iloc[0]
    s_name, s_class, s_points = s_row[1], s_row[2], int(float(s_row[8] if s_row[8] else 0))

    # هيدر الطالب
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 20px; color: white; text-align: center;">
            <h2 style="color:white; margin:0;">🎯 الطالب: {s_name}</h2>
            <p style="color:white; font-size:18px; margin:5px 0;">🏫 {s_class}</p>
        </div>
    """, unsafe_allow_html=True)

    # نظام الأوسمة
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 15px;">
                <div style="opacity: {'1' if s_points >= 10 else '0.2'}">🥉<br><b>برونزي</b></div>
                <div style="opacity: {'1' if s_points >= 50 else '0.2'}">🥈<br><b>فضي</b></div>
                <div style="opacity: {'1' if s_points >= 100 else '0.2'}">🥇<br><b>ذهبي</b></div>
            </div>
            <div style="background: #f59e0b; color: white; padding: 15px; border-radius: 15px; font-size: 24px; font-weight: bold;">
                النقاط: {s_points}
            </div>
        </div>
    """, unsafe_allow_html=True)

    s_tabs = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال", "⚙️ الإعدادات"])
    
    with s_tabs[0]: # تنبيهات
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            st.info(f"📢 {r[1]} | 📅 {r[2]}")

    with s_tabs[1]: # درجاتي
        my_g = df_g[df_g.iloc[:, 0].astype(str) == str(s_id)]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("⭐ المشاركة", my_g.iloc[0, 1])
            c2.metric("📚 الواجبات", my_g.iloc[0, 2])
            c3.metric("📝 الاختبارات", my_g.iloc[0, 3])
            st.success(f"💬 ملاحظة المعلم: {my_g.iloc[0, 5]}")
        else: st.write("لا توجد درجات مرصودة")

    with s_tabs[2]: # سلوكي
        my_b = df_b[df_b.iloc[:, 0].astype(str) == str(s_id)]
        for _, r in my_b.iloc[::-1].iterrows():
            st.warning(f"🏷️ {r[2]} | {r[3]} (📅 {r[1]})")

    with s_tabs[3]: # الأبطال
        df_st.iloc[:, 8] = pd.to_numeric(df_st.iloc[:, 8], errors='coerce').fillna(0)
        top = df_st.sort_values(by=df_st.columns[8], ascending=False).head(5)
        for i, row in top.iterrows():
            st.write(f"🏆 {row[1]} - {int(row[8])} نقطة")

    with s_tabs[4]: # إعدادات الطالب
        with st.form("st_update"):
            m = st.text_input("📧 البريد", value=s_row[6]); p = st.text_input("📱 الجوال", value=s_row[7])
            if st.form_submit_button("حفظ"):
                ws = sh.worksheet("students"); idx = df_st[df_st.iloc[:,0].astype(str)==str(s_id)].index[0]
                ws.update_cell(int(idx)+2, 7, m); ws.update_cell(int(idx)+2, 8, p)
                st.success("تم التحديث"); st.cache_data.clear(); st.rerun()

    if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()
