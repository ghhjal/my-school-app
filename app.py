import streamlit as st
import pandas as pd
import requests

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# 1. رابط القراءة (CSV) لورقة "ردود النموذج 1"
CSV_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/gviz/tq?tqx=out:csv&sheet=ردود%20النموذج%201"

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# عرض الجدول الحالي (مع إخفاء عمود الوقت)
try:
    df = pd.read_csv(CSV_URL)
    st.subheader("📋 قائمة الطلاب المسجلين")
    st.dataframe(df.iloc[:, 1:], use_container_width=True) 
except:
    st.info("لا توجد بيانات مسجلة بعد، قم بإضافة أول طالب.")

st.divider()

# 2. نموذج الإضافة الآلي باستخدام الأرقام المستخرجة
st.subheader("➕ إضافة طالب جديد")
with st.form("auto_entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        fname = st.text_input("اسم الطالب الكامل")
    with col2:
        fclass = st.text_input("الصف")
    
    submit = st.form_submit_button("🚀 حفظ البيانات فوراً")

    if submit:
        if fname:
            # رابط إرسال النموذج المباشر
            FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdyE_7B-6WvG99pA/formResponse"
            
            # البيانات مع أرقام entry المستخرجة من صورتك
            payload = {
                "entry.1776082434": fid,   # الرقم الأكاديمي
                "entry.64593526": fname,   # اسم الطالب
                "entry.1340307757": fclass # الصف
            }
            
            try:
                # إرسال البيانات في الخلفية
                response = requests.post(FORM_URL, data=payload)
                if response.status_code == 200:
                    st.success(f"✅ تم حفظ الطالب {fname} بنجاح في جوجل شيت!")
                    st.balloons()
                    st.info("يرجى تحديث الصفحة لرؤية البيانات الجديدة في الجدول.")
                else:
                    st.error("فشل في الحفظ التلقائي، يرجى التأكد من اتصال الإنترنت.")
            except Exception as e:
                st.error(f"خطأ في الاتصال: {e}")
        else:
            st.warning("يرجى كتابة اسم الطالب أولاً.")
