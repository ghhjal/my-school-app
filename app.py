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

   # --- 📊 شاشة الدرجات والسلوك (النسخة الاحترافية المعتمدة) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        
        # جلب الطلاب مع دعم مسميات مختلفة للأعمدة
        all_students = ws_students.get_all_records()
        if not all_students:
            st.warning("⚠️ يرجى إضافة طلاب أولاً.")
        else:
            names_list = [r.get('Name', r.get('name', 'بدون اسم')) for r in all_students]
            t1, t2 = st.tabs(["📝 إدارة الدرجات", "🎭 إدارة السلوك والمواظبة"])
            
            # مصفوفة الأيام بالعربية
            days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
                       "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}

            # --- 1. قسم الدرجات (P1, P2, perf) ---
            with t1:
                with st.form("grades_form_final"):
                    sel_student = st.selectbox("الطالب", names_list)
                    c1, c2, c3 = st.columns(3)
                    with c1: v_p1 = st.number_input("درجة P1", min_value=0.0)
                    with c2: v_p2 = st.number_input("درجة P2", min_value=0.0)
                    with c3: v_perf = st.number_input("الأداء (perf)", min_value=0.0)
                    
                    if st.form_submit_button("✅ حفظ الدرجات"):
                        try:
                            # محاولة الوصول للورقة بأي مسمى محتمل لتجنب خطأ الصورة
                            ws_g = sh.worksheet("Grades") if "Grades" in [w.title for w in sh.worksheets()] else sh.worksheet("grades")
                            ws_g.append_row([sel_student, v_p1, v_p2, v_perf])
                            st.success("تم الحفظ بنجاح")
                            st.rerun()
                        except Exception as e: st.error(f"خطأ في الوصول لجدول الدرجات: {e}")

                st.markdown("---")
                st.subheader("📋 سجل الدرجات الحالي (تعديل/حذف)")
                try:
                    ws_g = sh.worksheet("Grades") if "Grades" in [w.title for w in sh.worksheets()] else sh.worksheet("grades")
                    g_data = ws_g.get_all_values()
                    if len(g_data) > 1:
                        for i, row in enumerate(g_data[1:]):
                            col_txt, col_del = st.columns([5, 1])
                            with col_txt:
                                st.info(f"👤 **{row[0]}** | P1: `{row[1]}` | P2: `{row[2]}` | الأداء: `{row[3]}`")
                            with col_del:
                                if st.button("🗑️", key=f"del_g_{i}"):
                                    ws_g.delete_rows(i + 2); st.rerun()
                    else: st.info("السجل فارغ.")
                except: st.warning("تأكد من وجود ورقة باسم Grades في ملفك.")

            # --- 2. قسم السلوك (مع خيار أخرى وحذف جانبي) ---
            with t2:
                with st.form("behavior_form_final"):
                    sel_b_student = st.selectbox("اسم الطالب", names_list)
                    b_options = ["🌟 تميز", "📚 إحضار الكتاب", "✅ حل الواجب", "⚠️ إزعاج", "أخرى..."]
                    selected_behaviors = st.multiselect("السلوكيات", b_options)
                    
                    custom_b = ""
                    if "أخرى..." in selected_behaviors:
                        custom_b = st.text_input("اكتب السلوك المخصص هنا:")
                    
                    if st.form_submit_button("🚀 رصد السلوك"):
                        try:
                            ws_b = sh.worksheet("Behavior") if "Behavior" in [w.title for w in sh.worksheets()] else sh.worksheet("behavior")
                            now = datetime.now()
                            for b in selected_behaviors:
                                final_val = custom_b if b == "أخرى..." else b
                                # الترتيب: Student_id | Date | Type | note (اليوم)
                                ws_b.append_row([sel_b_student, str(now.date()), final_val, days_ar.get(now.strftime('%A'))])
                            st.success("تم الرصد!")
                            st.rerun()
                        except Exception as e: st.error(f"خطأ في الوصول لجدول السلوك: {e}")

                st.markdown("---")
                st.subheader("📋 سجل السلوك (حذف مباشر)")
                try:
                    ws_b = sh.worksheet("Behavior") if "Behavior" in [w.title for w in sh.worksheets()] else sh.worksheet("behavior")
                    b_data = ws_b.get_all_values()
                    if len(b_data) > 1:
                        for i, row in enumerate(b_data[1:]):
                            c_info, c_del = st.columns([5, 1])
                            with c_info:
                                # عرض: الطالب | السلوك | التاريخ (اليوم)
                                st.warning(f"🎭 **{row[0]}** | {row[2]} — 🗓️ {row[1]} ({row[3] if len(row)>3 else ''})")
                            with c_del:
                                if st.button("🗑️", key=f"del_b_{i}"):
                                    ws_b.delete_rows(i + 2); st.rerun()
                    else: st.info("لا توجد سلوكيات مرصودة.")
                except: st.warning("تأكد من وجود ورقة باسم Behavior في ملفك.")
                                
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
