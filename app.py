import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception:
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

# --- 2. نظام الدخول ---
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
                else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty:
            st.warning("⚠️ لا توجد بيانات طلاب")
            st.stop()
        
        t1, t2 = st.tabs(["🎭 رصد السلوك", "📝 رصد الدرجات"])
        
        with t2:
            st.subheader("تحديث درجات الطالب")
            df_g = fetch_safe("grades")
            target_name = st.selectbox("اختر الطالب لتعديل درجته", df_st.iloc[:, 1].tolist())
            
            # جلب القيم الحالية
            curr = df_g[df_g.iloc[:, 0] == target_name] if not df_g.empty else pd.DataFrame()
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)
            
            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1)
                f2 = c2.number_input("ف2", value=v2)
                wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث السجل"):
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target_name)
                        ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except:
                        ws_g.append_row([target_name, f1, f2, wrk])
                    st.success("✅ تم تحديث الدرجات")
                    time.sleep(1); st.rerun()

            # ✅ 1. جدول الدرجات في الأسفل (تمت إعادته)
            st.divider()
            st.subheader("📋 كشف الدرجات العام")
            st.dataframe(df_g, use_container_width=True, hide_index=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        col_add, col_del = st.columns([2, 1])
        
        with col_add:
            with st.form("add_student_full"):
                st.subheader("📝 إضافة طالب جديد")
                id_v = st.text_input("الرقم الأكاديمي")
                name_v = st.text_input("الاسم الثلاثي")
                c_cls, c_yr = st.columns(2)
                cls_v = c_cls.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
                yr_v = c_yr.text_input("العام", value="1446هـ")
                c_sub, c_lev = st.columns(2)
                sub_v = c_sub.text_input("المادة", value="اللغة الإنجليزية")
                lev_v = c_lev.selectbox("المرحلة", ["ابتدائي", "متوسط"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة"); time.sleep(1); st.rerun()

        with col_del:
            # ✅ 2. زر حذف كامل بيانات الطالب (تمت إضافته)
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اختر الطالب للحذف النهائي", [""] + df_st.iloc[:, 1].tolist())
            if st.button("تأكيد الحذف من كل السجلات"):
                if to_del:
                    # حذف من الطلاب، الدرجات، والسلوك
                    for s_name in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s_name)
                            cell = ws.find(to_del)
                            ws.delete_rows(cell.row)
                        except: pass
                    st.error(f"🗑️ تم حذف {to_del} نهائياً")
                    time.sleep(1); st.rerun()

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
