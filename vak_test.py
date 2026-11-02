import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. إعداد قاعدة البيانات (مستقلة لهذا التطبيق)
# ==========================================
DB_NAME = "vak_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    grade TEXT,
                    class_name TEXT,
                    vak_result TEXT
                 )''')
    
    # بيانات تجريبية تُضاف فقط إذا كانت القاعدة فارغة
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] == 0:
        sample_students = [
            ('1111', 'أحمد محمد', 'الأول متوسط', 'أ/1', 'غير مختبر'),
            ('2222', 'خالد عبدالله', 'الثالث الابتدائي', 'ج/3', 'غير مختبر'),
            ('3333', 'سعد فهد', 'الخامس الابتدائي', 'ب/5', 'غير مختبر')
        ]
        c.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?)", sample_students)
        conn.commit()
    conn.close()

def get_student_by_id(student_id):
    conn = sqlite3.connect(DB_NAME)
    student = pd.read_sql_query(f"SELECT * FROM students WHERE id = '{student_id}'", conn)
    conn.close()
    return student

def save_result(student_id, result):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE students SET vak_result = ? WHERE id = ?", (result, student_id))
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id AS 'رقم الهوية', name AS 'اسم الطالب', grade AS 'الصف', class_name AS 'الفصل', vak_result AS 'النتيجة' FROM students", conn)
    conn.close()
    return df

# ==========================================
# 2. إعداد الصفحة الأساسية
# ==========================================
st.set_page_config(page_title="مقياس أنماط التعلم", page_icon="🧠", layout="wide")

init_db()

# ==========================================
# 3. القائمة الجانبية: لوحة تحكم الإدارة (Admin Panel)
# ==========================================
with st.sidebar:
    st.header("⚙️ دخول المعلمين والإدارة")
    admin_password = st.text_input("كلمة المرور للوحة التحكم:", type="password")
    
    # يمكنك تغيير كلمة المرور هذه إلى أي كلمة تريدها
    is_admin = (admin_password == "admin123") 

# ==========================================
# 4. مسار الإدارة (يظهر فقط عند إدخال الباسورد الصحيح)
# ==========================================
if is_admin:
    st.title("📊 لوحة تحكم نتائج أنماط التعلم")
    st.success("تم تسجيل الدخول كمسؤول بنجاح.")
    
    df_all = get_all_students()
    
    # أدوات الفلترة
    col1, col2 = st.columns(2)
    with col1:
        classes = ["الكل"] + list(df_all['الفصل'].unique())
        selected_class = st.selectbox("فرز حسب الفصل:", classes)
    
    with col2:
        status = ["الكل", "مختبر", "غير مختبر"]
        selected_status = st.selectbox("حالة الاختبار:", status)
    
    # تطبيق الفلاتر
    filtered_df = df_all.copy()
    if selected_class != "الكل":
        filtered_df = filtered_df[filtered_df['الفصل'] == selected_class]
    
    if selected_status == "مختبر":
        filtered_df = filtered_df[filtered_df['النتيجة'] != "غير مختبر"]
    elif selected_status == "غير مختبر":
        filtered_df = filtered_df[filtered_df['النتيجة'] == "غير مختبر"]
    
    st.write(f"عدد الطلاب في هذا العرض: **{len(filtered_df)}**")
    
    # عرض الجدول
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # زر تصدير النتائج إلى Excel/CSV لطباعتها
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 تحميل التقرير (CSV) لطباعته",
        data=csv,
        file_name='VAK_Results.csv',
        mime='text/csv',
    )

# ==========================================
# 5. مسار الطلاب (الواجهة الرئيسية للاختبار)
# ==========================================
else:
    # --- إدارة حالة الجلسة للطالب ---
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'student_data' not in st.session_state:
        st.session_state.student_data = None
    if 'test_done' not in st.session_state:
        st.session_state.test_done = False

    st.title("🧠 مقياس أنماط التعلم (VAK)")
    st.write("حدد نمط تعلمك لتساعد معلميك في تقديم الدروس بالطريقة التي تناسبك!")
    st.markdown("---")

    # --- واجهة تسجيل دخول الطالب ---
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("الرجاء إدخال رقم الهوية للبدء")
            student_id_input = st.text_input("رقم الهوية / الإقامة:", placeholder="أدخل رقمك هنا...")
            
            if st.button("تسجيل الدخول للاختبار", use_container_width=True):
                if student_id_input:
                    df_student = get_student_by_id(student_id_input)
                    if not df_student.empty:
                        st.session_state.student_data = df_student.iloc[0]
                        st.session_state.logged_in = True
                        if st.session_state.student_data['vak_result'] != 'غير مختبر':
                            st.session_state.test_done = True
                        st.rerun()
                    else:
                        st.error("رقم الهوية غير مسجل، راجع إدارة المدرسة.")
                else:
                    st.warning("أدخل الرقم أولاً.")

    # --- واجهة إجراء الاختبار ---
    elif st.session_state.logged_in and not st.session_state.test_done:
        student = st.session_state.student_data
        st.success(f"أهلاً بك: **{student['name']}** | **{student['grade']}** - فصل: **{student['class_name']}**")
        
        questions = [
            {"q": "1. عندما أتعلم شيئاً جديداً، أفضل أن:", "options": ["أشاهد المعلم يكتبه على السبورة.", "أستمع لشرح المعلم وأتناقش معه.", "أقوم بتجربته وتطبيقه بيدي."], "keys": ["V", "A", "K"]},
            {"q": "2. في أوقات الفراغ، أحب:", "options": ["قراءة القصص أو مشاهدة التلفاز.", "الاستماع للأناشيد أو التحدث.", "اللعب والرياضة والفك والتركيب."], "keys": ["V", "A", "K"]},
            {"q": "3. الطريقة الأسهل لي للحفظ هي:", "options": ["الكتابة والتخطيط بالألوان.", "تكرار الكلام بصوت مسموع.", "المشي والحركة أثناء الحفظ."], "keys": ["V", "A", "K"]}
        ]
        
        with st.form("vak_form"):
            responses = []
            for i, quest in enumerate(questions):
                st.markdown(f"**{quest['q']}**")
                choice = st.radio(f"q_{i}", quest['options'], label_visibility="collapsed", index=None)
                responses.append({'choice': choice, 'keys': quest['keys'], 'options': quest['options']})
                st.write("---")
                
            if st.form_submit_button("إرسال النتيجة 🚀"):
                if None in [r['choice'] for r in responses]:
                    st.error("أجب على جميع الأسئلة.")
                else:
                    scores = {"V": 0, "A": 0, "K": 0}
                    for r in responses:
                        idx = r['options'].index(r['choice'])
                        scores[r['keys'][idx]] += 1
                    
                    labels = {"V": "بصري 👁️", "A": "سمعي 👂", "K": "حركي 🏃‍♂️"}
                    final_result = labels[max(scores, key=scores.get)]
                    
                    save_result(student['id'], final_result)
                    st.session_state.test_done = True
                    st.session_state.student_data['vak_result'] = final_result
                    st.rerun()

    # --- واجهة النتيجة النهائية ---
    elif st.session_state.logged_in and st.session_state.test_done:
        student = st.session_state.student_data
        st.success("تم تسجيل نتيجتك بنجاح!")
        st.markdown(f"### النمط الغالب لديك هو: **{student['vak_result']}**")
        if st.button("خروج"):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.rerun()
