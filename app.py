import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# 1. رابط القراءة (CSV) لورقة "ردود النموذج 1"
CSV_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/gviz/tq?tqx=out:csv&sheet=ردود%20النموذج%201"

st.title("👨‍🏫 نظام الأستاذ زياد - إدارة الطلاب")

# الجزء الأول: عرض البيانات
st.subheader("📋 قائمة الطلاب المسجلين حالياً")
try:
    # قراءة البيانات وعرضها
    df = pd.read_csv(CSV_URL)
    # إخفاء عمود الطابع الزمني لجمالية العرض
    st.dataframe(df.iloc[:, 1:], use_container_width=True)
except Exception:
    st.info("الجدول فارغ حالياً أو بانتظار أول عملية تسجيل.")

st.divider()

# الجزء الثاني: إضافة البيانات (روابط مباشرة)
st.subheader("➕ إضافة وإدارة البيانات")

col1, col2 = st.columns(2)

with col1:
    st.info("لإضافة طالب جديد، استخدم النموذج الرسمي:")
    # الرابط المختصر الذي أرسلته أنت والذي يعمل يقيناً
    st.markdown(f'''
        <a href="https://forms.gle/MCXFKq12xmmE3XMf8" target="_blank">
            <button style="
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                width: 100%;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;">
                📝 فتح نموذج تسجيل الطلاب
            </button>
        </a>
        ''', unsafe_allow_html=True)

with col2:
    st.info("للوصول المباشر لملف الإكسيل (جوجل شيت):")
    st.markdown(f'''
        <a href="https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/edit" target="_blank">
            <button style="
                background-color: #008CBA;
                color: white;
                padding: 15px;
                width: 100%;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;">
                📊 فتح ملف English_Grades
            </button>
        </a>
        ''', unsafe_allow_html=True)

st.success("بعد تعبئة النموذج، قم بتحديث هذه الصفحة لرؤية الاسم الجديد في الجدول أعلاه.")
