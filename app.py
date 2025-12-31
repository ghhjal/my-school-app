import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# ==========================================
# 1. إعدادات الصفحة وتهيئة الجلسة
# ==========================================
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="centered")

# منع أخطاء AttributeError بتعريف متغيرات الجلسة أولاً
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# ==========================================
# 2. وظائف الاتصال والبيانات
# ==========================================
def connect_to_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # تأكد من وجود مفاتيح GCP في Secrets بمنصة Streamlit
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # الرابط الخاص بملفك (الموجود في الصور)
        sheet_url = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        sh = client.open_by_url(sheet_url)
        return sh
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بجوجل شيت: {e}")
        return None

def get_data(sheet_name):
    sh = connect_to_sheet()
    if sh:
        try:
            worksheet = sh.worksheet(sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # توحيد نوع بيانات العمود الأول (الكود) ليكون نصاً دائماً
            if not df.empty:
                df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
            return df, worksheet
        except Exception as e:
            st.warning(f"⚠️ تنبيه: لم يتم العثور على ورقة '{sheet_name}' أو هي فارغة.")
            return pd.DataFrame(), None
    return pd.DataFrame(), None

# ==========================================
# 🏠 3. واجهة تسجيل الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #1e3a8a; font-family: 'Cairo';">🌟 منصة الأستاذ زياد العمري</h1>
            <p style="color: #64748b;">نظام الإدارة المدرسية الذكي</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div style='background: #f8fafc; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
            user_input = st.text_input("أدخل كود الدخول الخاص بك", placeholder="مثال: 1001").strip()
            
            if st.button("🚀 تسجيل الدخول", use_container_width=True):
                if login_type == "معلم":
                    if user_input == "1234": # كود المعلم الافتراضي
                        st.session_state.role = "teacher"
                        st.rerun()
                    else:
                        st.error("❌ كود المعلم غير صحيح")
                else:
                    df_students, _ = get_data("students")
                    if not df_students.empty and user_input in df_students.iloc[:, 0].values:
                        st.session_state.role = "student"
                        st.session_state.sid = user_input
                        st.success("✅ تم التحقق، جاري الدخول...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ كود الطالب غير مسجل في النظام")
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 👨‍🏫 4. واجهة المعلم (أ. زياد)
# ==========================================
elif st.session_state.role == "teacher":
    st.sidebar.title("👨‍🏫 لوحة التحكم")
    st.sidebar.info(f"مرحباً أ. زياد العمري")
    
    task = st.sidebar.selectbox("اختر المهمة:", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 سجل السلوك"])
    
    if st.sidebar.button("🚗 خروج"):
        st.session_state.role = None
        st.rerun()

    if task == "👥 إدارة الطلاب":
        st.header("👥 إضافة وإدارة الطلاب")
        
        # نموذج إضافة طالب
        with st.expander("➕ إضافة طالب جديد", expanded=True):
            with st.form("add_st_form"):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("كود الطالب (ID)")
                nname = c2.text_input("اسم الطالب الثلاثي")
                nclass = c3.selectbox("الصف", ["الرابع", "الخامس", "السادس"])
                
                if st.form_submit_button("حفظ البيانات"):
                    df_st, ws_st = get_data("students")
                    if ws_st:
                        # إضافة الصف مع ملء كافة الأعمدة الافتراضية لمنع الأخطاء
                        ws_st.append_row([nid, nname, nclass, "1447", "نشط", "English", "Primary", "0", "0", "0"])
                        st.success(f"✅ تم إضافة {nname} بنجاح!")
                        time.sleep(1)
                        st.rerun()

        # عرض الجدول الحالي
        df_display, _ = get_data("students")
        st.subheader("قائمة الطلاب المسجلين")
        st.dataframe(df_display, use_container_width=True)

    elif task == "📝 رصد الدرجات":
        st.header("📝 رصد الدرجات الأكاديمية")
        df_students, _ = get_data("students")
        df_grades, ws_grades = get_data("grades")
        
        student_choice = st.selectbox("اختر الطالب لرصد درجته:", [""] + df_students.iloc[:, 1].tolist())
        
        if student_choice:
            with st.form("grading_form"):
                p1 = st.number_input("درجة الفترة 1", 0, 100)
                p2 = st.number_input("درجة الفترة 2", 0, 100)
                perf = st.number_input("المشاركة والنشاط", 0, 100)
                
                if st.form_submit_button("تحديث الدرجة"):
                    # ابحث عن الطالب لتحديثه أو أضف صفاً جديداً
                    try:
                        cell = ws_grades.find(student_choice)
                        ws_grades.update(f'B{cell.row}:D{cell.row}', [[p1, p2, perf]])
                    except:
                        ws_grades.append_row([student_choice, p1, p2, perf])
                    st.success("✅ تم تحديث الدرجات بنجاح")

# ==========================================
# 👨‍🎓 5. واجهة الطالب (تصميم احترافي)
# ==========================================
elif st.session_state.role == "student":
    df_st, _ = get_data("students")
    df_gr, _ = get_data("grades")
    
    # جلب بيانات الطالب الحالي
    student_row = df_st[df_st.iloc[:, 0] == st.session_state.sid].iloc[0]
    s_name = student_row.iloc[1]
    s_class = student_row.iloc[2]
    try: s_points = int(student_row.iloc[9]) # بافتراض العمود J هو النقاط
    except: s_points = 0

    # هيدر الطالب
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <p style="color: #64748b; margin-bottom: 5px;">الملف الشخصي للطالب</p>
            <h2 style="color: #1e3a8a; margin: 0;">{s_name}</h2>
            <div style="background: #eff6ff; color: #3b82f6; display: inline-block; padding: 5px 15px; border-radius: 15px; margin-top: 10px; font-size: 0.9rem;">
                🏠 صف: {s_class}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # قسم الأوسمة والنقاط
    st.markdown(f"""
        <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
            <div style="border: 2px solid #cd7f32; padding: 10px; border-radius: 15px; width: 30%; background: #fffcf9; text-align: center;">
                <div style="font-size: 1.5rem;">🥉</div><div style="font-weight: bold; color: #cd7f32; font-size: 0.7rem;">برونزي</div>
            </div>
            <div style="border: 2px solid #c0c0c0; padding: 10px; border-radius: 15px; width: 30%; background: #f8f9fa; text-align: center;">
                <div style="font-size: 1.5rem;">🥈</div><div style="font-weight: bold; color: #7f8c8d; font-size: 0.7rem;">فضي</div>
            </div>
            <div style="border: 2px solid #ffd700; padding: 10px; border-radius: 15px; width: 30%; background: #ffffd0; text-align: center;">
                <div style="font-size: 1.5rem;">🥇</div><div style="font-weight: bold; color: #d4af37; font-size: 0.7rem;">ذهبي</div>
            </div>
        </div>
        <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px; text-align: center; box-shadow: 0 4px 10px rgba(217, 119, 6, 0.3);">
            <small>رصيد النقاط السلوكية الحالي</small><br>
            <b style="font-size: 2.2rem;">{s_points}</b>
        </div>
    """, unsafe_allow_html=True)

    # عرض الدرجات
    st.markdown("### 📊 السجل الأكاديمي")
    my_grade = df_gr[df_gr.iloc[:, 0] == s_name]
    if not my_grade.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("الفترة الأولى", my_grade.iloc[0, 1])
        c2.metric("الفترة الثانية", my_grade.iloc[0, 2])
        c3.metric("المشاركة", my_grade.iloc[0, 3])
    else:
        st.info("لم يتم رصد الدرجات لهذه الفترة بعد.")

    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None
        st.session_state.sid = None
        st.rerun()

# ==========================================
# 6. تذييل الصفحة
# ==========================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>تم التطوير بواسطة ذكاء Gemini للأستاذ زياد العمري © 2025</p>", unsafe_allow_html=True)
