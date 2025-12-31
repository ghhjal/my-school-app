import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=2)
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
        data = ws.get_all_values()
        if len(data) > 1:
            # حل جذري لمشكلة Duplicate column names
            raw_headers = data[0]
            headers = []
            for i, h in enumerate(raw_headers):
                new_h = h.strip() if h.strip() else f"col_{i}"
                if new_h in headers: new_h = f"{new_h}_{i}"
                headers.append(new_h)
            df = pd.DataFrame(data[1:], columns=headers)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        if st.text_input("كلمة المرور", type="password") == "1234":
            if st.button("دخول المعلم"): st.session_state.role = "teacher"; st.rerun()
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
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    if menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والملاحظات")
        df_st = fetch_safe("students")
        with st.form("b_form"):
            c1, c2 = st.columns(2)
            sb_name = c1.selectbox("اختر الطالب للرصد", [""] + df_st.iloc[:, 1].tolist())
            sb_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه", "أخرى"])
            sb_date = st.date_input("تاريخ الملاحظة")
            sb_note = st.text_area("نص الملاحظة")
            if st.form_submit_button("إرسال الرصد"):
                # الحالة الافتراضية هي "⏳ لم يتم القراءة"
                sh.worksheet("behavior").append_row([sb_name, str(sb_date), sb_type, sb_note, "⏳ لم يتم القراءة"])
                st.success("تم الرصد بنجاح"); st.rerun()
        
        st.divider()
        st.subheader("🔍 استعراض وفلترة الملاحظات")
        # طلب 3: فلتر اختيار طالب معين يعمل على الجدول بالأسفل
        f_name = st.selectbox("فلتر حسب اسم الطالب", ["عرض الكل"] + df_st.iloc[:, 1].tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_df = df_b if f_name == "عرض الكل" else df_b[df_b.iloc[:, 0] == f_name]
            st.dataframe(view_df, use_container_width=True, hide_index=True)

    # (بقية أقسام المعلم تبقى كما هي في الكود السابق مع استخدام fetch_safe المحدث)

# ==========================================
# 👨‍🎓 واجهة الطالب (حل مشكلة زر الشكر والدرجات)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📊 نتيجتي", "🎭 ملاحظاتي السلوكية"])
    
    with t1:
        # حل مشكلة ظهور النصوص التقنية بدلاً من الدرجات
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                st.table(my_g)
            else: st.info("لا توجد درجات مرصودة حالياً")

    with t2:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    # التحقق من الحالة الحالية
                    current_status = row.iloc[4] if len(row) > 4 else "⏳ لم يتم القراءة"
                    
                    with st.container(border=True):
                        st.write(f"📅 **التاريخ:** {row.iloc[1]} | **النوع:** {row.iloc[2]}")
                        st.info(f"💬 {row.iloc[3]}")
                        
                        # طلب 1 و 2: زر "شكراً أستاذي" يختفي بعد الضغط ويحدث الحالة
                        if "✅ تمت القراءة" not in current_status:
                            if st.button(f"❤️ شكراً أستاذي (تأكيد القراءة)", key=f"thx_{i}"):
                                try:
                                    ws_b = sh.worksheet("behavior")
                                    # تحديث الخلية في العمود الخامس (الحالة)
                                    # نبحث عن الصف المطابق (الاسم + التاريخ + الملاحظة)
                                    all_rows = ws_b.get_all_values()
                                    for idx, r in enumerate(all_rows):
                                        if r[0] == s_name and r[1] == str(row.iloc[1]) and r[3] == str(row.iloc[3]):
                                            ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                            st.success("شكراً لك، تم إبلاغ المعلم باطلاعك!")
                                            time.sleep(1)
                                            st.rerun() # لإخفاء الزر فوراً
                                except: st.error("حدث خطأ أثناء التحديث")
                        else:
                            st.markdown("<span style='color: green;'>✅ تمت القراءة وشكر الأستاذ</span>", unsafe_allow_html=True)
            else: st.success("🌟 لا توجد ملاحظات، أنت طالب متميز!")
