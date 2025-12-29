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
        # تنظيف أسماء الأعمدة من الفراغات الزائدة لتجنب KeyError
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🏛️ دخول منصة الأستاذ زياد")
    choice = st.radio("الدخول كـ", ["معلم", "طالب"], horizontal=True)
    if choice == "معلم":
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    else:
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])
    
    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        # التحقق من وجود عمود الاسم لتجنب انهيار التطبيق
        name_col = "الاسم" if "الاسم" in df_st.columns else df_st.columns[1]
        
        t1, t2 = st.tabs(["🎭 السلوك والتحفيز", "📝 رصد الدرجات"])
        
        with t1:
            st.subheader("رصد السلوك")
            with st.form("b_form"):
                st_name = st.selectbox("اسم الطالب", df_st[name_col].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("الملاحظة")
                submit_b = st.form_submit_button("حفظ الرصد") # التأكد من وجود الزر
                if submit_b:
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(st_name)
                    # تحديث النقاط في العمود التاسع
                    old = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old + pts)
                    st.success("تم الرصد"); time.sleep(1); st.rerun()
            st.dataframe(fetch_safe("behavior"), use_container_width=True)

        with t2:
            st.subheader("تحديث الدرجات (بدون تكرار)")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب للتعديل", df_st[name_col].tolist())
            
            # جلب القيم الحالية بدقة
            curr = df_g[df_g.iloc[:,0] == target]
            v1 = float(curr.iloc[0,1]) if not curr.empty else 0.0
            v2 = float(curr.iloc[0,2]) if not curr.empty else 0.0
            v3 = float(curr.iloc[0,3]) if not curr.empty else 0.0

            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1)
                f2 = c2.number_input("ف2", value=v2)
                wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("تحديث السجل"): # حل مشكلة الزر المفقود
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target)
                        ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except:
                        ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            st.dataframe(df_g, use_container_width=True)

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    me = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.header(f"أهلاً بك: {me.iloc[1]}")
    st.metric("نقاط التميز 🌟", f"{me.iloc[8]} نقطة")
    
    st.subheader("تقرير الدرجات")
    df_g = fetch_safe("grades")
    st.dataframe(df_g[df_g.iloc[:,0] == me.iloc[1]], hide_index=True)
