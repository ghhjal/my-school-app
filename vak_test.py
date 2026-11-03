import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مقياس أنماط التعلم", page_icon="🧠", layout="centered")

# ==========================================
# 0. إعدادات التصميم (RTL) وتصميم التقرير
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
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
    
    /* تصميم التقرير الفردي ليطابق الصورة المرفقة */
    .report-container {
        background-color: white;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-top: 20px;
        color: #333;
    }
    .report-title { text-align: center; color: #1f77b4; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .report-subtitle { text-align: center; color: #7f8c8d; font-size: 14px; margin-bottom: 30px; }
    .section-title { font-weight: bold; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; margin-top: 20px; margin-bottom: 15px; }
    
    .bar-bg { background-color: #f0f2f6; border-radius: 10px; width: 100%; height: 15px; margin-bottom: 15px; position: relative; }
    .bar-fill-v { background-color: #3498db; height: 100%; border-radius: 10px; }
    .bar-fill-a { background-color: #e67e22; height: 100%; border-radius: 10px; }
    .bar-fill-k { background-color: #2ecc71; height: 100%; border-radius: 10px; }
    .bar-label { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;}
    
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
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
    # التأكد من وجود أعمدة الدرجات (تحسباً إذا كانت فارغة)
    for col in ['v_score', 'a_score', 'k_score']:
        if col not in df.columns: df[col] = "0"
        df[col] = df[col].fillna("0")
    return df

def get_student_by_id(student_id):
    df = get_all_students()
    return df[df['id'] == str(student_id)]

def save_result(student_id, result, v, a, k):
    df = get_all_students()
    df.loc[df['id'] == str(student_id), 'vak_result'] = result
    df.loc[df['id'] == str(student_id), 'v_score'] = str(v)
    df.loc[df['id'] == str(student_id), 'a_score'] = str(a)
    df.loc[df['id'] == str(student_id), 'k_score'] = str(k)
    conn.update(spreadsheet=SHEET_URL, data=df)

# ==========================================
# 2. الواجهة الرئيسية
# ==========================================
st.title("🧠 منصة أنماط التعلم (VAK)")
tab_student, tab_admin = st.tabs(["👨‍🎓 دخول الطلاب", "⚙️ الإدارة والتقارير"])

# ==========================================
# 3. تبويب الإدارة والتقارير
# ==========================================
with tab_admin:
    admin_password = st.text_input("كلمة المرور:", type="password", key="admin_pass", placeholder="أدخل كلمة المرور...")
    
    if admin_password == "admin123":
        df_all = get_all_students()
        df_tested = df_all[df_all['vak_result'] != 'غير مختبر'].copy()
        
        # تحويل الدرجات لأرقام للعمليات الحسابية
        for col in ['v_score', 'a_score', 'k_score']:
            df_tested[col] = pd.to_numeric(df_tested[col], errors='coerce').fillna(0)
            
        st.markdown("### 🎛️ مركز التقارير والإدارة")
        section = st.selectbox("اختر التقرير المطلوب:", [
            "🏫 التقرير الإحصائي للمدرسة",
            "📊 التقرير الجماعي للفصل",
            "📄 التقرير الفردي للطالب (طباعة)",
            "👥 إدارة قائمة الطلاب"
        ])
        st.markdown("---")
        
        # ------------------------------------
        # أ. التقرير الإحصائي للمدرسة
        # ------------------------------------
        if section == "🏫 التقرير الإحصائي للمدرسة":
            st.subheader("إحصائيات المدرسة العامة")
            total = len(df_all)
            tested = len(df_tested)
            participation = round((tested / total * 100) if total > 0 else 0, 1)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الطلاب", total)
            c2.metric("الاختبارات المكتملة", tested)
            c3.metric("نسبة المشاركة", f"{participation}%")
            
            if tested > 0:
                v_count = len(df_tested[df_tested['vak_result'].str.contains('بصري', na=False)])
                a_count = len(df_tested[df_tested['vak_result'].str.contains('سمعي', na=False)])
                k_count = len(df_tested[df_tested['vak_result'].str.contains('حركي', na=False)])
                
                st.markdown("#### التوزيع الكلي لأنماط التعلم:")
                st.bar_chart({"بصري 👁️": v_count, "سمعي 👂": a_count, "حركي 🏃‍♂️": k_count})
                
                st.markdown("#### مقارنة الإنجاز بين الفصول:")
                class_stats = df_all.groupby('class_name').apply(
                    lambda x: pd.Series({
                        'الإجمالي': len(x),
                        'المختبرين': len(x[x['vak_result'] != 'غير مختبر']),
                        'نسبة الإنجاز %': round((len(x[x['vak_result'] != 'غير مختبر']) / len(x)) * 100, 1) if len(x) > 0 else 0
                    })
                ).reset_index()
                st.dataframe(class_stats, use_container_width=True, hide_index=True)

        # ------------------------------------
        # ب. التقرير الجماعي للفصل
        # ------------------------------------
        elif section == "📊 التقرير الجماعي للفصل":
            st.subheader("تقرير الفصل الشامل")
            classes = list(df_all['class_name'].dropna().unique())
            selected_class = st.selectbox("اختر الفصل:", classes)
            
            df_class = df_all[df_all['class_name'] == selected_class].copy()
            df_class_tested = df_class[df_class['vak_result'] != 'غير مختبر'].copy()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي طلاب الفصل", len(df_class))
            c2.metric("أدوا الاختبار", len(df_class_tested))
            c3.metric("لم يؤدوا الاختبار", len(df_class) - len(df_class_tested))
            
            if len(df_class_tested) > 0:
                st.markdown("#### توزيع أنماط التعلم في هذا الفصل:")
                vc = df_class_tested['vak_result'].value_counts()
                st.bar_chart(vc)
                
                st.markdown("#### تفصيل نتائج الطلاب:")
                # استخراج الطلاب ذوي النتائج المتقاربة
                df_class_tested['v_score'] = pd.to_numeric(df_class_tested['v_score'], errors='coerce').fillna(0)
                df_class_tested['a_score'] = pd.to_numeric(df_class_tested['a_score'], errors='coerce').fillna(0)
                df_class_tested['k_score'] = pd.to_numeric(df_class_tested['k_score'], errors='coerce').fillna(0)
                
                def check_mixed(row):
                    scores = [row['v_score'], row['a_score'], row['k_score']]
                    scores.sort(reverse=True)
                    if scores[0] - scores[1] <= 1: # إذا كان الفرق بين الأعلى والذي يليه نقطة واحدة أو أقل
                        return "نعم (نمط مزدوج)"
                    return "لا (نمط واضح)"
                    
                df_class_tested['نتيجة متقاربة؟'] = df_class_tested.apply(check_mixed, axis=1)
                
                display_cols = df_class_tested[['id', 'name', 'vak_result', 'نتيجة متقاربة؟']].rename(
                    columns={'id': 'الرقم', 'name': 'الاسم', 'vak_result': 'النمط الغالب'})
                st.dataframe(display_cols, use_container_width=True, hide_index=True)

        # ------------------------------------
        # ج. التقرير الفردي (تصميم متطابق مع الصورة)
        # ------------------------------------
        elif section == "📄 التقرير الفردي للطالب (طباعة)":
            st.subheader("استخراج تقرير الطالب")
            search_id = st.text_input("أدخل رقم هوية الطالب لإنشاء التقرير:")
            if search_id:
                student = df_all[df_all['id'] == str(search_id)]
                if not student.empty:
                    s = student.iloc[0]
                    if s['vak_result'] == 'غير مختبر':
                        st.warning("هذا الطالب لم يجرِ الاختبار بعد.")
                    else:
                        # حساب النسب من 10 أسئلة
                        v_pct = int(s['v_score']) * 10
                        a_pct = int(s['a_score']) * 10
                        k_pct = int(s['k_score']) * 10
                        
                        # تحديد التوصيات بناءً على النمط الأعلى
                        if "بصري" in s['vak_result']:
                            summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل البصرية."
                            recs = "<li>استخدام الصور والخرائط الذهنية.</li><li>الاعتماد على العروض المرئية والفيديوهات.</li><li>استخدام الألوان في التلخيص.</li>"
                        elif "سمعي" in s['vak_result']:
                            summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل السمعية."
                            recs = "<li>توظيف الشرح الشفهي والنقاش.</li><li>الاعتماد على التسجيلات الصوتية.</li><li>تشجيع الطالب على القراءة بصوت مسموع.</li>"
                        else:
                            summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل الحركية والعملية."
                            recs = "<li>دمج الأنشطة والتطبيقات العملية.</li><li>السماح بالحركة أثناء التعلم أو استخدام المجسمات.</li><li>تطبيق استراتيجية لعب الأدوار.</li>"

                        # رسم التقرير الفردي بـ HTML ليطابق الصورة
                        report_html = f"""
                        <div class="report-container">
                            <div class="report-title">تقرير قياس أنماط التعلم</div>
                            <div class="report-subtitle">VAK Learning Preferences Report</div>
                            
                            <div class="section-title">بيانات الطالب</div>
                            <ul style="list-style-type: none; padding: 0;">
                                <li><b>اسم الطالب:</b> {s['name']}</li>
                                <li><b>الصف والشعبة:</b> {s['grade']} - {s['class_name']}</li>
                                <li><b>الرقم المدرسي (الهوية):</b> {s['id']}</li>
                            </ul>
                            
                            <div class="section-title">نتائج الاختبار</div>
                            
                            <div class="bar-label"><span>بصري Visual</span> <span>{v_pct}%</span></div>
                            <div class="bar-bg"><div class="bar-fill-v" style="width: {v_pct}%;"></div></div>
                            
                            <div class="bar-label"><span>سمعي Auditory</span> <span>{a_pct}%</span></div>
                            <div class="bar-bg"><div class="bar-fill-a" style="width: {a_pct}%;"></div></div>
                            
                            <div class="bar-label"><span>حركي Kinesthetic</span> <span>{k_pct}%</span></div>
                            <div class="bar-bg"><div class="bar-fill-k" style="width: {k_pct}%;"></div></div>
                            
                            <div class="section-title">الملخص</div>
                            <p>{summary}</p>
                            
                            <div class="section-title">مقترحات تعليمية</div>
                            <ul>{recs}</ul>
                        </div>
                        """
                        st.markdown(report_html, unsafe_allow_html=True)
                        st.button("🖨️ اضغط (Ctrl + P) لطباعة هذا التقرير")
                else:
                    st.error("رقم الهوية غير صحيح.")
                    
        # ------------------------------------
        # د. إدارة قائمة الطلاب
        # ------------------------------------
        elif section == "👥 إدارة قائمة الطلاب":
            display_df = df_all.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة'})
            st.dataframe(display_df[['رقم الهوية', 'الاسم', 'الصف', 'الفصل', 'النتيجة']], use_container_width=True, hide_index=True)
            st.info("💡 لإضافة طلاب جدد، يرجى النسخ واللصق مباشرة داخل ملف Google Sheets الخاص بك.")

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
                    st.error("رقم الهوية غير مسجل.")

    elif st.session_state.logged_in and st.session_state.already_tested:
        student = st.session_state.student_data
        st.success(f"أهلاً بك يا **{student['name']}**")
        st.warning("✅ لقد أجريت هذا الاختبار مسبقاً، وتم حفظ نتيجتك بنجاح.")
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.session_state.already_tested = False
            st.rerun()

    elif st.session_state.logged_in and st.session_state.test_done and not st.session_state.already_tested:
        student = st.session_state.student_data
        st.balloons()
        st.success("🎉 رائع! تم إرسال نتيجتك بنجاح.")
        if st.button("خروج وإنهاء", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.session_state.already_tested = False
            st.rerun()

    elif st.session_state.logged_in and not st.session_state.test_done:
        student = st.session_state.student_data
        st.success(f"أهلاً بك: **{student['name']}**")
        st.write("أجب عن جميع الأسئلة التالية:")
        
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
                    
                    # حفظ النتيجة مع الدرجات التفصيلية الثلاثة
                    save_result(student['id'], final_result, scores["V"], scores["A"], scores["K"])
                    st.session_state.test_done = True
                    st.session_state.already_tested = False
                    st.rerun()
