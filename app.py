import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد التعليمية", layout="wide", initial_sidebar_state="expanded")

# تحسين المظهر العام عبر CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. إدارة الدخول ---
if 'role' not in st.session_state: st.session_state.role = "teacher"

# --- 3. واجهة المعلم المنسقة ---
if st.session_state.role == "teacher":
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("انتقل إلى:", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        st.markdown("## 📈 رصد الدرجات والتحفيز")
        df_st = fetch_safe("students")
        if df_st.empty: st.warning("⚠️ لا يوجد طلاب مسجلين"); st.stop()
        
        tab_b, tab_g = st.tabs(["🎭 سجل السلوك والتميز", "📝 رصد الدرجات"])
        
        with tab_b:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("🖋️ رصد جديد")
                with st.form("b_form", clear_on_submit=True):
                    t_st = st.selectbox("اختر الطالب", df_st['name'].tolist())
                    b_type = st.radio("نوع التأثير", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    note = st.text_input("ملاحظة تفصيلية")
                    if st.form_submit_button("اعتماد الرصد"):
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        sh.worksheet("behavior").append_row([t_st, str(datetime.now().date()), b_type, note])
                        ws_st = sh.worksheet("students"); c = ws_st.find(t_st)
                        old = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old + pts)
                        st.success("تم الحفظ"); time.sleep(0.5); st.rerun()
            
            with col2:
                st.subheader(f"📋 سجل: {t_st}")
                df_b = fetch_safe("behavior")
                if not df_b.empty:
                    st.dataframe(df_b[df_b.iloc[:, 0] == t_st], use_container_width=True, hide_index=True)

    elif menu == "👥 إدارة الطلاب":
        st.markdown("## 👥 إدارة البيانات الأساسية")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        c_del, c_add = st.columns([1, 2.5])
        
        with c_del:
            st.subheader("🗑️ حذف نهائي")
            to_del = st.selectbox("الطالب المراد حذفه", [""] + df_st['name'].tolist())
            if st.button("❌ تأكيد الحذف الشامل"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del)
                            ws.delete_rows(cell.row)
                        except: pass
                    st.success("تم الحذف"); time.sleep(0.5); st.rerun()

        with c_add:
            st.subheader("📝 إضافة طالب جديد (بيانات كاملة)")
            with st.form("add_full_st", clear_on_submit=True):
                r1_c1, r1_c2 = st.columns(2)
                id_v = r1_c1.text_input("الرقم الأكاديمي")
                name_v = r1_c2.text_input("الاسم الثلاثي")
                
                r2_c1, r2_c2, r2_c3 = st.columns(3)
                # إضافة كافة الصفوف والمراحل كما طلبت
                cls_v = r2_c1.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                year_v = r2_c2.text_input("العام الدراسي", value="1446هـ")
                lev_v = r2_c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                
                sub_v = st.text_input("المادة الدراسية", value="اللغة الإنجليزية")
                
                if st.form_submit_button("➕ إضافة الطالب إلى القاعدة"):
                    # ترتيب الأعمدة: id, name, class, year, sem(المادة), lev(المرحلة), email, mobile, points
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, year_v, sub_v, lev_v, "", "", 0])
                    st.success("✅ تمت إضافة الطالب بنجاح"); time.sleep(0.5); st.rerun()
