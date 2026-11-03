import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import base64

# ==========================================
# 1. إعدادات الصفحة والـ CSS
# ==========================================
st.set_page_config(page_title="مقياس أنماط التعلم", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio, .stSelectbox, .stTextInput {
        direction: rtl; text-align: right; font-family: 'Tajawal', 'Arial', sans-serif;
    }
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: space-evenly; direction: rtl; background-color: #f0f2f6; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الاتصال بـ Google Sheets
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit#gid=0"

# --- دوال الطلاب ---
def get_all_students():
    df = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
    if 'vak_result' not in df.columns: df['vak_result'] = "غير مختبر"
    df['vak_result'] = df['vak_result'].fillna("غير مختبر")
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

# --- دوال المعلمين ---
def get_all_teachers():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", ttl=0, dtype=str)
    return df

# ==========================================
# 3. محرك توليد تقارير HTML للطباعة
# ==========================================
def generate_html_page(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
            body {{ font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; background: #fff; color: #333; }}
            .header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ color: #2c3e50; margin: 0; }}
            .header p {{ color: #7f8c8d; margin: 5px 0 0 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #bdc3c7; padding: 12px; text-align: center; }}
            th {{ background-color: #ecf0f1; color: #2c3e50; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .summary-box {{ background: #fdfefe; border: 1px solid #e5e8e8; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size:18px; line-height:1.6;}}
            .bar-bg {{ background-color: #ecf0f1; border-radius: 5px; width: 100%; height: 15px; margin-bottom: 10px; }}
            .bar-v {{ background-color: #3498db; height: 100%; border-radius: 5px; }}
            .bar-a {{ background-color: #e67e22; height: 100%; border-radius: 5px; }}
            .bar-k {{ background-color: #2ecc71; height: 100%; border-radius: 5px; }}
            .no-print {{ text-align: center; margin-bottom: 20px; }}
            .print-btn {{ background: #2980b9; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; font-family: 'Tajawal'; }}
            @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; }} }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <button class="print-btn" onclick="window.print()">🖨️ طباعة التقرير</button>
        </div>
        <div class="header">
            <h1>{title}</h1>
            <p>تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        {content}
    </body>
    </html>
    """

def get_download_link(html_content, filename, link_text):
    b64 = base64.b64encode(html_content.encode('utf-8')).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: block; text-align: center; background-color: #27ae60; color: white; padding: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px;">{link_text}</a>'
    return href

# دالة ذكية لمعالجة النصوص (إزالة الهمزات والتاء المربوطة) لتسهيل البحث
def normalize_text(text):
    if not isinstance(text, str): return ""
    return text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').strip()

# ==========================================
# 4. الواجهة الرئيسية
# ==========================================
st.title("🧠 منصة أنماط التعلم (VAK)")
tab_student, tab_admin = st.tabs(["👨‍🎓 دخول الطلاب", "⚙️ الإدارة والمعلمين"])

# ==========================================
# 5. تبويب الإدارة والمعلمين (دخول برقم الهوية)
# ==========================================
with tab_admin:
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

    if st.session_state.current_user is None:
        st.header("تسجيل دخول الإدارة والمعلمين")
        st.info("💡 يرجى إدخال رقم الهوية الخاص بك للوصول إلى لوحة التحكم.")
        teacher_id_input = st.text_input("رقم الهوية:", placeholder="أدخل رقم هويتك هنا...")
        
        if st.button("تسجيل الدخول 🔑", use_container_width=True):
            if teacher_id_input:
                try:
                    df_teachers = get_all_teachers()
                    t_row = df_teachers[df_teachers['id'] == str(teacher_id_input)]
                    
                    if not t_row.empty:
                        t_data = t_row.iloc[0]
                        st.session_state.current_user = {
                            "name": t_data['name'],
                            "role": t_data['role'],
                            "class": t_data['class_name']
                        }
                        st.rerun()
                    else:
                        st.error("رقم الهوية غير مسجل في قاعدة بيانات المعلمين. راجع إدارة المدرسة.")
                except Exception as e:
                    st.error("⚠️ خطأ: لم يتم العثور على ورقة 'teachers' في Google Sheets. يرجى إنشاؤها أولاً.")
            else:
                st.warning("الرجاء إدخال رقم الهوية أولاً.")
    else:
        user = st.session_state.current_user
        
        if user['role'] == 'admin':
            st.success(f"أهلاً بك يا أستاذ/ة: **{user['name']}** (مدير النظام)")
        else:
            st.success(f"أهلاً بك يا أستاذ/ة: **{user['name']}**")
        
        if st.button("تسجيل الخروج", key="logout"):
            st.session_state.current_user = None
            st.rerun()
            
        df_all = get_all_students()
        df_tested = df_all[df_all['vak_result'] != 'غير مختبر'].copy()
        for col in ['v_score', 'a_score', 'k_score']:
            df_tested[col] = pd.to_numeric(df_tested[col], errors='coerce').fillna(0)

        # فلترة البيانات بناءً على صلاحية المعلم
        if user['role'] == 'teacher':
            st.info(f"صلاحياتك تتيح لك استعراض وطباعة تقارير الفصل: **{user['class']}** فقط.")
            df_all = df_all[df_all['class_name'] == str(user['class'])]
            df_tested = df_tested[df_tested['class_name'] == str(user['class'])]
            available_reports = ["📊 التقرير الجماعي للفصل", "📄 التقرير الفردي للطالب (طباعة)"]
        else:
            available_reports = ["🏫 التقرير الإحصائي للمدرسة", "📊 التقرير الجماعي للفصل", "📄 التقرير الفردي للطالب (طباعة)", "👥 إدارة قائمة الطلاب"]
            
        st.markdown("### 🎛️ مركز التقارير")
        section = st.selectbox("اختر التقرير المطلوب:", available_reports)
        st.markdown("---")
        
        # ------------------------------------
        # التقرير الإحصائي للمدرسة
        # ------------------------------------
        if section == "🏫 التقرير الإحصائي للمدرسة" and user['role'] == 'admin':
            st.subheader("إحصائيات المدرسة العامة")
            total, tested = len(df_all), len(df_tested)
            c1, c2 = st.columns(2)
            c1.metric("إجمالي الطلاب", total)
            c2.metric("الاختبارات المكتملة", tested)
            
            if tested > 0:
                v_count = len(df_tested[df_tested['vak_result'].str.contains('بصري', na=False)])
                a_count = len(df_tested[df_tested['vak_result'].str.contains('سمعي', na=False)])
                k_count = len(df_tested[df_tested['vak_result'].str.contains('حركي', na=False)])
                st.bar_chart({"بصري 👁️": v_count, "سمعي 👂": a_count, "حركي 🏃‍♂️": k_count})

        # ------------------------------------
        # التقرير الجماعي للفصل
        # ------------------------------------
        elif section == "📊 التقرير الجماعي للفصل":
            st.subheader("تقرير الفصل الشامل وتصدير الطباعة")
            if user['role'] == 'admin':
                classes = list(df_all['class_name'].dropna().unique())
                selected_class = st.selectbox("اختر الفصل:", classes)
                df_class = df_all[df_all['class_name'] == selected_class].copy()
            else:
                selected_class = user['class']
                df_class = df_all.copy()
                
            df_class_tested = df_class[df_class['vak_result'] != 'غير مختبر'].copy()
            
            st.write(f"إجمالي طلاب الفصل: **{len(df_class)}** | من أدوا الاختبار: **{len(df_class_tested)}**")
            
            if len(df_class_tested) > 0:
                display_cols = df_class_tested[['id', 'name', 'vak_result']].rename(columns={'id': 'الرقم', 'name': 'الاسم', 'vak_result': 'النمط الغالب'})
                st.dataframe(display_cols, use_container_width=True, hide_index=True)
                
                html_table = display_cols.to_html(index=False, classes="table", justify="center")
                v_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('بصري', na=False)]) / len(df_class_tested) * 100, 1)
                a_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('سمعي', na=False)]) / len(df_class_tested) * 100, 1)
                k_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('حركي', na=False)]) / len(df_class_tested) * 100, 1)
                
                class_content = f"""
                <div class="summary-box">
                    <h3>إحصائيات الفصل ({selected_class}):</h3>
                    <p>عدد الطلاب المنجزين للاختبار: {len(df_class_tested)}</p>
                    <p>نسبة النمط البصري: {v_pct}% | نسبة النمط السمعي: {a_pct}% | نسبة النمط الحركي: {k_pct}%</p>
                </div>
                <h3>قائمة الطلاب ونتائجهم:</h3>
                {html_table}
                """
                full_html = generate_html_page(f"تقرير قياس أنماط التعلم - فصل {selected_class}", class_content)
                st.markdown(get_download_link(full_html, f"Class_{selected_class}_Report.html", "📥 تحميل تقرير الفصل للطباعة (HTML)"), unsafe_allow_html=True)

        # ------------------------------------
        # التقرير الفردي (استخراج ذكي بالاسم)
        # ------------------------------------
        elif section == "📄 التقرير الفردي للطالب (طباعة)":
            st.subheader("استخراج تقرير الطالب")
            st.info("💡 اكتب أي جزء من اسم الطالب للبحث عنه (لا داعي للقلق بشأن الهمزات أو التاء المربوطة).")
            
            search_query = st.text_input("🔍 ابحث عن اسم الطالب:")
            
            if search_query:
                # تصفية الطلاب بناءً على البحث الذكي (تجاهل الهمزات)
                norm_query = normalize_text(search_query)
                matches = df_all[df_all['name'].apply(lambda x: norm_query in normalize_text(x))]
                
                if matches.empty:
                    st.warning("لم يتم العثور على طالب يطابق هذا الاسم ضمن نطاق صلاحياتك.")
                else:
                    # دمج الاسم والهوية والصف لتسهيل الاختيار في حالة تشابه الأسماء
                    options = matches['name'] + " | الهوية: " + matches['id'] + " | الصف: " + matches['grade']
                    selected_choice = st.selectbox("الطلاب المطابقين (اختر الطالب المطلوب):", options)
                    
                    if st.button("📄 إنشاء تقرير الطالب المحدد", use_container_width=True):
                        # استخراج الهوية من النص المحدد
                        exact_id = selected_choice.split("الهوية: ")[1].split(" |")[0]
                        s = df_all[df_all['id'] == exact_id].iloc[0]
                        
                        if s['vak_result'] == 'غير مختبر':
                            st.error("هذا الطالب لم يجرِ الاختبار بعد، لا يمكن استخراج تقرير له.")
                        else:
                            v_pct = int(float(s['v_score'])) * 10
                            a_pct = int(float(s['a_score'])) * 10
                            k_pct = int(float(s['k_score'])) * 10
                            
                            # تحديد التوصيات بناءً على النمط
                            if "بصري" in s['vak_result']:
                                summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل البصرية المرئية."
                                recs = "<li>استخدام الصور والخرائط الذهنية في الشرح.</li><li>الاعتماد على العروض المرئية والفيديوهات.</li><li>استخدام الألوان في التلخيص والتنظيم.</li>"
                            elif "سمعي" in s['vak_result']:
                                summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل السمعية والحوارية."
                                recs = "<li>توظيف الشرح الشفهي والنقاشات الجماعية.</li><li>الاعتماد على الترديد والتسجيلات الصوتية.</li><li>تشجيع الطالب على القراءة بصوت مسموع.</li>"
                            else:
                                summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل الحركية والعملية."
                                recs = "<li>دمج الأنشطة والتطبيقات العملية اليدوية.</li><li>السماح بالحركة أثناء التعلم أو استخدام المجسمات.</li><li>تطبيق استراتيجية لعب الأدوار.</li>"

                            student_content = f"""
                            <div class="summary-box">
                                <p><b>اسم الطالب:</b> {s['name']}</p>
                                <p><b>الصف والفصل:</b> {s['grade']} - {s['class_name']}</p>
                                <p><b>الرقم المدرسي (الهوية):</b> {s['id']}</p>
                            </div>
                            
                            <h3>النتيجة التفصيلية:</h3>
                            <div style="font-weight: bold; margin-bottom: 5px;">بصري Visual ({v_pct}%)</div>
                            <div class="bar-bg"><div class="bar-v" style="width: {v_pct}%;"></div></div>
                            
                            <div style="font-weight: bold; margin-bottom: 5px;">سمعي Auditory ({a_pct}%)</div>
                            <div class="bar-bg"><div class="bar-a" style="width: {a_pct}%;"></div></div>
                            
                            <div style="font-weight: bold; margin-bottom: 5px;">حركي Kinesthetic ({k_pct}%)</div>
                            <div class="bar-bg"><div class="bar-k" style="width: {k_pct}%;"></div></div>
                            
                            <div class="summary-box" style="margin-top: 20px;">
                                <h3 style="color:#2c3e50;">النمط الغالب: {s['vak_result']}</h3>
                                <p>{summary}</p>
                            </div>
                            
                            <h3>مقترحات تعليمية للطالب:</h3>
                            <ul style="font-size: 18px; line-height: 1.8;">{recs}</ul>
                            """
                            full_html = generate_html_page(f"التقرير الفردي - {s['name']}", student_content)
                            st.markdown(get_download_link(full_html, f"Student_{s['id']}_Report.html", f"📥 تحميل التقرير الجاهز للطباعة للطالب ({s['name']})"), unsafe_allow_html=True)
                    
        # ------------------------------------
        # إدارة قائمة الطلاب
        # ------------------------------------
        elif section == "👥 إدارة قائمة الطلاب" and user['role'] == 'admin':
            display_df = df_all.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة'})
            st.dataframe(display_df[['رقم الهوية', 'الاسم', 'الصف', 'الفصل', 'النتيجة']], use_container_width=True, hide_index=True)

# ==========================================
# 6. تبويب دخول الطلاب (الاختبار)
# ==========================================
with tab_student:
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'student_data' not in st.session_state: st.session_state.student_data = None
    if 'test_done' not in st.session_state: st.session_state.test_done = False
    if 'already_tested' not in st.session_state: st.session_state.already_tested = False

    if not st.session_state.logged_in:
        st.info("الرجاء إدخال رقم الهوية للبدء")
        student_id_input = st.text_input("رقم الهوية / الإقامة:", placeholder="أدخل رقمك هنا...", key="student_login")
        
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
        if st.button("تسجيل الخروج", use_container_width=True, key="logout_btn_1"):
            st.session_state.logged_in = False
            st.session_state.test_done = False
            st.session_state.already_tested = False
            st.rerun()

    elif st.session_state.logged_in and st.session_state.test_done and not st.session_state.already_tested:
        student = st.session_state.student_data
        st.balloons()
        st.success("🎉 رائع! تم إرسال نتيجتك بنجاح.")
        if st.button("خروج وإنهاء", use_container_width=True, key="logout_btn_2"):
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
                    
                    save_result(student['id'], final_result, scores["V"], scores["A"], scores["K"])
                    st.session_state.test_done = True
                    st.session_state.already_tested = False
                    st.rerun()
