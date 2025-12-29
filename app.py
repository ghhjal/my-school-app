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
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        return pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
    except: return pd.DataFrame()

# --- 2. إدارة الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🏛️ دخول منصة الأستاذ زياد")
    role_choice = st.radio("نوع الدخول", ["معلم", "طالب"], horizontal=True)
    if role_choice == "معلم":
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    else:
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and sid in df_st['الرقم'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])

    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_data("students")
        tab1, tab2 = st.tabs(["🎭 السلوك والتحفيز", "📝 رصد الدرجات"])

        with tab1:
            st.subheader("رصد السلوك")
            with st.form("behavior_form"):
                st_name = st.selectbox("اسم الطالب", df_st['الاسم'].tolist())
                b_type = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("ملاحظة")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    # تحديث النقاط
                    ws = sh.worksheet("students"); cell = ws.find(st_name)
                    old_pts = int(ws.cell(cell.row, 9).value or 0)
                    ws.update_cell(cell.row, 9, old_pts + pts)
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
            
            st.dataframe(fetch_data("behavior"), use_container_width=True)

        with tab2:
            st.subheader("تحديث الدرجات")
            df_grades = fetch_data("grades")
            target_st = st.selectbox("اختر الطالب لتعديل درجته", df_st['الاسم'].tolist())
            
            # جلب البيانات الحالية خارج النموذج لمنع أخطاء ValueError
            current = df_grades[df_grades['الطالب'] == target_st]
            v1 = float(current.iloc[0]['ف1']) if not current.empty else 0.0
            v2 = float(current.iloc[0]['ف2']) if not current.empty else 0.0
            v3 = float(current.iloc[0]['مشاركة']) if not current.empty else 0.0

            with st.form("grade_edit"):
                c1, c2, c3 = st.columns(3)
                nf1 = c1.number_input("ف1", value=v1)
                nf2 = c2.number_input("ف2", value=v2)
                nwrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث السجل"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(target_st)
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[nf1, nf2, nwrk]])
                    except:
                        ws_g.append_row([target_st, nf1, nf2, nwrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            
            st.dataframe(df_grades, use_container_width=True)

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    df_st = fetch_data("students")
    me = df_st[df_st['الرقم'].astype(str) == st.session_state.sid].iloc[0]
    st.header(f"أهلاً بك: {me['الاسم']}")
    st.metric("نقاط التميز 🌟", f"{me['النقاط']} نقطة")
    
    st.subheader("درجاتك")
    df_g = fetch_data("grades")
    st.dataframe(df_g[df_g['الطالب'] == me['الاسم']], hide_index=True)
