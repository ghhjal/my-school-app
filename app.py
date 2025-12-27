import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة الملكية
st.set_page_config(page_title="نظام الأستاذ زياد التعليمي", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 20px; font-weight: bold; }
    .student-card { 
        background-color: white; padding: 15px; border-radius: 12px; 
        border-right: 6px solid #d4af37; margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    h1 { color: #1a1a1a; text-align: center; border-bottom: 3px solid #d4af37; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط السحابي
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# مصفوفة ترجمة الأيام
def get_day_ar(day_en):
    days = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
            "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    return days.get(day_en, day_en)

try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws_students = sh.worksheet("students")

    with st.sidebar:
        st.title("بوابة الأستاذ زياد")
        page = st.radio("انتقل إلى:", ["🏠 الرئيسية", "👥 إدارة الطلاب", "📊 الدرجات والسلوك", "🎓 شاشة الطلاب"])
        st.divider()
        st.info("v5.0 - النسخة الاحترافية")

    # --- 👥 شاشة إدارة الطلاب (المستقرة) ---
    if page == "👥 إدارة الطلاب":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["➕ تسجيل جديد", "📋 قائمة الطلاب"])
        with tab1:
            with st.form("add_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ")
                    st.rerun()
        with tab2:
            data = ws_students.get_all_records()
            if data:
                df = pd.DataFrame(data)
                for i, r in df.iterrows():
                    st.markdown(f'<div class="student-card"><strong>{r.get("name", "؟؟")}</strong> (ID: {r.get("id", i)})</div>', unsafe_allow_html=True)
                    if st.button("🗑️ حذف", key=f"ds_{i}"):
                        ws_students.delete_rows(i + 2); st.rerun()

  # --- 📊 شاشة الدرجات والسلوك (النسخة النهائية المستقرة) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        
        # جلب قائمة الطلاب
        all_students = ws_students.get_all_records()
        if not all_students:
            st.warning("⚠️ يرجى إضافة طلاب أولاً من شاشة إدارة الطلاب.")
        else:
            # استخراج الأسماء مع دعم مسميات مختلفة (Name أو name)
            names_list = [r.get('Name', r.get('name', 'بدون اسم')) for r in all_students]
            t1, t2 = st.tabs(["📝 إدارة الدرجات", "🎭 إدارة السلوك والمواظبة"])
            
            days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
                       "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}

            # --- 1. تبويب الدرجات (P1, P2, perf) ---
            with t1:
                with st.form("f_grades"):
                    sel_st = st.selectbox("اختر الطالب", names_list)
                    c1, c2, c3 = st.columns(3)
                    with c1: v1 = st.number_input("درجة P1", min_value=0.0)
                    with c2: v2 = st.number_input("درجة P2", min_value=0.0)
                    with c3: vp = st.number_input("الأداء (perf)", min_value=0.0)
                    
                    if st.form_submit_button("✅ حفظ الدرجات"):
                        try:
                            # استخدام الاسم الصغير 'grades' كما طلبت
                            ws_g = sh.worksheet("grades")
                            ws_g.append_row([sel_st, v1, v2, vp])
                            st.success("تم الحفظ بنجاح"); st.rerun()
                        except: st.error("خطأ: تأكد من وجود ورقة باسم 'grades' في ملفك.")

                st.markdown("### 📋 سجل الدرجات الحالي")
                try:
                    ws_g = sh.worksheet("grades")
                    g_vals = ws_g.get_all_values()
                    if len(g_vals) > 1:
                        for i, row in enumerate(g_vals[1:]):
                            ci, cd = st.columns([5, 1])
                            with ci: st.info(f"👤 **{row[0]}** | P1: `{row[1]}` | P2: `{row[2]}` | الأداء: `{row[3]}`")
                            with cd:
                                if st.button("🗑️", key=f"dg_{i}"):
                                    ws_g.delete_rows(i + 2); st.rerun()
                    else: st.info("سجل الدرجات فارغ.")
                except: st.warning("ورقة 'grades' غير موجودة.")

            # --- 2. تبويب السلوك (Student_id, Date, Type, note) ---
            with t2:
                with st.form("f_behavior"):
                    sel_b = st.selectbox("اسم الطالب", names_list)
                    b_opts = ["🌟 تميز", "📚 إحضار الكتاب", "✅ حل الواجب", "⚠️ إزعاج", "أخرى..."]
                    selected_b = st.multiselect("السلوكيات المرصودة", b_opts)
                    
                    custom = ""
                    if "أخرى..." in selected_b:
                        custom = st.text_input("اكتب السلوك المخصص:")
                    
                    if st.form_submit_button("🚀 رصد السلوك"):
                        try:
                            ws_b = sh.worksheet("behavior")
                            now = datetime.now()
                            for b in selected_b:
                                val = custom if b == "أخرى..." else b
                                # الترتيب: الطالب | التاريخ | السلوك | اليوم
                                ws_b.append_row([sel_b, str(now.date()), val, days_ar.get(now.strftime('%A'))])
                            st.success("تم الرصد!"); st.rerun()
                        except: st.error("خطأ: تأكد من وجود ورقة باسم 'behavior' في ملفك.")

                st.markdown("### 📋 سجل السلوك الحالي")
                try:
                    ws_b = sh.worksheet("behavior")
                    b_vals = ws_b.get_all_values()
                    if len(b_vals) > 1:
                        for i, row in enumerate(b_vals[1:]):
                            ci, cd = st.columns([5, 1])
                            with ci:
                                # عرض متكامل: الطالب | السلوك | التاريخ (اليوم)
                                n = row[0] if len(row)>0 else "؟؟"
                                d = row[1] if len(row)>1 else ""
                                t = row[2] if len(row)>2 else "-"
                                dy = row[3] if len(row)>3 else ""
                                st.warning(f"🎭 **{n}** | {t} — 🗓️ {d} ({dy})")
                            with cd:
                                if st.button("🗑️", key=f"db_{i}"):
                                    ws_b.delete_rows(i + 2); st.rerun()
                    else: st.info("سجل السلوك فارغ.")
                except: st.warning("ورقة 'behavior' غير موجودة.")
                                
    # --- 🎓 شاشة الطلاب ---
    elif page == "🎓 شاشة الطلاب":
        st.markdown("<h1>🎓 بوابة الطلاب</h1>", unsafe_allow_html=True)
        all_s = ws_students.get_all_records()
        if all_s:
            s_name = st.selectbox("اختر اسمك للعرض:", [r['name'] for r in all_s])
            if s_name:
                c1, c2 = st.columns(2)
                with c1:
                    st.info("📊 درجاتك")
                    dg = pd.DataFrame(sh.worksheet("grades").get_all_records())
                    st.dataframe(dg[dg['name']==s_name])
                with c2:
                    st.warning("🎭 سلوكك")
                    db = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                    st.dataframe(db[db['name']==s_name])

except Exception as e:
    st.error(f"حدث خطأ: {e}")
