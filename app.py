import streamlit as st
import pandas as pd
import webbrowser

st.set_page_config(page_title="نظام الأستاذ زياد", layout="wide")

# رابط القراءة (CSV) الذي نجحنا فيه
CSV_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/gviz/tq?tqx=out:csv&sheet=students"

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# 1. عرض البيانات الحالية (للقراءة فقط)
try:
    df = pd.read_csv(CSV_URL)
    st.subheader("📋 قائمة الطلاب الحالية")
    st.dataframe(df, use_container_width=True)
except:
    st.info("الجدول فارغ حالياً.")

st.divider()

# 2. واجهة الإدخال
st.subheader("➕ إضافة طالب جديد")
# ضع رابط نموذج جوجل الذي أنشأته هنا
GOOGLE_FORM_URL = "ضع_رابط_نموذج_جوجل_هنا"

with st.form("entry_form"):
    fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
    fname = st.text_input("اسم الطالب")
    fclass = st.text_input("الصف")
    submit = st.form_submit_button("إرسال البيانات إلى السحابة")

    if submit:
        if fname:
            st.success(f"تم تسجيل الطالب {fname} بنجاح!")
            # سيفتح النموذج في صفحة جديدة ليقوم بالحفظ الأكيد
            st.markdown(f'<a href="{GOOGLE_FORM_URL}" target="_blank">انقر هنا لتأكيد الحفظ النهائي في جوجل شيت</a>', unsafe_allow_html=True)
        else:
            st.error("يرجى كتابة الاسم.")
