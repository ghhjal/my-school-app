import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="مقياس أنماط التعلم", page_icon="🧠", layout="wide")

# ==========================================
# 1. الاتصال بـ Google Sheets
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# ضع رابط ملف جوجل شيت الخاص بالاختبار هنا
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit?gid=0#gid=0"

def get_all_students():
    # قراءة البيانات مع تحديد الرابط صراحة
    df = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
    # ملء الفراغات بكلمة غير مختبر لتجنب الأخطاء
    df['vak_result'] = df['vak_result'].fillna("غير مختبر")
    return df

def get_student_by_id(student_id):
    df = get_all_students()
    student = df[df['id'] == str(student_id)]
    return student

def save_result(student_id, result):
    df = get_all_students()
    # تحديث الخلية الخاصة بنتيجة الطالب المطابق
    df.loc[df['id'] == str(student_id), 'vak_result'] = result
    # إرسال التحديث إلى جوجل شيت مع تحديد الرابط صراحة
    conn.update(spreadsheet=SHEET_URL, data=df)

# ==========================================
# 2. القائمة الجانبية: لوحة تحكم الإدارة
# ==========================================
with st.sidebar:
    st.header("⚙️ دخول المعلمين والإدارة")
    admin_password = st.text_input("كلمة المرور للوحة التحكم:", type="password")
    is_admin = (admin_password == "admin123") 

# ==========================================
# 3. مسار الإدارة
# ==========================================
if is_admin:
    st.title("📊 لوحة تحكم نتائج أنماط التعلم")
    st.success("تم تسجيل الدخول كمسؤول بنجاح.")
    
    df_all = get_all_students()
    
    # تغيير أسماء الأعمدة للعرض باللغة العربية
    display_df = df_all.rename(columns={
        'id': 'رقم الهوية', 
        'name': 'اسم الطالب', 
        'grade': 'الصف', 
        'class_name': 'الفصل', 
        'vak_result': 'النتيجة'
    })
    
    col1, col2 = st.columns(2)
    with col1:
        classes = ["الكل"] + list(display_df['الفصل'].unique())
        selected_class = st.selectbox("فرز حسب الفصل:", classes)
    
    with col2:
        status = ["الكل", "مختبر", "غير مختبر"]
        selected_status = st.selectbox("حالة الاختبار:", status)
    
    filtered_df = display_df.copy()
    if selected_class != "الكل":
        filtered_df = filtered_df[filtered_df['الفصل'] == selected_class]
    
    if selected_status == "مختبر":
        filtered_df = filtered_df[filtered_df['النتيجة'] != "غير مختبر"]
    elif selected_status == "غير مختبر":
        filtered_df = filtered_df[filtered_df['النتيجة'] == "غير مختبر"]
    
    st.write(f"عدد الطلاب في هذا العرض: **{len(filtered_df)}**")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 تحميل التقرير (CSV) لطباعته", data=csv, file_name='VAK_Results.csv', mime='text/csv')

# ==========================================
# 4. مسار الطلاب (الواجهة الرئيسية للاختبار)
# ==========================================
else:
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'student_data' not in st.session_state:
        st.session_state.student_data = None
    if 'test_done' not in st.session_state:
        st.session_state.test_done = False

    st.title("🧠 مقياس أنماط التعلم (VAK)")
    st.write("حدد نمط تعلمك لتساعد معلميك في تقديم الدروس بالطريقة التي تناسبك!")
    st.markdown("---")

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

    elif st.session_state.logged_in and st.session_state.test_done:
        student = st.session_state.student_data
        st.success("تم تسجيل نتيجتك بنجاح!")
        st.markdown(f"### النمط الغالب لديك هو: **{student['vak_result']}**")
        if st.button("خروج"):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.rerun()
