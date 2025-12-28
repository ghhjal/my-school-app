import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="نظام المدرسة الرقمي المتكامل", layout="wide")

def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        # معرف ملفك
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال: {e}")
        return None

sh = get_db()

# --- وظيفة التحديث لمنع التكرار ---
def update_or_append_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        # تحديث الصف الموجود
        ws.update_cell(cell.row, 2, p1)
        ws.update_cell(cell.row, 3, p2)
        ws.update_cell(cell.row, 4, pf)
        return "تم تحديث الدرجات بنجاح ✅"
    except:
        # إضافة صف جديد إذا لم يوجد
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "تم رصد الدرجات لأول مرة ✅"

# --- 2. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t_login1, t_login2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t_login1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور خاطئة")
    with t_login2:
        sid_in = st.text_input("الرقم الأكاديمي", key="login_sid")
        if st.button("دخول الطالب"):
            if sid_in:
                st.session_state.role = "student"
                st.session_state.student_id = sid_in
                st.rerun()
    st.stop()

# زر تسجيل الخروج
if st.sidebar.button("🚪 تسجيل الخروج", key="logout_btn"):
    st.session_state.role = None
    st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_new, tab_list = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with tab_new:
            with st.form("reg_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, "1446هـ", ssub])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success(f"✅ تم تسجيل {sname}")
                        st.rerun()

        with tab_list:
            st.subheader("📋 كشف الطلاب (مع الحذف الشامل)")
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                for idx, row in enumerate(data):
                    col_i, col_d = st.columns([4, 1])
                    col_i.write(f"👤 {row['name']} (ID: {row['id']})")
                    if col_d.button("🗑️ حذف", key=f"del_{row['id']}"):
                        ws_st.delete_rows(idx + 2)
                        # الحذف من الأوراق الأخرى
                        for sn in ["grades", "behavior", "sheet1"]:
                            try:
                                target_ws = sh.worksheet(sn)
                                cells = target_ws.findall(str(row['name']) if sn != "sheet1" else str(row['id']))
                                for cell in reversed(cells): target_ws.delete_rows(cell.row)
                            except: pass
                        st.success("تم الحذف بنجاح")
                        st.rerun()
            except: st.info("القائمة فارغة")

    elif menu == "📊 الدرجات والسلوك":
        with t_b:
                # 1. جلب بيانات السلوك وتخزينها في الجلسة لضمان ثبات العرض
                if 'behavior_df' not in st.session_state:
                    try:
                        st.session_state.behavior_df = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                    except:
                        st.session_state.behavior_df = pd.DataFrame(columns=["student_id", "date", "type", "note"])

                # 2. نموذج رصد السلوك
                with st.form("beh_form_final"):
                    b_st = st.selectbox("اختر الطالب", names, key="b_select_final")
                    b_t = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_n = st.text_input("الملاحظة / وصف السلوك")
                    
                    if st.form_submit_button("رصد السلوك"):
                        with st.spinner("جاري الحفظ..."):
                            # إضافة الصف الجديد في جوجل شيت
                            new_entry = [b_st, str(datetime.now().date()), b_t, b_n]
                            sh.worksheet("behavior").append_row(new_entry)
                            
                            # تحديث جدول العرض في الجلسة فوراً
                            st.session_state.behavior_df = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                            st.success(f"✅ تم رصد سلوك الطالب {b_st} بنجاح")
                            st.rerun()
                
                # 3. عرض الجدول بالأسفل (مثل قسم الدرجات)
                st.subheader("📋 سجل السلوكيات المرصودة")
                if not st.session_state.behavior_df.empty:
                    # عرض الجدول مع تحسين المظهر
                    st.dataframe(
                        st.session_state.behavior_df, 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.info("لا توجد سلوكيات مرصودة حالياً.")
        
        # جلب البيانات مرة واحدة في بداية القسم لتجنب الاختفاء
        if 'grades_df' not in st.session_state:
            st.session_state.grades_df = pd.DataFrame(sh.worksheet("grades").get_all_records())

        try:
            names = [r[1] for r in sh.worksheet("students").get_all_values()[1:]]
            t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with t_g:
                with st.form("grade_update"):
                    sel_st = st.selectbox("اختر الطالب", names)
                    g1, g2, gp = st.columns(3)
                    v1 = g1.number_input("P1", 0.0)
                    v2 = g2.number_input("P2", 0.0)
                    vp = gp.number_input("Perf", 0.0)
                    
                    if st.form_submit_button("حفظ وتحديث"):
                        with st.spinner("جاري التحديث..."):
                            msg = update_or_append_grades(sel_st, v1, v2, vp)
                            # تحديث البيانات في الجلسة مباشرة لمنع الاختفاء
                            st.session_state.grades_df = pd.DataFrame(sh.worksheet("grades").get_all_records())
                            st.success(msg)
                            st.rerun()
                
                # عرض الجدول من الجلسة (Session State) لضمان السرعة والثبات
                st.subheader("📋 سجل الدرجات المرصودة")
                st.dataframe(st.session_state.grades_df, use_container_width=True)

            with t_b:
                # قسم السلوك يبقى كما هو
                with st.form("beh_form"):
                    b_st = st.selectbox("الطالب", names, key="b_select")
                    b_t = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_n = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_t, b_n])
                        st.success("تم الرصد بنجاح")
                        st.rerun()
        except Exception as e:
            st.warning("تأكد من وجود طلاب مسجلين أولاً.")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 ملف نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("P1", res[2]); c2.metric("P2", res[3]); c3.metric("الأداء", res[4])
        else: st.error("رقم غير مسجل")
    except: st.info("تحميل...")
