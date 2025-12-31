import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            # تنظيف وتوحيد أسماء الأعمدة لمنع الأخطاء
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
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
            else: st.error("عذراً، الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إدارة متكاملة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    # 1. إدارة الطلاب (كاملة الحقول + الحذف)
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        with st.form("add_st_form"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nstage = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            c4, c5, c6 = st.columns(3)
            nclass = c4.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            nyear = c5.text_input("العام", value="1447هـ")
            nsub = c6.text_input("المادة", value="لغة إنجليزية")
            if st.form_submit_button("إضافة الطالب"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, "1", nsub, nstage, "", "", "0"])
                    st.success("تمت الإضافة بنجاح"); st.rerun()
        
        st.divider()
        st.subheader("🗑️ حذف طالب من النظام")
        del_target = st.selectbox("اختر الطالب المراد حذفه نهائياً", [""] + df_st.iloc[:, 1].tolist())
        if st.button("⚠️ تنفيذ الحذف الشامل"):
            if del_target:
                for sn in ["students", "grades", "behavior"]:
                    try:
                        ws = sh.worksheet(sn)
                        cell = ws.find(del_target)
                        ws.delete_rows(cell.row)
                    except: pass
                st.warning(f"تم حذف {del_target} من كافة الجداول"); time.sleep(1); st.rerun()

    # 2. شاشة الدرجات (الفترات والمشاركة)
    elif menu == "📝 شاشة الدرجات":
        st.header("📝 رصد الدرجات الدراسية")
        df_st = fetch_safe("students")
        target = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("درجة المشاركة", 0, 100, value=v3)
                if st.form_submit_button("حفظ وتحديث الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([target, p1, p2, part])
                    st.success("تم التحديث"); st.rerun()
        st.subheader("📋 جدول الدرجات العام")
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- شاشة رصد السلوك (عند المعلم) ---
if menu == "🎭 رصد السلوك":
    st.header("🎭 سجل السلوك والملاحظات")
    df_st = fetch_safe("students")
    
    with st.form("behavior_form"):
        c1, c2, c3 = st.columns(3)
        b_name = c1.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
        b_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه"])
        b_date = c3.date_input("التاريخ")
        b_note = st.text_area("نص الملاحظة")
        if st.form_submit_button("رصد الملاحظة"):
            # يتم التسجيل الآن بدون الحاجة لحقل "الحالة" المعقد برمجياً
            sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
            st.success("تم الرصد بنجاح"); st.rerun()

    st.divider()
    st.subheader("🔍 استعراض الفلتر الذكي")
    f_name = st.selectbox("اختر اسم الطالب لعرض سجلاته فقط", ["الكل"] + df_st.iloc[:, 1].unique().tolist())
    df_b = fetch_safe("behavior")
    if not df_b.empty:
        # الفلتر يعمل الآن مباشرة على جدول البيانات
        view_df = df_b if f_name == "الكل" else df_b[df_b.iloc[:, 0] == f_name]
        st.table(view_df)
    # 4. شاشة الاختبارات (تعمل الآن بانتظام)
    elif menu == "📢 شاشة الاختبارات":
        st.header("📢 إدارة إعلانات الاختبارات")
        with st.form("ex_form"):
            c1, c2, c3 = st.columns(3)
            e_class = c1.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_date = c2.date_input("موعد الاختبار")
            e_title = c3.text_input("موضوع الاختبار")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(e_date), e_title, e_class])
                st.success("تم النشر"); st.rerun()
        
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    c1.write(f"📢 **{row.iloc[1]}** | 📅 {row.iloc[0]} | 👥 {row.iloc[2]}")
                    if c2.button("🗑️ حذف", key=f"del_ex_{i}"):
                        sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (تصميم احترافي وفعال)
# ==========================================
# --- شاشة الطالب (مع تنبيهات الإعلانات في الأعلى) ---
if st.session_state.role == "student":
    # زر خروج جانبي مريح للجوال
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    
    # جلب بيانات الطالب
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name, s_email, s_phone, s_points = s_row.iloc[1], s_row.iloc[7], s_row.iloc[8], s_row.iloc[9]

    # 1️⃣ قسم الإعلانات والتنبيهات (أعلى الشاشة)
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        # فلترة الإعلانات الخاصة بصف الطالب أو الموجهة للكل
        my_ex = df_ex[(df_ex.iloc[:, 2] == s_row.iloc[2]) | (df_ex.iloc[:, 2] == "الكل")]
        for _, ex in my_ex.iterrows():
            # عرض التنبيه بلون أصفر مميز لجذب الانتباه
            st.warning(f"🔔 **إعلان:** {ex.iloc[1]} \n\n 📅 التاريخ: {ex.iloc[0]}")

    # 2️⃣ لوحة الهوية والأوسمة (تصميم متجاوب للجوال)
    st.markdown(f"""
        <div style="text-align: center; background-color: #ffffff; padding: 15px; border-radius: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); border-top: 5px solid #1E3A8A; margin-top: 10px;">
            <h3 style="color: #1E3A8A; margin-bottom: 5px;">أهلاً بك يا بطل: {s_name}</h3>
            <p style="font-size: 14px; color: #777;">📱 {s_phone} | 📧 {s_email}</p>
            <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 10px;">
                <div style="text-align: center;">
                    <div style="font-size: 40px;">🏆</div>
                    <div style="font-weight: bold; color: #1E3A8A;">{s_points}</div>
                    <div style="font-size: 12px; color: #888;">نقطة</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 40px;">🥇</div>
                    <div style="font-weight: bold; color: #1E3A8A;">متميز</div>
                    <div style="font-size: 12px; color: #888;">وسام</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.write("") 

    # 3️⃣ التبويبات (الدرجات والملاحظات)
    t1, t2 = st.tabs(["📊 درجاتي", "🎭 ملاحظاتي"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                st.metric("الفترة الأولى", f"{my_g.iloc[0, 1]} / 100")
                st.metric("الفترة الثانية", f"{my_g.iloc[0, 2]} / 100")
                st.metric("درجة المشاركة", f"{my_g.iloc[0, 3]} / 100")
            else:
                st.info("لم يتم رصد درجات حتى الآن")

    with t2:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    # استخدام expander لتوفير مساحة على الجوال
                    with st.expander(f"🗓️ {row.iloc[1]} - {row.iloc[2]}", expanded=True):
                        st.info(f"{row.iloc[3]}")
            else:
                st.info("سجلك السلوكي نظيف")
