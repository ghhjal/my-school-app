import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# رابط الملف ومعرف الورقة
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/edit#gid=0"

# إنشاء الاتصال
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # قراءة البيانات مع تعطيل التخزين المؤقت لضمان رؤية التحديثات
        return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    except:
        # إنشاء هيكل بيانات افتراضي في حال كانت الورقة فارغة تماماً
        if worksheet_name == "students": return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])
        if worksheet_name == "grades": return pd.DataFrame(columns=['student_id', 'p1', 'p2', 'perf'])
        return pd.DataFrame()

st.title("👨‍🏫 لوحة تحكم الأستاذ زياد")

# واجهة إضافة طالب جديد
with st.expander("➕ إضافة طالب جديد", expanded=True):
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        with col1:
            st_id = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            st_name = st.text_input("اسم الطالب")
        with col2:
            st_class = st.text_input("الصف")
            st_year = st.selectbox("العام", ["1447هـ", "1448هـ"])
            st_sem = st.selectbox("الفصل", ["الأول", "الثاني", "الثالث"])
        
        if st.form_submit_button("حفظ البيانات"):
            if st_name:
                df_existing = get_data("students")
                new_entry = pd.DataFrame([{"id": st_id, "name": st_name, "class": st_class, "year": st_year, "sem": st_sem}])
                # دمج البيانات ومنع التكرار بناءً على الرقم الأكاديمي
                updated_df = pd.concat([df_existing, new_entry]).drop_duplicates(subset=['id'], keep='last')
                
                try:
                    conn.update(spreadsheet=SHEET_URL, worksheet="students", data=updated_df)
                    st.success(f"تم حفظ بيانات الطالب {st_name} بنجاح!")
                    st.balloons()
                except Exception as e:
                    st.error(f"خطأ أثناء التحديث: {e}")
            else:
                st.warning("يرجى إدخال اسم الطالب")

# عرض البيانات الحالية للتأكد
st.divider()
st.subheader("📋 قائمة الطلاب الحالية")
st.dataframe(get_data("students"), use_container_width=True)
