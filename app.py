import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import urllib.parse
import io
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إعدادات المحرك وإدارة البيانات
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية v3.0", layout="wide")

class DataManager:
    """فئة لإدارة الاتصال والبيانات لضمان الاستقرار ومنع أخطاء الفهرسة"""
    def __init__(self):
        self.conn = self._connect()
        self.sheets = ["students", "grades", "behavior", "users", "exams"]

    def _connect(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
        except Exception:
            return None

    def load_all_to_state(self, force=False):
        """تحميل البيانات للذاكرة لتقليل ضغط الـ API"""
        if 'data_loaded' not in st.session_state or force:
            with st.spinner("جاري مزامنة البيانات..."):
                for sheet in self.sheets:
                    try:
                        ws = self.conn.worksheet(sheet)
                        data = ws.get_all_values()
                        if data:
                            st.session_state[f"df_{sheet}"] = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
                        else:
                            st.session_state[f"df_{sheet}"] = pd.DataFrame()
                    except:
                        st.session_state[f"df_{sheet}"] = pd.DataFrame()
                st.session_state.data_loaded = True

    def get_df(self, name):
        return st.session_state.get(f"df_{name}", pd.DataFrame())

    def update_record(self, sheet_name, unique_val, new_row_data, id_col_idx=0):
        try:
            ws = self.conn.worksheet(sheet_name)
            cells = ws.col_values(id_col_idx + 1)
            try:
                row_idx = cells.index(str(unique_val)) + 1
                ws.update(f"A{row_idx}", [new_row_data])
            except ValueError:
                ws.append_row(new_row_data)
            self.load_all_to_state(force=True)
            return True
        except: return False

if 'manager' not in st.session_state: st.session_state.manager = DataManager()
db = st.session_state.manager
db.load_all_to_state()

# ==========================================
# 2. ميزات إضافية: الأوسمة والتقارير التلقائية
# ==========================================
def get_badge(points):
    """تحديد الوسام برمجياً بناءً على النقاط لمنع أخطاء KeyError"""
    try:
        p = int(float(str(points or 0)))
        if p >= 100: return "🏆 القائد الذهبي"
        if p >= 50: return "🌟 الطالب المتميز"
        if p >= 20: return "✨ المتفاعل"
        if p < 0: return "⚠️ يحتاج توجيه"
        return "🌱 برعم صاعد"
    except: return "🌱 برعم صاعد"

def send_detailed_report(to_email, s_name, grade_df, beh_df):
    """إرسال تقرير HTML احترافي لولي الأمر عبر الإيميل"""
    try:
        conf = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = conf["sender_email"]; msg['To'] = to_email
        msg['Subject'] = f"📊 تقرير الأداء للطالب: {s_name}"
        
        # بناء محتوى التقرير
        grade_info = "لا توجد درجات مرصودة حالياً."
        if not grade_df.empty:
            g = grade_df.iloc[0]
            grade_info = f"المهام: {g[1]} | الاختبار: {g[2]} | المجموع: {g[3]}"

        body = f"""
        <div dir="rtl" style="font-family: 'Cairo', sans-serif; text-align: right;">
            <h2 style="color: #1e40af;">التقرير الشهري للطالب: {s_name}</h2>
            <hr>
            <h3>📈 السجل الأكاديمي:</h3>
            <p>{grade_info}</p>
            <h3>🎭 سجل السلوك:</h3>
            <p>عدد الملاحظات المرصودة: {len(beh_df)}</p>
            <hr>
            <p style="font-size: 12px; color: gray;">منصة الأستاذ زياد الذكية - نظام التقارير التلقائي</p>
        </div>
        """
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(conf["sender_email"], conf["sender_password"])
            s.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. الواجهة والتصميم (The View)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin-top: -60px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold !important; height: 3em !important; width: 100% !important; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <h1 style="margin:0;">منصة زياد الذكية v3.0</h1>
        <p>نظام رصد الدرجات والسلوك المطور</p>
    </div>
""", unsafe_allow_html=True)

# إدارة الدخول
if "role" not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطالب", "🔐 الإدارة"])
    with t1:
        with st.form("st_login_form"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول للمنصة"):
                df_st = db.get_df("students")
                if not df_st.empty and sid in df_st.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("admin_login_form"):
            u, p = st.text_input("اسم المستخدم"), st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df_u = db.get_df("users")
                if not df_u.empty and u == df_u.iloc[0,0] and hashlib.sha256(p.encode()).hexdigest() == df_u.iloc[0,1]:
                    st.session_state.role = "teacher"; st.rerun()
                else: st.error("بيانات خاطئة")
    st.stop()

# ==========================================
# 4. واجهة المعلم (حل مشاكل KeyError و IndexError)
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[0]: # الإحصائيات
        df_s = db.get_df("students")
        st.metric("إجمالي الطلاب المسجلين", len(df_s))
        if not df_s.empty:
            df_s['pts'] = pd.to_numeric(df_s.iloc[:, 8], errors='coerce').fillna(0)
            st.write("🏆 أوائل المنصة حسب النقاط والأوسمة:")
            for _, r in df_s.nlargest(5, 'pts').iterrows():
                st.write(f"• {r[1]} - {int(r['pts'])} نقطة ({get_badge(r['pts'])})")

    with tabs[1]: # الطلاب والتقارير التلقائية
        st.subheader("👥 إدارة الطلاب")
        df_st = db.get_df("students")
        if not df_st.empty:
            # إضافة عمود الأوسمة ديناميكياً لتجنب KeyError
            df_st['الوسام'] = df_st.iloc[:, 8].apply(get_badge)
            st.dataframe(df_st, use_container_width=True)
            
            with st.expander("📤 إرسال تقرير تلقائي لولي الأمر"):
                sel_st = st.selectbox("اختر الطالب لإرسال تقريره الأكاديمي:", options=df_st.iloc[:, 1].tolist())
                if st.button("🚀 إرسال التقرير الآن"):
                    s_info = df_st[df_st.iloc[:, 1] == sel_st].iloc[0]
                    g_info = db.get_df("grades"); g_info = g_info[g_info.iloc[:, 0] == sel_st]
                    b_info = db.get_df("behavior"); b_info = b_info[b_info.iloc[:, 0] == sel_st]
                    if send_detailed_report(s_info.iloc[6], sel_st, g_info, b_info):
                        st.success(f"تم إرسال التقرير بنجاح لولي أمر {sel_st}")
                    else: st.error("فشل الإرسال، تحقق من إعدادات الإيميل")

    with tabs[2]: # الدرجات (حل IndexError و Missing Submit Button)
        st.subheader("📈 رصد وتعديل الدرجات")
        df_s = db.get_df("students"); df_g = db.get_df("grades")
        sel_name = st.selectbox("👤 اختر الطالب:", options=[""] + df_s.iloc[:, 1].tolist())
        
        if sel_name:
            curr_g = df_g[df_g.iloc[:, 0] == sel_name]
            has_p = not curr_g.empty
            with st.form(key=f"grade_form_{sel_name}"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(curr_g.iloc[0,1]) if has_p else 0.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(curr_g.iloc[0,2]) if has_p else 0.0)
                # حل IndexError: الفحص الآمن قبل الوصول للفهرس 5
                note_val = str(curr_g.iloc[0, 5]) if has_p and curr_g.shape[1] > 5 else ""
                note = st.text_input("ملاحظات", value=note_val)
                # حل Missing Submit Button
                if st.form_submit_button("💾 حفظ الدرجة"):
                    new_row = [sel_name, p1, p2, p1+p2, str(datetime.date.today()), note]
                    if db.update_record("grades", sel_name, new_row):
                        st.success("تم الحفظ بنجاح"); st.rerun()

    with tabs[4]: # خروج
        if st.button("تسجيل الخروج من الإدارة"): st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب (نظام الأوسمة التحفيزي)
# ==========================================
elif st.session_state.role == "student":
    df_st = db.get_df("students")
    s_id = str(st.session_state.sid)
    s_data = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
    points = int(float(str(s_data.iloc[8] or 0)))
    
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #e2e8f0;">
            <h3>مرحباً، {s_data.iloc[1]} 👋</h3>
            <h1 style="color: #1e40af; margin: 10px 0;">{points} نقطة</h1>
            <span style="font-size: 20px; font-weight: bold; background: #fef3c7; color: #92400e; padding: 5px 20px; border-radius: 20px;">
                {get_badge(points)}
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()
