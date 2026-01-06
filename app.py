import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات النظام والاستقرار ---
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

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
        st.error("⚠️ خطأ في الاتصال بقاعدة البيانات")
        return None

sh = get_gspread_client()

# --- 2. دوال معالجة البيانات (ديناميكية وبالاعتماد على الـ ID كـ نص) ---
@st.cache_data(ttl=60)
def fetch_data(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # تحويل المعرف (ID) في جميع الجداول إلى نص لضمان دقة الربط والحذف
        if not df.empty and df.columns[0]:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """إيجاد رقم العمود بناءً على اسمه لضمان عدم تأثر الكود بتغيير ترتيب الأعمدة"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

# --- 3. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 40px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; height: 3.5em; }
    div[data-testid="stForm"] { border-radius: 20px !important; padding: 25px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>نظام المتابعة الإداري المتكامل - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 بوابة الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_log"):
            sid_input = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_check = fetch_data("students")
                if not df_check.empty and sid_input in df_check.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid_input; st.rerun()
                else: st.error("عذراً، الرقم الأكاديمي غير مسجل")
    with t2:
        with st.form("admin_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_data("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (الهيكلية المدمجة بالحقول الكاملة)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1️⃣ تبويب: الطلاب (إدارة كاملة + منع تكرار + تنسيق هاتف) ---
    # --- داخل تبويب الطلاب (menu[0]) ---
with menu[0]:
    st.subheader("👥 إدارة قاعدة بيانات الطلاب")
    
    # 1. نموذج الإضافة (يبقى كما هو مع استمرار حفظ المادة في الخلفية)
    with st.expander("➕ إضافة طالب جديد", expanded=False):
        with st.form("add_st_final"):
            # الحقول السبعة كاملة...
            # (كود الإضافة السابق مع منطق منع التكرار وتنسيق الهاتف)
            pass 

    st.divider()
    
    # جلب البيانات
    df_st = fetch_data("students")
    
    if not df_st.empty:
        c_search, c_del = st.columns([2, 1])
        
        with c_search:
            q = st.text_input("🔍 ابحث عن طالب (اسم أو رقم):")
        
        with c_del:
            # 2. تطوير زر الحذف (رسالة تحذير + تأكيد)
            st.markdown("##### 🗑️ منطقة الحذف الآمن")
            target_del = st.selectbox("اختر الرقم الأكاديمي:", [""] + df_st.iloc[:, 0].tolist(), key="del_select")
            
            if target_del:
                # إظهار رسالة تحذيرية ملونة
                st.warning(f"⚠️ هل أنت متأكد من حذف الطالب صاحب الرقم ({target_del})؟ لا يمكن التراجع عن هذه العملية.")
                
                # زر التأكيد النهائي
                if st.button("🚨 نعم، قم بالحذف النهائي الآن"):
                    with st.spinner("جاري المسح الشامل..."):
                        for s in ["students", "grades", "behavior"]:
                            ws_del = sh.worksheet(s)
                            df_del = fetch_data(s)
                            if not df_del.empty and str(target_del) in df_del.iloc[:, 0].values:
                                # تحديد السطر وحذفه
                                idx_del = df_del[df_del.iloc[:, 0] == str(target_del)].index[0]
                                ws_del.delete_rows(int(idx_del) + 2)
                        
                        # رسالة النجاح بعد الحذف
                        st.success(f"💥 تم حذف الطالب وكافة سجلاته بنجاح")
                        st.cache_data.clear()
                        time.sleep(1.5)
                        st.rerun()

        # 3. عرض الجدول (إخفاء عمود اللغة الإنجليزية)
        st.markdown("##### 📋 سجل الطلاب الحالي")
        
        # نقوم بإسقاط العمود من العرض فقط (View) دون حذفه من الـ Google Sheet
        # نستخدم errors='ignore' لتجنب الأخطاء في حال تغير اسم العمود
        cols_to_hide = ["لغة إنجليزية", "المادة", "sem"] 
        df_display = df_st.drop(columns=[c for c in cols_to_hide if c in df_st.columns], errors='ignore')
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    else:
        st.info("لا يوجد طلاب مسجلون حالياً.")

    # --- 2️⃣ تبويب: التقييم والمتابعة (درجات وسلوك) ---
    with menu[1]:
        st.subheader("📈 رصد الأداء الأكاديمي والسلوكي")
        if not df_st.empty:
            st_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            sel_st = st.selectbox("🎯 اختر الطالب:", [""] + list(st_dict.keys()))
            if sel_st:
                sid = st_dict[sel_st]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                    if st.button("💾 حفظ الدرجة"):
                        ws_g = sh.worksheet("grades"); df_g = fetch_data("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v1); ws_g.update_cell(idx, 3, v2)
                        else: ws_g.append_row([sid, v1, v2, "0", str(datetime.date.today()), ""])
                        st.success("تم الحفظ")
                with col_b:
                    st.markdown("##### 🥇 رصد السلوك")
                    b_type = st.selectbox("النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "❌ سلبي (-5)"])
                    if st.button("💾 تحديث النقاط"):
                        sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                        p_idx = get_col_idx(df_st, "النقاط")
                        row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                        points = 10 if "+" in b_type else (5 if "إيجابي" in b_type else -5)
                        old_p = int(df_st[df_st.iloc[:, 0] == sid].iloc[0]["النقاط"] or 0)
                        sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + points))
                        st.success("تم التحديث")

    # --- 3️⃣ تبويب: التواصل والتنبيهات ---
    with menu[2]:
        st.subheader("📢 التواصل والتنبيهات")
        with st.form("exam_comm"):
            e_t = st.text_input("عنوان التنبيه")
            e_c = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث"])
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_c, e_t, str(datetime.date.today()), ""])
                st.success("تم النشر")

    # --- 4️⃣ تبويب: الإعدادات ---
    with menu[3]:
        st.subheader("⚙️ أدوات التحكم")
        c_excel, c_auth = st.columns(2)
        with c_excel:
            st.info("📥 استيراد بيانات الطلاب من Excel")
            up = st.file_uploader("ارفع الملف", type="xlsx")
            if up and st.button("تأكيد الاستبدال"):
                new_df = pd.read_excel(up)
                sh.worksheet("students").update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم التحديث بنجاح")
        with c_auth:
            if st.button("🧹 تحديث البيانات (تصفير الكاش)"): st.cache_data.clear(); st.rerun()

    with menu[4]:
        if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_data("students")
    s_info = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #3b82f6;">
            <h2>مرحباً بك: {s_info.iloc[1]}</h2>
            <p>النقاط: <b>{s_info['النقاط']}</b> | الصف: {s_info.iloc[4]}</p>
        </div>
    """, unsafe_allow_html=True)
    # تبويبات الطالب (درجاتي، سلوكي، تنبيهات)...
