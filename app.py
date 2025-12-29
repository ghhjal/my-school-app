import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

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

# --- 2. التنسيق البصري ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. واجهة المعلم (تم إضافة ميزة الفلترة) ---
if 'role' in st.session_state and st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty: st.warning("لا يوجد طلاب"); st.stop()
        
        name_col = df_st.columns[1]
        t1, t2 = st.tabs(["🎭 رصد السلوك", "📝 رصد الدرجات"])
        
        with t1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            with st.form("b_form"):
                st.subheader("إضافة سلوك ونقاط تميز")
                # اختيار الطالب (سيستخدم للفلترة أيضاً)
                st_name = st.selectbox("اختر الطالب", df_st[name_col].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("الملاحظة")
                if st.form_submit_button("حفظ ورصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(st_name)
                    old = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old + pts)
                    st.success("تم الرصد"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- ميزة الفلترة التلقائية بناءً على الاختيار ---
            st.subheader(f"📋 سجل سلوك الطالب: {st_name}")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                # فلترة الجدول ليظهر فقط الطالب المختار في القائمة أعلاه [طلب المستخدم]
                filtered_df = df_b[df_b.iloc[:, 0] == st_name]
                if not filtered_df.empty:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                else:
                    st.info("لا يوجد سجل سلوك لهذا الطالب حتى الآن")

        with t2:
            st.subheader("تحديث الدرجات")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب للتعديل", df_st[name_col].tolist())
            # إصلاح الخطأ البرمجي في جلب الدرجات
            curr = df_g[df_g.iloc[:,0] == target]
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)

            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث السجل"):
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target)
                        ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            st.dataframe(df_g, use_container_width=True)

# --- واجهة الطالب (إصلاح خطأ العرض) ---
elif 'role' in st.session_state and st.session_state.role == "student":
    df_st = fetch_safe("students")
    me = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.header(f"🎓 الطالب: {me.iloc[1]}")
    st.metric("رصيد التميز 🌟", f"{me.iloc[8]} نقطة")
    
    st.subheader("📊 تقرير الدرجات")
    df_grades = fetch_safe("grades")
    # حل مشكلة UndefinedVariableError باستخدام الفلترة المباشرة
    student_grades = df_grades[df_grades.iloc[:, 0] == me.iloc[1]]
    st.dataframe(student_grades, use_container_width=True, hide_index=True)
