import streamlit as st

# السطرين القادمين هما أهم شيء لحل مشكلة AttributeError
if 'role' not in st.session_state:
    st.session_state.role = None

st.title("منصة الأستاذ زياد - نسخة فحص الأخطاء")

# فحص الحالة
if st.session_state.role is None:
    st.write("تعريف الجلسة تم بنجاح ✅")
    if st.button("دخول تجريبي كمعلم"):
        st.session_state.role = "teacher"
        st.rerun()
else:
    st.write(f"أنت مسجل الآن بصفة: {st.session_state.role}")
    if st.button("تسجيل خروج"):
        st.session_state.role = None
        st.rerun()
