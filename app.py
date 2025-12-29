import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

# --- الاتصال بالقاعدة ---
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

# --- واجهة المعلم ---
if 'role' in st.session_state and st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        t1, t2 = st.tabs(["🎭 رصد السلوك", "📝 رصد الدرجات"])
        
        with t2:
            st.subheader("تحديث درجات الطالب")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب لتعديل درجته", df_st.iloc[:, 1].tolist())
            
            # عرض حقول التعديل
            curr = df_g[df_g.iloc[:, 0] == target] if not df_g.empty else pd.DataFrame()
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)
            
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target); ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            
            # 1️⃣ استعادة جدول الدرجات في الأسفل (المطلب الأول)
            st.divider()
            st.subheader("📋 جدول الدرجات العام")
            if not df_g.empty:
                st.dataframe(df_g, use_container_width=True, hide_index=True)
            else:
                st.info("لا توجد درجات مرصودة حالياً")

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        col_add, col_del = st.columns([2, 1.2])
        
        with col_add: # شاشة الإضافة
            with st.form("add_student"):
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

        with col_del: # 2️⃣ إضافة ميزة حذف الطالب (المطلب الثاني)
            st.subheader("🗑️ حذف طالب نهائياً")
            to_delete = st.selectbox("اختر الطالب المراد حذفه", [""] + df_st.iloc[:, 1].tolist())
            if to_delete:
                st.warning(f"سيتم حذف {to_delete} من جميع السجلات!")
                if st.button("تأكيد الحذف النهائي"):
                    # حذف من جدول الطلاب
                    ws_s = sh.worksheet("students"); c_s = ws_s.find(to_delete)
                    ws_s.delete_rows(c_s.row)
                    # حذف من جدول الدرجات (اختياري)
                    try:
                        ws_g = sh.worksheet("grades"); c_g = ws_g.find(to_delete)
                        ws_g.delete_rows(c_g.row)
                    except: pass
                    # حذف من جدول السلوك (اختياري)
                    try:
                        ws_b = sh.worksheet("behavior")
                        cells = ws_b.findall(to_delete)
                        for cell in reversed(cells): ws_b.delete_rows(cell.row)
                    except: pass
                    st.error("تم حذف الطالب وكافة بياناته"); time.sleep(1); st.rerun()
