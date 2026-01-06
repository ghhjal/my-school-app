import streamlit as st
import pandas as pd

# إعداد الصفحة - يجب أن يكون أول أمر
st.set_page_config(page_title="منصة المدرسة الذكية", layout="wide")

# دالة لجلب البيانات بشكل آمن
def load_school_data():
    try:
        # هنا تضع كود قراءة ملفك (Excel أو CSV)
        df = pd.read_excel("students_data.xlsx")
        return df
    except Exception as e:
        st.error(f"فشل في تحميل بيانات الطلاب: {e}")
        return None

def main():
    st.title("🏫 نظام إدارة المدرسة الاحترافي")
    
    data = load_school_data()
    
    if data is not None:
        # البحث بالاسم بدلاً من رقم العمود لضمان الاستقرار
        search_term = st.text_input("ابحث عن طالب بالاسم:")
        
        if search_term:
            # فلترة احترافية باستخدام اسم العمود
            results = data[data['اسم_الطالب'].str.contains(search_term, na=False)]
            st.dataframe(results, use_container_width=True)
        else:
            st.info("يرجى إدخال اسم الطالب للبحث.")

if __name__ == "__main__":
    main()
