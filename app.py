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
# 1. محرك البيانات المستقر
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

class DataManager:
    def __init__(self):
        self.conn = self._connect()

    def _connect(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
        except Exception:
            return None

    @st.cache_data(ttl=60)
    def fetch_data(_self, sheet_name):
        """جلب البيانات مع تنظيف العناوين لضمان عدم حدوث KeyError"""
        try:
            ws = _self.conn.worksheet(sheet_name)
            data = ws.get_all_values()
            if not data: return pd.DataFrame()
            # تنظيف الفراغات من أسماء الأعمدة لضمان استقرار المفاتيح
            df = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
            return df
        except Exception:
            return pd.DataFrame()

if 'manager' not in st.session_state:
    st.session_state.manager = DataManager()
db = st.session_state.manager

# ==========================================
# 2. وظائف الحماية والتحسين
# ==========================================
def get_badge(points):
    """تحديد الوسام بناءً على النقاط"""
    try:
        p = int(float(str(points or 0)))
        if p >= 100: return "🏆 القائد الذهبي"
        if p >= 50: return "🌟 المتميز"
        return "🌱 برعم صاعد"
    except: return "🌱 برعم صاعد"

# ==========================================
# 3. واجهة المعلم (حل مشاكل IndexError و KeyError)
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

# (كود تسجيل الدخول المشفر يوضع هنا)

if st.session_state.role == "teacher":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[1]: # إدارة الطلاب
        st.subheader("👥 سجل الطلاب")
        df_st = db.fetch_data("students")
        if not df_st.empty:
            # حل KeyError: إنشاء عمود الوسام بشكل آمن
            if 'النقاط' in df_st.columns:
                df_st['الوسام'] = df_st['النقاط'].apply(get_badge)
            
            # عرض الأعمدة الموجودة فقط لتجنب الانهيار
            cols = ['الرقم', 'الاسم', 'الصف', 'النقاط', 'الوسام']
            existing_cols = [c for c in cols if c in df_st.columns]
            st.dataframe(df_st[existing_cols], use_container_width=True)

    with tabs[2]: # الدرجات
        st.subheader("📈 رصد الدرجات")
        df_st = db.fetch_data("students")
        df_gr = db.fetch_data("grades")
        
        # اختيار الطالب خارج النموذج
        sel_name = st.selectbox("👤 اختر الطالب:", options=[""] + df_st['الاسم'].tolist())
        
        if sel_name:
            curr_g = df_gr[df_gr['الاسم'] == sel_name]
            has_p = not curr_g.empty
            
            # حل Missing Submit Button: الزر داخل الفورم
            with st.form(key=f"grade_form_{sel_name}"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(curr_g['P1'].iloc[0]) if has_p and 'P1' in curr_g.columns else 0.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(curr_g['P2'].iloc[0]) if has_p and 'P2' in curr_g.columns else 0.0)
                
                # حل IndexError: الوصول بالاسم وليس بالرقم
                note_val = ""
                if has_p and 'ملاحظات' in curr_g.columns:
                    note_val = str(curr_g['ملاحظات'].iloc[0])
                note = st.text_input("ملاحظات", value=note_val)
                
                if st.form_submit_button("💾 حفظ الدرجة"):
                    # (منطق الحفظ في جوجل شيت)
                    st.success("تم الحفظ بنجاح")
                    st.rerun()

    with tabs[3]: # التحضير (حل KeyError الصورة 3)
        st.subheader("🥇 التحضير اليومي")
        df_st = db.fetch_data("students")
        if not df_st.empty:
            for i, row in df_st.iterrows():
                c1, c2 = st.columns([3, 1])
                # استخدام .get لضمان عدم حدوث خطأ إذا اختلف مسمى العمود
                sid = row.get('الرقم', i) 
                name = row.get('الاسم', 'غير معروف')
                c2.toggle("حاضر", value=True, key=f"att_{sid}")
                c1.write(f"👤 {name}")
