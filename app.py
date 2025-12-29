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
        # الربط مع ملف English_Grades
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

        with col_add:
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
        df_st = fetch_data("students")

        with tab1: # شاشة الدرجات
            st.subheader("تحديث درجات الطالب (p1, p2, perf)")
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

        with tab2: # شاشة السلوك المحدثة
            st.subheader("🎭 رصد السلوك والتحفيز")
            sel_st = st.selectbox("اسم الطالب", df_st['name'].tolist(), key="behavior_select")
            with st.form("b_form", clear_on_submit=True):
                c_date, c_type = st.columns([1, 2])
                b_date = c_date.date_input("تاريخ الرصد", datetime.now())
                b_type = c_type.radio("نوع السلوك", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("ملاحظة السلوك")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(b_date), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old_pts = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old_pts + pts)
                    st.success(f"تم رصد السلوك وتحديث النقاط ✅"); time.sleep(1); st.rerun()

            st.divider()
            st.subheader(f"📜 سجل ملاحظات الطالب: {sel_st}")
            df_bh = fetch_data("behavior")
            if not df_bh.empty:
                st.dataframe(df_bh[df_bh['student_id'] == sel_st], use_container_width=True, hide_index=True)

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

# --- 4. واجهة الطالب المحدثة بالكامل ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    st.markdown(f"## 👋 مرحباً بك يا بطل: {s_data['name']}")
    st.info(f"📍 الصف: {s_data['class']} | المرحلة: {s_data['المرحلة']} | المادة: {s_data['sem']}")

    # عرض تنبيهات الاختبارات الخاصة بصف الطالب
    df_ex = fetch_data("exams")
    my_exams = df_ex[df_ex['الصف'] == s_data['class']]
    if not my_exams.empty:
        for _, row in my_exams.iterrows():
            st.warning(f"📢 **تنبيه اختبار جديد:** {row['العنوان']} بتاريخ {row['التاريخ']}")

    t_grades, t_behavior, t_profile = st.tabs(["📊 نتيجتي التفصيلية", "🎭 سجل سلوكي وتحفيزي", "📧 تحديث بياناتي"])
    
    with t_grades: # عرض الدرجات
        st.subheader("📝 درجات الاختبارات والمشاركة")
        df_g = fetch_data("grades")
        my_grade = df_g[df_g['student_id'] == s_data['name']]
        if not my_grade.empty:
            # عرض الأعمدة ف1، ف2، ومشاركة
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1 (p1)", my_grade.iloc[0]['p1'])
            c2.metric("فترة 2 (p2)", my_grade.iloc[0]['p2'])
            c3.metric("المشاركة (perf)", my_grade.iloc[0]['perf'])
            st.dataframe(my_grade, use_container_width=True, hide_index=True)
        else:
            st.info("لم يتم رصد درجات لك بعد.")

    with t_behavior: # عرض السلوك والنقاط
        st.subheader("⭐ رصيد نقاط التميز")
        st.write(f"رصيدك الحالي هو: **{s_data['النقاط']}** نقطة")
        
        st.divider()
        st.subheader("📜 سجل السلوك والملاحظات")
        df_bh = fetch_data("behavior")
        my_bh = df_bh[df_bh['student_id'] == s_data['name']]
        if not my_bh.empty:
            st.dataframe(my_bh[['date', 'type', 'note']], use_container_width=True, hide_index=True)
        else:
            st.info("سجلك نظيف ومتميز! لا توجد ملاحظات سلبية.")

    with t_profile: # تحديث البيانات
        with st.form("st_up"):
            n_mail = st.text_input("البريد الإلكتروني", value=str(s_data.get('الإيميل', '')))
            n_phone = st.text_input("رقم الجوال", value=str(s_data.get('الجوال', '')))
            if st.form_submit_button("حفظ التغييرات"):
                ws_st = sh.worksheet("students"); cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 7, n_mail) # تحديث العمود G
                ws_st.update_cell(cell.row, 8, n_phone) # تحديث العمود H
                st.success("تم تحديث بياناتك بنجاح ✅"); st.rerun()
