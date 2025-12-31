import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال الآمن ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1) # تقليل التخزين المؤقت لتحديث اللحظي
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
            # حل مشكلة Duplicate Column Names لضمان عدم ظهور الخطأ الأحمر
            headers = []
            for i, h in enumerate(data[0]):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in headers: name = f"{name}_{i}"
                headers.append(name)
            return pd.DataFrame(data[1:], columns=headers)
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
# 🛠️ واجهة المعلم (رصد السلوك مع الفلتر)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    if menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والملاحظات")
        df_st = fetch_safe("students")
        with st.form("b_form"):
            c1, c2 = st.columns(2)
            sb_name = c1.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
            sb_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه", "أخرى"])
            sb_date = st.date_input("التاريخ")
            sb_note = st.text_area("الملاحظة")
            if st.form_submit_button("إرسال الرصد"):
                sh.worksheet("behavior").append_row([sb_name, str(sb_date), sb_type, sb_note, "⏳ لم يتم القراءة"])
                st.success("تم الرصد"); st.rerun()
        
        st.divider()
        st.subheader("🔍 استعراض الملاحظات")
        # فلتر السلوك حسب اسم الطالب
        f_name = st.selectbox("فلتر حسب الطالب", ["عرض الكل"] + df_st.iloc[:, 1].tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_df = df_b if f_name == "عرض الكل" else df_b[df_b.iloc[:, 0] == f_name]
            st.dataframe(view_df, use_container_width=True, hide_index=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (التصميم الفعال + منطق الزر)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]
    s_points = s_row.iloc[9] if len(s_row) > 9 else "0"

    # 1. التنبيهات في أعلى الشاشة
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        my_ex = df_ex[(df_ex.iloc[:, 2] == s_row.iloc[2]) | (df_ex.iloc[:, 2] == "الكل")]
        for _, ex in my_ex.iterrows():
            st.warning(f"📢 **إعلان عاجل:** {ex.iloc[1]} | 📅 التاريخ: {ex.iloc[0]}")

    # 2. تصميم الأوسمة والترحيب (فعال للحاسوب والجوال)
    st.markdown(f"""
        <div style="text-align: center; background-color: #f8f9fa; padding: 20px; border-radius: 20px; border: 2px solid #1E3A8A; margin-bottom: 20px;">
            <h2 style="color: #1E3A8A; margin:0;">👋 بطل الصف: {s_name}</h2>
            <div style="display: flex; justify-content: center; gap: 15px; margin-top: 15px;">
                <div style="background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 120px;">
                    <span style="font-size: 35px;">🏆</span><br><b>{s_points} نقطة</b>
                </div>
                <div style="background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 120px;">
                    <span style="font-size: 35px;">🥇</span><br><b>وسام التميز</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.tabs(["📊 نتيجتي الدراسية", "🎭 سجل ملاحظاتي"])
    
    with t1:
        # حل مشكلة عدم ظهور الدرجات والنصوص التقنية
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة 1", my_g.iloc[0,1])
                c2.metric("الفترة 2", my_g.iloc[0,2])
                c3.metric("المشاركة", my_g.iloc[0,3])
            else: st.info("لا توجد درجات مرصودة")

    with t2:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for i, row in my_b.iterrows():
                # التحقق من الحالة الحالية
                status = row.iloc[4] if len(row) > 4 else "⏳ لم يتم القراءة"
                is_read = "تمت القراءة" in status
                
                with st.container(border=True):
                    st.write(f"📅 **التاريخ:** {row.iloc[1]} | **النوع:** {row.iloc[2]}")
                    st.info(f"💬 {row.iloc[3]}")
                    
                    # منطق زر الشكر المطور (يختفي فوراً ويحدث جوجل شيت)
                    if not is_read:
                        if st.button(f"❤️ شكراً أستاذي (تأكيد القراءة)", key=f"th_{i}"):
                            try:
                                ws_b = sh.worksheet("behavior")
                                all_v = ws_b.get_all_values()
                                # البحث عن الصف المطابق وتحديثه
                                for idx, r in enumerate(all_v):
                                    if r[0] == s_name and r[1] == str(row.iloc[1]) and r[3] == str(row.iloc[3]):
                                        ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                        st.success("تم إرسال شكرك للأستاذ!")
                                        time.sleep(1)
                                        st.rerun() # الزر يختفي فوراً بعد الريرن
                            except: st.error("فشل التحديث")
                    else:
                        st.markdown("<span style='color: green; font-weight: bold;'>✅ تم الاطلاع وشكر المعلم</span>", unsafe_allow_html=True)
