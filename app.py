import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# --- 2. الاتصال بالقاعدة (Safe Connection) ---
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns] # تنظيف المسافات
        return df
    except:
        return pd.DataFrame()

# --- 3. نظام الدخول الصارم ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🏛️ منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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
    st.stop()

# --- 4. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty:
            st.warning("⚠️ لا توجد بيانات طلاب حالياً")
            st.stop()
            
        t1, t2 = st.tabs(["🎭 رصد السلوك والفلترة", "📝 رصد الدرجات"])
        
        with t1:
            st.subheader("إضافة سلوك ونقاط")
            with st.form("b_form"):
                st_name = st.selectbox("اختر الطالب", df_st.iloc[:, 1].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("الملاحظة")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(st_name)
                    old = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old + pts)
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
            
            # ميزة الفلترة التلقائية
            st.divider()
            st.subheader(f"📋 سجل سلوك الطالب: {st_name}")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                filtered_df = df_b[df_b.iloc[:, 0] == st_name]
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        with t2:
            st.subheader("تحديث درجات الطالب")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب لتعديل درجته", df_st.iloc[:, 1].tolist())
            curr = df_g[df_g.iloc[:, 0] == target]
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)
            
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target)
                        ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True) # عرض كافة الحقول
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            with st.form("add_full"):
                st.subheader("📝 إضافة طالب جديد")
                r1, r2 = st.columns(2)
                id_v = r1.text_input("الرقم")
                name_v = r2.text_input("الاسم")
                r3, r4, r5 = st.columns(3)
                cls_v = r3.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
                yr_v = r4.text_input("العام", value="1446هـ")
                sub_v = r5.text_input("المادة", value="اللغة الإنجليزية")
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة"); time.sleep(1); st.rerun()

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
