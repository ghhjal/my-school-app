import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import io
import time

# ==========================================
# 1. إعدادات الصفحة والـ CSS (تحميل فوري بدون عوائق)
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية - أنماط التعلم", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio, .stSelectbox, .stTextInput { direction: rtl; text-align: right; font-family: 'Tajawal', 'Arial', sans-serif; }
    
    .custom-header {
        background: linear-gradient(135deg, #2c3e50 0%, #2980b9 100%);
        padding: 12px 15px; border-radius: 8px; color: white; margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column;
        align-items: center; justify-content: center;
    }
    .title-wrapper { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 4px; width: 100%; }
    .header-main-title { font-size: 24px !important; font-weight: bold; margin: 0 !important; padding: 0 !important; line-height: 1.2; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); }
    
    @keyframes float-cap {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-3px) rotate(-10deg); }
        50% { transform: translateY(-5px) rotate(0deg); }
        75% { transform: translateY(-3px) rotate(10deg); }
    }
    .header-icon { font-size: 26px; display: inline-block; animation: float-cap 3.5s ease-in-out infinite; }
    
    .header-sub-title { font-size: 13px !important; color: #d1d8e0 !important; margin: 0 !important; padding: 0 !important; font-weight: normal; text-align: center !important; width: 100% !important; position: relative; right: 25px; }

    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 2px solid #e0e0e0; border-radius: 0; padding: 0; gap: 20px; justify-content: right; overflow-x: auto; margin-bottom: 15px;}
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; font-size: 14px; padding: 10px 15px; color: #555; font-weight: bold; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #2980b9 !important; border-bottom: 3px solid #2980b9 !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #2980b9 !important; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    .dashboard-stats-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
    .dash-card { flex: 1; padding: 12px; border-radius: 8px; text-align: center; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid; }
    .dash-card.total { border-color: #9b59b6; } 
    .dash-card.completed { border-color: #2ecc71; } 
    .dash-card.pending { border-color: #f1c40f; } 
    .dash-title { font-size: 12px; margin-bottom: 5px; color: #555; font-weight: bold; }
    .dash-value { font-size: 22px; font-weight: bold; color: #2c3e50; }
    .welcome-box { background-color: #ebf5fb; border: 1px solid #3498db; border-radius: 8px; padding: 10px; color: #2980b9; font-size: 14px; font-weight: bold; }
    
    button[kind="secondary"] { background-color: #f8f9fa !important; border: 1px solid #d1d8e0 !important; border-radius: 8px !important; color: #2c3e50 !important; font-weight: bold !important; transition: all 0.3s ease !important; }
    button[kind="secondary"]:hover { background-color: #eef2f5 !important; border-color: #2980b9 !important; color: #2980b9 !important; }
    button[kind="primary"] { background-color: #ffeaeb !important; color: #d63031 !important; border: 1px solid #ffb8b8 !important; border-radius: 8px !important; font-weight: bold !important; }
    button[kind="primary"]:hover { background-color: #ffc2c2 !important; color: #c0392b !important; border-color: #ff9999 !important; }
    div[data-testid="stButton"] button p { font-size: 13.5px !important; white-space: nowrap !important; overflow: visible !important; }
    
    .custom-chart-container { display: flex; justify-content: space-around; align-items: flex-end; height: 200px; padding: 20px 0; border-bottom: 1px solid #eee; margin-top: 20px; }
    .chart-bar-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; width: 25%; }
    .chart-value { font-weight: bold; font-size: 15px; margin-bottom: 5px; } 
    .chart-bar { width: 100%; border-radius: 6px 6px 0 0; transition: height 0.5s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .chart-label { margin-top: 10px; font-weight: bold; font-size: 13px; color: #333; }
    
    .custom-footer { text-align: center; color: #7f8c8d; font-size: 13px; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-family: 'Tajawal', sans-serif; }
</style>
""", unsafe_allow_html=True)

# رسم الهيدر فوراً على الشاشة
st.markdown("""
<div class="custom-header">
    <div class="title-wrapper">
        <span class="header-icon">🎓</span>
        <h1 class="header-main-title">منصة زياد الذكية</h1>
    </div>
    <h2 class="header-sub-title">أنماط التعلم - لوحة الإدارة</h2>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. دوال الاتصال المشترك والتخزين المؤقت طويل الأمد
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u3D_ZqDXkzTla-cIkYpoQPs4-0pWXuQQZ--ye817Krs/edit#gid=0"

def clean_id(val):
    if pd.isna(val): return ""
    val = str(val).translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    return val.split('.')[0].strip()

@st.cache_resource
def get_gsheets_conn():
    from streamlit_gsheets import GSheetsConnection
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=7200)
def get_all_teachers():
    conn = get_gsheets_conn()
    try:
        df_teachers = conn.read(spreadsheet=SHEET_URL, worksheet="teachers", dtype=str)
        df_teachers['id'] = df_teachers['id'].apply(clean_id)
        return df_teachers
    except:
        return pd.DataFrame(columns=['id', 'name', 'role', 'class_name'])

@st.cache_data(ttl=7200)
def get_all_students():
    conn = get_gsheets_conn()
    try: 
        df_students = conn.read(spreadsheet=SHEET_URL, worksheet="df_students", dtype=str)
    except: 
        try: df_students = conn.read(spreadsheet=SHEET_URL, dtype=str)
        except: df_students = pd.DataFrame()
        
    required_cols = ['id', 'name', 'grade', 'class_name']
    for col in required_cols:
        if col not in df_students.columns: df_students[col] = ""
            
    if 'vak_result' not in df_students.columns: df_students['vak_result'] = "غير مختبر"
    df_students['vak_result'] = df_students['vak_result'].fillna("غير مختبر")
    
    for col in ['v_score', 'a_score', 'k_score']:
        if col not in df_students.columns: df_students[col] = "0"
        df_students[col] = df_students[col].fillna("0")
        
    df_students['id'] = df_students['id'].apply(clean_id)
    return df_students

def clear_all_caches():
    get_all_students.clear()
    get_all_teachers.clear()
    st.cache_data.clear()

def intelligent_merge_students(new_df):
    current_df = get_all_students()
    current_df['id'] = current_df['id'].apply(clean_id)
    new_df['id'] = new_df['id'].apply(clean_id)
    new_students = new_df[~new_df['id'].isin(current_df['id'])].copy()
    if not new_students.empty:
        new_students['vak_result'] = "غير مختبر"
        for col in ['v_score', 'a_score', 'k_score']: new_students[col] = "0"
        updated_df = pd.concat([current_df, new_students], ignore_index=True)
        conn = get_gsheets_conn()
        try: conn.update(spreadsheet=SHEET_URL, worksheet="df_students", data=updated_df)
        except: conn.update(spreadsheet=SHEET_URL, data=updated_df)
        clear_all_caches()
        return len(new_students)
    return 0

def intelligent_merge_teachers(new_df):
    current_df = get_all_teachers()
    current_df['id'] = current_df['id'].apply(clean_id)
    new_df['id'] = new_df['id'].apply(clean_id)
    new_teachers = new_df[~new_df['id'].isin(current_df['id'])].copy()
    if not new_teachers.empty:
        new_teachers['role'] = 'teacher'
        new_teachers['class_name'] = 'all'
        if 'role' not in current_df.columns: current_df['role'] = 'teacher'
        if 'class_name' not in current_df.columns: current_df['class_name'] = 'all'
        updated_df = pd.concat([current_df, new_teachers[['id', 'name', 'role', 'class_name']]], ignore_index=True)
        conn = get_gsheets_conn()
        conn.update(spreadsheet=SHEET_URL, worksheet="teachers", data=updated_df)
        clear_all_caches()
        return len(new_teachers)
    return 0

# ==========================================
# 3. محرك التصحيح الآلي
# ==========================================
def get_vak_style(answer):
    ans = str(answer).strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    if any(x in ans for x in ["فيديو", "السبوره", "الاحداث", "فيلم", "الاقلام", "التخطيط", "الرسم", "التلوين", "مصوره", "خريطه", "يشاهدني", "الفوضى", "حركه", "النهائي", "كيف يبدو", "شكله", "ملامح", "ابتسم", "تلمع", "الكلمه مكتوبه", "راسي"]): return 'V'
    if any(x in ans for x in ["استمع", "اردد", "شفتي", "مسموع", "تكرار", "تسجيل", "الاصدقاء", "للقصص", "القوانين", "بالكلام", "الاصوات", "الضجيج", "تحدث", "اسال", "يخبرني", "وصوته", "اضحك", "بحماس", "اتهجى", "حروف"]): return 'A'
    if any(x in ans for x in ["تجربه", "اتحرك", "بالملل", "المشي", "الحفظ", "الرياضه", "الركض", "تركيب", "يمسك", "يجربها", "الجلوس", "دون حركه", "القطع", "فورا", "فعلنا", "اين لعبنا", "سلمنا", "اقفز", "اصفق", "ورقه", "مرات"]): return 'K'
    return None

def sync_google_forms():
    conn = get_gsheets_conn()
    try:
        try: df_students_fresh = conn.read(spreadsheet=SHEET_URL, worksheet="df_students", ttl=0, dtype=str)
        except: df_students_fresh = conn.read(spreadsheet=SHEET_URL, ttl=0, dtype=str)
        df_forms_fresh = conn.read(spreadsheet=SHEET_URL, worksheet="responses", ttl=0, dtype=str)
    except Exception as e:
        st.error("⚠️ خطأ في الاتصال أو لم يتم العثور على الأوراق.")
        return

    required_cols = ['id', 'name', 'grade', 'class_name', 'vak_result', 'v_score', 'a_score', 'k_score']
    for col in required_cols:
        if col not in df_students_fresh.columns: df_students_fresh[col] = ""
    df_students_fresh['id'] = df_students_fresh['id'].apply(clean_id)
    
    id_col = None
    for col in df_forms_fresh.columns:
        if 'هوي' in str(col) or 'رقم' in str(col) or 'id' in str(col).lower():
            id_col = col
            break
            
    if not id_col:
        st.toast("⚠️ لم يتعرف النظام على عمود الهوية في النموذج.", icon="❌")
        return

    df_forms_fresh[id_col] = df_forms_fresh[id_col].apply(clean_id)
    updates_count = 0
    
    for _, row in df_forms_fresh.iterrows():
        s_id = row.get(id_col, '')
        if not s_id: continue
            
        mask = (df_students_fresh['id'] == s_id)
        if mask.any():
            v, a, k = 0, 0, 0
            for col in df_forms_fresh.columns:
                if col != id_col and not any(skip in str(col).lower() for skip in ['time', 'email', 'name', 'اسم', 'إيميل', 'تاريخ', 'طابع', 'score']):
                    style = get_vak_style(row[col])
                    if style == 'V': v += 1
                    elif style == 'A': a += 1
                    elif style == 'K': k += 1
            
            if (v + a + k) > 0:
                scores = {"V": v, "A": a, "K": k}
                labels = {"V": "بصري 👁️", "A": "سمعي 👂", "K": "حركي 🏃‍♂️"}
                final_result = labels[max(scores, key=scores.get)]
                
                df_students_fresh.loc[mask, 'vak_result'] = final_result
                df_students_fresh.loc[mask, 'v_score'] = str(v)
                df_students_fresh.loc[mask, 'a_score'] = str(a)
                df_students_fresh.loc[mask, 'k_score'] = str(k)
                updates_count += 1
                
    if updates_count > 0:
        try: conn.update(spreadsheet=SHEET_URL, worksheet="df_students", data=df_students_fresh)
        except: conn.update(spreadsheet=SHEET_URL, data=df_students_fresh)
        clear_all_caches()
        st.toast(f"تم استيراد وتحديث نتائج {updates_count} طالب بنجاح! 🎉", icon="✅")
        time.sleep(1) 
        st.rerun()
    else:
        st.toast("اكتمل الفحص ولم يتم رصد درجات جديدة.", icon="ℹ️")

# ==========================================
# 4. الترويسة الذكية وتوليد تقارير HTML والملفات
# ==========================================
def add_serial_column(df):
    """إضافة عمود الرقم التسلسلي (م) في بداية الجدول ليظهر يمين التقرير"""
    df_out = df.copy().reset_index(drop=True)
    df_out.insert(0, 'م', range(1, len(df_out) + 1))
    return df_out

def get_school_name(df_subset):
    text_to_search = " ".join(df_subset['grade'].fillna("").astype(str)) + " " + " ".join(df_subset['class_name'].fillna("").astype(str))
    if "ابتدائي" in text_to_search and "متوسط" in text_to_search: return "ابتدائية عبادة بن قيس الأنصاري<br>متوسطة عبدالرحمن الناصر"
    elif "متوسط" in text_to_search: return "متوسطة عبدالرحمن الناصر"
    else: return "ابتدائية عبادة بن قيس الأنصاري"

def generate_html_page(title, content, school_names_html):
    # التعرف على اسم المعلم تلقائياً إذا لم يكن الحساب حساب مدير النظام
    curr_user = st.session_state.get('current_user')
    if curr_user and curr_user.get('role') != 'admin':
        teacher_name_display = f"أ. {curr_user.get('name')}"
    else:
        teacher_name_display = "............................................."

    signature_html = f"""
    <div class="signature-section">
        <div class="sig-box">
            <div class="sig-title">معلم المادة / المختص</div>
            <div class="sig-line">الاسم: {teacher_name_display}</div>
            <div class="sig-line">التوقيع: .............................................</div>
        </div>
        <div class="sig-stamp">
            <div class="stamp-circle">الختم الرسمي</div>
        </div>
        <div class="sig-box">
            <div class="sig-title">يعتمد ،، مدير المدرسة</div>
            <div class="sig-line">الاسم: أ. عبدالمجيد الحربي</div>
            <div class="sig-line">التوقيع: .............................................</div>
        </div>
    </div>
    """

    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>{title}</title><style>@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap'); body {{ font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; background: #fff; color: #000; }} @page {{ margin: 15mm; }} thead {{ display: table-header-group; }} tfoot {{ display: table-footer-group; }} .official-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px double #000; padding-bottom: 10px; margin-bottom: 20px; font-weight: bold; }} .header-right {{ text-align: right; flex: 1; font-size: 13px; line-height: 1.5; }} .header-center {{ text-align: center; flex: 1; font-size: 16px; color: #2c3e50; line-height: 1.3; }} .header-left {{ text-align: left; flex: 1; font-size: 13px; line-height: 1.5; }} .report-main-title {{ text-align: center; color: #2980b9; background-color: #ebf5fb; border: 1px solid #3498db; border-radius: 8px; padding: 10px; margin-bottom: 20px; font-size: 20px; font-weight: bold; }} table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; page-break-inside: auto; }} tr {{ page-break-inside: avoid; page-break-after: auto; }} th, td {{ border: 1px solid #000; padding: 6px; text-align: center; }} th {{ background-color: #f2f2f2; font-weight: bold; }} td:first-child, th:first-child {{ width: 40px; font-weight: bold; background-color: #f4f6f7; }} tr:nth-child(even) {{ background-color: #f9f9f9; }} .summary-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #fafafa; font-size: 15px; }} .bar-bg {{ background-color: #e0e0e0; border-radius: 5px; width: 100%; height: 14px; margin-bottom: 8px; border: 1px solid #ccc; overflow: hidden; }} .bar-v {{ background-color: #3498db; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .bar-a {{ background-color: #e67e22; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .bar-k {{ background-color: #2ecc71; height: 100%; border-radius: 5px 0 0 5px; transition: width 0.5s; }} .stats-container {{ display: flex; justify-content: space-between; margin-top: 15px; gap: 10px; }} .stat-card {{ flex: 1; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #ccc; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }} .stat-card.visual {{ border-color: #3498db; color: #2980b9; background-color: #ebf5fb; }} .stat-card.auditory {{ border-color: #e67e22; color: #d35400; background-color: #fdf2e9; }} .stat-card.kinesthetic {{ border-color: #2ecc71; color: #27ae60; background-color: #eafaf1; }} .stat-title {{ font-size: 14px; margin-bottom: 5px; font-weight: bold; }} .stat-value {{ font-size: 18px; font-weight: bold; }} .signature-section {{ display: flex; justify-content: space-between; align-items: center; margin-top: 35px; padding-top: 15px; border-top: 1px dashed #ccc; page-break-inside: avoid; }} .sig-box {{ flex: 1; text-align: center; font-size: 14px; line-height: 2; }} .sig-title {{ font-weight: bold; font-size: 15px; color: #2c3e50; margin-bottom: 5px; }} .sig-line {{ font-weight: bold; }} .sig-stamp {{ flex: 0.6; display: flex; justify-content: center; align-items: center; }} .stamp-circle {{ width: 85px; height: 85px; border: 2px dashed #bbb; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px; font-weight: bold; }} .no-print {{ text-align: center; margin-bottom: 15px; }} .print-btn {{ background: #2980b9; color: white; border: none; padding: 8px 16px; font-size: 14px; border-radius: 5px; cursor: pointer; font-family: 'Tajawal'; }} @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; margin: 0; }} .stat-card {{ box-shadow: none; }} .official-header {{ border-bottom: 2px solid #000; }} .header-center {{ color: #000; }} }}</style></head><body>
    <div class="no-print"><button class="print-btn" onclick="window.print()">🖨️ طباعة التقرير / حفظ PDF</button></div>
    <table style="width: 100%; border: none;"><thead style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0; background: none;">
    <div class="official-header"><div class="header-right">المملكة العربية السعودية<br>{school_names_html}</div><div class="header-center">وزارة التعليم<br><span style="font-size: 12px; font-weight: normal; color: #7f8c8d;">Ministry of Education</span></div><div class="header-left">العام الدراسي: 1448 هـ<br>تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}</div></div>
    </td></tr></thead><tbody style="border: none;"><tr style="border: none;"><td style="border: none; padding: 0; text-align: right; font-weight: normal; background: none;"><div class="report-main-title">{title}</div>{content}{signature_html}</td></tr></tbody></table>
    </body></html>"""

def get_download_link(html_content, filename, link_text):
    b64 = base64.b64encode(html_content.encode('utf-8')).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: block; text-align: center; background-color: #27ae60; color: white; padding: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px;">{link_text}</a>'

@st.cache_data
def create_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# ==========================================
# 5. منطق تسجيل الدخول والواجهة الإدارية
# ==========================================
if 'current_user' not in st.session_state: st.session_state.current_user = None

if st.session_state.current_user is None:
    st.info("💡 يرجى إدخال رقم الهوية الخاص بك للوصول إلى لوحة التحكم.")
    teacher_id_input = st.text_input("رقم الهوية:", placeholder="أدخل رقم هويتك هنا...")
    
    if st.button("تسجيل الدخول 🔑", use_container_width=True):
        if teacher_id_input:
            with st.spinner("جاري التحقق من الهوية..."):
                try:
                    df_teachers = get_all_teachers()
                    norm_id = clean_id(teacher_id_input)
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
    
    if user['role'] == 'admin':
        col_user, col_actions, col_logout = st.columns([5.5, 2.5, 2])
        
        with col_user:
            st.markdown(f'<div class="welcome-box" style="height: 100%; min-height: 95px; display: flex; align-items: center; justify-content: center;">مرحباً بك: {user["name"]} (مدير)</div>', unsafe_allow_html=True)
            
        with col_actions:
            if st.button("📥 جلب النتائج", use_container_width=True):
                with st.spinner("جاري جلب وتصحيح الإجابات..."):
                    sync_google_forms()
            if st.button("🔄 تحديث الشاشة", use_container_width=True):
                clear_all_caches()
                st.rerun()
                
        with col_logout:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("تسجيل الخروج", type="primary", use_container_width=True, key="logout"):
                st.session_state.current_user = None
                st.rerun()
                
    else:
        col_user, col_logout = st.columns([8, 2])
        with col_user:
            st.markdown(f'<div class="welcome-box" style="height: 100%; min-height: 50px; display: flex; align-items: center; justify-content: center;">مرحباً بك: {user["name"]}</div>', unsafe_allow_html=True)
        with col_logout:
            if st.button("تسجيل الخروج", type="primary", use_container_width=True, key="logout"):
                st.session_state.current_user = None
                st.rerun()
            
    df_all = get_all_students()
    df_tested = df_all[df_all['vak_result'] != 'غير مختبر'].copy()
    for col in ['v_score', 'a_score', 'k_score']: df_tested[col] = pd.to_numeric(df_tested[col], errors='coerce').fillna(0)

    total_students = len(df_all)
    completed_tests = len(df_tested)
    pending_tests = total_students - completed_tests
    
    st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="dashboard-stats-container">
        <div class="dash-card pending"><div class="dash-title">⏳ لم يؤدوا الاختبار</div><div class="dash-value">{pending_tests}</div></div>
        <div class="dash-card completed"><div class="dash-title">✅ الاختبارات المكتملة</div><div class="dash-value">{completed_tests}</div></div>
        <div class="dash-card total"><div class="dash-title">👥 إجمالي الطلاب</div><div class="dash-value">{total_students}</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0 20px 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

    if user['role'] == 'admin':
        tabs = st.tabs(["🏠 الرئيسية (الإحصائيات)", "📊 التقارير (طباعة)", "👥 إدارة البيانات (استيراد/تصدير)"])
        tab_main, tab_reports, tab_data = tabs
    else:
        tabs = st.tabs(["📊 التقارير (طباعة)"])
        tab_reports = tabs[0]
        tab_main, tab_data = None, None

    if tab_main is not None:
        with tab_main:
            st.markdown("<h3 style='text-align: center; color: #2c3e50;'>توزيع أنماط التعلم في المدرسة</h3>", unsafe_allow_html=True)
            if len(df_tested) > 0:
                v_count = len(df_tested[df_tested['vak_result'].str.contains('بصري', na=False)])
                a_count = len(df_tested[df_tested['vak_result'].str.contains('سمعي', na=False)])
                k_count = len(df_tested[df_tested['vak_result'].str.contains('حركي', na=False)])
                max_val = max(v_count, a_count, k_count)
                h_v = int((v_count / max_val * 100)) if max_val > 0 else 0
                h_a = int((a_count / max_val * 100)) if max_val > 0 else 0
                h_k = int((k_count / max_val * 100)) if max_val > 0 else 0
                
                chart_html = f"""
                <div class="custom-chart-container">
                    <div class="chart-bar-wrapper"><div class="chart-value" style="color: #2980b9;">{v_count}</div><div class="chart-bar" style="height: {h_v}%; background: linear-gradient(180deg, #3498db, #2980b9);"></div><div class="chart-label">بصري 👁️</div></div>
                    <div class="chart-bar-wrapper"><div class="chart-value" style="color: #27ae60;">{k_count}</div><div class="chart-bar" style="height: {h_k}%; background: linear-gradient(180deg, #2ecc71, #27ae60);"></div><div class="chart-label">حركي 🏃‍♂️</div></div>
                    <div class="chart-bar-wrapper"><div class="chart-value" style="color: #d35400;">{a_count}</div><div class="chart-bar" style="height: {h_a}%; background: linear-gradient(180deg, #e67e22, #d35400);"></div><div class="chart-label">سمعي 👂</div></div>
                </div>
                """
                st.markdown(chart_html, unsafe_allow_html=True)
            else: st.info("لا توجد بيانات كافية لعرض الرسم البياني.")

    with tab_reports:
        report_type = st.radio(
            "حدد نوع التقرير الذي تود استخراجه:",
            ["تقرير الفصول الشامل", "تقرير فرز الأنماط (بصري / سمعي / حركي)", "تقرير غير المختبرين", "التقرير الفردي لطالب"],
            horizontal=True
        )
        st.markdown("---")
        
        # 1️⃣ تقرير الفصول الشامل
        if report_type == "تقرير الفصول الشامل":
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                classes = ["جميع الفصول"] + list(df_all['class_name'].dropna().unique())
                selected_class = st.selectbox("اختر النطاق (الفصل):", classes, key="cls_comp")
            with col_f2:
                style_filter = st.selectbox("تصفية حسب نمط التعلم:", ["جميع الأنماط", "بصري", "سمعي", "حركي"], key="sty_comp")
                
            df_class = df_all.copy() if selected_class == "جميع الفصول" else df_all[df_all['class_name'] == selected_class].copy()
            df_class_tested = df_class[df_class['vak_result'] != 'غير مختبر'].copy()
            
            if style_filter != "جميع الأنماط":
                df_class_tested = df_class_tested[df_class_tested['vak_result'].str.contains(style_filter, na=False)].copy()
            
            if len(df_class_tested) > 0:
                display_cols = df_class_tested[['id', 'name', 'class_name', 'vak_result']].rename(
                    columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب'}
                )
                display_cols = add_serial_column(display_cols)
                st.dataframe(display_cols, use_container_width=True, hide_index=True)
                
                html_table = display_cols.to_html(index=False, classes="table", justify="center")
                v_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('بصري', na=False)]) / len(df_class_tested) * 100, 1)
                a_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('سمعي', na=False)]) / len(df_class_tested) * 100, 1)
                k_pct = round(len(df_class_tested[df_class_tested['vak_result'].str.contains('حركي', na=False)]) / len(df_class_tested) * 100, 1)
                
                class_content = f"""
                <div class="summary-box"><h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">الإحصائية الإجمالية: <span style="font-weight: normal; font-size: 15px;">عدد الطلاب في هذا التقرير: {len(df_class_tested)} طالب</span></h3>
                <div class="stats-container"><div class="stat-card visual"><div class="stat-title">👁️ بصري</div><div class="stat-value">{v_pct}%</div></div><div class="stat-card auditory"><div class="stat-title">👂 سمعي</div><div class="stat-value">{a_pct}%</div></div><div class="stat-card kinesthetic"><div class="stat-title">🏃‍♂️ حركي</div><div class="stat-value">{k_pct}%</div></div></div></div>
                <h3 style="margin-top: 20px; font-size: 16px;">قائمة بيانات الطلاب:</h3>{html_table}"""
                
                base_title = "التقرير الشامل لأنماط التعلم - جميع الفصول" if selected_class == "جميع الفصول" else f"تقرير أنماط التعلم - فصل {selected_class}"
                if style_filter != "جميع الأنماط":
                    base_title += f" (النمط ال{style_filter})"
                full_html = generate_html_page(base_title, class_content, get_school_name(df_class_tested))
                st.markdown(get_download_link(full_html, f"Group_Report_{selected_class}_{style_filter}.html", "📥 تحميل التقرير للطباعة (A4)"), unsafe_allow_html=True)
            else:
                st.warning("لا يوجد طلاب مطابقين لهذا الفلتر في النطاق المحدد.")

        # 2️⃣ تقرير فرز الأنماط المخصص
        elif report_type == "تقرير فرز الأنماط (بصري / سمعي / حركي)":
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                chosen_style_label = st.selectbox("اختر نمط التعلم المطلوب استخراجه:", ["بصري 👁️", "سمعي 👂", "حركي 🏃‍♂️"])
                chosen_style_key = chosen_style_label.split()[0]
            with col_s2:
                classes = ["جميع الفصول"] + list(df_all['class_name'].dropna().unique())
                selected_class_style = st.selectbox("اختر النطاق (الفصل):", classes, key="cls_style_only")
                
            df_style_sub = df_all.copy() if selected_class_style == "جميع الفصول" else df_all[df_all['class_name'] == selected_class_style].copy()
            df_style_matched = df_style_sub[df_style_sub['vak_result'].str.contains(chosen_style_key, na=False)].copy()
            
            if len(df_style_matched) > 0:
                display_cols = df_style_matched[['id', 'name', 'class_name', 'vak_result']].rename(
                    columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل', 'vak_result': 'النمط الغالب'}
                )
                display_cols = add_serial_column(display_cols)
                st.dataframe(display_cols, use_container_width=True, hide_index=True)
                
                html_table = display_cols.to_html(index=False, classes="table", justify="center")
                
                if chosen_style_key == "بصري":
                    style_tips = "<li>الاعتماد على الخرائط الذهنية، الصور، والرسوم البيانية على السبورة.</li><li>استخدام الأقلام الملونة لتمييز الكلمات والمفاهيم الأساسية.</li><li>عرض مقاطع الفيديو التعليمية والعروض المرئية.</li>"
                elif chosen_style_key == "سمعي":
                    style_tips = "<li>التركيز على الشرح الشفهي المباشر والحوار والنقاش الجماعي.</li><li>توظيف القراءة الجهرية والترديد الصوتي للمعلومات المهمة.</li><li>تشجيع الطلاب على تلخيص الدرس شفهياً لزملائهم.</li>"
                else:
                    style_tips = "<li>دمج الأنشطة الحركية والتجارب العملية والمجسمات اليدوية في الدرس.</li><li>تطبيق استراتيجية لعب الأدوار والتعلم بالمحاكاة.</li><li>تقسيم المهام الطويلة وإتاحة فرص للحركة الهادفة داخل الفصل.</li>"

                style_content = f"""
                <div class="summary-box">
                    <h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">
                        إحصائية النمط ({chosen_style_label}): <span style="font-weight: normal; font-size: 15px;">العدد الإجمالي: {len(df_style_matched)} طالب</span>
                    </h3>
                    <p style="margin: 5px 0; font-weight: bold; color: #2980b9;">💡 استراتيجيات التدريس الموصى بها لهذه المجموعة داخل الفصل:</p>
                    <ul style="margin: 5px 0 0 0; line-height: 1.6; font-size: 14px;">{style_tips}</ul>
                </div>
                <h3 style="margin-top: 20px; font-size: 16px;">قائمة بأسماء طلاب النمط ال{chosen_style_key}:</h3>{html_table}"""
                
                scope_text = "جميع الفصول" if selected_class_style == "جميع الفصول" else f"فصل {selected_class_style}"
                report_title = f"تقرير حصر طلاب النمط ال{chosen_style_key} ({chosen_style_label}) - {scope_text}"
                full_html = generate_html_page(report_title, style_content, get_school_name(df_style_matched))
                st.markdown(get_download_link(full_html, f"Style_Report_{chosen_style_key}_{selected_class_style}.html", f"📥 تحميل تقرير النمط ال{chosen_style_key} للطباعة (A4)"), unsafe_allow_html=True)
            else:
                st.warning(f"لا يوجد طلاب مسجلين ضمن النمط ({chosen_style_label}) في هذا النطاق.")

        # 3️⃣ تقرير غير المختبرين
        elif report_type == "تقرير غير المختبرين":
            classes = ["جميع الفصول"] + list(df_all['class_name'].dropna().unique())
            selected_class = st.selectbox("اختر النطاق (الفصل):", classes, key="cls_untested")
            df_untested = df_all[df_all['vak_result'] == 'غير مختبر'].copy() if selected_class == "جميع الفصول" else df_all[(df_all['class_name'] == selected_class) & (df_all['vak_result'] == 'غير مختبر')].copy()
            if len(df_untested) > 0:
                display_cols = df_untested[['id', 'name', 'class_name']].rename(columns={'id': 'الرقم', 'name': 'الاسم', 'class_name': 'الفصل'})
                display_cols = add_serial_column(display_cols)
                st.dataframe(display_cols, use_container_width=True, hide_index=True)
                
                html_table = display_cols.to_html(index=False, classes="table", justify="center")
                untested_content = f"""<div class="summary-box"><h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px;">إحصائية المتأخرين: <span style="font-weight: normal; font-size: 15px;">العدد الإجمالي: {len(df_untested)} طالب</span></h3></div><h3 style="margin-top: 20px; font-size: 16px;">قائمة بأسماء الطلاب المطالبين بإجراء الاختبار:</h3>{html_table}"""
                report_title = "تقرير حصر الطلاب غير المختبرين - جميع الفصول" if selected_class == "جميع الفصول" else f"تقرير حصر الطلاب غير المختبرين - فصل {selected_class}"
                full_html = generate_html_page(report_title, untested_content, get_school_name(df_untested))
                st.markdown(get_download_link(full_html, f"Untested_Report_{selected_class}.html", "📥 تحميل تقرير غير المختبرين للطباعة (A4)"), unsafe_allow_html=True)
            else: st.success("🎉 رائع! جميع الطلاب في هذا النطاق أتموا الاختبار.")

        # 4️⃣ التقرير الفردي لطالب
        elif report_type == "التقرير الفردي لطالب":
            st.subheader("استخراج تقرير الطالب")
            st.info("💡 اكتب اسم الطالب أو رقم هويته ثم اضغط على زر (بحث).")
            
            col_search_in, col_search_btn = st.columns([4, 1.2])
            with col_search_in:
                search_query = st.text_input("🔍 ابحث باسم الطالب أو رقم الهوية:", placeholder="مثال: أحمد خالد أو رقم الهوية...", key="indiv_search_input")
            with col_search_btn:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                search_clicked = st.button("🔍 بحث", use_container_width=True, key="btn_indiv_search")
                
            if search_query or search_clicked:
                norm_query = search_query.strip()
                if not norm_query:
                    st.warning("الرجاء كتابة اسم الطالب أو رقم الهوية في مربع البحث أولاً.")
                else:
                    matches = df_all[
                        df_all['name'].apply(lambda x: norm_query in str(x)) |
                        df_all['id'].apply(lambda x: norm_query in str(x))
                    ]
                    if matches.empty:
                        st.warning("لم يتم العثور على طالب يطابق هذا البحث.")
                    else:
                        options = matches['name'] + " | الهوية: " + matches['id'] + " | الفصل: " + matches['class_name']
                        selected_choice = st.selectbox("الطلاب المطابقين للبحث:", options)
                        
                        exact_id = selected_choice.split("الهوية: ")[1].split(" |")[0]
                        s = df_all[df_all['id'] == exact_id].iloc[0]
                        
                        if s['vak_result'] == 'غير مختبر':
                            st.error("⚠️ هذا الطالب لم يجرِ الاختبار بعد.")
                        else:
                            school_names_html = get_school_name(pd.DataFrame([s]))
                            v_pct = int(float(s['v_score'])) * 10
                            a_pct = int(float(s['a_score'])) * 10
                            k_pct = int(float(s['k_score'])) * 10
                            if "بصري" in s['vak_result']: summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل البصرية المرئية."; recs = "<li>استخدام الصور والخرائط الذهنية في الشرح.</li><li>الاعتماد على العروض المرئية والفيديوهات.</li><li>استخدام الألوان في التلخيص والتنظيم.</li>"
                            elif "سمعي" in s['vak_result']: summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل السمعية والحوارية."; recs = "<li>توظيف الشرح الشفهي والنقاشات الجماعية.</li><li>الاعتماد على الترديد والتسجيلات الصوتية.</li><li>تشجيع الطالب على القراءة بصوت مسموع.</li>"
                            else: summary = "يميل الطالب في إجاباته إلى تفضيل الوسائل الحركية والعملية."; recs = "<li>دمج الأنشطة والتطبيقات العملية اليدوية.</li><li>السماح بالحركة أثناء التعلم أو استخدام المجسمات.</li><li>تطبيق استراتيجية لعب الأدوار.</li>"
                            student_content = f"""
                            <div class="summary-box"><p><b>اسم الطالب:</b> {s['name']}</p><p><b>الصف والفصل:</b> {s['grade']} - {s['class_name']}</p><p><b>الرقم المدرسي (الهوية):</b> {s['id']}</p></div>
                            <h3 style="font-size: 16px;">النتيجة التفصيلية:</h3>
                            <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>بصري Visual</span><span>{v_pct}%</span></div><div class="bar-bg"><div class="bar-v" style="width: {v_pct}%;"></div></div>
                            <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>سمعي Auditory</span><span>{a_pct}%</span></div><div class="bar-bg"><div class="bar-a" style="width: {a_pct}%;"></div></div>
                            <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; font-size: 14px;"><span>حركي Kinesthetic</span><span>{k_pct}%</span></div><div class="bar-bg"><div class="bar-k" style="width: {k_pct}%;"></div></div>
                            <div class="summary-box" style="margin-top: 20px;"><h3 style="color:#2c3e50; text-align:center; margin: 0 0 10px 0; font-size: 18px;">النمط الغالب: {s['vak_result']}</h3><p style="text-align:center; margin: 0; font-size: 14px;">{summary}</p></div>
                            <h3 style="font-size: 16px;">مقترحات تعليمية للطالب:</h3><ul style="font-size: 15px; line-height: 1.6;">{recs}</ul>
                            """
                            full_html = generate_html_page("تقرير مقياس أنماط التعلم (VAK)", student_content, school_names_html)
                            st.markdown(get_download_link(full_html, f"Student_{s['id']}_Report.html", f"📥 تحميل التقرير الفردي للطالب ({s['name']}) للطباعة"), unsafe_allow_html=True)

    if tab_data is not None:
        with tab_data:
            st.subheader("إدارة قواعد البيانات (الاستيراد والتصدير)")
            sub_tab_students, sub_tab_teachers = st.tabs(["👨‍🎓 بيانات الطلاب", "👨‍🏫 بيانات المعلمين"])
            
            with sub_tab_students:
                col1_s, col2_s = st.columns(2)
                with col1_s:
                    template_s_df = pd.DataFrame(columns=['id', 'name', 'grade', 'class_name'])
                    excel_s_data = create_excel_download(template_s_df)
                    st.download_button("📥 تحميل قالب إضافة الطلاب", data=excel_s_data, file_name='students_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_s")
                with col2_s:
                    backup_s_excel = create_excel_download(df_all)
                    st.download_button("💾 تحميل نسخة احتياطية (الطلاب)", data=backup_s_excel, file_name='students_backup.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_bkp_s")
                st.markdown("---")
                st.write("**📤 الاستيراد الذكي لبيانات الطلاب:**")
                uploaded_s_file = st.file_uploader("اختر ملف Excel (.xlsx أو .csv) للطلاب", type=['xlsx', 'csv'], key="up_s")
                if uploaded_s_file is not None:
                    try:
                        new_s_data = pd.read_csv(uploaded_s_file) if uploaded_s_file.name.endswith('.csv') else pd.read_excel(uploaded_s_file)
                        if all(col in new_s_data.columns for col in ['id', 'name', 'grade', 'class_name']):
                            added_s_count = intelligent_merge_students(new_s_data)
                            if added_s_count > 0: st.success(f"✅ تم إضافة {added_s_count} طالب جديد بنجاح!"); st.rerun()
                            else: st.warning("⚠️ جميع الطلاب الموجودين في الملف مسجلون بالفعل في النظام.")
                        else: st.error("⚠️ الملف لا يحتوي على الأعمدة المطلوبة.")
                    except Exception as e: st.error("حدث خطأ أثناء قراءة الملف.")
                st.markdown("---")
                
                col_db_q, col_db_b = st.columns([4, 1.2])
                with col_db_q:
                    db_search_q = st.text_input("🔍 بحث سريع في سجل الطلاب:", placeholder="ابحث بالاسم أو الهوية أو الفصل...", key="db_s_q")
                with col_db_b:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    st.button("🔍 بحث", use_container_width=True, key="btn_db_s")
                
                df_s_view = df_all.copy()
                if db_search_q.strip():
                    q_str = db_search_q.strip()
                    df_s_view = df_s_view[
                        df_s_view['name'].apply(lambda x: q_str in str(x)) |
                        df_s_view['id'].apply(lambda x: q_str in str(x)) |
                        df_s_view['class_name'].apply(lambda x: q_str in str(x))
                    ]
                
                display_s_df = df_s_view.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'grade': 'الصف', 'class_name': 'الفصل', 'vak_result': 'النتيجة الغالبة'})
                display_s_df = add_serial_column(display_s_df[['رقم الهوية', 'الاسم', 'الصف', 'الفصل', 'النتيجة الغالبة']])
                st.dataframe(display_s_df, use_container_width=True, hide_index=True)

            with sub_tab_teachers:
                col1_t, col2_t = st.columns(2)
                with col1_t:
                    template_t_df = pd.DataFrame(columns=['id', 'name'])
                    excel_t_data = create_excel_download(template_t_df)
                    st.download_button("📥 تحميل قالب إضافة المعلمين", data=excel_t_data, file_name='teachers_template.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_tpl_t")
                with col2_t:
                    try: df_teachers = get_all_teachers()
                    except: df_teachers = pd.DataFrame(columns=['id', 'name', 'role', 'class_name'])
                    backup_t_excel = create_excel_download(df_teachers)
                    st.download_button("💾 تحميل نسخة احتياطية (المعلمين)", data=backup_t_excel, file_name='teachers_backup.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True, key="btn_bkp_t")
                st.markdown("---")
                st.write("**📤 الاستيراد الذكي التلقائي لبيانات المعلمين:**")
                uploaded_t_file = st.file_uploader("اختر ملف Excel (.xlsx أو .csv) للمعلمين", type=['xlsx', 'csv'], key="up_t")
                if uploaded_t_file is not None:
                    try:
                        new_t_data = pd.read_csv(uploaded_t_file) if uploaded_t_file.name.endswith('.csv') else pd.read_excel(uploaded_t_file)
                        if all(col in new_t_data.columns for col in ['id', 'name']):
                            added_t_count = intelligent_merge_teachers(new_t_data)
                            if added_t_count > 0: st.success(f"✅ تم إضافة {added_t_count} حساب معلم جديد بنجاح!"); st.rerun()
                            else: st.warning("⚠️ جميع المعلمين الموجودين في الملف مسجلون بالفعل في النظام.")
                        else: st.error("⚠️ الملف لا يحتوي على الأعمدة المطلوبة.")
                    except Exception as e: st.error("حدث خطأ أثناء قراءة الملف.")
                st.markdown("---")
                display_t_df = df_teachers.rename(columns={'id': 'رقم الهوية', 'name': 'الاسم', 'role': 'الصلاحية', 'class_name': 'نطاق الفصول'})
                display_t_df = add_serial_column(display_t_df)
                st.dataframe(display_t_df, use_container_width=True, hide_index=True)

# ==========================================
# 6. تذييل الصفحة (الحقوق)
# ==========================================
st.markdown("""
<div class="custom-footer">
    جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية © 2026
</div>
""", unsafe_allow_html=True)
