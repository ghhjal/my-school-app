import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الاتصال وقاعدة البيانات ---
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال: {e}")
        return None

sh = get_db()

# --- وظيفة التحديث الذكي (منع التكرار) ---
def update_or_append(sheet_name, search_val, new_row):
    ws = sh.worksheet(sheet_name)
    try:
        # البحث عن الطالب بالاسم في العمود الأول
        cell = ws.find(search_val)
        # إذا وجده، يقوم بتحديث الصف بالكامل
        for i, val in enumerate(new_row):
            ws.update_cell(cell.row, i + 1, val)
        return "تم تحديث البيانات بنجاح ✅"
    except gspread.exceptions.CellNotFound:
        # إذا لم يجده، يضيف صفاً جديداً
        ws.append_row(new_row)
        return "تم رصد بيانات جديدة بنجاح ✅"

# --- 2. واجهة المعلم - قسم الدرجات ---
if 'role' in st.session_state and st.session_state.role == "teacher":
    st.sidebar.title("القائمة")
    menu = st.sidebar.radio("انتقل إلى", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        
        try:
            ws_st = sh.worksheet("students")
            names = [r[1] for r in ws_st.get_all_values()[1:]] # قائمة الأسماء
            
            tab_g, tab_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])

            with tab_g:
                with st.form("grades_form"):
                    selected_student = st.selectbox("اختر الطالب", names)
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("درجة الفترة الأولى (P1)", 0.0, 100.0)
                    p2 = c2.number_input("درجة الفترة الثانية (P2)", 0.0, 100.0)
                    pf = c3.number_input("درجة الأداء (Perf)", 0.0, 100.0)
                    
                    if st.form_submit_button("حفظ / تحديث الدرجات"):
                        msg = update_or_append("grades", selected_student, [selected_student, p1, p2, pf])
                        st.success(msg)
                        st.rerun()

                # --- عرض الجدول بالأسفل كما كان سابقاً ---
                st.subheader("📋 كشف الدرجات المرصودة")
                ws_grades = sh.worksheet("grades")
                grades_data = ws_grades.get_all_records()
                if grades_data:
                    df_grades = pd.DataFrame(grades_data)
                    st.dataframe(df_grades, use_container_width=True)
                else:
                    st.info("لا توجد درجات مرصودة حالياً.")

            with tab_b:
                # قسم السلوك (يبقى بنظام الإضافة لمتابعة السجل التاريخي)
                with st.form("behavior_form"):
                    b_student = st.selectbox("اسم الطالب", names, key="beh_names")
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.selectbox("الوصف", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى"])
                    if st.form_submit_button("رصد السلوك"):
                        sh.worksheet("behavior").append_row([b_student, str(datetime.now().date()), b_type, b_note])
                        st.success("تم رصد السلوك")
                        st.rerun()
                
                # عرض سجل السلوك
                st.subheader("📋 سجل السلوكيات")
                behav_data = sh.worksheet("behavior").get_all_records()
                if behav_data:
                    st.table(pd.DataFrame(behav_data))

        except Exception as e:
            st.warning("يرجى التأكد من إضافة طلاب في ورقة 'students' أولاً.")
