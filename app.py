import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. الإعدادات الملكية (الأستاذ زياد المعمري) ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري السحابي", layout="wide", page_icon="🇬🇧")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .royal-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white; padding: 25px; border-radius: 15px; text-align: center;
        box-shadow: 0 10px 20px rgba(30, 58, 138, 0.2); margin-bottom: 25px;
        border-bottom: 5px solid #fbbf24;
    }
    .card { background: white; padding: 15px; border-radius: 12px; border-right: 8px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط السحابي مع Google Sheets ---
# ملاحظة: سيعتمد البرنامج على الرابط الذي وضعته في Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0s")
    except:
        # إنشاء بيانات وهمية إذا كان الملف فارغاً تماماً في البداية
        return pd.DataFrame()

# --- 3. نظام الجلسة والدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_id': None})

if not st.session_state.logged_in:
    st.markdown("""
        <div class="royal-header">
            <h1>🇬🇧 نظام رصد درجات اللغة الإنجليزية</h1>
            <h3 style='color: #fbbf24;'>إشراف الأستاذ: زياد المعمري</h3>
        </div>
        """, unsafe_allow_html=True)
    
    col_log, _ = st.columns([1, 1])
    with col_log:
        tab1, tab2 = st.tabs(["🔐 بوابة المعلم", "🎓 بوابة الطالب"])
        with tab1:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول النظام"):
                if pwd == "admin123":
                    st.session_state.update({'logged_in': True, 'role': 'admin'})
                    st.rerun()
        with tab2:
            sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            if st.button("استعلام"):
                df_students = get_data("students")
                if not df_students.empty and sid_in in df_students['id'].values:
                    st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                    st.rerun()
                else: st.error("الرقم الأكاديمي غير مسجل.")

# --- 4. واجهات النظام (بعد الدخول) ---
else:
    # خيار الخروج يظهر للجميع
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- واجهة المعلم ---
    if st.session_state.role == 'admin':
        with st.sidebar:
            st.markdown("<div style='text-align:center;'><b>أ/ زياد المعمري</b></div>", unsafe_allow_html=True)
            menu = st.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])

        if menu == "👥 إدارة الطلاب":
            st.header("👥 إدارة الطلاب (سحابة جوجل)")
            with st.form("student_form"):
                fid = st.number_input("الرقم الأكاديمي", min_value=1)
                fname = st.text_input("اسم الطالب")
                fclass = st.text_input("الصف")
                fyear = st.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                fsem = st.selectbox("الفصل", ["الأول", "الثاني", "الثالث"])
                
                if st.form_submit_button("💾 حفظ في جوجل شيت"):
                    df_students = get_data("students")
                    new_data = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": fyear, "sem": fsem}])
                    updated_df = pd.concat([df_students, new_data]).drop_duplicates(subset=['id'], keep='last')
                    conn.update(worksheet="students", data=updated_df)
                    st.success("تم الحفظ والمزامنة مع جوجل شيت!")

            st.write("---")
            st.subheader("📋 الطلاب الحاليين")
            st.dataframe(get_data("students"), use_container_width=True)

        elif menu == "📊 رصد الدرجات":
            st.header("📊 رصد الدرجات")
            df_st = get_data("students")
            if not df_st.empty:
                target = st.selectbox("اختر الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target]['id'].values[0]
                
                with st.form("grade_form"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0)
                    pf = g3.number_input("المشاركة", 0.0, 40.0)
                    if st.form_submit_button("📝 تحديث الدرجات"):
                        df_grades = get_data("grades")
                        new_grade = pd.DataFrame([{"student_id": tid, "p1": p1, "p2": p2, "perf": pf}])
                        updated_grades = pd.concat([df_grades, new_grade]).drop_duplicates(subset=['student_id'], keep='last')
                        conn.update(worksheet="grades", data=updated_grades)
                        st.success("تم التحديث في جوجل شيت")
            
        elif menu == "📅 سجل السلوك":
            st.header("📅 سجل السلوك")
            df_st = get_data("students")
            if not df_st.empty:
                target = st.selectbox("اختر الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target]['id'].values[0]
                with st.form("beh_form"):
                    b_type = st.selectbox("النوع", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("الملاحظة")
                    if st.form_submit_button("إضافة"):
                        df_beh = get_data("behavior")
                        new_beh = pd.DataFrame([{"student_id": tid, "date": str(date.today()), "type": b_type, "note": b_note}])
                        updated_beh = pd.concat([df_beh, new_beh])
                        conn.update(worksheet="behavior", data=updated_beh)
                        st.success("تمت الإضافة")

    # --- واجهة الطالب (نظيفة) ---
    elif st.session_state.role == 'student':
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        sid = st.session_state.user_id
        df_students = get_data("students")
        info = df_students[df_students['id'] == sid].iloc[0]
        
        st.markdown(f"""
            <div class="royal-header">
                <h1>🎓 تقرير الطالب: {info['name']}</h1>
                <h3 style='color: #fbbf24;'>إشراف الأستاذ: زياد المعمري</h3>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

        st.write(f"**الصف:** {info['class']} | **العام:** {info['year']}")
        
        st.divider()
        df_g = get_data("grades")
        grade = df_g[df_g['student_id'] == sid]
        if not grade.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", f"{grade.iloc[0]['p1']} / 20")
            c2.metric("الفترة 2", f"{grade.iloc[0]['p2']} / 20")
            c3.metric("المشاركة", f"{grade.iloc[0]['perf']} / 40")
        
        st.divider()
        st.subheader("📅 سجل الملاحظات")
        df_b = get_data("behavior")
        st.table(df_b[df_b['student_id'] == sid][['date', 'type', 'note']])
