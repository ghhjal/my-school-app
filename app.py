import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والربط ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except: return pd.DataFrame()

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        st.divider()
        col_del, col_add = st.columns([1, 2])
        
        with col_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اسم الطالب للحذف النهائي", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                if to_del:
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s)
                            cell = ws.find(to_del)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.error(f"تم حذف {to_del} من كافة السجلات"); time.sleep(1); st.rerun()

        with col_add: # شاشة إضافة طالب
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_st_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                id_v = c1.text_input("الرقم (id)")
                name_v = c2.text_input("الاسم")
                c3, c4, c5 = st.columns(3)
                cls_v = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = c4.text_input("العام", value="1446هـ")
                sub_v = c5.text_input("المادة (sem)", value="اللغة الإنجليزية")
                lev_v = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة ✅"); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        
        with tab1: # شاشة الدرجات
            st.subheader("تحديث درجات الطالب (p1, p2, perf)")
            df_st = fetch_data("students")
            target = st.selectbox("اختر الطالب لتعديل درجته", df_st['name'].tolist())
            with st.form("g_form"):
                col_g1, col_g2, col_g3 = st.columns(3)
                v1 = col_g1.number_input("ف1")
                v2 = col_g2.number_input("ف2")
                v3 = col_g3.number_input("مشاركة")
                if st.form_submit_button("تحديث الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        fnd = ws_g.find(target)
                        ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                    except: ws_g.append_row([target, v1, v2, v3])
                    st.success("تم التحديث ✅")
            st.dataframe(fetch_data("grades"), use_container_width=True)

        with tab2: # شاشة السلوك والتحفيز
            st.subheader("🎭 رصد السلوك والتحفيز")
            with st.form("b_form", clear_on_submit=True):
                sel_st = st.selectbox("اسم الطالب", df_st['name'].tolist())
                b_type = st.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("ملاحظة السلوك")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    # حفظ في جدول السلوك
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, note])
                    # تحديث نقاط الطالب في جدول الطلاب
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old_pts = int(ws_st.cell(c.row, 9).value or 0) # العمود التاسع "النقاط"
                    ws_st.update_cell(c.row, 9, old_pts + pts)
                    st.success(f"تم رصد السلوك وتحديث النقاط الطالب: {sel_st} ✅")

    elif menu == "📢 إعلانات الاختبارات": # شاشة الاختبارات
        st.header("📢 إضافة تنبيه اختبار جديد")
        with st.form("ex_form"):
            e_cls = st.selectbox("حدد الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = st.text_input("عنوان الاختبار")
            e_date = st.date_input("موعد الاختبار")
            if st.form_submit_button("إرسال التنبيه للطلاب 🚀"):
                sh.worksheet("exams").append_row([e_cls, e_title, str(e_date)])
                st.success("تم النشر")
        st.dataframe(fetch_data("exams"), use_container_width=True)

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    st.title(f"مرحباً: {s_data['name']}")
    
    tab_res, tab_up = st.tabs(["📊 نتيجتي", "📧 تحديث بياناتي"])
    with tab_res:
        df_g = fetch_data("grades")
        st.table(df_g[df_g['student_id'] == s_data['name']])
        st.metric("رصيد نقاط التميز ⭐", s_data['النقاط'])
    with tab_up:
        with st.form("st_up"):
            n_mail = st.text_input("الإيميل", value=str(s_data.get('الإيميل', '')))
            n_phone = st.text_input("الجوال", value=str(s_data.get('الجوال', '')))
            if st.form_submit_button("حفظ"):
                ws_st = sh.worksheet("students"); cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 7, n_mail); ws_st.update_cell(cell.row, 8, n_phone)
                st.success("تم الحفظ ✅"); st.rerun()
