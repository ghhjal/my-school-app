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
    
    /* تصميم خاص لتبويبات الإدارة الداخلية */
    .admin-tabs [data-baseweb="tab-list"] {
        background-color: transparent; border-bottom: 2px solid #e0e0e0; border-radius: 0; padding: 0; gap: 20px; justify-content: right; overflow-x: auto;
    }
    .admin-tabs [data-baseweb="tab"] { background-color: transparent; border: none; font-size: 15px; padding: 10px 15px; color: #555; }
    .admin-tabs [data-baseweb="tab"][aria-selected="true"] { color: #2980b9; border-bottom: 3px solid #2980b9; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الاتصال بـ Google Sheets والتخزين المؤقت
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit#gid=0"

@st.cache_data(ttl=600)
def fetch_all_data():
    df_students = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
    if 'vak_result' not in df_students.columns: df_students['vak_result'] = "غير مختبر"
    df_students['vak_result'] = df_students['vak_result'].fillna("غير مختبر")
    for col in ['v_score', 'a_score', 'k_score']:
        if col not in df_students.columns: df_students[col] = "0"
        df_students[col] = df_students[col].fillna("0")
        
    try:
        df_teachers = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", ttl=0, dtype=str)
    except Exception:
        df_teachers = pd.DataFrame()
        
    return df_students, df_teachers

def get_all_students():
    df, _ = fetch_all_data()
    return df

def get_all_teachers():
    _, df = fetch_all_data()
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
    fetch_all_data.clear()

# ==========================================
# 3. الترويسة الذكية وتوليد تقارير HTML
# ==========================================
def get_school_name(df_subset):
    text_to_search = " ".join(df_subset['grade'].fillna("").astype(str)) + " " + " ".join(df_subset['class_name'].fillna("").astype(str))
    has_primary = "ابتدائي" in text_to_search or "ابتدائية" in text_to_search
    has_middle = "متوسط" in text_to_search or "متوسطة" in text_to_search
    
    if has_primary and has_middle: return "ابتدائية عبادة بن قيس الأنصاري<br>متوسطة عبدالرحمن الناصر"
    elif has_middle: return "متوسطة عبدالرحمن الناصر"
    else: return "ابتدائية عبادة بن قيس الأنصاري"

def generate_html_page(title, content, school_names_html):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
            body {{ font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; background: #fff; color: #000; }}
            @page {{ margin: 15mm; }}
            thead {{ display: table-header-group; }}
            tfoot {{ display: table-footer-group; }}
            .official-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px double #000; padding-bottom: 10px; margin-bottom: 20px; font-weight: bold; }}
            .header-right {{ text-align: right; flex: 1; font-size: 13px; line-height: 1.5; }}
            .header-center {{ text-align: center; flex: 1; font-size: 16px; color: #2c3e50; line-height: 1.3; }}
            .header-left {{ text-align: left; flex: 1; font-size: 13px; line-height: 1.5; }}
            .report-main-title {{ text-align: center; color: #2980b9; background-color: #ebf5fb; border: 1px solid #3498db; border-radius: 8px; padding: 10px; margin-bottom: 20px; font-size: 20px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
            th, td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .summary-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #fafafa; font-size: 15px; }}
            .bar-bg {{ background-color: #e0e0e0; border-radius: 5px; width: 100%; height: 14px; margin-bottom: 8px; border: 1px solid #ccc; overflow: hidden; }}
            .bar-v {{ background-color: #3498db; height: 100%; border-radius: 5px 0 0 5px; }}
            .bar-a {{ background-color: #e67e22; height: 100%; border-radius: 5px 0 0 5px; }}
            .bar-k {{ background-color: #2ecc71; height: 100%; border-radius: 5px 0 0 5px; }}
            .stats-container {{ display: flex; justify-content: space-between; margin-top: 15px; gap: 10px; }}
            .stat-card {{ flex: 1; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #ccc; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .stat-card.visual {{ border-color: #3498db; color: #2980b9; background-color: #ebf5fb; }}
            .stat-card.auditory {{ border-color: #e67e22; color: #d35400; background-color: #fdf2e9; }}
            .stat-card.kinesthetic {{ border-color: #2ecc71; color: #27ae60; background-color: #eafaf1; }}
            .stat-title {{ font-size: 14px; margin-bottom: 5px; font-weight: bold; }}
            .stat-value {{ font-size: 18px; font-weight: bold; }}
            .no-print {{ text-align: center; margin-bottom: 15px; }}
            .print-btn {{ background: #2980b9; color: white; border: none; padding: 8px 16px; font-size: 14px; border-radius: 5px; cursor: pointer; font-family: 'Tajawal'; }}
            @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; margin: 0; }} .stat-card {{ box-shadow: none; }} .official-header {{ border-bottom: 2px solid #000; }} .header-center {{ color: #000; }} }}
        </style>
    </head>
    <body>
        <div class="no-print"><button class="print-btn" onclick="window.print()">🖨️ طباعة التقرير الرسمي</button></div>
        <table style="width: 100%; border: none;"><thead style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0;">
            <div class="official-header">
                <div class="header-right">المملكة العربية السعودية<br>{school_names_html}</div>
                <div class="header-center">وزارة التعليم<br><span style="font-size: 12px; font-weight: normal; color: #7f8c8d;">Ministry of Education</span></div>
                <div class="header-left">العام الدراسي: 1448 هـ<br>تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
        </td></tr></thead><tbody style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0; text-align: right;">
            <div class="report-main-title">{title}</div>{content}
        </td></tr></tbody></table>
    </body>
    </html>
    """

def get_download_link(html_content, filename, link_text):
    b64 = base64.b64encode(html_content.encode('utf-8')).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: block; text-align: center; background-color: #27ae60; color: white; padding: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px;">{link_text}</a>'

def normalize_text(text):
    if not isinstance(text, str): return ""
    return text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').strip()

def normalize_numbers(text):
    if not isinstance(text, str): return ""
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(arabic_to_english).strip()

# ==========================================
# 4. الواجهة الرئيسية
# ==========================================
st.title("🧠 منصة أنماط التعلم (VAK)")
tab_student, tab_admin = st.tabs(["👨‍🎓 دخول الطلاب", "⚙️ الإدارة والمعلمين"])

# ==========================================
# 5. تبويب الإدارة والمعلمين (اللوحة الاحترافية)
# ==========================================
with tab_admin:
    if 'current_user' not in st.session_state: st.session_state.current_user = None

    if st.session_state.current_user is None:
        st.header("تسجيل دخول الإدارة والمعلمين")
        st.info("💡 يرجى إدخال رقم الهوية الخاص بك للوصول إلى لوحة التحكم.")
        teacher_id_input = st.text_input("رقم الهوية:", placeholder="أدخل رقم هويتك هنا...")
        if st.button("تسجيل الدخول 🔑", use_container_width=True):
            if teacher_id_input:
                try:
                    df_teachers = get_all_teachers()
                    norm_id = normalize_numbers(teacher_id_input)
                    t_row = df_teachers[df_teachers['id'] == str(norm_id)]
                    if not t_row.empty:
                        t_data = t_row.iloc[0]
                        st.session_state.current_user = {"name": t_data['name'], "role": t_data['role']}
                        st.rerun()
                    else: st.error("رقم الهوية غير مسجل في قاعدة بيانات المعلمين. راجع إدارة المدرسة.")
                except Exception as e: st.error("⚠️ خطأ: لم يتم العثور على ورقة 'teachers' في Google Sheets.")
            else: st.warning("الرجاء إدخال رقم الهوية أولاً.")
    else:
        user = st.session_state.current_user
        
        # ترويسة اللوحة وتحديث البيانات
        col_user, col_refresh, col_logout = st.columns([6, 2, 2])
        with col_user:
            role_text = "(مدير النظام)" if user['role'] == 'admin' else ""
            st.markdown(f"<h4 style='color: #2980b9; margin-bottom: 0;'>مرحباً بك: {user['name']} {role_text}</h4>", unsafe_allow_html=True)
        with col_refresh:
            if st.button("🔄 تحديث البيانات", use_container_width=True):
                fetch_all_data.clear()
                st.toast("تم تحديث البيانات بنجاح.")
        with col_logout:
            if st.button("تسجيل الخروج", use_container_width=True, key="logout"):
                st.session_state.current_user = None
                st.rerun()
                
        df_all = get_all_students()
        df_tested = df_all[df_all['vak_result'] != 'غير مختبر'].copy()
        
        # مؤشرات لوحة التحكم العلوية (تظهر للجميع)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 إجمالي الطلاب", len(df_all))
        c2.metric("✅ الاختبارات المكتملة", len(df_tested))
        c3.metric("⏳ لم يؤدوا الاختبار", len(df_all) - len(df_tested))
        st.markdown("<hr style='margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

        # إنشاء تبويبات الأقسام بناءً على الصلاحيات
        st.markdown('<div class="admin-tabs">', unsafe_allow_html=True)
        if user['role'] == 'admin':
            tabs = st.tabs(["🏠 الرئيسية (الإحصائيات)", "📊 التقارير (طباعة)", "👥 إدارة البيانات"])
            tab_main, tab_reports, tab_data = tabs
        else:
            tabs = st.tabs(["📊 التقارير (طباعة)"])
            tab_reports = tabs[0]
            tab_main = None
            tab_data = None
        st.markdown('</div>', unsafe_allow_html=True)

        # --- التبويب 1: الرئيسية (متاح للمدير) ---
        if tab_main is not None:
            with tab_main:
                st.subheader("توزيع أنماط التعلم في المدرسة")
                if len(df_tested) > 0:
                    v_count = len(df_tested[df_tested['vak_result'].str.contains('بصري', na=False)])
                    a_count = len(df_tested[df_tested['vak_result'].str.contains('سمعي', na=False)])
                    k_count = len(df_tested[df_tested['vak_result'].str.contains('حركي', na=False)])
                    
                    # رسم بياني محسّن
                    chart_data = pd.DataFrame({
                        "النمط": ["بصري 👁️", "سمعي 👂", "حركي 🏃‍♂️"],
                        "عدد الطلاب": [v_count, a_count, k_count]
                    })
                    st.bar_chart(chart_data.set_index("النمط"))
                else:
                    st.info("لا توجد بيانات كافية لعرض الرسم البياني.")

        # --- التبويب 2: التقارير (متاح للجميع) ---
        with tab_reports:
            report_type = st.radio("حدد نوع التقرير الذي تود استخراجه:", 
                                   ["تقرير الفصول الشامل", "تقرير غير المختبرين", "التقرير الفردي لطالب"], 
                                   horizontal=True)
            st.markdown("---")
            
            if report_type == "تقرير الفصول الشامل":
                classes = ["جميع الفصول"] + list(df_all['class_name'].dropna().unique())
                selected_class = st.selectbox("اختر النطاق (الفصل):", classes)
                
                df_class = df_all.copy() if selected_class == "جميع الفصول" else df_all[df_all['class_name'] == selected_class].copy()
                df_class_tested = df_class[df_class['vak_result'] != 'غير مختبر'].copy()
                
                if len(df_class_tested) > 0:
                    display_cols = df_class_tested[['id', 'name', 'class_name', 'vak_result']].rename(columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب'})
                    html_table = display_cols.to_html(index=False, classes="table", justify="center")
                    
                    v_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('بصري', na=False)]) / len(df_class_tested) * 100, 1)
                    a_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('سمعي', na=False)]) / len(df_class_tested) * 100, 1)
                    k_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('حركي', na=False)]) / len(df_class_tested) * 100, 1)
                    
                    class_content = f"""
                    <div class="summary-box">
                        <h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">
                            الإحصائية الإجمالية: <span style="font-weight: normal; font-size: 15px;">عدد الطلاب المنجزين لهذا الاختبار: {len(df_class_tested)}</span>
                        </h3>
                        <div class="stats-container">
                            <div class="stat-card visual"><div class="stat-title">👁️ بصري</div><div class="stat-value">{v_pct}%</div></div>
                            <div class="stat-card auditory"><div class="stat-title">👂 سمعي</div><div class="stat-value">{a_pct}%</div></div>
                            <div class="stat-card kinesthetic"><div class="stat-title">🏃‍♂️ حركي</div><div class="stat-value">{k_pct}%</div></div>
                        </div>
                    </div>
                    <h3 style="margin-top: 20px; font-size: 16px;">قائمة بيانات الطلاب:</h3>
                    {html_table}
                    """
                    report_title = "التقرير الشامل لأنماط التعلم - جميع الفصول" if selected_class == "جميع الفصول" else f"تقرير أنماط التعلم - فصل {selected_class}"
                    full_html = generate_html_page(report_title, class_content, get_school_name(df_class_tested))
                    st.markdown(get_download_link(full_html, f"Group_Report_{selected_class}_{datetime.now().strftime('%H%M%S')}.html", "📥 تحميل التقرير للطباعة (A4)"), unsafe_allow_html=True)
                else: st.warning("لا يوجد طلاب مختبرين في هذا النطاق.")

            elif report_type == "تقرير غير المختبرين":
                classes = ["جميع الفصول"] + list(df_all['class_name'].dropna().unique())
                selected_class = st.selectbox("اختر النطاق (الفصل):", classes)
                
                df_untested = df_all[df_all['vak_result'] == 'غير مختبر'].copy() if selected_class == "جميع الفصول" else df_all[(df_all['class_name'] == selected_class) & (df_all['vak_result'] == 'غير مختبر')].copy()
                
                if len(df_untested) > 0:
                    display_cols = df_untested[['id', 'name', 'class_name']].rename(columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل'})
                    html_table = display_cols.to_html(index=False, classes="table", justify="center")
                    untested_content = f"""<div class="summary-box"><h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">إحصائية المتأخرين: <span style="font-weight: normal; font-size: 15px;">العدد الإجمالي: {len(df_untested)} طالب</span></h3></div><h3 style="margin-top: 20px; font-size: 16px;">قائمة بأسماء الطلاب المطالبين بإجراء الاختبار:</h3>{html_table}"""
                    report_title = "تقرير حصر الطلاب غير المختبرين - جميع الفصول" if selected_class == "جميع الفصول" else f"تقرير حصر الطلاب غير المختبرين - فصل {selected_class}"
                    full_html = generate_html_page(report_title, untested_content, get_school_name(df_untested))
                    st.markdown(get_download_link(full_html, f"Untested_Report_{selected_class}_{datetime.now().strftime('%H%M%S')}.html", "📥 تحميل تقرير غير المختبرين للطباعة (A4)"), unsafe_allow_html=True)
                else: st.success("🎉 رائع! جميع الطلاب في هذا النطاق أتموا الاختبار.")

            elif report_type == "التقرير الفردي لطالب":
                search_query = st.text_input("🔍 ابحث عن اسم الطالب:")
                if search_query:
                    norm_query = normalize_text(search_query)
                    matches = df_all[df_all['name'].apply(lambda x: norm_query in normalize_text(x))]
                    if matches.empty: st.warning("لم يتم العثور على طالب يطابق هذا الاسم.")
                    else:
                        options = matches['name'] + " | الهوية: " + matches['id'] + " | الصف: " + matches['grade']
                        selected_choice = st.selectbox("الطلاب المطابقين:", options)
                        if st.button("📄 إنشاء تقرير الطالب المحدد", use_container_width=True):
                            exact_id = selected_choice.split("الهوية: ")[1].split(" |")[0]
                            s = df_all[df_all['id'] == exact_id].iloc[0]
                            if s['vak_result'] == 'غير مختبر': st.error("هذا الطالب لم يجرِ الاختبار بعد.")
                            else:
                                v_pct = int(float(s['v_score'])) * 10
                                a_pct = int(float(s['a_score'])) * 10
                                k_pct = int(float(s['k_score'])) * 10
                                
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
                                <div class="summary-box"><p><b>اسم الطالب:</b> {s['name']}</p><p><b>الصف والفصل:</b> {s['grade']} - {s['class_name']}</p><p><b>الرقم المدرسي (الهوية):</b> {s['id']}</p></div>
                                <h3 style="font-size: 16px;">النتيجة التفصيلية:</h3>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>بصري Visual</span><span>{v_pct}%</span></div><div class="bar-bg"><div class="bar-v" style="width: {v_pct}%;"></div></div>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>سمعي Auditory</span><span>{a_pct}%</span></div><div class="bar-bg"><div class="bar-a" style="width: {a_pct}%;"></div></div>
                                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>حركي Kinesthetic</span><span>{k_pct}%</span></div><div class="bar-bg"><div class="bar-k" style="width: {k_pct}%;"></div></div>
                                <div class="summary-box" style="margin-top: 20px;"><h3 style="color:#2c3e50; text-align:center; margin: 0 0 10px 0; font-size: 18px;">النمط الغالب: {s['vak_result']}</h3><p style="text-align:center; margin: 0; font-size: 14px;">{summary}</p></div>
                                <h3 style="font-size: 16px;">مقترحات تعليمية للطالب:</h3><ul style="font-size: 15px; line-height: 1.6;">{recs}</ul>
                                """
                                full_html = generate_html_page("تقرير مقياس أنماط التعلم (VAK)", student_content, get_school_name(pd.DataFrame([s])))
                                st.markdown(get_download_link(full_html, f"Student_{s['id']}_Report_{datetime.now().strftime('%H%M%S')}.html", f"📥 تحميل التقرير الفردي للطباعة"), unsafe_allow_html=True)

        # --- التبويب 3: البيانات (متاح للمدير) ---
        if tab_data is not None:
            with tab_data:
                st.subheader("إدارة قاعدة بيانات الطلاب")
                display_df = df_all.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة الغالبة'})
                st.dataframe(display_df[['رقم الهوية', 'الاسم', 'الصف', 'الفصل', 'النتيجة الغالبة']], use_container_width=True, hide_index=True)
                st.info("💡 للتعديل أو الحذف، يرجى إجراء التغييرات مباشرة داخل ملف Google Sheets الخاص بالمنصة، ثم الضغط على 'تحديث البيانات'.")

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
                norm_id = normalize_numbers(student_id_input)
                df_student = get_student_by_id(norm_id)
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
            st.session_state.logged_in = False; st.session_state.test_done = False; st.session_state.already_tested = False
            st.rerun()

    elif st.session_state.logged_in and st.session_state.test_done and not st.session_state.already_tested:
        student = st.session_state.student_data
        st.balloons()
        st.success("🎉 رائع! تم إرسال نتيجتك بنجاح.")
        if st.button("خروج وإنهاء", use_container_width=True, key="logout_btn_2"):
            st.session_state.logged_in = False; st.session_state.test_done = False; st.session_state.already_tested = False
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
