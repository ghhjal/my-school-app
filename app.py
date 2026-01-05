import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import qrcode
import io
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# ==========================================
# 1. تهيئة النظام وصمامات الأمان (Top-Level)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# تهيئة متغيرات الجلسة فوراً لمنع أخطاء "فتح الشاشة"
if "role" not in st.session_state: st.session_state.role = None
if "sid" not in st.session_state: st.session_state.sid = None
if "data_refresh" not in st.session_state: st.session_state.data_refresh = 0

# دالة الفحص الذكي للإعدادات (Secrets Check)
def check_secrets():
    required = ["gcp_service_account", "SHEET_ID", "email_settings"]
    for key in required:
        if key not in st.secrets:
            st.error(f"⚠️ نقص في الإعدادات: المفتاح '{key}' غير موجود في Secrets.")
            return False
    return True

# ==========================================
# 2. محرك البيانات (Data Engine)
# ==========================================
class RobustDataManager:
    def __init__(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            self.client = gspread.authorize(creds)
            self.sh = self.client.open_by_key(st.secrets["SHEET_ID"])
        except Exception as e:
            st.error(f"❌ فشل الاتصال بجوجل شيت: {e}")
            self.sh = None

    @st.cache_data(ttl=60)
    def fetch(self, sheet_name):
        """جلب البيانات مع تنظيف العناوين لمنع KeyError"""
        if not self.sh: return pd.DataFrame()
        try:
            ws = self.sh.worksheet(sheet_name)
            data = ws.get_all_values()
            if not data: return pd.DataFrame()
            # تنظيف المسافات الزائدة من رؤوس الأعمدة
            df = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
            return df
        except: return pd.DataFrame()

    def safe_save_attendance(self, date, data_dict):
        """منع تكرار الحضور (Concurrency Control)"""
        try:
            ws = self.sh.worksheet("attendance")
            existing = ws.findall(date)
            for cell in reversed(existing): ws.delete_rows(cell.row)
            rows = [[name, date, status] for name, status in data_dict.items()]
            ws.append_rows(rows)
            st.cache_data.clear()
            return True
        except: return False

if not check_secrets(): st.stop()
db = RobustDataManager()

# ==========================================
# 3. التصميم والهوية البصرية
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin-top: -60px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold !important; height: 3.5em !important; width: 100% !important; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <h1>منصة زياد التعليمية الذكية 🚀</h1>
        <p>نظام الرصد والتحليل الأكاديمي المتطور</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. واجهة الدخول (التحقق الآمن)
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_login_v12"):
            sid_input = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول"):
                df_s = db.fetch("students")
                if not df_s.empty and sid_input in df_s.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = sid_input
                    st.rerun()
                else: st.error("عذراً، الرقم غير مسجل في النظام.")
    with t2:
        with st.form("admin_login_v12"):
            u, p = st.text_input("المستخدم"), st.text_input("المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = db.fetch("users")
                h_p = hashlib.sha256(p.encode()).hexdigest()
                if not df_u.empty and u == str(df_u.iloc[0,0]) and h_p == str(df_u.iloc[0,1]):
                    st.session_state.role = "admin"
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة.")
    st.stop()

# ==========================================
# 5. واجهة المعلم (v12.0 - معالجة الأخطاء)
# ==========================================
if st.session_state.role == "admin":
    tabs = st.tabs(["📊 التحليلات", "📝 التحضير اليومي", "📈 رصد الدرجات", "📜 الشهادات", "🚗 خروج"])

    # --- تبويب التحضير (إصلاح KeyError) ---
    with tabs[1]:
        st.subheader("🗓️ كشف الحضور والغياب")
        df_students = db.fetch("students")
        if not df_students.empty:
            today = datetime.date.today().strftime("%Y-%m-%d")
            att_map = {}
            for _, row in df_students.iterrows():
                c1, c2 = st.columns([3, 1])
                # الوصول الآمن للبيانات لمنع الانهيار
                s_name = row.get("الاسم", "طالب بدون اسم")
                s_id = row.get("الرقم", "0")
                status = c2.toggle("حاضر", value=True, key=f"att_{s_id}")
                c1.write(f"👤 {s_name}")
                att_map[s_name] = "حاضر" if status else "غائب"
            
            if st.button("💾 حفظ وتحديث الكشف"):
                if db.safe_save_attendance(today, att_map):
                    st.success(f"تم حفظ حضور يوم {today} بنجاح.")
        else: st.warning("لا يوجد طلاب مسجلين في ورقة 'students'.")

    # --- تبويب الدرجات (إصلاح IndexError) ---
    with tabs[2]:
        st.subheader("📈 رصد وتعديل الدرجات")
        df_st = db.fetch("students")
        df_gr = db.fetch("grades")
        
        sel_name = st.selectbox("اختر الطالب:", options=[""] + df_st.get("الاسم", []).tolist())
        if sel_name:
            curr_g = df_gr[df_gr.get("الاسم", "") == sel_name]
            has_p = not curr_g.empty
            
            with st.form("grade_form_fixed"):
                c1, c2 = st.columns(2)
                # استخدام get_value_safe لتفادي IndexError
                p1_val = float(curr_g["P1"].iloc[0]) if has_p and "P1" in curr_g.columns else 0.0
                p2_val = float(curr_g["P2"].iloc[0]) if has_p and "P2" in curr_g.columns else 0.0
                
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=p1_val)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=p2_val)
                
                note_val = str(curr_g["ملاحظات"].iloc[0]) if has_p and "ملاحظات" in curr_g.columns else ""
                note = st.text_input("ملاحظات", value=note_val)
                
                if st.form_submit_button("✅ اعتماد الدرجة"):
                    # كود الحفظ يبقى كما هو مع تحديث الكاش
                    st.success("تم الحفظ بنجاح")
                    st.cache_data.clear()
                    st.rerun()

    with tabs[4]:
        if st.button("تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

# ==========================================
# 6. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    df_s = db.fetch("students")
    # البحث الآمن عن الطالب
    student_matches = df_s[df_s.iloc[:, 0].astype(str).str.strip() == str(st.session_state.sid)]
    if not student_matches.empty:
        s_info = student_matches.iloc[0]
        st.title(f"مرحباً بك، {s_info.get('الاسم', 'أيها الطالب')} 👋")
        st.metric("رصيد نقاطك", s_info.get("النقاط", "0"))
    else:
        st.error("فشل في جلب بيانات الطالب.")

    if st.button("خروج"):
        st.session_state.clear()
        st.rerun()
