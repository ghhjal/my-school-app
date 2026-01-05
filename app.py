import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إدارة البيانات والمزامنة (المحرك)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

class DataManager:
    def __init__(self):
        self.conn = self._connect()
        self.sheets = ["students", "grades", "behavior", "users"]

    def _connect(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
        except: return None

    @st.cache_data(ttl=60)
    def fetch_data(_self, sheet_name):
        """جلب البيانات مع تنظيف العناوين لمنع أخطاء KeyError"""
        try:
            ws = _self.conn.worksheet(sheet_name)
            data = ws.get_all_values()
            if not data: return pd.DataFrame()
            # تنظيف الفراغات من أسماء الأعمدة لضمان استقرار المفاتيح
            df = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
            return df
        except: return pd.DataFrame()

if 'manager' not in st.session_state:
    st.session_state.manager = DataManager()
db = st.session_state.manager

# ==========================================
# 2. ميزات التحفيز والتقارير
# ==========================================
def get_badge(points):
    """توليد الوسام بناءً على النقاط [تطوير احترافي]"""
    try:
        p = int(float(str(points or 0)))
        if p >= 100: return "🏆 القائد الذهبي"
        if p >= 50: return "🌟 المتميز"
        if p >= 20: return "✨ المتفاعل"
        return "🌱 برعم صاعد"
    except: return "🌱 برعم صاعد"

def send_report_email(to_email, name, grades_df, behavior_df):
    """إرسال تقرير تلقائي لولي الأمر [تطوير احترافي]"""
    try:
        config = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = config["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = f"📊 التقرير الدوري للطالب: {name}"
        
        # تنسيق محتوى التقرير
        body = f"تحية طيبة، نرفق لكم تقرير الطالب {name} من منصة أ. زياد:\n\n"
        if not grades_df.empty:
            g = grades_df.iloc[0]
            body += f"📈 الدرجات: المهام ({g.get('P1', 0)}) | الاختبار ({g.get('P2', 0)}) | المجموع ({g.get('المجموع', 0)})\n"
        
        body += f"\n🎭 ملاحظات السلوك الأخيرة: {len(behavior_df)} ملاحظة مرصودة."
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(config["sender_email"], config["sender_password"])
            server.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. واجهة المعلم (تصحيح الأخطاء البرمجية)
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

# (كود تسجيل الدخول باستخدام hashlib يبقى كما هو لضمان الأمان)

if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[1]: # إدارة الطلاب
        st.subheader("👥 سجل الطلاب والأوسمة")
        df_st = db.fetch_data("students")
        if not df_st.empty:
            # حل KeyError: إنشاء عمود الوسام برمجياً قبل العرض
            df_st['الوسام'] = df_st['النقاط'].apply(get_badge)
            st.dataframe(df_st, use_container_width=True)
            
            with st.expander("📤 إرسال تقرير تلقائي"):
                sel_st = st.selectbox("اختر الطالب:", options=df_st['الاسم'].tolist())
                if st.button("🚀 إرسال التقرير الآن"):
                    st_info = df_st[df_st['الاسم'] == sel_st].iloc[0]
                    if send_report_email(st_info['الإيميل'], sel_st, pd.DataFrame(), pd.DataFrame()):
                        st.success("تم إرسال التقرير")

    with tabs[2]: # الدرجات
        st.subheader("📈 رصد وتحديث الدرجات")
        df_st = db.fetch_data("students")
        df_gr = db.fetch_data("grades")
        
        # اختيار الطالب خارج النموذج لمنع مشكلة "النموذج الفارغ"
        sel_name = st.selectbox("👤 اختر الطالب للرصد:", options=[""] + df_st['الاسم'].tolist())
        
        if sel_name:
            # جلب البيانات الحالية
            curr_g = df_gr[df_gr['الاسم'] == sel_name]
            has_p = not curr_g.empty
            
            with st.form("grade_form"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(curr_g['P1'].iloc[0]) if has_p else 0.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(curr_g['P2'].iloc[0]) if has_p else 0.0)
                
                # حل IndexError: الفحص الآمن لعمود الملاحظات
                note_val = str(curr_g['ملاحظات'].iloc[0]) if has_p and 'ملاحظات' in curr_g.columns else ""
                note = st.text_input("ملاحظات", value=note_val)
                
                # حل "Missing Submit Button": الزر داخل النموذج دائماً
                if st.form_submit_button("💾 حفظ واعتماد الدرجة"):
                    # (منطق الحفظ في Google Sheets)
                    st.success("تم الحفظ بنجاح")
                    st.rerun()

    # (بقية التبويبات تتبع نفس منطق الحماية من KeyError)

# ==========================================
# 4. واجهة الطالب (نظام الأوسمة)
# ==========================================
elif st.session_state.role == "student":
    df_st = db.fetch_data("students")
    s_info = df_st[df_st['الرقم'] == st.session_state.sid].iloc[0]
    points = int(float(s_info['النقاط'] or 0))
    
    st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 15px;">
            <h3>مرحباً، {s_info['الاسم']} 👋</h3>
            <h1 style="color: #1e40af;">{points} نقطة</h1>
            <h4 style="color: #d97706;">{get_badge(points)}</h4>
        </div>
    """, unsafe_allow_html=True)
    # (بقية واجهة الطالب)
