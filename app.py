import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال الآمن ---
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
        data = ws.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state: st.session_state.role = "teacher"

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty: 
            st.warning("⚠️ جدول الطلاب فارغ"); st.stop()
        
        tab_b, tab_g = st.tabs(["🎭 رصد السلوك والفلترة", "📝 رصد الدرجات"])
        
        with tab_b:
            st.subheader("🎭 إضافة سلوك جديد")
            with st.form("b_form"):
                # اختيار الطالب للرصد وللفلترة
                target_st = st.selectbox("اختر الطالب", df_st.iloc[:, 1].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("الملاحظة")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([target_st, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(target_st)
                    old = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old + pts)
                    st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()
            
            # ميزة الفلترة التلقائية
            st.divider()
            st.subheader(f"📋 سجل سلوك الطالب: {target_st}")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                filtered_b = df_b[df_b.iloc[:, 0] == target_st]
                st.dataframe(filtered_b, use_container_width=True, hide_index=True)

        with tab_g:
            st.subheader("📝 تحديث الدرجات")
            df_g = fetch_safe("grades")
            target_g = st.selectbox("الطالب للتعديل", df_st.iloc[:, 1].tolist())
            curr = df_g[df_g.iloc[:, 0] == target_g] if not df_g.empty else pd.DataFrame()
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)
            
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث الدرجة"):
                    ws_g = sh.worksheet("grades")
                    try:
                        fnd = ws_g.find(target_g); ws_g.update(f'B{fnd.row}:D{fnd.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target_g, f1, f2, wrk])
                    st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
            
            # إعادة جدول الدرجات في الأسفل
            st.divider()
            st.subheader("📋 كشف الدرجات العام")
            st.dataframe(df_g, use_container_width=True, hide_index=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        col_del, col_add = st.columns([1, 2])
        
        with col_del: # زر الحذف الشامل
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
            if st.button("تأكيد الحذف النهائي"):
                if to_del:
                    for sheet in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(sheet); cell = ws.find(to_del)
                            ws.delete_rows(cell.row)
                        except: pass
                    st.error(f"🗑️ تم حذف {to_del}"); time.sleep(1); st.rerun()
        
        with col_add: # شاشة الإضافة بكافة الحقول
            with st.form("add_st"):
                st.subheader("📝 إضافة طالب")
                id_v = st.text_input("الرقم")
                name_v = st.text_input("الاسم")
                cls_v = st.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
                sub_v = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("إضافة"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, "1446هـ", sub_v, "ابتدائي", "", "", 0])
                    st.success("تمت الإضافة"); time.sleep(1); st.rerun()
