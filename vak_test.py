import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. إعداد قاعدة البيانات (للتجربة)
# ==========================================
DB_NAME = "school_students.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # إنشاء جدول الطلاب إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    grade TEXT,
                    class_name TEXT,
                    vak_result TEXT
                 )''')
    
    # إضافة طلاب للتجربة (أرقام هويات افتراضية)
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

# ==========================================
# 2. إعداد المتغيرات وحالة الجلسة (Session State)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_data' not in st.session_state:
    st.session_state.student_data = None
if 'test_done' not in st.session_state:
    st.session_state.test_done = False

# تشغيل إعداد قاعدة البيانات
init_db()

# ==========================================
# 3. واجهة التطبيق
# ==========================================
st.set_page_config(page_title="مقياس أنماط التعلم - منصة زياد الذكية", page_icon="🧠", layout="centered")

st.title("🧠 مقياس أنماط التعلم (VAK)")
st.write("حدد نمط تعلمك لتساعد معلميك في تقديم الدروس بالطريقة التي تناسبك!")
st.markdown("---")

# --- واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.subheader("تسجيل الدخول للاختبار")
    student_id_input = st.text_input("أدخل رقم الهوية / الإقامة الخاص بك:", placeholder="مثال: 1111")
    
    if st.button("دخول"):
        if student_id_input:
            df_student = get_student_by_id(student_id_input)
            if not df_student.empty:
                st.session_state.student_data = df_student.iloc[0]
                st.session_state.logged_in = True
                
                # التحقق مما إذا كان الطالب قد اختبر مسبقاً
                if st.session_state.student_data['vak_result'] != 'غير مختبر':
                    st.session_state.test_done = True
                
                st.rerun()
            else:
                st.error("رقم الهوية غير مسجل في النظام، الرجاء التأكد من الرقم أو مراجعة الإدارة.")
        else:
            st.warning("الرجاء إدخال رقم الهوية أولاً.")

# --- واجهة الاختبار ---
elif st.session_state.logged_in and not st.session_state.test_done:
    student = st.session_state.student_data
    st.success(f"أهلاً بك يا بطل: **{student['name']}** | الصف: **{student['grade']}** - فصل: **{student['class_name']}**")
    st.info("الرجاء قراءة الأسئلة بعناية واختيار الإجابة التي تمثلك أكثر.")
    
    # أسئلة الاختبار (مصفوفة مبسطة لـ 5 أسئلة للتجربة)
    questions = [
        {
            "q": "1. عندما أتعلم شيئاً جديداً، أفضل أن:",
            "options": ["أشاهد المعلم يكتبه أو أرى صوراً توضيحية.", "أستمع لشرح المعلم وأتناقش معه.", "أقوم بتجربته وتطبيقه بيدي."],
            "keys": ["V", "A", "K"]
        },
        {
            "q": "2. في أوقات الفراغ، أكثر شيء أحب فعله هو:",
            "options": ["قراءة القصص المصورة أو مشاهدة التلفاز.", "الاستماع للقصص، الأناشيد، أو التحدث مع أصدقائي.", "اللعب في الخارج، الرياضة، أو الفك والتركيب."],
            "keys": ["V", "A", "K"]
        },
        {
            "q": "3. عندما أتذكر قصة سمعتها أو قرأتها، فإني أتذكر:",
            "options": ["صور وأشكال الأبطال والمكان.", "الأصوات والحوارات التي دارت.", "الأحداث وماذا فعل الأبطال وحركتهم."],
            "keys": ["V", "A", "K"]
        },
        {
            "q": "4. الطريقة التي تجعلني أحفظ بسرعة هي:",
            "options": ["الكتابة عدة مرات والتخطيط بالألوان.", "تكرار الكلام بصوت مسموع.", "المشي والحركة أثناء الحفظ."],
            "keys": ["V", "A", "K"]
        },
        {
            "q": "5. عندما يغضبني شيء ما، فإنني غالباً:",
            "options": ["أسكت ويبدو الغضب على ملامح وجهي.", "أرفع صوتي وأتحدث بسرعة.", "أتحرك كثيراً أو أضرب الأشياء."],
            "keys": ["V", "A", "K"]
        }
    ]
    
    # نموذج الاختبار باستخدام st.form حتى لا تعاد تحميل الصفحة مع كل نقرة
    with st.form("vak_form"):
        responses = []
        for i, quest in enumerate(questions):
            st.markdown(f"**{quest['q']}**")
            # إخفاء التسمية الافتراضية لزر الراديو لتصميم أنظف
            choice = st.radio(f"label_hidden_{i}", quest['options'], label_visibility="collapsed", index=None)
            responses.append({'choice': choice, 'keys': quest['keys'], 'options': quest['options']})
            st.write("---")
            
        submit_btn = st.form_submit_button("إرسال الإجابات 🚀")
        
        if submit_btn:
            # التحقق من الإجابة على جميع الأسئلة
            if None in [r['choice'] for r in responses]:
                st.error("الرجاء الإجابة على جميع الأسئلة قبل الإرسال.")
            else:
                # حساب النتيجة
                scores = {"V": 0, "A": 0, "K": 0}
                for r in responses:
                    idx = r['options'].index(r['choice'])
                    key = r['keys'][idx]
                    scores[key] += 1
                
                # تحديد النمط الغالب
                labels = {"V": "بصري (Visual) 👁️", "A": "سمعي (Auditory) 👂", "K": "حركي (Kinesthetic) 🏃‍♂️"}
                dominant_key = max(scores, key=scores.get)
                final_result = labels[dominant_key]
                
                # حفظ في قاعدة البيانات
                save_result(student['id'], final_result)
                
                st.session_state.test_done = True
                st.session_state.student_data['vak_result'] = final_result
                st.rerun()

# --- واجهة النتيجة ---
elif st.session_state.logged_in and st.session_state.test_done:
    st.success("تم تسجيل إجاباتك بنجاح! شكراً لك.")
    student = st.session_state.student_data
    
    st.markdown(f"""
    ### نتيجة مقياس أنماط التعلم الخاص بك:
    **النمط الغالب لديك هو:** 
    ## {student['vak_result']}
    
    يمكنك الآن إغلاق هذه الصفحة، سيقوم معلموك بالاطلاع على نتيجتك لتقديم الأفضل لك!
    """)
    
    if st.button("خروج"):
        st.session_state.logged_in = False
        st.session_state.student_data = None
        st.session_state.test_done = False
        st.rerun()
