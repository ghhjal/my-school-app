import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# الربط السحابي
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    # قراءة البيانات مع ضمان عدم التخزين المؤقت (لحل مشكلة الخطأ)
    return conn.read(worksheet=sheet_name, ttl="0s")

# --- واجهة إضافة الطالب (المعلم) ---
st.title("👥 تسجيل بيانات الطلاب")
with st.form("add_student_form"):
    fid = st.number_input("الرقم الأكاديمي", min_value=1)
    fname = st.text_input("اسم الطالب الكامل")
    fclass = st.text_input("الصف")
    fyear = st.selectbox("العام الدراسي", ["1447هـ", "1448هـ"])
    fsem = st.selectbox("الفصل الدراسي", ["الأول", "الثاني", "الثالث"])
    
    submit = st.form_submit_button("💾 حفظ في سحابة جوجل")
    
    if submit:
        if fname:
            try:
                # جلب البيانات الحالية
                df_existing = load_data("students")
                # إضافة السطر الجديد
                new_row = pd.DataFrame([{"id": fid, "name": fname, "class": fclass, "year": fyear, "sem": fsem}])
                updated_df = pd.concat([df_existing, new_row]).drop_duplicates(subset=['id'], keep='last')
                
                # تحديث ملف جوجل
                conn.update(worksheet="students", data=updated_df)
                st.success(f"تم تسجيل الطالب {fname} بنجاح في ملفك!")
                st.balloons()
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال: {e}")
        else:
            st.warning("يرجى إدخال اسم الطالب")

# عرض الجدول الحالي للتأكد من المزامنة
st.divider()
st.subheader("📋 القائمة الحالية في جوجل شيت")
st.dataframe(load_data("students"), use_container_width=True)
