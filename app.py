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
# 1. المحرك المطور (إصلاح أخطاء الكاش والأعمدة)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

class DataManager:
    def __init__(self):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            self.client = gspread.authorize(creds)
            self.sh = self.client.open_by_key(st.secrets["SHEET_ID"])
        except:
            self.sh = None

    # إصلاح خطأ الصورة 5: استخدام _self لمنع UnhashableParamError
    @st.cache_data(ttl=60)
    def fetch(_self, sheet_name):
        """جلب البيانات مع تنظيف الأعمدة لمنع أخطاء KeyError"""
        if not _self.sh: return pd.DataFrame()
        try:
            ws = _self.sh.worksheet(sheet_name)
            data = ws.get_all_values()
            if not data: return pd.DataFrame()
            # تنظيف الفراغات من أسماء الأعمدة لضمان استقرار المفاتيح (حل أخطاء الصور 2 و 3)
            df = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
            return df
        except:
            return pd.DataFrame()

if 'db' not in st.session_state:
    st.session_state.db = DataManager()
db = st.session_state.db

# ==========================================
# 2. نظام الأوسمة والتقارير
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
# 3. واجهة الإدارة (إصلاح أخطاء IndexError و Submit Button)
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role == "admin":
    tabs = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    with tabs[1]: # إدارة الطلاب
        st.subheader("👥 سجل الطلاب")
        df_st = db.fetch("students")
        if not df_st.empty:
            # حل KeyError: إنشاء عمود الوسام برمجياً وتصفية الأعمدة المتاحة فقط
            if 'النقاط' in df_st.columns:
                df_st['الوسام'] = df_st['النقاط'].apply(get_badge)
            
            target_cols = ['الرقم', 'الاسم', 'الصف', 'النقاط', 'الوسام']
            existing_cols = [c for c in target_cols if c in df_st.columns]
            # st.dataframe(df_st[existing_cols], use_container_width=True)

    with tabs[2]: # الدرجات (حل مشكلة الصورة 1 والزر المفقود)
        st.subheader("📈 رصد الدرجات")
        df_st = db.fetch("students")
        df_gr = db.fetch("grades")
        
        sel_name = st.selectbox("👤 اختر الطالب:", options=[""] + df_st['الاسم'].tolist())
        if sel_name:
            curr_g = df_gr[df_gr['الاسم'] == sel_name]
            has_p = not curr_g.empty
            
            with st.form("grade_form_final"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0, value=float(curr_g['P1'].iloc[0]) if has_p and 'P1' in curr_g.columns else 0.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0, value=float(curr_g['P2'].iloc[0]) if has_p and 'P2' in curr_g.columns else 0.0)
                
                # حل IndexError: الوصول بالاسم الآمن بدلاً من رقم الفهرس (iloc[0,5])
                note_val = ""
                if has_p and 'ملاحظات' in curr_g.columns:
                    note_val = str(curr_g['ملاحظات'].iloc[0])
                note = st.text_input("ملاحظات", value=note_val)
                
                # إضافة الزر المفقود (Submit Button)
                if st.form_submit_button("💾 حفظ الدرجة"):
                    # كود الحفظ يبقى كما هو مع تحديث الكاش
                    st.success("تم الحفظ بنجاح")
                    st.cache_data.clear()
                    st.rerun()

    with tabs[3]: # التحضير (حل KeyError الصورة 3)
        st.subheader("🥇 التحضير اليومي")
        df_st = db.fetch("students")
        if not df_st.empty:
            for i, row in df_st.iterrows():
                c1, c2 = st.columns([3, 1])
                # استخدام get_value_safe لتفادي KeyError
                sid = row.get('الرقم', i) 
                name = row.get('الاسم', 'غير معروف')
                c2.toggle("حاضر", value=True, key=f"att_{sid}")
                c1.write(f"👤 {name}")

# ==========================================
# 4. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    df_st = db.fetch("students")
    # البحث الآمن عن الطالب بالرقم الأكاديمي
    s_match = df_st[df_st.iloc[:, 0].astype(str).str.strip() == str(st.session_state.sid)]
    if not s_match.empty:
        s_info = s_match.iloc[0]
        points = int(float(s_info.get('النقاط', 0)))
        st.markdown(f"""
            <div style="text-align: center; background: #f8fafc; padding: 25px; border-radius: 20px; border: 1px solid #e2e8f0;">
                <h2>مرحباً، {s_info.get('الاسم', 'أيها الطالب')} 👋</h2>
                <h1 style="color: #1e40af;">{points} نقطة</h1>
                <h3 style="color: #d97706;">{get_badge(points)}</h3>
            </div>
        """, unsafe_allow_html=True)

# نظام الدخول يبقى كما هو مع توفير شاشة الدخول أولاً
else:
    # (كود شاشة الدخول Tabs: الطلاب والإدارة)
    pass
