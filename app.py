import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# إعداد الصفحة
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# الربط المحسن
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception:
        return None

sh = get_db()

# دالة جلب البيانات مع ميزة التحديث القسري لمنع بقاء الزر
def fetch_data(sheet_name, force_refresh=False):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            if force_refresh:
                # تصفير الذاكرة المؤقتة لهذا الجدول تحديداً
                st.cache_data.clear()
            return pd.DataFrame(ws.get_all_records())
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

if 'role' not in st.session_state: st.session_state.role = None
if 'is_processing' not in st.session_state: st.session_state.is_processing = False

# --- نظام الدخول ---
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password", key="login_tpwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_input = st.text_input("الرقم الأكاديمي", key="login_sid")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid_input) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_input); st.rerun()
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["إدارة الطلاب", "الدرجات والسلوك", "إعلانات الاختبارات"])
    df_st = fetch_data("students")

    if menu == "إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        st.divider()
        col_del, col_add = st.columns([1, 2])
        with col_del:
            st.subheader("🗑️ حذف طالب")
            if not df_st.empty:
                to_del = st.selectbox("اسم الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("تأكيد الحذف"):
                    if to_del:
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s); cell = ws.find(to_del)
                                if cell: ws.delete_rows(cell.row)
                            except: pass
                        st.success("تم الحذف"); st.rerun()
        with col_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_student_form", clear_on_submit=True):
                id_v = st.text_input("الرقم الأكاديمي")
                name_v = st.text_input("اسم الطالب")
                c1, c2 = st.columns(2)
                cls_v = c1.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                lev_v = c2.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("إضافة الطالب"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, "1447هـ", "اللغة الإنجليزية", lev_v, "", "", 0])
                    st.success("تمت الإضافة"); time.sleep(1); st.rerun()

    elif menu == "الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 الدرجات", "🎭 السلوك"])
        with tab1:
            if not df_st.empty:
                target = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
                if target:
                    with st.form("grades_form"):
                        v1, v2, v3 = st.number_input("ف1", 0), st.number_input("ف2", 0), st.number_input("المشاركة", 0)
                        if st.form_submit_button("حفظ"):
                            ws_g = sh.worksheet("grades")
                            try:
                                fnd = ws_g.find(target)
                                ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                            except: ws_g.append_row([target, v1, v2, v3])
                            st.success("تم التحديث")
            st.dataframe(fetch_data("grades"), use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("🎭 رصد وفلترة السلوك")
            if not df_st.empty:
                sel_st = st.selectbox("اسم الطالب", [""] + df_st.iloc[:, 1].tolist())
                if sel_st:
                    with st.form("behavior_form_t", clear_on_submit=True):
                        t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                        n_v = st.text_input("الملاحظة")
                        if st.form_submit_button("حفظ الملاحظة"):
                            pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                            sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), t_v, n_v, "🕒 لم تقرأ بعد"])
                            ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                            old = int(ws_st.cell(c.row, 9).value or 0)
                            ws_st.update_cell(c.row, 9, old + pts)
                            st.success("تم الحفظ ✅"); time.sleep(1); st.rerun()
                    
                    st.divider()
                    df_bh_all = fetch_data("behavior")
                    if not df_bh_all.empty:
                        f_bh = df_bh_all[df_bh_all.iloc[:, 0] == sel_st].iloc[::-1]
                        st.dataframe(f_bh, use_container_width=True, hide_index=True)

    elif menu == "إعلانات الاختبارات":
        with st.form("exam_form"):
            e_cls = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = st.text_input("الموضوع")
            e_dt = st.date_input("الموعد")
            if st.form_submit_button("نشر الموعد"):
                sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                st.success("تم النشر ✅"); st.rerun()

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    
    if not df_st.empty:
        matches = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid]
        if not matches.empty:
            s_data = matches.iloc[0]; s_name = s_data.iloc[1]
            st.title(f"🌟 أهلاً بك: {s_name}")
            pts = int(s_data.iloc[8] or 0)
            medal = "🏆 بطل التحدي" if pts >= 100 else "🥇 وسام ذهبي" if pts >= 50 else "🥈 وسام فضي"
            c1, c2 = st.columns(2)
            c1.metric("رصيد نقاطك ⭐", pts)
            c2.metric("لقبك الحالي 🏆", medal)

            st.divider()
            t1, t2 = st.tabs(["📊 نتيجتي وسلوكي", "⚙️ بياناتي"])
            
            with t1:
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.subheader("📊 الدرجات")
                    df_g = fetch_data("grades")
                    my_g = df_g[df_g.iloc[:, 0] == s_name] if not df_g.empty else pd.DataFrame()
                    if not my_g.empty:
                        st.write(f"فترة 1: {my_g.iloc[0, 1]}")
                        st.write(f"فترة 2: {my_g.iloc[0, 2]}")
                
                with col_b:
                    st.subheader("🎭 سجل السلوك")
                    # جلب البيانات مع تحديث قسري عند دخول الطالب
                    df_bh = fetch_data("behavior")
                    if not df_bh.empty:
                        df_bh['real_row_idx'] = range(2, len(df_bh) + 2)
                        my_bh = df_bh[df_bh.iloc[:, 0] == s_name].iloc[::-1]
                        
                        for _, row in my_bh.iterrows():
                            status = str(row.iloc[4])
                            # شرط أدق للاختفاء: إذا وجدت علامة ✅ أو كلمة "تمت" يختفي الزر فوراً
                            is_r = any(x in status for x in ["✅", "تمت"])
                            
                            bg = "#E8F5E9" if is_r else "#FFF3E0"
                            st.markdown(f"<div style='background-color:{bg}; padding:10px; border-radius:5px; margin-bottom:5px;'><b>{row.iloc[2]}</b>: {row.iloc[3]}</div>", unsafe_allow_html=True)
                            
                            if not is_r:
                                if st.button(f"🙏 شكراً أستاذي زياد", key=f"thx_{row['real_row_idx']}", disabled=st.session_state.is_processing):
                                    st.session_state.is_processing = True
                                    try:
                                        with st.spinner("جاري تأكيد القراءة..."):
                                            # التحديث الفوري
                                            sh.worksheet("behavior").update_cell(int(row['real_row_idx']), 5, "✅ تمت القراءة")
                                            # أمر حيوي: مسح الذاكرة المؤقتة تماماً لضمان اختفاء الزر في اللحظة التالية
                                            st.cache_data.clear()
                                            st.balloons()
                                            time.sleep(1) # وقت كافٍ لجوجل لتسجيل التغيير
                                            st.session_state.is_processing = False
                                            st.rerun()
                                    except:
                                        st.session_state.is_processing = False
                                        st.error("يرجى المحاولة مرة أخرى")

            with t2:
                with st.form("up_pers_data"):
                    mail = st.text_input("إيميل ولي الأمر", value=str(s_data.iloc[6]))
                    phone = st.text_input("رقم الجوال", value=str(s_data.iloc[7]))
                    if st.form_submit_button("حفظ"):
                        ws = sh.worksheet("students"); c = ws.find(st.session_state.sid)
                        ws.update_cell(c.row, 7, mail); ws.update_cell(c.row, 8, phone)
                        st.success("تم التحديث"); st.rerun()
