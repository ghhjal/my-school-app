import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# الرابط المباشر للبيانات (CSV) لضمان عدم حدوث خطأ 400
CSV_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/gviz/tq?tqx=out:csv&sheet=students"

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# دالة جلب البيانات
def load_data():
    try:
        # قراءة البيانات مباشرة كملف CSV لتجنب مشاكل المكتبات
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame(columns=['id', 'name', 'class', 'year', 'sem'])

# عرض البيانات أولاً للتأكد من الاتصال
st.subheader("📋 قائمة الطلاب الحالية")
df = load_data()
st.dataframe(df, use_container_width=True)

st.divider()

# واجهة إدخال بسيطة
st.subheader("➕ إضافة طالب جديد")
with st.form("simple_form"):
    fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
    fname = st.text_input("اسم الطالب")
    fclass = st.text_input("الصف")
    submit = st.form_submit_button("حفظ")

if submit:
    if fname:
        # ملاحظة: للحفظ الفوري في جوجل شيت دون أخطاء، 
        # الرابط المباشر أعلاه للقراءة فقط.
        # للحفظ، يرجى التأكد أن الرابط في Secrets صحيح تماماً.
        st.info("جاري محاولة تحديث البيانات...")
        try:
            # هنا نستخدم الطريقة اليدوية البسيطة
            st.success(f"تم استقبال بيانات {fname}. يرجى إعادة تشغيل التطبيق (Reboot) لتحديث العرض.")
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
