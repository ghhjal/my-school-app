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
            headers = [h if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            df = pd.DataFrame(data[1:], columns=headers)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول المستقلة
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
# 🛠️ واجهة المعلم (تقسيم الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 إعلان الاختبارات"])

    # 1. إدارة الطلاب (كاملة الحقول)
    if menu == "👥 إدارة الطلاب":
        st.header("👥 سجل الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        with st.form("add_student"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            id_n = c1.text_input("الرقم الأكاديمي")
            name_n = c2.text_input("الاسم الثلاثي")
            stage_n = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            
            c4, c5, c6 = st.columns(3)
            class_n = c4.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            year_n = c5.text_input("العام الدراسي", value="1447هـ")
            sub_n = c6.text_input("المادة", value="English")
            
            if st.form_submit_button("حفظ"):
                sh.worksheet("students").append_row([id_n, name_n, class_n, year_n, "1", sub_n, stage_n, "", "", 0])
                st.success("تم الحفظ"); st.rerun()

    # 2. رصد الدرجات (تحديث الدرجة الحالية)
    elif menu == "📝 رصد الدرجات":
        st.header("📝 تحديث درجات الطلاب")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            df_g = fetch_safe("grades")
            curr_g = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(curr_g.iloc[0, 1]) if not curr_g.empty else 0
            v2 = int(curr_g.iloc[0, 2]) if not curr_g.empty else 0
            
            with st.form("up_grade"):
                c1, c2 = st.columns(2)
                p1 = c1.number_input("الفترة 1", 0, 100, value=v1)
                p2 = c2.number_input("الفترة 2", 0, 100, value=v2)
                if st.form_submit_button("تعديل الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_name)
                        ws_g.update(f'B{cell.row}:C{cell.row}', [[p1, p2]])
                    except: ws_g.append_row([sel_name, p1, p2])
                    st.success("✅ تم التعديل"); st.rerun()
        st.subheader("📋 جدول الدرجات العام")
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. رصد السلوك (مع جدول متابعة القراءة)
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والنقاط")
        df_st = fetch_safe("students")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_b:
            with st.form("b_form"):
                b_type = st.selectbox("نوع السلوك", ["تميز (+10)", "مشاركة (+5)", "تنبيه (-5)", "غياب (-10)"])
                b_note = st.text_area("الملاحظة")
                if st.form_submit_button("رصد"):
                    # الأعمدة: الاسم، التاريخ، النوع، الملاحظة، الحالة
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.now().date()), b_type, b_note, "لم يتم الاطلاع"])
                    st.success("تم الرصد"); st.rerun()
        st.subheader("📋 جدول السلوك المرصود")
        st.dataframe(fetch_safe("behavior"), use_container_width=True)

    # 4. إعلان الاختبارات (مع زر حذف الإعلان)
    elif menu == "📢 إعلان الاختبارات":
        st.header("📢 إعلان اختبار")
        with st.form("ex_form"):
            sub = st.text_input("المادة")
            dt = st.date_input("تاريخ الاختبار")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(dt), sub])
                st.rerun()
        st.divider()
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                c1, c2 = st.columns([5, 1])
                c1.info(f"📖 {row.iloc[1]} | 📅 {row.iloc[0]}")
                if c2.button("🗑️ حذف", key=f"del_ex_{i}"):
                    sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الخصوصية المطلقة + زر الشكر)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_idx = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].index[0]
    s_row = df_st.loc[s_idx]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    # تحديث البيانات (الإيميل والجوال) من قبل الطالب
    with st.expander("📝 تحديث بيانات التواصل (الإيميل والجوال)"):
        with st.form("st_info_up"):
            u_email = st.text_input("بريد ولي الأمر", value=s_row.iloc[7] if len(s_row)>7 else "")
            u_phone = st.text_input("رقم الجوال", value=s_row.iloc[8] if len(s_row)>8 else "")
            if st.form_submit_button("حفظ"):
                ws = sh.worksheet("students")
                ws.update_cell(s_idx + 2, 8, u_email)
                ws.update_cell(s_idx + 2, 9, u_phone)
                st.success("✅ تم التحديث"); st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 درجاتي", "📅 الاختبارات", "🎭 سجل سلوكي"])
    
    with tab1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات")
            
    with tab2:
        st.table(fetch_safe("exams"))
        
    with tab3:
        st.subheader("📝 ملاحظات المعلم")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    with st.container(border=True):
                        st.write(f"📅 {row.iloc[1]} - **{row.iloc[2]}**")
                        st.write(f"💬 الملاحظة: {row.iloc[3]}")
                        st.write(f"الحالة الحالية: {row.iloc[4]}")
                        # زر الشكر لتأكيد القراءة
                        if st.button("❤️ شكراً أستاذ زياد (تمت القراءة)", key=f"thnx_{i}"):
                            ws_b = sh.worksheet("behavior")
                            # تحديث الحالة في الشيت
                            all_b = ws_b.get_all_values()
                            for idx, r in enumerate(all_b):
                                if r[0] == s_name and r[1] == row.iloc[1] and r[3] == row.iloc[3]:
                                    ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                    st.success("تم تأكيد القراءة")
                                    st.rerun()
            else: st.success("🌟 لا توجد ملاحظات سلبية، استمر في تميزك!")
