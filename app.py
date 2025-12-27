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

    # --- 📊 شاشة الدرجات والسلوك (متوافق مع ملفك الحالي) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        
        all_s = ws_students.get_all_records()
        if not all_s:
            st.warning("⚠️ أضف طلاباً أولاً")
        else:
            names = [r.get('name', 'بدون اسم') for r in all_s]
            t1, t2 = st.tabs(["📝 إدارة الدرجات", "🎭 إدارة السلوك"])

            # --- تبويب السلوك (مطابق لصورة الإكسيل الخاصة بك) ---
            with t2:
                with st.form("b_fix_form"):
                    sb_name = st.selectbox("اسم الطالب", names)
                    behav_opts = ["🌟 تميز", "📚 كتاب", "✅ واجب", "أخرى..."]
                    select_b = st.multiselect("السلوكيات", behav_opts)
                    other_txt = st.text_input("اكتب السلوك المخصص:") if "أخرى..." in select_b else ""
                    if st.form_submit_button("رصد"):
                        now = datetime.now()
                        ws_bh = sh.worksheet("behavior")
                        for b in select_b:
                            val = other_txt if b == "أخرى..." else b
                            # الترتيب حسب صورتك: student_id | date | type | note
                            # سنضع الاسم في خانة student_id لكي يظهر لك
                            ws_bh.append_row([sb_name, str(now.date()), val, get_day_ar(now.strftime('%A'))])
                        st.success("تم الحفظ"); st.rerun()

                st.markdown("### 📋 سجل السلوك الحالي")
                ws_bh = sh.worksheet("behavior")
                b_records = ws_bh.get_all_records()
                if b_records:
                    for i, row in enumerate(b_records):
                        # قراءة البيانات حسب مسميات أعمدتك في الصورة
                        bn = row.get('student_id', '؟؟')
                        bd = row.get('date', '')
                        bt = row.get('type', '-') # هنا يظهر السلوك (مثل إيجابي)
                        
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            st.warning(f"🎭 **{bn}**: {bt} — بتاريخ: {bd}")
                        with col_del:
                            if st.button("🗑️ حذف", key=f"db_fix_{i}"):
                                ws_bh.delete_rows(i + 2); st.rerun()
                                
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
