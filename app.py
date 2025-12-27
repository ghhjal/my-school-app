import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# 1. رابط القراءة (CSV) لورقة "ردود النموذج 1" لضمان عرض البيانات
CSV_URL = "https://docs.google.com/spreadsheets/d/1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c/gviz/tq?tqx=out:csv&sheet=ردود%20النموذج%201"

st.title("👨‍🏫 إدارة بيانات الطلاب - الأستاذ زياد")

# عرض الجدول الحالي
try:
    df = pd.read_csv(CSV_URL)
    st.subheader("📋 قائمة الطلاب المسجلين")
    # عرض البيانات مع إخفاء عمود الطابع الزمني
    st.dataframe(df.iloc[:, 1:], use_container_width=True) 
except:
    st.info("لا توجد بيانات مسجلة بعد.")

st.divider()

# 2. واجهة الإضافة (استخدام الرابط المختصر الجديد)
st.subheader("➕ إضافة طالب جديد")
with st.form("entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        fid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
        fname = st.text_input("اسم الطالب الكامل")
    with col2:
        fclass = st.text_input("الصف")
    
    submit = st.form_submit_button("🚀 تجهيز بيانات الحفظ")

    if submit:
        if fname:
            # الرابط الأساسي الذي أرسلته أنت
            base_url = "https://docs.google.com/forms/d/e/1FAIpQLSdyE_7B-6WvG99pA/viewform"
            
            # بناء رابط التعبئة التلقائية باستخدام أرقام entry من صورتك السابقة
            final_link = f"{base_url}?entry.1776082434={fid}&entry.64593526={fname}&entry.1340307757={fclass}"
            
            st.success(f"✅ تم تجهيز بيانات الطالب: {fname}")
            
            # الزر الكبير للحفظ النهائي
            st.markdown(f"""
                <a href="{final_link}" target="_blank">
                    <button style="
                        background-color: #ff4b4b;
                        color: white;
                        padding: 18px;
                        border: none;
                        border-radius: 12px;
                        width: 100%;
                        font-weight: bold;
                        font-size: 18px;
                        cursor: pointer;">
                        اضغط هنا لإتمام الحفظ في جوجل شيت (خطوة أخيرة)
                    </button>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.warning("يرجى إدخال اسم الطالب.")
