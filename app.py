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

# الاتصال بـ Google Sheets
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من Secrets.")
        return None

sh = get_gspread_client()

# --- 2. دوال معالجة البيانات (الذكاء البرمجي) ---

@st.cache_data(ttl=30)
def fetch_safe(worksheet_name):
    """جلب البيانات مع ضمان تحويل المعرف (ID) لنص لمنع انهيار البرنامج"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty:
            # الاعتماد على المعرف كـ نص لمنع فقدان الأصفار
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """إيجاد رقم العمود بناءً على اسمه لضمان عدم تأثر الكود بتغيير الترتيب في الشيت"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

def dynamic_append_student(f_id, f_name, f_stage, f_year, f_class, f_email, f_phone):
    """إضافة طالب بناءً على أسماء الأعمدة الفعلية لتجنب مشكلة إزاحة البيانات"""
    try:
        ws = sh.worksheet("students")
        headers = ws.row_values(1)
        data_map = {
            "id": str(f_id).strip(),
            "name": f_name,
            "class": f_class,
            "year": f_year,
            "sem": f_stage,
            "الإيميل": f_email,
            "الجوال": str(f_phone),
            "النقاط": "0"
        }
        # بناء السطر بناءً على الترتيب الحقيقي للأعمدة في ملفك
        new_row = [data_map.get(h, "") for h in headers]
        ws.append_row(new_row)
        return True
    except:
        return False

# --- 3. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 40px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; height: 3.5em; }
    div[data-testid="stForm"] { border-radius: 20px !important; padding: 25px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>الإصدار الإداري المتكامل - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 نظام الدخول الموحد
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
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("كلمة المرور خاطئة")
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (التقسيم المدمج المطور)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    with menu[0]: # تبويب الطلاب
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        with st.expander("➕ إضافة طالب جديد (الحقول السبعة)", expanded=False):
            with st.form("add_st_full", clear_on_submit=True):
                c1, c2 = st.columns(2)
                f_id = c1.text_input("🔢 الرقم الأكاديمي (نص)")
                f_name = c2.text_input("👤 الاسم الثلاثي")
                c3, c4, c5 = st.columns(3)
                f_stage = c3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                f_year = c4.text_input("🗓️ العام", "1447هـ")
                f_class = c5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                f_mail = st.text_input("📧 البريد الإلكتروني")
                f_phone = st.text_input("📱 الجوال (بدون 0)")
                if st.form_submit_button("✅ اعتماد وحفظ"):
                    df_cur = fetch_safe("students")
                    if f_id.strip() in df_cur.iloc[:, 0].values:
                        st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً")
                    elif f_id and f_name:
                        # تنسيق الجوال تلقائياً
                        phone = f_phone.strip()
                        if phone.startswith("0"): phone = phone[1:]
                        if not phone.startswith("966"): phone = "966" + phone
                        if dynamic_append_student(f_id.strip(), f_name, f_stage, f_year, f_class, f_mail, phone):
                            st.success(f"تمت إضافة {f_name} بنجاح"); st.cache_data.clear(); st.rerun()

        st.divider()
        df_st = fetch_safe("students")
        if not df_st.empty:
            c_s, c_d = st.columns([2, 1])
            with c_s: q = st.text_input("🔍 ابحث (اسم/رقم):")
            with c_d:
                st.markdown("##### 🗑️ الحذف الآمن")
                t_del = st.selectbox("اختر الرقم للحذف:", [""] + df_st.iloc[:, 0].tolist())
                if t_del:
                    st.warning(f"⚠️ هل أنت متأكد من حذف {t_del}؟")
                    if st.button("🚨 نعم، حذف نهائي من كافة الجداول"):
                        for s in ["students", "grades", "behavior"]:
                            ws = sh.worksheet(s); df_t = fetch_safe(s)
                            if not df_t.empty and str(t_del) in df_t.iloc[:, 0].values:
                                idx = df_t[df_t.iloc[:, 0] == str(t_del)].index[0]
                                ws.delete_rows(int(idx) + 2)
                        st.success("تم الحذف بنجاح"); st.cache_data.clear(); st.rerun()
            
            # عرض الجدول مع إخفاء المادة كما طلبت
            cols_hide = ["لغة إنجليزية", "المادة", "sem"]
            df_disp = df_st.drop(columns=[c for c in cols_hide if c in df_st.columns], errors='ignore')
            if q: df_disp = df_disp[df_disp.iloc[:, 0].str.contains(q) | df_disp.iloc[:, 1].str.contains(q)]
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

    with menu[1]: # التقييم والمتابعة
        st.subheader("📈 التقييم الأكاديمي والسلوكي المدمج")
        if not df_st.empty:
            st_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            sel_st = st.selectbox("🎯 اختر الطالب للتقييم:", [""] + list(st_map.keys()))
            if sel_st:
                sid = st_map[sel_st]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 الدرجات")
                    v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                    if st.button("💾 حفظ الدرجات"):
                        ws_g = sh.worksheet("grades"); df_g = fetch_safe("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v1); ws_g.update_cell(idx, 3, v2)
                        else: ws_g.append_row([sid, v1, v2, "0", str(datetime.date.today()), ""])
                        st.success("تم الحفظ")
                with col_b:
                    st.markdown("##### 🥇 السلوك والنقاط")
                    b_type = st.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
                    if st.button("💾 تحديث رصيد النقاط"):
                        sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                        p_idx = get_col_idx(df_st, "النقاط")
                        row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                        points = 10 if "متميز" in b_type else (5 if "إيجابي" in b_type else -5 if "سلبي" in b_type else 0)
                        old_p = int(df_st[df_st.iloc[:, 0] == sid].iloc[0]["النقاط"] or 0)
                        sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + points))
                        st.success("تم تحديث السلوك والنقاط بنجاح")

    with menu[2]: # التواصل والتنبيهات
        st.subheader("📢 التواصل والتنبيهات")
        with st.form("exam_comm"):
            e_t = st.text_input("موضوع التنبيه")
            e_c = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("🚀 نشر الإعلان"):
                sh.worksheet("exams").append_row([e_c, e_t, str(datetime.date.today()), ""])
                st.success("تم النشر")

    with menu[3]: # الإعدادات
        st.subheader("⚙️ أدوات التحكم المتقدمة")
        c_excel, c_auth = st.columns(2)
        with c_excel:
            st.info("📥 استيراد قاعدة بيانات الطلاب")
            up = st.file_uploader("ارفع ملف Excel", type="xlsx")
            if up and st.button("تأكيد الاستبدال النهائي"):
                new_df = pd.read_excel(up)
                sh.worksheet("students").update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم تحديث البيانات"); st.cache_data.clear(); st.rerun()
        with c_auth:
            if st.button("🧹 تصفير الكاش (تحديث فوري للمنصة)"): st.cache_data.clear(); st.rerun()

    with menu[4]:
        if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب الكاملة (المستقرة)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students"); df_g = fetch_safe("grades"); df_b = fetch_safe("behavior"); df_ex = fetch_safe("exams")
    s_id = str(st.session_state.sid)
    try:
        s_row = df_st[df_st.iloc[:, 0] == s_id].iloc[0]
        # الربط الذكي بأسماء الأعمدة لتفادي الإزاحة
        s_name = s_row['name'] if 'name' in s_row else s_row.iloc[1]
        p_col = "النقاط"
        raw_p = str(s_row[p_col]).strip() if p_col in s_row else "0"
        s_points = int(float(raw_p)) if raw_p.replace('.','',1).isdigit() else 0

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 20px; color: white; text-align: center;">
                <h2 style="color: white; margin: 0;">أهلاً بك يا بطل: {s_name}</h2>
                <div style="font-size: 28px; font-weight: bold; color: #f59e0b; margin-top:10px;">🏆 النقاط الحالية: {s_points}</div>
            </div>
        """, unsafe_allow_html=True)
        
        t_st = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال", "⚙️ الإعدادات", "🚗 خروج"])
        
        with t_st[1]: # درجاتي
            my_g = df_g[df_g.iloc[:, 0] == s_id]
            if not my_g.empty: st.dataframe(my_g, use_container_width=True, hide_index=True)
            else: st.info("لا توجد درجات مرصودة")
            
        with t_st[3]: # الأبطال
            df_st["النقاط"] = pd.to_numeric(df_st["النقاط"], errors='coerce').fillna(0)
            top = df_st.sort_values(by="النقاط", ascending=False).head(10)
            for i, row in top.iterrows():
                st.write(f"🏆 {row['name'] if 'name' in row else row.iloc[1]} - {int(row['النقاط'])} نقطة")

        with t_st[5]: # خروج
            if st.button("تسجيل الخروج الطالب"): st.session_state.role = None; st.rerun()
    except:
        st.error("بيانات الطالب غير موجودة أو هناك مشكلة في أعمدة الشيت.")
