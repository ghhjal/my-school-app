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

    # --- 📊 شاشة الدرجات والسلوك (التحديث المطلوب) ---
    elif page == "📊 الدرجات والسلوك":
        st.markdown("<h1>📊 سجل الدرجات والسلوك</h1>", unsafe_allow_html=True)
        all_s = ws_students.get_all_records()
        if not all_s: st.warning("أضف طلاباً أولاً")
        else:
            names = [r['name'] for r in all_s]
            t1, t2 = st.tabs(["📝 إدارة الدرجات", "🎭 إدارة السلوك"])
            
            with t1:
                with st.form("g_form"):
                    c1, c2, c3 = st.columns([2,1,1])
                    with c1: st_g = st.selectbox("الطالب", names)
                    with c2: tp_g = st.selectbox("النوع", ["مشاركة", "واجب", "فتري", "نهائي"])
                    with c3: sc_g = st.number_input("الدرجة", min_value=0.0)
                    if st.form_submit_button("حفظ الدرجة"):
                        now = datetime.now()
                        sh.worksheet("grades").append_row([st_g, tp_g, sc_g, str(now.date()), get_day_ar(now.strftime('%A'))])
                        st.success("تم الرصد"); st.rerun()
                
                st.subheader("📋 جدول الدرجات")
                df_g = pd.DataFrame(sh.worksheet("grades").get_all_records())
                if not df_g.empty:
                    for i, row in df_g.iterrows():
                        with st.expander(f"📝 {row.get('name', '؟؟')} - {row.get('score', 0)}"):
                            if st.button("🗑️ حذف هذه الدرجة", key=f"dg_{i}"):
                                sh.worksheet("grades").delete_rows(i+2); st.rerun()
                    st.dataframe(df_g, use_container_width=True)

            with t2:
                with st.form("b_form"):
                    st_b = st.selectbox("الطالب", names, key="sb")
                    behavs = st.multiselect("السلوكيات", ["🌟 تميز", "📚 كتاب", "✅ واجب", "⚠️ إزعاج", "أخرى..."])
                    other = st.text_input("إذا اخترت أخرى، اكتبها هنا:") if "أخرى..." in behavs else ""
                    if st.form_submit_button("رصد السلوك"):
                        now = datetime.now()
                        for b in behavs:
                            final_b = other if b == "أخرى..." else b
                            sh.worksheet("behavior").append_row([st_b, final_b, str(now.date()), get_day_ar(now.strftime('%A'))])
                        st.success("تم الحفظ"); st.rerun()
                
                st.subheader("📋 جدول السلوك")
                df_b = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                if not df_b.empty:
                    st.dataframe(df_b, use_container_width=True)
                    for i, row in df_b.iterrows():
                        if st.button(f"🗑️ حذف سلوك {row.get('name', i)}", key=f"db_{i}"):
                            sh.worksheet("behavior").delete_rows(i+2); st.rerun()

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
