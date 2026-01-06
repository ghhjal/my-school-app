import streamlit as st

# التأكد من أن هذا هو أول سطر برمجي
st.set_page_config(page_title="نظام المدرسة - تجربة الاستقرار", layout="wide")

def main():
    st.success("✅ الخادم يعمل والمكتبات مستقرة!")
    st.title("لوحة تحكم النظام المدرسي")
    
    # عرض معلومات البيئة للتأكد
    st.info(f"إصدار ستريمليت الحالي: {st.__version__}")
    
    if st.button("اضغط لاختبار التفاعل"):
        st.balloons()
        st.write("التفاعل يعمل بنجاح!")

if __name__ == "__main__":
    main()
