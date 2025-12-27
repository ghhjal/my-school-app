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

# 3. تشغيل النظام
try:
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    ws_students = sh.worksheet("students")

    # القائمة الجانبية
    with st.sidebar:
        st.title("بوابة الأستاذ زياد")
        page = st.radio("القوائم المتاحة:", ["🏠 الرئيسية", "👥 إدارة الطلاب والتحكم", "📊 الدرجات والسلوك"])
        st.divider()
        st.info("النسخة المستقرة v4.0")

    # --- شاشة إدارة الطلاب (التي أعجبتك) ---
    if page == "👥 إدارة الطلاب والتحكم":
        st.markdown("<h1>👥 إدارة شؤون الطلاب</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["➕ تسجيل طالب جديد", "🛠️ عرض وتحكم"])
        
        with tab1:
            with st.form("new_student_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب الثلاثي")
                    sphase = st.selectbox("المرحلة الدراسية", ["الابتدائية", "المتوسطة", "الثانوية"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("السنة الدراسية", ["1446هـ", "1447هـ", "1448هـ"])
                    ssubject = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("✨ حفظ في السحابة"):
                    ws_students.append_row([int(sid), sname, sphase, sclass, syear, ssubject])
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()

        with tab2:
            all_data = ws_students.get_all_records()
            if all_data:
                df = pd.DataFrame(all_data)
                for index, row in df.iterrows():
                    st.markdown(f"""<div class="student-card">
                        <strong>🆔 {row.get('id', index+1)} | 👤 {row.get('name', 'طالب')}</strong><br>
                        <small>المرحلة: {row.get('phase', 'غير محدد')} | الصف: {row.get('class', '-')} | المادة: {row.get('subject', 'الإنجليزية')}</small>
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️ حذف الطالب", key=f"del_{index}"):
                        ws_students.delete_rows(int(index) + 2)
                        st.warning("تم الحذف.")
                        st.rerun()
            else:
                st.info("لا توجد بيانات مسجلة.")

   # --- 📊 شاشة رصد الدرجات والسلوك المحدثة (النسخة الاحترافية) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك اليومي</h1>", unsafe_allow_html=True)
        
        # جلب البيانات لربط القوائم
        all_students = ws_students.get_all_records()
        if not all_students:
            st.warning("⚠️ لا توجد بيانات طلاب. يرجى الإضافة من شاشة 'إدارة الطلاب'.")
        else:
            df_s = pd.DataFrame(all_students)
            names_list = df_s['name'].tolist()

            t1, t2 = st.tabs(["📝 رصد وتعديل الدرجات", "🎭 سجل السلوك والمواظبة"])

            # --- 1. قسم الدرجات مع جدول العرض ---
            with t1:
                with st.form("grades_form"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1: student_g = st.selectbox("اختر الطالب", names_list)
                    with c2: type_g = st.selectbox("التقييم", ["مشاركة", "واجب", "اختبار قصير", "فتري", "نهائي"])
                    with c3: score_g = st.number_input("الدرجة", min_value=0.0, max_value=100.0)
                    
                    if st.form_submit_button("💾 حفظ الدرجة"):
                        # تسجيل: الاسم، النوع، الدرجة، التاريخ، اليوم
                        now = datetime.now()
                        day_ar = now.strftime('%A') # سيظهر بالإنجليزية، يمكن ترجمته لاحقاً
                        sh.worksheet("grades").append_row([student_g, type_g, score_g, str(now.date()), day_ar])
                        st.success(f"تم رصد درجة {student_g}")

                st.markdown("---")
                st.subheader("📋 جدول الدرجات المرصودة")
                g_data = sh.worksheet("grades").get_all_records()
                if g_data:
                    st.table(pd.DataFrame(g_data).tail(10)) # عرض آخر 10 درجات مرصودة
                else: st.info("لا توجد درجات مرصودة بعد.")

            # --- 2. قسم السلوك المتعدد مع جدول العرض ---
            with t2:
                with st.form("behavior_multi_form"):
                    st.write("### رصد سلوك جديد")
                    c1, c2 = st.columns(2)
                    with c1: 
                        student_b = st.selectbox("اسم الطالب", names_list, key="sb_multi")
                        # رصد أكثر من سلوك في وقت واحد
                        behaviors = st.multiselect("السلوكيات المرصودة", 
                                                ["🌟 مشاركة متميزة", "📚 إحضار الكتاب", "✅ حل الواجب", 
                                                 "⚠️ عدم تركيز", "🚫 غياب بدون عذر", "🔇 إزعاج"])
                    with c2:
                        b_date = st.date_input("تاريخ الرصد", datetime.now())
                        b_notes = st.text_area("ملاحظات إضافية")
                    
                    if st.form_submit_button("🚀 حفظ السجل السلوكي"):
                        ws_b = sh.worksheet("behavior")
                        day_name = b_date.strftime('%A')
                        for b in behaviors:
                            ws_b.append_row([student_b, b, b_notes, str(b_date), day_name])
                        st.success(f"تم تسجيل {len(behaviors)} سلوكيات للطالب {student_b}")

                st.markdown("---")
                st.subheader("📋 جدول سجل السلوك")
                b_data = sh.worksheet("behavior").get_all_records()
                if b_data:
                    st.dataframe(pd.DataFrame(b_data), use_container_width=True)
                else: st.info("سجل السلوك فارغ حالياً.")

    # --- 🎓 شاشة خاصة بالطلاب (جديدة) ---
    elif page == "🎓 شاشة الطلاب":
        st.markdown("<h1>🎓 بوابة استعلام الطلاب</h1>", unsafe_allow_html=True)
        search_name = st.selectbox("ابحث عن اسمك لاستعراض تقريرك:", [""] + names_list)
        
        if search_name:
            col1, col2 = st.columns(2)
            # عرض الدرجات
            with col1:
                st.info(f"📊 درجات الطالب: {search_name}")
                all_g = pd.DataFrame(sh.worksheet("grades").get_all_records())
                st.dataframe(all_g[all_g['name'] == search_name][['type', 'score', 'date']])
            
            # عرض السلوك
            with col2:
                st.warning(f"🎭 سجل سلوك: {search_name}")
                all_b = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                st.dataframe(all_b[all_b['name'] == search_name][['behavior', 'date', 'day']])
    elif page == "🏠 الرئيسية":
        st.markdown("<h1>👑 نظام الأستاذ زياد - الصفحة الرئيسية</h1>", unsafe_allow_html=True)
        st.write("أهلاً بك في نظامك المتكامل. استخدم القائمة الجانبية للتنقل.")

except Exception as e:
    st.error(f"خطأ: {e}")
