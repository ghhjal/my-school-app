import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# --- 2. الاتصال الآمن بالقاعدة ---
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
        data = ws.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 3. التنسيق (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; direction: rtl; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border-top: 4px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. نظام الدخول (إصلاح الشاشة البيضاء) ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🏛️ منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col_in = st.columns([1, 2, 1])[1]
    with col_in:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        choice = st.radio("نوع الدخول", ["معلم", "طالب"], horizontal=True)
        if choice == "معلم":
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if pwd == "1234":
                    st.session_state.role = "teacher"
                    st.rerun()
        else:
            sid = st.text_input("الرقم الأكاديمي")
            if st.button("دخول الطالب"):
                df_st = fetch_safe("students")
                if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid)
                    st.rerun()
                else: st.error("الرقم غير مسجل")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty:
            st.warning("⚠️ جدول الطلاب فارغ حالياً")
            st.stop()
        
        name_col = df_st.columns[1]
        t1, t2 = st.tabs(["🎭 رصد السلوك", "📝 رصد الدرجات"])
        
        with t1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            with st.form("behavior_form"):
                st.subheader("إضافة سلوك")
                st_name = st.selectbox("اختر الطالب", df_st[name_col].tolist())
                b_type = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("الملاحظة")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(st_name)
                    old_p = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old_p + pts)
                    st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- ميزة الفلترة الذكية (طلبك الأخير) ---
            st.subheader(f"📋 سجل سلوك: {st_name}")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                # الفلترة بناءً على اختيار الطالب في القائمة أعلاه
                filtered_b = df_b[df_b.iloc[:, 0] == st_name]
                st.dataframe(filtered_b, use_container_width=True, hide_index=True)

        with t2:
            st.subheader("تحديث الدرجات")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب للتعديل", df_st[name_col].tolist())
            curr = df_g[df_g.iloc[:, 0] == target] if not df_g.empty else pd.DataFrame()
            
            # جلب القيم الحالية بأمان
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)

            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("🔄 تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        fnd = ws_g.find(target); ws_g.update(f'B{fnd.row}:D{fnd.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            st.dataframe(df_g, use_container_width=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # (بقية كود الإضافة والحذف...)
        if st.sidebar.button("خروج"):
            st.session_state.role = None; st.rerun()

# --- 6. واجهة الطالب (إصلاح خطأ UndefinedVariable) ---
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    me = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.markdown(f"<div class='card'><h2>🎓 الطالب: {me.iloc[1]}</h2></div>", unsafe_allow_html=True)
    st.metric("نقاط التميز 🌟", f"{me.iloc[8]} نقطة")
    
    st.subheader("📊 درجاتك")
    df_grades = fetch_safe("grades")
    if not df_grades.empty:
        # استخدام الفلترة المباشرة لمنع الخطأ الأحمر
        my_g = df_grades[df_grades.iloc[:, 0] == me.iloc[1]]
        st.dataframe(my_g, use_container_width=True, hide_index=True)
