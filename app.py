import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials

# --- 1. الإعدادات والاتصال الموحد ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات")
        return None

sh = get_gspread_client()

# --- 2. دوال معالجة البيانات (الاستقرار البرمجي) ---
@st.cache_data(ttl=30)
def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # تحويل المعرف (العمود الأول) إلى نص دائماً لضمان الدقة
        if not df.empty:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """البحث عن رقم العمود بناءً على اسمه لضمان المرونة"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

# --- 3. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; height: 3.5em; transition: 0.3s; }
    .stButton>button:hover { background: #1e3a8a !important; transform: scale(1.02); }
    div[data-testid="stForm"] { border-radius: 20px !important; padding: 25px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>الإصدار الإداري المتكامل - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 بوابة تسجيل الدخول (موحدة)
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_log"):
            sid = st.text_input("🆔 الرقم الأكاديمي (نص)").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_st = fetch_data("students")
                if not df_st.empty and sid in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("عذراً، الرقم الأكاديمي غير مسجل")
    with t2:
        with st.form("te_log"):
            u = st.text_input("👤 اسم المستخدم"); p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_data("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (التقسيم المدمج والذكي)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 ملفات الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1️⃣ تبويب: ملفات الطلاب (إضافة كاملة + بحث + حذف ذكي) ---
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        with st.expander("➕ إضافة طالب جديد (الحقول السبعة)", expanded=False):
            with st.form("full_add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                f_id = c1.text_input("🔢 الرقم الأكاديمي (نص)")
                f_name = c2.text_input("👤 الاسم الثلاثي")
                c3, c4, c5 = st.columns(3)
                f_stage = c3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                f_year = c4.text_input("🗓️ العام الدراسي", "1447هـ")
                f_class = c5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                c6, c7 = st.columns(2)
                f_email = c6.text_input("📧 البريد الإلكتروني")
                f_phone = c7.text_input("📱 الجوال")
                
                if st.form_submit_button("✅ اعتماد وحفظ"):
                    df_check = fetch_data("students")
                    if f_id in df_check.iloc[:, 0].values:
                        st.error(f"⚠️ الرقم ({f_id}) مسجل مسبقاً باسم: {df_check[df_check.iloc[:,0]==f_id].iloc[0,1]}")
                    elif f_id and f_name:
                        sh.worksheet("students").append_row([f_id, f_name, f_stage, f_year, f_class, f_email, f_phone, "0"])
                        st.success("تم الإضافة بنجاح"); st.cache_data.clear(); st.rerun()

        st.divider()
        c_search, c_del = st.columns([2, 1])
        df_st = fetch_data("students")
        with c_search:
            query = st.text_input("🔍 ابحث (اسم/رقم):")
        with c_del:
            if not df_st.empty:
                del_id = st.selectbox("🗑️ حذف ذكي شامل:", [""] + df_st.iloc[:, 0].tolist())
                if st.button("🚨 حذف نهائي من كافة السجلات"):
                    if del_id:
                        for s in ["students", "grades", "behavior"]:
                            ws_del = sh.worksheet(s); df_del = fetch_data(s)
                            if not df_del.empty and str(del_id) in df_del.iloc[:,0].values:
                                idx_del = df_del[df_del.iloc[:,0] == str(del_id)].index[0]
                                ws_del.delete_rows(int(idx_del) + 2)
                        st.success("تم الحذف بنجاح"); st.cache_data.clear(); st.rerun()

        if query:
            df_st = df_st[df_st.iloc[:, 0].str.contains(query) | df_st.iloc[:, 1].str.contains(query)]
        st.dataframe(df_st, use_container_width=True, hide_index=True)

    # --- 2️⃣ تبويب: التقييم والمتابعة (درجات وسلوك مدمجة) ---
    with menu[1]:
        st.subheader("📊 التقييم والمتابعة (الدرجات والسلوك)")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            sel_st = st.selectbox("🎯 اختر الطالب للتقييم:", [""] + list(st_map.keys()))
            if sel_st:
                sid = st_map[sel_st]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                    if st.button("💾 حفظ الدرجات"):
                        ws_g = sh.worksheet("grades"); df_g = fetch_data("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v1); ws_g.update_cell(idx, 3, v2)
                        else: ws_g.append_row([sid, v1, v2, "0", str(datetime.date.today()), ""])
                        st.success("تم الحفظ")

                with col_b:
                    st.markdown("##### 🥇 رصد السلوك والنقاط")
                    b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                    if st.button("💾 رصد السلوك وتحديث النقاط"):
                        sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                        p_idx = get_col_idx(df_st, "النقاط")
                        row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                        points = 10 if "+" in b_type else (5 if "إيجابي" in b_type else -5 if "سلبي" in b_type else 0)
                        old_p = int(df_st[df_st.iloc[:,0] == sid].iloc[0]["النقاط"] or 0)
                        sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + points))
                        st.success("تم التحديث بنجاح")

    # --- 3️⃣ تبويب: التواصل والتنبيهات (الواتساب والرسائل) ---
    with menu[2]:
        st.subheader("📢 التواصل والتنبيهات")
        with st.form("comm_form"):
            e_t = st.text_input("عنوان التنبيه أو الاختبار")
            e_c = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث"])
            if st.form_submit_button("🚀 نشر الإعلان"):
                sh.worksheet("exams").append_row([e_c, e_t, str(datetime.date.today()), ""])
                st.success("تم النشر")

    # --- 4️⃣ تبويب: الإعدادات (الأدوات الإدارية) ---
    with menu[3]:
        st.subheader("⚙️ الإعدادات المتقدمة")
        c_up, c_auth = st.columns(2)
        with c_up:
            st.markdown("##### 📥 استيراد بيانات الطلاب")
            up_f = st.file_uploader("ارفع ملف Excel", type="xlsx")
            if up_f and st.button("تحديث قاعدة البيانات"):
                new_df = pd.read_excel(up_f)
                sh.worksheet("students").update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم الاستبدال بنجاح")
        with c_auth:
            st.markdown("##### 🔐 إدارة الحساب")
            if st.button("🧹 تصفير الكاش (تحديث فوري)"): st.cache_data.clear(); st.rerun()

    with menu[4]:
        if st.button("🚗 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (النسخة النهائية المستقرة)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_data("students")
    s_id = st.session_state.sid
    # العثور على بيانات الطالب بالـ ID لضمان عدم حدوث تكرار
    s_info = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].iloc[0]
    
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #3b82f6;">
            <h2 style="color: #1e40af;">أهلاً بك: {s_info.iloc[1]}</h2>
            <div style="font-size: 24px; font-weight: bold; color: orange;">النقاط الحالية: {s_info['النقاط']}</div>
            <p>الصف: {s_info.iloc[4]} | المرحلة: {s_info.iloc[2]}</p>
        </div>
    """, unsafe_allow_html=True)

    t_st = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🚗 خروج"])
    
    with t_st[0]:
        df_ex = fetch_data("exams")
        if not df_ex.empty: st.table(df_ex.iloc[::-1])

    with t_st[1]:
        df_g = fetch_data("grades")
        my_g = df_g[df_g.iloc[:, 0].astype(str) == str(s_id)]
        if not my_g.empty: st.dataframe(my_g, use_container_width=True, hide_index=True)
        else: st.info("لا توجد درجات حالياً")

    with t_st[3]:
        if st.button("خروج الطالب"): st.session_state.role = None; st.rerun()
