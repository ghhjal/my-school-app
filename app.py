import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. الإعدادات الملكية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .royal-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white; padding: 25px; border-radius: 15px; text-align: center;
        box-shadow: 0 10px 20px rgba(30, 58, 138, 0.2); margin-bottom: 25px;
    }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط السحابي الصحيح ---
# البرنامج سيبحث عن الرابط في Secrets تلقائياً
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        # قراءة البيانات مع ضمان عدم التخزين المؤقت لرؤية التحديثات فوراً
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception:
        # إنشاء ترويسات مطابقة للصور التي أرفقتها في حال وجود مشكلة
        [cite_start]if sheet_name == "students": return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem']) [cite: 3]
        [cite_start]if sheet_name == "grades": return pd.DataFrame(columns=['student_id', 'p1', 'p2', 'perf']) [cite: 2]
        [cite_start]if sheet_name == "behavior": return pd.DataFrame(columns=['student_id', 'date', 'type', 'note']) [cite: 1]
        return pd.DataFrame()

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown('<div class="royal-header"><h1>🇬🇧 نظام الأستاذ زياد المعمري</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 المعلم", "🎓 الطالب"])
    with tab1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with tab2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("استعلام"):
            df_s = load_data("students")
            if not df_s.empty and sid_in in df_s['id'].values:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("غير مسجل.")

# --- 4. واجهة المعلم بعد الإصلاح ---
else:
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات", "📅 السلوك"])

        if menu == "👥 إدارة الطلاب":
            st.header("تسجيل طالب جديد")
            with st.form("add_st"):
                fid = st.number_input("الرقم الأكاديمي", min_value=1)
                fname = st.text_input("الاسم")
                fclass = st.text_input("الصف")
                fyear = st.selectbox("العام", ["1447هـ", "1448هـ", "1449هـ"])
                fsem = st.selectbox("الفصل", ["الأول", "الثاني", "الثالث"])
                
                if st.form_submit_button("💾 حفظ في سحابة جوجل"):
                    # جلب البيانات الحالية
                    df_existing = load_data("students")
                    # تجهيز السطر الجديد
                    new_row = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": fyear, "sem": fsem}])
                    # الدمج والحفظ
                    updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
                    conn.update(worksheet="students", data=updated_df)
                    st.success("تم الحفظ والمزامنة بنجاح!")
                    st.balloons()

            st.write("---")
            st.dataframe(load_data("students"), use_container_width=True)
            
        # (باقي الأقسام تتبع نفس منطق conn.update)
