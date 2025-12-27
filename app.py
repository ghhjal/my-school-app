import streamlit as st
import pandas as pd
import sqlite3

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام مدرستي الإلكتروني", layout="wide")

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_v2.db')
    c = conn.cursor()
    # إنشاء جدول الطلاب إذا لم يكن موجوداً (أضفنا رقم الطالب كمعرف فريد)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (student_id TEXT PRIMARY KEY, name TEXT, subject TEXT, score INTEGER, grade TEXT)''')
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect('school_v2.db')
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

# --- واجهة البرنامج الرئيسية ---
init_db()
st.title("🏫 نظام النتائج المدرسية الذكي")

# القائمة الجانبية للتنقل
menu = st.sidebar.selectbox("اختر نوع الدخول:", ["لوحة الطالب (استعلام)", "لوحة المعلم (إدارة)"])

# ------------------- لوحة المعلم -------------------
if menu == "لوحة المعلم (إدارة)":
    st.header("👨‍🏫 لوحة التحكم الخاصة بالمعلم")
    
    tab1, tab2, tab3 = st.tabs(["إضافة طالب", "تعديل/حذف", "عرض الكل"])
    
    with tab1:
        with st.form("add_form"):
            s_id = st.text_input("رقم الطالب (Unique ID)")
            s_name = st.text_input("اسم الطالب")
            s_subject = st.selectbox("المادة", ["الرياضيات", "العلوم", "اللغة العربية", "الإنجليزية"])
            s_score = st.number_input("الدرجة", 0, 100, 50)
            submit = st.form_submit_button("إضافة للمنظومة")
            
            if submit:
                if s_id and s_name:
                    # حساب التقدير
                    if s_score >= 90: g = "ممتاز"
                    elif s_score >= 80: g = "جيد جداً"
                    elif s_score >= 50: g = "ناجح"
                    else: g = "راسب"
                    
                    try:
                        conn = sqlite3.connect('school_v2.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (s_id, s_name, s_subject, s_score, g))
                        conn.commit()
                        st.success(f"تم تسجيل الطالب {s_name} بنجاح")
                    except:
                        st.error("رقم الطالب موجود مسبقاً! استخدم رقم آخر أو عدل البيانات.")
                else:
                    st.warning("يرجى ملء جميع الحقول")

    with tab2:
        st.subheader("تعديل أو حذف بيانات")
        df = get_all_data()
        if not df.empty:
            selected_id = st.selectbox("اختر رقم الطالب للتعديل/الحذف", df['student_id'].tolist())
            current_data = df[df['student_id'] == selected_id].iloc[0]
            
            new_name = st.text_input("الاسم الجديد", value=current_data['name'])
            new_score = st.number_input("الدرجة الجديدة", 0, 100, int(current_data['score']))
            
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("تحديث البيانات"):
                    # تحديث التقدير
                    if new_score >= 90: g = "ممتاز"
                    elif new_score >= 80: g = "جيد جداً"
                    elif new_score >= 50: g = "ناجح"
                    else: g = "راسب"
                    
                    conn = sqlite3.connect('school_v2.db')
                    c = conn.cursor()
                    c.execute("UPDATE students SET name=?, score=?, grade=? WHERE student_id=?", (new_name, new_score, g, selected_id))
                    conn.commit()
                    st.success("تم التحديث!")
                    st.rerun()
            
            with col_del:
                if st.button("حذف الطالب نهائياً", type="primary"):
                    conn = sqlite3.connect('school_v2.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM students WHERE student_id=?", (selected_id,))
                    conn.commit()
                    st.warning("تم الحذف!")
                    st.rerun()

    with tab3:
        st.subheader("قائمة الطلاب الحالية")
        df_all = get_all_data()
        st.dataframe(df_all, use_container_width=True)

# ------------------- لوحة الطالب -------------------
elif menu == "لوحة الطالب (استعلام)":
    st.header("🎓 استعلام عن النتيجة")
    st.info("أدخل رقمك الأكاديمي للحصول على درجتك")
    
    search_id = st.text_input("أدخل رقم الطالب الخاص بك:")
    
    if st.button("عرض النتيجة"):
        if search_id:
            conn = sqlite3.connect('school_v2.db')
            df = pd.read_sql_query("SELECT * FROM students WHERE student_id=?", conn, params=(search_id,))
            conn.close()
            
            if not df.empty:
                student = df.iloc[0]
                st.balloons() # حركة احتفالية
                
                # عرض النتيجة بشكل جميل
                col1, col2, col3 = st.columns(3)
                col1.metric("اسم الطالب", student['name'])
                col2.metric("المادة", student['subject'])
                col3.metric("الدرجة النهائية", f"{student['score']}%")
                
                if student['score'] >= 50:
                    st.success(f"مبارك النجاح! تقديرك هو: {student['grade']}")
                else:
                    st.error(f"للأسف تقديرك: {student['grade']}. حظاً أوفر في المرة القادمة.")
            else:
                st.error("عذراً، هذا الرقم غير مسجل في النظام. تأكد من الرقم أو راجع المعلم.")
        else:
            st.warning("يرجى إدخال الرقم أولاً")
