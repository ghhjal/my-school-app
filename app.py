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

# 1- إعداد تسجيل الأخطاء للاستقرار
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2- تقليل الاتصال بـ Google Sheets عبر الـ Cache
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        logging.error(f"فشل الاتصال: {e}")
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
        logging.error(f"خطأ في جلب {worksheet_name}: {e}")
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) - يبقى كما هو تماماً ---
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
    }
    .stButton>button { background: #2563eb !important; color: white !important; border-radius: 12px !important; }
    </style>
    <div class="header-section">
        <h1 style="color:white;">منصة زياد الذكية</h1>
        <p style="color:white;">نظام متابعة الطلاب المتطور</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# --- نظام تسجيل الدخول ---
if st.session_state.role is None:
    tab_log1, tab_log2 = st.tabs(["🎓 الطلاب", "🔐 الإدارة"])
    with tab_log1:
        with st.form("student_login"):
            sid_input = st.text_input("🆔 الرقم الأكاديمي")
            if st.form_submit_button("دخول"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid_input.strip() in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid_input.strip()
                    st.rerun()
                else: st.error("الرقم غير صحيح")
    with tab_log2:
        with st.form("admin_login"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول"):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# --- واجهة المعلم الكاملة ---
if st.session_state.role == "teacher":
    tabs = st.tabs(["👥 الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])
    
    # 1. إدارة الطلاب
    with tabs[0]:
        st.subheader("👥 إضافة وحذف الطلاب")
        with st.form("add_st"):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nclass = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("إضافة الطالب"):
                if nid and nname:
                    try:
                        sh.worksheet("students").append_row([nid, nname, nclass, "1447هـ", "ابتدائي", "لغة إنجليزية", "", "", "0"])
                        st.success("تمت الإضافة"); st.cache_data.clear(); st.rerun()
                    except Exception as e: logging.error(e)

        st.markdown("---")
        df_all = fetch_safe("students")
        if not df_all.empty:
            st.write("سجل الطلاب:")
            st.dataframe(df_all, use_container_width=True)
            target_del = st.selectbox("اختر طالب للحذف النهائي:", [""] + df_all.iloc[:, 1].tolist())
            if st.button("🚨 حذف الطالب نهائياً"):
                if target_del:
                    tid = df_all[df_all.iloc[:,1] == target_del].iloc[0,0]
                    for s in ["students", "grades", "behavior"]:
                        ws = sh.worksheet(s)
                        df_tmp = fetch_safe(s)
                        if not df_tmp.empty and str(tid) in df_tmp.iloc[:,0].astype(str).values:
                            idx = df_tmp[df_tmp.iloc[:,0].astype(str) == str(tid)].index[0]
                            ws.delete_rows(int(idx)+2)
                    st.success("تم الحذف"); st.cache_data.clear(); st.rerun()

    # 2. شاشة الدرجات
    with tabs[1]:
        st.subheader("📈 رصد الدرجات")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("grade_form"):
                s_name = st.selectbox("اختر الطالب:", options=list(st_map.keys()))
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("المشاركة", 0.0, 20.0); p2 = c2.number_input("الواجبات", 0.0, 20.0); ex = c3.number_input("الاختبار", 0.0, 20.0)
                note = st.text_input("ملاحظة")
                if st.form_submit_button("حفظ الدرجات"):
                    sid = st_map[s_name]
                    ws = sh.worksheet("grades")
                    df_g = fetch_safe("grades")
                    row = [sid, p1, p2, ex, str(datetime.date.today()), note]
                    if not df_g.empty and str(sid) in df_g.iloc[:, 0].astype(str).values:
                        idx = df_g[df_g.iloc[:, 0].astype(str) == str(sid)].index[0]
                        ws.update(f"B{idx+2}:F{idx+2}", [[p1, p2, ex, str(datetime.date.today()), note]])
                    else: ws.append_row(row)
                    st.success("تم الحفظ"); st.cache_data.clear(); st.rerun()

    # 3. البحث المطور
    with tabs[2]:
        st.subheader("🔍 البحث السريع")
        query = st.text_input("ابحث بالاسم أو الرقم:")
        df_st = fetch_safe("students")
        if query and not df_st.empty:
            res = df_st[df_st.iloc[:,0].astype(str).str.contains(query) | df_st.iloc[:,1].str.contains(query)]
            st.dataframe(res)

    # 4. رصد السلوك
    with tabs[3]:
        st.subheader("🥇 نقاط السلوك")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("beh_form"):
                s_name = st.selectbox("الطالب:", list(st_map.keys()))
                b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "❌ سلبي (-5)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد السلوك"):
                    sid = st_map[s_name]
                    sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, b_note])
                    # تحديث النقاط
                    ws_st = sh.worksheet("students")
                    idx = df_st[df_st.iloc[:,0] == sid].index[0]
                    points = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "❌ سلبي (-5)": -5}
                    curr = int(df_st.iloc[idx, 8] if df_st.iloc[idx, 8] else 0)
                    ws_st.update_cell(int(idx)+2, 9, str(curr + points[b_type]))
                    st.success("تم تحديث السلوك"); st.cache_data.clear(); st.rerun()

    # 5. الاختبارات
    with tabs[4]:
        st.subheader("📢 نشر التنبيهات")
        with st.form("ex_form"):
            e_class = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث"])
            e_title = st.text_input("عنوان التنبيه")
            e_date = st.date_input("التاريخ")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date), ""])
                st.success("تم النشر"); st.cache_data.clear(); st.rerun()

    # 6. الإعدادات
    with tabs[5]:
        st.subheader("⚙️ إعدادات الحساب")
        with st.form("pass_form"):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_p = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("تحديث البيانات"):
                h = hashlib.sha256(str.encode(new_p)).hexdigest()
                sh.worksheet("users").update("A2:B2", [[new_u, h]])
                st.success("تم التحديث بنجاح")

    with tabs[6]:
        if st.button("خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب الكاملة
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_data = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"### أهلاً بك يا {s_data[1]}")
    st.info(f"رصيدك الحالي من النقاط: {s_data[8]}")
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "🎭 سلوكي", "📢 تنبيهات"])
    
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:,0].astype(str) == st.session_state.sid]
        if not my_g.empty: st.write(my_g)
        else: st.write("لا يوجد درجات حالياً")
    
    with t2:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:,0].astype(str) == st.session_state.sid]
        if not my_b.empty: st.write(my_b)
    
    with t3:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:,0] == s_data[2]) | (df_ex.iloc[:,0] == "الكل")]
            st.dataframe(f_ex)

    if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()
