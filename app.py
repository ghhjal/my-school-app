import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. الإعدادات الجمالية والملكية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide", page_icon="🇬🇧")

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
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #fbbf24; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط المباشر بملفك في جوجل شيت ---
# تم استخدام الرابط الذي أرسلته مع إضافة التعديل التقني اللازم للاتصال
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        # قراءة البيانات مع تعطيل التخزين المؤقت لضمان التحديث الفوري
        return conn.read(spreadsheet=SHEET_URL, worksheet=sheet_name, ttl="0s")
    except Exception:
        # في حال كانت الورقة فارغة تماماً، نقوم بإنشاء ترويسات افتراضية
        if sheet_name == "students": return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])
        if sheet_name == "grades": return pd.DataFrame(columns=['student_id', 'p1', 'p2', 'perf'])
        if sheet_name == "behavior": return pd.DataFrame(columns=['student_id', 'date', 'type', 'note'])
        return pd.DataFrame()

# --- 3. إدارة الجلسة والدخول ---
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
        t1, t2 = st.tabs(["🔐 دخول المعلم", "🎓 دخول الطالب"])
        with t1:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول النظام"):
                if pwd == "admin123":
                    st.session_state.update({'logged_in': True, 'role': 'admin'})
                    st.rerun()
        with t2:
            sid_in = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            if st.button("استعلام عن نتيجة"):
                df_s = load_data("students")
                if not df_s.empty and sid_in in df_s['id'].values:
                    st.session_state.update({'logged_in': True, 'role': 'student', 'user_id': int(sid_in)})
                    st.rerun()
                else: st.error("عذراً، الرقم الأكاديمي غير مسجل.")

# --- 4. واجهات النظام بعد الدخول ---
else:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        with st.sidebar:
            st.markdown("<div style='text-align:center;'><b>أ/ زياد المعمري</b><br>English Teacher</div>", unsafe_allow_html=True)
            st.write("---")
            menu = st.radio("التنقل بين الصفحات", ["👥 إدارة الطلاب", "📊 رصد الدرجات", "📅 سجل السلوك"])

        # --- شاشة إدارة الطلاب ---
        if menu == "👥 إدارة الطلاب":
            st.markdown("<h2 style='color:#1e3a8a;'>👥 تسجيل بيانات الطلاب</h2>", unsafe_allow_html=True)
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                fid = c1.number_input("الرقم الأكاديمي", min_value=1)
                fname = c2.text_input("اسم الطالب الكامل")
                
                c3, c4 = st.columns(2)
                fclass = c3.text_input("الصف")
                fyear = c4.selectbox("العام الدراسي", ["1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                fsem = st.selectbox("الفصل الدراسي", ["الأول", "الثاني", "الثالث"])
                
                if st.form_submit_button("💾 حفظ في سحابة جوجل"):
                    if fname:
                        df_existing = load_data("students")
                        new_row = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": fyear, "sem": fsem}])
                        updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
                        conn.update(spreadsheet=SHEET_URL, worksheet="students", data=updated_df)
                        st.success(f"تم تسجيل الطالب {fname} بنجاح!")
                        st.balloons()
                    else: st.warning("يرجى إدخال اسم الطالب.")

            st.write("---")
            st.subheader("📋 قائمة الطلاب المسجلين")
            st.dataframe(load_data("students"), use_container_width=True)

        # --- شاشة رصد الدرجات ---
        elif menu == "📊 رصد الدرجات":
            st.markdown("<h2 style='color:#1e3a8a;'>📊 رصد درجات الإنجليزي</h2>", unsafe_allow_html=True)
            df_st = load_data("students")
            if not df_st.empty:
                target_name = st.selectbox("اختر اسم الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target_name]['id'].values[0]
                
                with st.form("grade_entry"):
                    g1, g2, g3 = st.columns(3)
                    p1 = g1.number_input("الفترة 1", 0.0, 20.0)
                    p2 = g2.number_input("الفترة 2", 0.0, 20.0)
                    pf = g3.number_input("المشاركة", 0.0, 40.0)
                    
                    if st.form_submit_button("✅ تحديث الدرجات في جوجل"):
                        df_grades = load_data("grades")
                        new_grade = pd.DataFrame([{"student_id": tid, "p1": p1, "p2": p2, "perf": pf}])
                        updated_grades = pd.concat([df_grades, new_grade]).drop_duplicates(subset=['student_id'], keep='last')
                        conn.update(spreadsheet=SHEET_URL, worksheet="grades", data=updated_grades)
                        st.success("تم تحديث الدرجات في ملف جوجل بنجاح!")

        # --- شاشة سجل السلوك ---
        elif menu == "📅 سجل السلوك":
            st.markdown("<h2 style='color:#1e3a8a;'>📅 سجل السلوك والملاحظات</h2>", unsafe_allow_html=True)
            df_st = load_data("students")
            if not df_st.empty:
                target_name = st.selectbox("الطالب", df_st['name'])
                tid = df_st[df_st['name'] == target_name]['id'].values[0]
                
                with st.form("behavior_entry"):
                    b_type = st.selectbox("نوع السلوك", ["إيجابي ✅", "سلبي ⚠️"])
                    b_note = st.text_area("تفاصيل الملاحظة")
                    if st.form_submit_button("➕ إضافة للسجل السحابي"):
                        df_beh = load_data("behavior")
                        new_beh = pd.DataFrame([{"student_id": tid, "date": str(date.today()), "type": b_type, "note": b_note}])
                        updated_beh = pd.concat([df_beh, new_beh])
                        conn.update(spreadsheet=SHEET_URL, worksheet="behavior", data=updated_beh)
                        st.success("تمت إضافة الملاحظة بنجاح!")

    # --- واجهة الطالب (الملكية) ---
    elif st.session_state.role == 'student':
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        sid = st.session_state.user_id
        df_students = load_data("students")
        info = df_students[df_students['id'] == sid].iloc[0]
        
        st.markdown(f"""
            <div class="royal-header">
                <h1>🎓 تقرير الطالب: {info['name']}</h1>
                <h3 style='color: #fbbf24;'>إشراف الأستاذ: زياد المعمري</h3>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚪 تسجيل الخروج والعودة"):
            st.session_state.clear()
            st.rerun()

        st.write(f"**المعلومات:** {info['class']} | {info['year']} | {info['sem']}")
        
        # عرض الدرجات
        st.divider()
        df_g = load_data("grades")
        grade_row = df_g[df_g['student_id'] == sid]
        if not grade_row.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الفترة 1", f"{grade_row.iloc[0]['p1']} / 20")
            c2.metric("الفترة 2", f"{grade_row.iloc[0]['p2']} / 20")
            c3.metric("المشاركة والمهام", f"{grade_row.iloc[0]['perf']} / 40")
        else:
            st.info("لم يتم رصد درجات حتى الآن.")

        # عرض السلوك
        st.divider()
        st.subheader("📅 سجل السلوك والملاحظات")
        df_b = load_data("behavior")
        student_beh = df_b[df_b['student_id'] == sid]
        if not student_beh.empty:
            st.table(student_beh[['date', 'type', 'note']])
        else:
            st.success("السجل نظيف. استمر في تميزك! 🌟")
