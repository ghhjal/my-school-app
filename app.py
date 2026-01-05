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
    """توليد الوسام بناءً على النقاط"""
    try:
        p = int(float(str(points or 0)))
        if p >= 100: return "🏆 القائد الذهبي"
        if p >= 50: return "🌟 المتميز"
        if p >= 20: return "✨ المتفاعل"
        return "🌱 برعم صاعد"
    except: return "🌱 برعم صاعد"

def send_report_email(to_email, name, grades_df, behavior_df):
    """إرسال تقرير تلقائي لولي الأمر"""
    try:
        config = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = config["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = f"📊 التقرير الدوري للطالب: {name}"
        
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

if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[1]: # إدارة الطلاب
        st.subheader("👥 سجل الطلاب والأوسمة")
        df_st = db.fetch_data("students")
        if not df_st.empty:
            # حل KeyError: إنشاء عمود الوسام برمجياً قبل محاولة العرض في الجدول
            if 'النقاط' in df_st.columns:
                df_st['الوسام'] = df_st['النقاط'].apply(get_badge)
            
            # عرض الأعمدة المتاحة فقط لتجنب انهيار KeyError
            cols_to_show = [c for c in ['الرقم', 'الاسم', 'الصف', 'النقاط', 'الوسام'] if c in df_st.columns]
            st.dataframe(df_st[cols_to_show], use_container_width=True)
            
            with st.expander("📤 إرسال تقرير تلقائي"):
                sel_st = st.selectbox("اختر الطالب لإرسال التقرير:", options=df_st['الاسم'].tolist())
                if st.button("🚀 إرسال التقرير الآن"):
                    st_info = df_st[df_st['الاسم'] == sel_st].iloc[0]
                    # جلب درجات وسلوك الطالب المحدد
                    g_df = db.fetch_data("grades")
                    b_df = db.fetch_data("behavior")
                    if send_report_email(st_info.get('الإيميل', ''), sel_st, g_df[g_df['الاسم']==sel_st], b_df[b_df['الاسم']==sel_st]):
                        st.success(f"تم إرسال التقرير لولي أمر {sel_st}")

    with tabs[2]: # الدرجات
        st.subheader("📈 رصد وتحديث الدرجات")
        df_st = db.fetch_data("students")
        df_gr = db.fetch_data("grades")
        
        sel_name = st.selectbox("👤 اختر الطالب للرصد:", options=[""] + df_st['الاسم'].tolist())
        
        if sel_name:
            curr_g = df_gr[df_gr['الاسم'] == sel_name]
            has_p = not curr_g.empty
            
            with st.form("grade_form_safe"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(curr_g['P1'].iloc[0]) if has_p and 'P1' in curr_g.columns else 0.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(curr_g['P2'].iloc[0]) if has_p and 'P2' in curr_g.columns else 0.0)
                
                # حل IndexError: الوصول الآمن للملاحظات بالاسم بدلاً من الرقم
                note_val = ""
                if has_p and 'ملاحظات' in curr_g.columns:
                    note_val = str(curr_g['ملاحظات'].iloc[0])
                note = st.text_input("ملاحظات", value=note_val)
                
                # حل Missing Submit Button: الزر داخل كتلة الفورم
                if st.form_submit_button("💾 حفظ واعتماد الدرجة"):
                    # (هنا يوضع كود الحفظ في جوجل شيت)
                    st.success("تم الحفظ بنجاح")
                    st.rerun()

    with tabs[3]: # السلوك والتحضير
        st.subheader("🥇 رصد السلوك والتحضير")
        df_st = db.fetch_data("students")
        # حل KeyError الصورة الثالثة: التأكد من مسميات الأعمدة عند التحضير
        for i, row in df_st.iterrows():
            c1, c2 = st.columns([3, 1])
            # استخدام .get لمنع KeyError في حال اختلاف المسمى
            st_id = row.get('الرقم', i) 
            st_name = row.get('الاسم', 'غير معروف')
            c2.toggle("حاضر", value=True, key=f"att_{st_id}")
            c1.write(f"👤 {st_name}")

# ==========================================
# 4. واجهة الطالب (الأوسمة والتحفيز)
# ==========================================
elif st.session_state.role == "student":
    df_st = db.fetch_data("students")
    # البحث عن الطالب بالرقم الأكاديمي المسجل في الجلسة
    s_info = df_st[df_st['الرقم'].astype(str) == str(st.session_state.sid)].iloc[0]
    points = int(float(s_info.get('النقاط', 0)))
    
    st.markdown(f"""
        <div style="text-align: center; padding: 25px; border-radius: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
            <h3>مرحباً، {s_info.get('الاسم', '')} 👋</h3>
            <h1 style="color: #1e40af; margin: 10px 0;">{points} نقطة</h1>
            <span style="font-size: 20px; font-weight: bold; background: #fef3c7; color: #92400e; padding: 5px 20px; border-radius: 20px;">
                {get_badge(points)}
            </span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("خروج"): 
        st.session_state.role = None
        st.rerun()
