import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال الآمن ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

# دالة ذكية لجلب البيانات وحل مشكلة الأعمدة المكررة
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 0:
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"Column_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إصلاح شاشة السلوك والفلتر)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 سجل الطلاب")
        df_st = fetch_safe("students")
        # عرض الجدول بشكل صحيح بدون أخطاء حمراء
        st.dataframe(df_st, use_container_width=True, hide_index=True)

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والملاحظات")
        df_st = fetch_safe("students")
        
        with st.form("b_form"):
            c1, c2, c3 = st.columns(3)
            sb_name = c1.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            sb_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه"])
            sb_date = c3.date_input("التاريخ")
            sb_note = st.text_area("الملاحظة")
            if st.form_submit_button("إرسال الرصد"):
                # الحالة عند الرصد تكون دائماً "لم يتم القراءة"
                sh.worksheet("behavior").append_row([sb_name, str(sb_date), sb_type, sb_note, "لم يتم القراءة"])
                st.success("تم رصد السلوك بنجاح"); time.sleep(1); st.rerun()
        
        st.divider()
        st.subheader("🔍 استعراض الملاحظات مع الفلتر")
        # تفعيل الفلتر ليرتبط بالجدول
        all_students = ["عرض الكل"] + df_st.iloc[:, 1].unique().tolist()
        f_name = st.selectbox("فلترة حسب اسم الطالب", all_students)
        
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            if f_name != "عرض الكل":
                filtered_df = df_b[df_b.iloc[:, 0] == f_name]
            else:
                filtered_df = df_b
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (إصلاح زر الشكر والحالة)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h2 style='text-align:center;'>أهلاً بك يا بطل: {s_name} 👋</h2>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📊 درجاتي", "🎭 ملاحظاتي السلوكية"])
    
    with t2:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for i, row in my_b.iterrows():
                # التحقق من الحالة الحالية
                status = str(row.iloc[4]) if len(row) > 4 else "لم يتم القراءة"
                
                with st.container(border=True):
                    st.write(f"📅 **التاريخ:** {row.iloc[1]} | **النوع:** {row.iloc[2]}")
                    st.info(f"💬 {row.iloc[3]}")
                    
                    # منطق زر الشكر: يظهر فقط إذا لم يتم القراءة، ويختفي بعد الضغط
                    if "تمت القراءة" not in status:
                        if st.button(f"❤️ شكراً أستاذي (تأكيد القراءة)", key=f"btn_{i}"):
                            try:
                                ws_b = sh.worksheet("behavior")
                                all_v = ws_b.get_all_values()
                                # البحث عن الصف لتحديث الحالة في جوجل شيت
                                for idx, r in enumerate(all_v):
                                    if r[0] == s_name and r[3] == str(row.iloc[3]):
                                        ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                        st.success("تم إرسال الشكر!")
                                        time.sleep(1)
                                        st.rerun() # يختفي الزر فوراً بعد التحديث
                            except: st.error("عذراً، حدث خطأ في التحديث")
