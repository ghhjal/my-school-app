import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# الربط مع الرابط الذي وضعته في Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# دالة لجلب البيانات
def load_students():
    return conn.read(worksheet="students", ttl=0)

# واجهة الإدخال
with st.form("add_form"):
    c1, c2 = st.columns(2)
    with c1:
        sid = st.number_input("الرقم الأكاديمي", min_value=1)
        sname = st.text_input("اسم الطالب")
    with c2:
        sclass = st.text_input("الصف")
        syear = st.selectbox("العام", ["1447هـ", "1448هـ"])
    
    if st.form_submit_button("حفظ في جوجل شيت"):
        if sname:
            df_existing = load_students()
            new_data = pd.DataFrame([{"id": sid, "name": sname, "class": sclass, "year": syear, "sem": "الأول"}])
            updated_df = pd.concat([df_existing, new_data]).drop_duplicates(subset=['id'], keep='last')
            
            # تحديث الملف
            conn.update(worksheet="students", data=updated_df)
            st.success("تم الحفظ بنجاح!")
            st.balloons()
        else:
            st.error("يرجى كتابة اسم الطالب")

# عرض الجدول للتأكد
st.divider()
st.subheader("📋 قائمة الطلاب المسجلة")
st.dataframe(load_students(), use_container_width=True)
