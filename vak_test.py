import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# إعدادات الصفحة
st.set_page_config(page_title="مقياس أنماط التعلم", page_icon="🧠", layout="centered")

# ==========================================
# 0. إعدادات التصميم (RTL) ودعم الجوال
# ==========================================
st.markdown("""
<style>
    /* توجيه كامل التطبيق من اليمين لليسار */
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Arial', sans-serif;
    }
    
    /* تنسيق أزرار التبويبات لتكون واضحة في الجوال */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: space-evenly;
        direction: rtl;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: bold;
        font-size: 16px;
    }
    
    /* إخفاء القائمة العلوية الافتراضية الخاصة بـ Streamlit لتنظيف الواجهة للجوال */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. الاتصال بـ Google Sheets
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit#gid=0"

def get_all_students():
    df = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
    df['vak_result'] = df['vak_result'].fillna("غير مختبر")
    return df

def get_student_by_id(student_id):
    df = get_all_students()
    return df[df['id'] == str(student_id)]

def save_result(student_id, result):
    df = get_all_students()
    df.loc[df['id'] == str(student_id), 'vak_result'] = result
    conn.update(spreadsheet=SHEET_URL, data=df)

# ==========================================
# 2. الواجهة الرئيسية (التبويبات بدلاً من القائمة الجانبية)
# ==========================================
st.title("🧠 مقياس أنماط التعلم (VAK)")
st.write("مرحباً بك! حدد نمط تعلمك لتساعد معلميك في تقديم الدروس بالطريقة التي تناسبك.")
st.markdown("---")

# إنشاء تبويبين
tab_student, tab_admin = st.tabs(["👨‍🎓 دخول الطلاب", "⚙️ لوحة الإدارة"])

# ==========================================
# 3. تبويب لوحة الإدارة
# ==========================================
with tab_admin:
    st.header("تسجيل دخول المعلمين")
    admin_password = st.text_input("كلمة المرور للوحة التحكم:", type="password", key="admin_pass")
    
    if admin_password == "admin123":
        st.success("تم تسجيل الدخول كمسؤول بنجاح.")
        df_all = get_all_students()
        
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
            selected_class = st.selectbox("فرز حسب الفصل:", classes, key="filter_class")
        with col2:
            status = ["الكل", "مختبر", "غير مختبر"]
            selected_status = st.selectbox("حالة الاختبار:", status, key="filter_status")
        
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
        st.download_button(label="📥 تحميل التقرير (CSV)", data=csv, file_name='VAK_Results.csv', mime='text/csv', use_container_width=True)
    elif admin_password:
        st.error("كلمة المرور غير صحيحة.")

# ==========================================
# 4. تبويب دخول الطلاب (الاختبار)
# ==========================================
with tab_student:
    # تهيئة متغيرات الجلسة
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'student_data' not in st.session_state:
        st.session_state.student_data = None
    if 'test_done' not in st.session_state:
        st.session_state.test_done = False
    if 'already_tested' not in st.session_state:
        st.session_state.already_tested = False

    # حالة 1: لم يسجل الدخول بعد
    if not st.session_state.logged_in:
        st.info("الرجاء إدخال رقم الهوية للبدء")
        student_id_input = st.text_input("رقم الهوية / الإقامة:", placeholder="أدخل رقمك هنا...")
        
        if st.button("تسجيل الدخول للاختبار 🚀", use_container_width=True):
            if student_id_input:
                df_student = get_student_by_id(student_id_input)
                if not df_student.empty:
                    st.session_state.student_data = df_student.iloc[0]
                    st.session_state.logged_in = True
                    
                    # التحقق مما إذا كان الطالب قد أجرى الاختبار مسبقاً
                    if st.session_state.student_data['vak_result'] != 'غير مختبر':
                        st.session_state.test_done = True
                        st.session_state.already_tested = True
                    else:
                        st.session_state.test_done = False
                        st.session_state.already_tested = False
                        
                    st.rerun()
                else:
                    st.error("رقم الهوية غير مسجل، راجع إدارة المدرسة.")
            else:
                st.warning("أدخل الرقم أولاً.")

    # حالة 2: سجل الدخول وكان قد اختبر مسبقاً
    elif st.session_state.logged_in and st.session_state.already_tested:
        student = st.session_state.student_data
        st.success(f"أهلاً بك يا **{student['name']}**")
        st.warning("✅ لقد أجريت هذا الاختبار مسبقاً، وتم حفظ نتيجتك بنجاح.")
        st.markdown(f"<h3 style='text-align: center;'>نمط التعلم الخاص بك هو: <br><br> <b>{student['vak_result']}</b></h3>", unsafe_allow_html=True)
        
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.session_state.already_tested = False
            st.rerun()

    # حالة 3: سجل الدخول وأنهى الاختبار للتو (رسالة النجاح)
    elif st.session_state.logged_in and st.session_state.test_done and not st.session_state.already_tested:
        student = st.session_state.student_data
        st.balloons()
        st.success("🎉 رائع! تم إرسال نتيجتك وحفظها بنجاح.")
        st.markdown(f"<h3 style='text-align: center;'>النمط الغالب لديك هو: <br><br> <b>{student['vak_result']}</b></h3>", unsafe_allow_html=True)
        
        if st.button("خروج وإنهاء", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.session_state.already_tested = False
            st.rerun()

    # حالة 4: سجل الدخول ويقوم بإجراء الاختبار الآن (الأسئلة العشرة)
    elif st.session_state.logged_in and not st.session_state.test_done:
        student = st.session_state.student_data
        st.success(f"أهلاً بك: **{student['name']}** | الصف: **{student['grade']}**")
        
        st.write("أجب عن جميع الأسئلة التالية بصراحة:")
        
        # 10 أسئلة احترافية مخصصة لأنماط التعلم (VAK)
        questions = [
            {"q": "1. عندما أتعلم درساً جديداً، أفضل أن:", "options": ["أشاهد صوراً أو فيديو أو أقرأ من السبورة.", "أستمع لشرح المعلم وأردد المعلومات.", "أقوم بتجربة الأمر بنفسي وأتحرك."], "keys": ["V", "A", "K"]},
            {"q": "2. عندما أقرأ قصة، فإنني غالباً:", "options": ["أتخيل الأحداث والصور في عقلي كأنها فيلم.", "أقرأ بصوت مسموع أو أحرك شفتي أثناء القراءة.", "أشعر بالملل من الجلوس وأحب أن أتحرك أثناء القراءة."], "keys": ["V", "A", "K"]},
            {"q": "3. ما هو أكثر شيء يساعدك على حفظ المعلومات؟", "options": ["استخدام الأقلام الملونة والتخطيط على الكتاب.", "تكرار قراءة الدرس بصوت عالٍ أو الاستماع لتسجيل.", "المشي والحركة أثناء الحفظ والمراجعة."], "keys": ["V", "A", "K"]},
            {"q": "4. في وقت الفراغ، ماذا تفضل أن تفعل؟", "options": ["الرسم، التلوين، أو قراءة القصص المصورة.", "التحدث مع الأصدقاء أو الاستماع للقصص.", "ممارسة الرياضة، الركض، أو اللعب بالأشياء وتركيبها."], "keys": ["V", "A", "K"]},
            {"q": "5. عندما تريد أن تشرح لصديقك كيف يلعب لعبة جديدة، كيف تفعل ذلك؟", "options": ["أرسم له خريطة أو أجعله يشاهدني وأنا ألعب.", "أشرح له القوانين والخطوات بالكلام.", "أجعله يمسك اللعبة ويجربها بنفسه ليتعلم."], "keys": ["V", "A", "K"]},
            {"q": "6. ما الذي يشتت انتباهك أكثر وأنت تذاكر؟", "options": ["الفوضى في الغرفة أو حركة الأشخاص من حولي.", "الأصوات المزعجة والضجيج أو تحدث الآخرين.", "الجلوس لفترة طويلة على الكرسي دون حركة."], "keys": ["V", "A", "K"]},
            {"q": "7. عندما يطلب منك المعلم تركيب شيء أو حل لغز (Puzzle)، فكيف تبدأ؟", "options": ["أنظر إلى صورة الشكل النهائي أولاً لأعرف كيف يبدو.", "أسأل المعلم أو أطلب من أحد أن يخبرني بالخطوات.", "أبدأ بمسك القطع وتجربتها فوراً حتى أصل للحل."], "keys": ["V", "A", "K"]},
            {"q": "8. كيف تتذكر شخصاً قابلته من قبل؟", "options": ["أتذكر شكله وملامح وجهه، لكن قد أنسى اسمه.", "أتذكر اسمه وصوته بوضوح.", "أتذكر ماذا فعلنا معاً (أين لعبنا، كيف سلمنا على بعض)."], "keys": ["V", "A", "K"]},
            {"q": "9. عندما تشعر بالسعادة والمرح، كيف تعبر عن ذلك غالباً؟", "options": ["أبتسم كثيراً وتلمع عيناي.", "أضحك بصوت عالٍ أو أتحدث بحماس ومرح.", "أقفز، أتحرك بسرعة، أو أصفق بيدي."], "keys": ["V", "A", "K"]},
            {"q": "10. لتذكر طريقة كتابة كلمة صعبة (إملاء)، ماذا تفعل؟", "options": ["أتخيل شكل الكلمة مكتوبة في رأسي.", "أتهجى حروف الكلمة بصوت مسموع.", "أكتبها بيدي عدة مرات في ورقة خارجية حتى أتعود عليها."], "keys": ["V", "A", "K"]}
        ]
        
        with st.form("vak_form"):
            responses = []
            for i, quest in enumerate(questions):
                st.markdown(f"**{quest['q']}**")
                choice = st.radio(f"q_{i}", quest['options'], label_visibility="collapsed", index=None)
                responses.append({'choice': choice, 'keys': quest['keys'], 'options': quest['options']})
                st.write("---")
                
            if st.form_submit_button("إرسال النتيجة واعتمادها 📤", use_container_width=True):
                if None in [r['choice'] for r in responses]:
                    st.error("⚠️ الرجاء الإجابة على جميع الأسئلة قبل الإرسال.")
                else:
                    scores = {"V": 0, "A": 0, "K": 0}
                    for r in responses:
                        idx = r['options'].index(r['choice'])
                        scores[r['keys'][idx]] += 1
                    
                    labels = {"V": "بصري 👁️", "A": "سمعي 👂", "K": "حركي 🏃‍♂️"}
                    final_result = labels[max(scores, key=scores.get)]
                    
                    save_result(student['id'], final_result)
                    st.session_state.test_done = True
                    st.session_state.already_tested = False
                    st.session_state.student_data['vak_result'] = final_result
                    st.rerun()
