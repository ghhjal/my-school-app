import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. إعدادات الهوية الملكية (الأستاذ زياد المعمري) ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

st.markdown("""
    <style>
    .royal-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white; padding: 25px; border-radius: 15px; text-align: center;
        margin-bottom: 25px; border-bottom: 5px solid #fbbf24;
    }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط السحابي مع Google Sheets ---
# سيستخدم البرنامج الرابط الموجود في Secrets تلقائياً
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception:
        # إنشاء جداول فارغة بالترويسات الصحيحة في حال حدوث خطأ
        if sheet_name == "students": return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])
        if sheet_name == "grades": return pd.DataFrame(columns=['student_id', 'p1', 'p2', 'perf'])
        if sheet_name == "behavior": return pd.DataFrame(columns=['student_id', 'date', 'type', 'note'])
        return pd.DataFrame()

# --- 3. نظام الجلسة والدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown('<div class="royal-header"><h1>🇬🇧 نظام الأستاذ زياد المعمري</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 دخول المعلم", "🎓 دخول الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "admin123":
                st.session_state.update({'logged_in': True, 'role': 'admin'})
                st.rerun()
    with t2:
        sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        if st.button("استعلام"):
            df_s = load_data("students")
            if not df_s.empty and sid_in in df_s['id'].values:
                st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                st.rerun()
            else: st.error("الرقم غير مسجل.")

# --- 4. واجهات النظام ---
else:
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])

        if menu == "👥 إدارة الطلاب":
            st.header("إدارة الطلاب")
            with st.form("add_st"):
                fid = st.number_input("الرقم الأكاديمي", min_value=1)
                fname = st.text_input("اسم الطالب")
                fclass = st.text_input("الصف")
                fyear = st.selectbox("العام", ["1447هـ", "1448هـ", "1449هـ"])
                fsem = st.selectbox("الفصل", ["الأول", "الثاني", "الثالث"])
                if st.form_submit_button("💾 حفظ في سحابة جوجل"):
                    df_existing = load_data("students")
                    new_row = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": fyear, "sem": fsem}])
                    updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
                    conn.update(worksheet="students", data=updated_df)
                    st.success("تم الحفظ والمزامنة بنجاح!")
            st.dataframe(load_data("students"), use_container_width=True)

        elif menu == "📊 رصد الدرجات":
            st.header("رصد الدرجات")
            df_st = load_data("students")
            if not df_st.empty:
                target = st.selectbox("اختر الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target]['id'].values[0]
                with st.form("gr_form"):
                    p1 = st.number_input("الفترة 1", 0.0, 20.0)
                    p2 = st.number_input("الفترة 2", 0.0, 20.0)
                    pf = st.number_input("المشاركة", 0.0, 40.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        df_g = load_data("grades")
                        new_g = pd.DataFrame([{"student_id": tid, "p1": p1, "p2": p2, "perf": pf}])
                        updated_g = pd.concat([df_g, new_g]).drop_duplicates(subset=['student_id'], keep='last')
                        conn.update(worksheet="grades", data=updated_g)
                        st.success("تم تحديث الدرجات")

        elif menu == "📅 سجل السلوك":
            st.header("سجل السلوك")
            df_st = load_data("students")
            if not df_st.empty:
                target = st.selectbox("الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target]['id'].values[0]
                with st.form("bh_form"):
                    b_type = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة ملاحظة"):
                        df_b = load_data("behavior")
                        new_b = pd.DataFrame([{"student_id": tid, "date": str(date.today()), "type": b_type, "note": b_note}])
                        updated_b = pd.concat([df_b, new_b])
                        conn.update(worksheet="behavior", data=updated_b)
                        st.success("تمت الإضافة للسجل")

    elif st.session_state.role == 'student':
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        df_s = load_data("students")
        info = df_s[df_s['id'] == st.session_state.user_id].iloc[0]
        st.markdown(f'<div class="royal-header"><h1>🎓 تقرير الطالب: {info["name"]}</h1></div>', unsafe_allow_html=True)
        # عرض البيانات كما في النسخة السابقة...
