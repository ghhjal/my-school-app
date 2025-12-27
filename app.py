import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام متابعة الطالب المتكامل", layout="wide")

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_integrated_v5.db')
    c = conn.cursor()
    # 1. جدول السجلات اليومية (السلوك) - كما في الصورة
    c.execute('''CREATE TABLE IF NOT EXISTS daily_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, log_date TEXT, pos_behavior TEXT, neg_behavior TEXT, neg_count INTEGER, reward TEXT, notes TEXT)''')
    
    # 2. جدول الدرجات الأكاديمية الجديد
    c.execute('''CREATE TABLE IF NOT EXISTS academic_grades
                 (student_id TEXT PRIMARY KEY,
                  name TEXT,
                  period1 INTEGER,
                  period2 INTEGER,
                  participation INTEGER,
                  projects INTEGER,
                  final_total INTEGER)''')

    # 3. جدول أسماء الطلاب الأساسية
    c.execute('''CREATE TABLE IF NOT EXISTS students_master (student_id TEXT PRIMARY KEY, name TEXT)''')
    conn.commit()
    conn.close()

def get_master_students_df():
    conn = sqlite3.connect('school_integrated_v5.db')
    df = pd.read_sql_query("SELECT * FROM students_master", conn)
    conn.close()
    return df

def get_academic_grades_df():
    conn = sqlite3.connect('school_integrated_v5.db')
    df = pd.read_sql_query("SELECT * FROM academic_grades", conn)
    conn.close()
    return df

# --- واجهة البرنامج الرئيسية ---
init_db()
st.title("🎓 نظام متابعة الطالب المتكامل")

menu = st.sidebar.selectbox("اختر نوع الدخول:", ["لوحة الطالب", "لوحة المعلم 🔐"])

# ------------------- لوحة المعلم -------------------
if menu == "لوحة المعلم 🔐":
    password = st.sidebar.text_input("أدخل كلمة مرور المعلم", type="password")
    if password == "1234": # كلمة المرور: 1234
        st.sidebar.success("تم الدخول بنجاح")
        
        tab_daily, tab_grades, tab_master = st.tabs(["📊 السجل اليومي (السلوك)", "📝 الدرجات الأكاديمية", "🧑‍🎓 إدارة الطلاب الأساسية"])
        
        # --- تبويب السجل اليومي (السلوك) ---
        with tab_daily:
            st.subheader("إضافة سجل متابعة يومي جديد (مطابق للصورة)")
            df_master = get_master_students_df()
            if df_master.empty:
                st.warning("الرجاء إضافة أسماء الطلاب أولاً في التبويب الأخير.")
            else:
                with st.form("daily_log_form"):
                    selected_student_name = st.selectbox("اختر اسم الطالب", df_master['name'].tolist())
                    s_id = df_master[df_master['name'] == selected_student_name]['student_id'].iloc[0]
                    log_date = st.date_input("اليوم / التاريخ", datetime.date.today())
                    
                    # باقي حقول السجل اليومي... (pos_behavior, neg_behavior, neg_count, reward, notes)
                    # ... (المنطق هو نفسه من الكود السابق، يعمل على جدول daily_logs)
                    
                    submit = st.form_submit_button("حفظ السجل اليومي")
                    if submit:
                         # (كود الحفظ في daily_logs يوضع هنا)
                         st.success(f"تم تسجيل متابعة يوم {log_date} للطالب {selected_student_name}")

        # --- تبويب الدرجات الأكاديمية الجديدة ---
        with tab_grades:
            st.subheader("إدخال وتعديل الدرجات الأكاديمية")
            df_grades = get_academic_grades_df()
            df_master = get_master_students_df()

            if not df_master.empty:
                # عرض قائمة بأسماء الطلاب مع إمكانية التعديل
                st.dataframe(df_grades, use_container_width=True)

                st.markdown("---")
                st.markdown("**تحديث درجات طالب محدد:**")
                
                selected_student_id_for_grade = st.selectbox("اختر الرقم الأكاديمي للطالب لتعديل درجاته", df_master['student_id'].tolist())
                student_name_for_grade = df_master[df_master['student_id'] == selected_student_id_for_grade]['name'].iloc[0]

                # جلب البيانات الحالية للطالب إذا كانت موجودة
                current_grades = df_grades[df_grades['student_id'] == selected_student_id_for_grade]
                
                p1_val = int(current_grades['period1'].sum()) if not current_grades.empty else 0
                p2_val = int(current_grades['period2'].sum()) if not current_grades.empty else 0
                part_val = int(current_grades['participation'].sum()) if not current_grades.empty else 0
                proj_val = int(current_grades['projects'].sum()) if not current_grades.empty else 0

                with st.form("update_grades_form"):
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        p1 = st.number_input("درجة اختبار الفترة الأولى", 0, 100, p1_val)
                        p2 = st.number_input("درجة اختبار الفترة الثانية", 0, 100, p2_val)
                    with col_g2:
                        part = st.number_input("درجة المشاركة", 0, 100, part_val)
                        proj = st.number_input("درجة المهام والمشاريع", 0, 100, proj_val)
                        
                    submit_grades = st.form_submit_button(f"حفظ درجات {student_name_for_grade}")
                    
                    if submit_grades:
                        total = p1 + p2 + part + proj
                        conn = sqlite3.connect('school_integrated_v5.db')
                        c = conn.cursor()
                        # نستخدم REPLACE INTO لتحديث الصف إذا كان موجوداً أو إضافته إذا كان جديداً
                        c.execute("REPLACE INTO academic_grades VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (selected_student_id_for_grade, student_name_for_grade, p1, p2, part, proj, total))
                        conn.commit()
                        st.success(f"تم تحديث الدرجات النهائية بنجاح للطالب {student_name_for_grade}. المجموع: {total}")
                        st.rerun()

            else:
                st.info("لا يوجد طلاب مسجلين بعد.")


        # --- تبويب إدارة الطلاب الأساسية (يبقى كما هو) ---
        with tab_master:
            st.subheader("إدارة قائمة الطلاب الأساسية")
            # ... (كود إضافة وحذف الطلاب الأساسيين هنا) ...


    else:
        st.warning("يرجى إدخال كلمة المرور الصحيحة.")

# ------------------- لوحة الطالب (ولي الأمر) -------------------
elif menu == "لوحة الطالب":
    st.header("🔍 استعلام الطالب وولي الأمر")
    search_id = st.text_input("أدخل الرقم الأكاديمي للطالب:")
    
    if st.button("عرض ملف المتابعة والدرجات"):
        if search_id:
            conn = sqlite3.connect('school_integrated_v5.db')
            df_name = pd.read_sql_query("SELECT name FROM students_master WHERE student_id=?", conn, params=(search_id,))
            
            if not df_name.empty:
                student_name = df_name.iloc[0]['name']
                st.subheader(f"ملف المتابعة للطالب/ة: {student_name}")

                # عرض السجل السلوكي اليومي (جدول)
                st.markdown("#### 🗓️ السجل السلوكي اليومي")
                df_logs = pd.read_sql_query("SELECT log_date AS 'التاريخ', pos_behavior AS 'إيجابي', neg_behavior AS 'سلبي', neg_count AS 'مخالفات', reward AS 'المكافأة', notes AS 'ملاحظات' FROM daily_logs WHERE student_id=?", conn, params=(search_id,))
                if not df_logs.empty:
                    st.table(df_logs)
                else:
                    st.info("لا يوجد سجل سلوكي يومي لهذا الطالب حتى الآن.")

                # عرض الدرجات الأكاديمية (جدول مختصر)
                st.markdown("#### 📝 الدرجات الأكاديمية")
                df_grades = pd.read_sql_query("SELECT period1 AS 'الفترة الأولى', period2 AS 'الفترة الثانية', participation AS 'المشاركة', projects AS 'المشاريع', final_total AS 'المجموع الكلي' FROM academic_grades WHERE student_id=?", conn, params=(search_id,))
                if not df_grades.empty:
                    st.dataframe(df_grades, hide_index=True, use_container_width=True)
                else:
                    st.info("لم يتم إدخال الدرجات الأكاديمية بعد.")
                
            else:
                st.error("عذراً، هذا الرقم الأكاديمي غير مسجل في النظام.")
        else:
            st.warning("يرجى إدخال الرقم أولاً")
