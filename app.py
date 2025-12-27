import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# 2. الربط مع جوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("👨‍🏫 إدارة بيانات الطلاب")

# 3. دالة جلب البيانات
def load_data():
    return conn.read(worksheet="students", ttl=0)

# 4. نموذج الإدخال
with st.form("student_form"):
    fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
    fname = st.text_input("اسم الطالب")
    fclass = st.text_input("الصف")
    submit = st.form_submit_button("حفظ في جوجل شيت")

if submit:
    try:
        df_existing = load_data()
        new_row = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": "1447هـ", "sem": "الأول"}])
        updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
        
        # التحديث الفعلي
        conn.update(worksheet="students", data=updated_df)
        st.success("تم الحفظ بنجاح!")
        st.balloons()
    except Exception as e:
        st.error(f"خطأ: {e}")

# 5. عرض الجدول
st.divider()
st.dataframe(load_data(), use_container_width=True)
