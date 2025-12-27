import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# إنشاء الاتصال
conn = st.connection("gsheets", type=GSheetsConnection)

# معرف ملف جوجل شيت الخاص بك (مستخرج من رابطك)
SPREADSHEET_ID = "1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c"

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# دالة جلب البيانات
def load_data():
    try:
        # القراءة باستخدام المعرف والاسم المباشر للورقة
        return conn.read(spreadsheet=SPREADSHEET_ID, worksheet="students", ttl=0)
    except Exception as e:
        # إنشاء جدول فارغ إذا لم يجد البيانات
        return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])

# نموذج الإدخال
with st.form("student_form"):
    st.subheader("إضافة طالب جديد")
    fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
    fname = st.text_input("اسم الطالب")
    fclass = st.text_input("الصف")
    submit = st.form_submit_button("حفظ في جوجل شيت")

if submit:
    if fname:
        try:
            df_existing = load_data()
            new_row = pd.DataFrame([{
                "id": fid, 
                "name": fname, 
                "class": fclass, 
                "year": "1447هـ", 
                "sem": "الأول"
            }])
            updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
            
            # التحديث باستخدام المعرف لضمان عدم حدوث Bad Request
            conn.update(spreadsheet=SPREADSHEET_ID, worksheet="students", data=updated_df)
            st.success("✅ تم الحفظ بنجاح!")
            st.balloons()
        except Exception as e:
            st.error(f"⚠️ فشل التحديث: {e}")
    else:
        st.warning("يرجى إدخال اسم الطالب")

# عرض الجدول
st.divider()
st.subheader("📋 قائمة الطلاب المسجلة")
st.dataframe(load_data(), use_container_width=True)
