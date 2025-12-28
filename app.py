import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال الذكي لتقليل Quota ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة ذكية لتحديث البيانات بطلب واحد فقط
def safe_update_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
        return "✅ تم التحديث بنجاح"
    except:
        try:
            sh.worksheet("grades").append_row([student_name, p1, p2, pf])
            return "✅ تم الرصد بنجاح"
        except:
            return "⚠️ تعذر الاتصال حالياً، يرجى المحاولة بعد قليل"

# --- 2. إدارة الجلسة وزر الخروج المعرب ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

# --- 3. واجهة المعلم (تعريب شامل + منع أخطاء NameError) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sphase = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    if sname:
                        sh.worksheet("students").append_row([str(sid), sname, "الأول", "1446هـ", ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success("✅ تم التسجيل"); time.sleep(1); st.rerun()

        with tab_view:
            st.subheader("🔍 البحث والإدارة")
            search_query = st.text_input("ابحث بالاسم أو الرقم الأكاديمي", placeholder="اكتب للبحث...")
            try:
                ws_st = sh.worksheet("students")
                df = pd.DataFrame(ws_st.get_all_records())
                if not df.empty:
                    df.columns = ["الرقم الأكاديمي", "اسم الطالب", "الصف", "السنة", "المادة", "المرحلة"]
                    filtered = df[df.apply(lambda r: search_query in str(r["اسم الطالب"]) or search_query in str(r["الرقم الأكاديمي"]), axis=1)]
                    st.dataframe(filtered, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    for idx, row in filtered.iterrows():
                        c_name, c_btn = st.columns([4, 1])
                        c_name.write(f"👤 **{row['اسم الطالب']}**")
                        if c_btn.button("حذف", key=f"del_{row['الرقم الأكاديمي']}"):
                            for sn in ["behavior", "grades", "sheet1"]:
                                try:
                                    target = sh.worksheet(sn)
                                    term = str(row['اسم الطالب']) if sn != "sheet1" else str(row['الرقم الأكاديمي'])
                                    for cell in reversed(target.findall(term)): target.delete_rows(cell.row)
                                except: continue
                            ws_st.delete_rows(idx + 2)
                            st.success("تم الحذف"); time.sleep(1); st.rerun()
            except: st.error("⚠️ يرجى الانتظار قليلاً لتحديث البيانات")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            all_st = sh.worksheet("students").get_all_values()
            if len(all_st) > 1:
                names = [r[1] for r in all_st[1:]]
                t_grad, t_beh = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
                
                with t_grad:
                    with st.form("grade_form"):
                        sel_st = st.selectbox("اختر الطالب", names)
                        c1, c2, c3 = st.columns(3)
                        p1 = c1.number_input("الفترة الأولى", 0.0)
                        p2 = c2.number_input("الفترة الثانية", 0.0)
                        pf = c3.number_input("درجة الأداء", 0.0)
                        if st.form_submit_button("تحديث الدرجات"):
                            st.success(safe_update_grades(sel_st, p1, p2, pf))
                            time.sleep(1); st.rerun()
                    try:
                        dg = pd.DataFrame(sh.worksheet("grades").get_all_records())
                        if not dg.empty:
                            dg.columns = ["اسم الطالب", "الفترة 1", "الفترة 2", "الأداء"]
                            st.dataframe(dg, use_container_width=True, hide_index=True)
                    except: pass

                with t_beh:
                    with st.form("beh_form"):
                        b_st = st.selectbox("اسم الطالب", names, key="b_s")
                        b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                        b_note = st.text_input("الملاحظة")
                        if st.form_submit_button("رصد السلوك"):
                            sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                            st.success("✅ تم الرصد"); time.sleep(1); st.rerun()
                    try:
                        db = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                        if not db.empty:
                            db.columns = ["اسم الطالب", "التاريخ", "النوع", "الملاحظة"]
                            st.dataframe(db, use_container_width=True, hide_index=True)
                    except: pass
        except: st.warning("🔄 جاري مزامنة البيانات مع Google Sheets...")

# --- 4. واجهة الطالب المعربة ---
elif st.session_state.role == "student":
    st.title("🎓 نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً بك: {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة الأولى", res[2]); c2.metric("الفترة الثانية", res[3]); c3.metric("درجة الأداء", res[4])
        else: st.error("الرقم غير مسجل")
    except: st.info("🔄 جاري التحميل...")
