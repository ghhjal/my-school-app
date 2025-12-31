import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال الآمن ---
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
            # حل مشكلة Duplicate column names عبر ترقيم الأعمدة الفارغة أو المكررة
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

# إدارة الجلسة
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
# 🛠️ واجهة المعلم (الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    # --- 1. إدارة الطلاب (المادة + الحذف الشامل) ---
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة ملفات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.form("add_st"):
                st.subheader("➕ إضافة طالب")
                cid = st.text_input("الرقم الأكاديمي")
                cname = st.text_input("الاسم الثلاثي")
                cstage = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                cclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                csub = st.text_input("المادة الدراسية", value="لغة إنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([cid, cname, cclass, "1447هـ", "1", csub, cstage, "", "", 0])
                    st.success("تم الحفظ"); st.rerun()
        
        with c2:
            st.subheader("🗑️ حذف شامل لبيانات طالب")
            del_target = st.selectbox("اختر الطالب لحذف كافة بياناته", [""] + df_st.iloc[:, 1].tolist())
            if st.button("⚠️ حذف الطالب من كافة الجداول"):
                if del_target:
                    for s_name in ["students", "grades", "behavior"]:
                        ws = sh.worksheet(s_name)
                        try:
                            cell = ws.find(del_target)
                            ws.delete_rows(cell.row)
                        except: pass
                    st.warning(f"تم حذف {del_target} من كافة السجلات"); time.sleep(1); st.rerun()

    # --- 2. شاشة الدرجات (حقل المشاركة + الجدول السفلي) ---
    elif menu == "📝 شاشة الدرجات":
        st.header("📝 رصد وتحديث درجات الطلاب")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        
        if sel_name:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty and len(curr.columns)>3 else 0
            
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة 1", 0, 100, value=v1)
                p2 = c2.number_input("الفترة 2", 0, 100, value=v2)
                part = c3.number_input("المشاركة", 0, 100, value=v3)
                if st.form_submit_button("تحديث الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        cell = ws_g.find(sel_name)
                        ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws_g.append_row([sel_name, p1, p2, part])
                    st.success("✅ تمت العملية"); st.rerun()
        
        st.subheader("📋 جدول الدرجات الكلي")
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # --- 3. رصد السلوك (الأنواع الجديدة + فلتر الطالب) ---
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك والملاحظات")
        df_st = fetch_safe("students")
        with st.form("b_form"):
            c1, c2 = st.columns(2)
            sb_name = c1.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
            sb_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه", "أخرى"])
            sb_date = st.date_input("تاريخ الملاحظة السلوكية")
            sb_note = st.text_area("نص الملاحظة")
            if st.form_submit_button("رصد السلوك"):
                sh.worksheet("behavior").append_row([sb_name, str(sb_date), sb_type, sb_note, "لم يتم الاطلاع"])
                st.success("تم الرصد"); st.rerun()
        
        st.divider()
        st.subheader("🔍 استعراض ملاحظات طالب معين")
        f_name = st.selectbox("فلتر حسب الطالب", ["الكل"] + df_st.iloc[:, 1].tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_b = df_b if f_name == "الكل" else df_b[df_b.iloc[:, 0] == f_name]
            st.table(view_b)

    # --- 4. شاشة الاختبارات (الصف + الحذف الفردي) ---
    elif menu == "📢 شاشة الاختبارات":
        st.header("📢 إدارة إعلانات الاختبارات")
        with st.form("ex_form"):
            c1, c2, c3 = st.columns(3)
            ex_class = c1.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            ex_date = c2.date_input("التاريخ")
            ex_title = c3.text_input("عنوان الاختبار / المادة")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(ex_date), ex_title, ex_class])
                st.success("تم النشر"); st.rerun()
        
        st.subheader("📋 الإعلانات الحالية")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    c1.write(f"📢 **{row.iloc[1]}** | 📅 {row.iloc[0]} | 👥 الصف: {row.iloc[2]}")
                    if c2.button("🗑️ حذف", key=f"ex_{i}"):
                        sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الخصوصية المطلقة)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h1 style='text-align: center;'>👋 أهلاً بك يا بطل: {s_name}</h1>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 درجاتي", "📅 جدول الاختبارات", "🎭 ملاحظاتي السلوكية"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            st.table(my_g) if not my_g.empty else st.info("لا توجد درجات")
            
    with t2:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            # يرى الطالب إعلانات صفه أو الإعلانات العامة (الكل)
            my_ex = df_ex[(df_ex.iloc[:, 2] == s_row.iloc[2]) | (df_ex.iloc[:, 2] == "الكل")]
            st.table(my_ex)
            
    with t3:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            if not my_b.empty:
                for i, row in my_b.iterrows():
                    with st.expander(f"📅 {row.iloc[1]} - نوع: {row.iloc[2]}"):
                        st.write(f"💬 {row.iloc[3]}")
                        if st.button("❤️ شكراً أستاذ زياد (تمت القراءة)", key=f"th_{i}"):
                            ws_b = sh.worksheet("behavior")
                            # تحديث الحالة
                            all_b = ws_b.get_all_values()
                            for idx, r in enumerate(all_b):
                                if r[0] == s_name and r[1] == row.iloc[1] and r[3] == row.iloc[3]:
                                    ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                    st.success("تم الإرسال"); st.rerun()
