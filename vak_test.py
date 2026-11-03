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
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio, .stSelectbox {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Arial', sans-serif;
    }
    
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
    
    /* تنسيق بطاقات الإحصائيات */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
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
# 2. الواجهة الرئيسية
# ==========================================
st.title("🧠 مقياس أنماط التعلم (VAK)")
st.write("مرحباً بك! حدد نمط تعلمك لتساعد معلميك في تقديم الدروس بالطريقة التي تناسبك.")
st.markdown("---")

tab_student, tab_admin = st.tabs(["👨‍🎓 دخول الطلاب", "⚙️ لوحة الإدارة"])

# ==========================================
# 3. تبويب لوحة الإدارة (المركزية)
# ==========================================
with tab_admin:
    st.header("تسجيل دخول الإدارة")
    admin_password = st.text_input("كلمة المرور:", type="password", key="admin_pass", placeholder="أدخل كلمة مرور الإدارة...")
    
    if admin_password == "admin123":
        st.success("✅ تم تسجيل الدخول كمسؤول.")
        df_all = get_all_students()
        
        # قائمة التنقل الذكية للجوال
        st.markdown("### 🎛️ مركز إدارة النظام")
        section = st.selectbox("اختر القسم الذي تود إدارته:", [
            "📊 الإحصائيات العامة",
            "👥 إدارة الطلاب",
            "📝 سجل الاختبارات",
            "📄 تقارير الطلاب",
            "💾 إدارة البيانات",
            "👨‍🏫 إدارة المعلمين (قريباً)",
            "🛡️ الأمان والصلاحيات (قريباً)",
            "❓ إدارة الأسئلة (قريباً)"
        ])
        
        st.markdown("---")
        
        # ------------------------------------
        # قسم 1: الإحصائيات العامة
        # ------------------------------------
        if section == "📊 الإحصائيات العامة":
            st.subheader("نظرة عامة على الأداء والتوزيع")
            
            total_students = len(df_all)
            tested = len(df_all[df_all['vak_result'] != 'غير مختبر'])
            untested = total_students - tested
            
            v_count = len(df_all[df_all['vak_result'].str.contains('بصري', na=False)])
            a_count = len(df_all[df_all['vak_result'].str.contains('سمعي', na=False)])
            k_count = len(df_all[df_all['vak_result'].str.contains('حركي', na=False)])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("إجمالي الطلاب", total_students)
            col2.metric("أكملوا الاختبار", tested)
            col3.metric("لم يختبروا", untested)
            
            st.markdown("#### توزيع أنماط التعلم:")
            c1, c2, c3 = st.columns(3)
            c1.metric("👁️ بصري", v_count)
            c2.metric("👂 سمعي", a_count)
            c3.metric("🏃‍♂️ حركي", k_count)

        # ------------------------------------
        # قسم 2: إدارة الطلاب
        # ------------------------------------
        elif section == "👥 إدارة الطلاب":
            st.subheader("قائمة الطلاب والفصول")
            
            display_df = df_all.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة'})
            
            classes = ["الكل"] + list(display_df['الفصل'].dropna().unique())
            selected_class = st.selectbox("فرز حسب الفصل:", classes, key="filter_class")
            
            if selected_class != "الكل":
                display_df = display_df[display_df['الفصل'] == selected_class]
                
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info("💡 لإضافة طلاب جدد أو حذفهم، يرجى التعديل مباشرة على ملف Google Sheets لضمان استقرار القاعدة.")

        # ------------------------------------
        # قسم 3: سجل الاختبارات
        # ------------------------------------
        elif section == "📝 سجل الاختبارات":
            st.subheader("الطلاب المنجزين للاختبار")
            tested_df = df_all[df_all['vak_result'] != 'غير مختبر']
            display_tested = tested_df.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة'})
            
            st.write(f"عدد الطلاب المنجزين: **{len(display_tested)}**")
            st.dataframe(display_tested, use_container_width=True, hide_index=True)

        # ------------------------------------
        # قسم 4: تقارير الطلاب
        # ------------------------------------
        elif section == "📄 تقارير الطلاب":
            st.subheader("البحث الفردي عن طالب")
            search_id = st.text_input("أدخل رقم هوية الطالب للبحث:")
            if search_id:
                student = df_all[df_all['id'] == str(search_id)]
                if not student.empty:
                    s_data = student.iloc[0]
                    st.success(f"الاسم: {s_data['name']} | الصف: {s_data['grade']} | الفصل: {s_data['class_name']}")
                    st.info(f"النتيجة: **{s_data['vak_result']}**")
                else:
                    st.error("لم يتم العثور على طالب بهذا الرقم.")

        # ------------------------------------
        # قسم 5: إدارة البيانات
        # ------------------------------------
        elif section == "💾 إدارة البيانات":
            st.subheader("تصدير قاعدة البيانات")
            st.write("يمكنك تحميل نسخة احتياطية من جميع النتائج والبيانات بصيغة Excel (CSV).")
            display_df = df_all.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة'})
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 تحميل النسخة الاحتياطية (CSV)", data=csv, file_name='VAK_Full_Backup.csv', mime='text/csv', use_container_width=True)

        # ------------------------------------
        # الأقسام المستقبلية (Placeholders)
        # ------------------------------------
        else:
            st.info(f"🚧 قسم **{section.replace(' (قريباً)', '')}** قيد التطوير.")
            st.write("سيتم تفعيل هذه الميزة في التحديث القادم للنظام لتعمل بشكل مستقل وموثوق.")
            
    elif admin_password:
        st.error("كلمة المرور غير صحيحة.")

# ==========================================
# 4. تبويب دخول الطلاب (الاختبار)
# ==========================================
with tab_student:
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'student_data' not in st.session_state: st.session_state.student_data = None
    if 'test_done' not in st.session_state: st.session_state.test_done = False
    if 'already_tested' not in st.session_state: st.session_state.already_tested = False

    if not st.session_state.logged_in:
        st.info("الرجاء إدخال رقم الهوية للبدء")
        student_id_input = st.text_input("رقم الهوية / الإقامة:", placeholder="أدخل رقمك هنا...")
        
        if st.button("تسجيل الدخول للاختبار 🚀", use_container_width=True):
            if student_id_input:
                df_student = get_student_by_id(student_id_input)
                if not df_student.empty:
                    st.session_state.student_data = df_student.iloc[0]
                    st.session_state.logged_in = True
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

    elif st.session_state.logged_in and not st.session_state.test_done:
        student = st.session_state.student_data
        st.success(f"أهلاً بك: **{student['name']}** | الصف: **{student['grade']}**")
        st.write("أجب عن جميع الأسئلة التالية بصراحة:")
        
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
