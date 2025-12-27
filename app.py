import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعداد الصفحة الأساسي
st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# 2. إنشاء الاتصال (سيسحب الرابط من Secrets تلقائياً)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. دالة جلب البيانات مع معالجة الأخطاء
def load_students_data():
    try:
        # قراءة ورقة الطلاب مباشرة
        return conn.read(worksheet="students", ttl=0)
    except:
        # إذا كانت الورقة فارغة، ننشئ الأعمدة كما في ملفك
        return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])

st.title("👨‍🏫 تسجيل الطلاب - الأستاذ زياد المعمري")

# 4. نموذج الإدخال
with st.form("student_entry_form"):
    st.subheader("إضافة طالب جديد")
    c1, c2 = st.columns(2)
    with c1:
        new_id = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        new_name = st.text_input("اسم الطالب")
    with c2:
        new_class = st.text_input("الصف")
        new_year = st.selectbox("العام الدراسي", ["1447هـ", "1448هـ"])
    
    save_btn = st.form_submit_button("💾 حفظ البيانات في جوجل شيت")

if save_btn:
    if new_name:
        try:
            # جلب البيانات الموجودة حالياً
            df_existing = load_students_data()
            
            # تجهيز السطر الجديد
            new_row = pd.DataFrame([{
                "id": new_id,
                "name": new_name,
                "class": new_class,
                "year": new_year,
                "sem": "الأول"
            }])
            
            # دمج البيانات الجديدة مع القديمة ومنع التكرار
            updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
            
            # إرسال التحديث إلى جوجل شيت
            conn.update(worksheet="students", data=updated_df)
            
            st.success(f"✅ تم حفظ الطالب {new_name} بنجاح!")
            st.balloons()
        except Exception as e:
            st.error(f"❌ تعذر الحفظ: تأكد من أن صلاحية الملف 'Editor' للجميع")
    else:
        st.warning("⚠️ يرجى إدخال اسم الطالب أولاً")

# 5. عرض البيانات للتأكد من المزامنة
st.divider()
st.subheader("📋 قائمة الطلاب المسجلة في ملفك:")
st.dataframe(load_students_data(), use_container_width=True)
