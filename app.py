import streamlit as st

st.set_page_config(
    page_title="انتقال المنصة | منصة زياد الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://googleapis.com');

header, footer, [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu {
    display: none !important;
}

html, body, .stApp {
    font-family: 'Cairo', sans-serif !important;
    background-color: #F8FAFC !important;
    direction: rtl !important;
    text-align: center !important;
}

.redirect-card {
    background: #FFFFFF;
    border-radius: 22px;
    padding: 35px 25px;
    margin-top: 40px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    border: 1.5px solid #E2E8F0;
}

.badge-pill {
    background: #DBEAFE;
    color: #1E40AF;
    padding: 6px 18px;
    border-radius: 99px;
    font-weight: 800;
    font-size: 14px;
    display: inline-block;
    margin-bottom: 15px;
}

.main-heading {
    color: #0F172A;
    font-size: 26px;
    font-weight: 900;
    margin: 0 0 12px 0;
}

.sub-text {
    color: #475569;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.7;
    margin-bottom: 25px;
}

.go-btn {
    display: inline-block;
    background: linear-gradient(135deg, #0F172A 0%, #1E40AF 50%, #2563EB 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    padding: 14px 36px;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 800;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
    transition: transform 0.2s ease;
}

.go-btn:hover {
    transform: translateY(-2px);
}

.note-box {
    margin-top: 25px;
    padding-top: 15px;
    border-top: 1px dashed #CBD5E1;
    color: #64748B;
    font-size: 13.5px;
    font-weight: 700;
}
</style>

<div class="redirect-card">
    <div class="badge-pill">🎓 منصة زياد الذكية • إشراف أ. زياد المعمري</div>
    <h1 class="main-heading">🚀 تم نقل البوابة إلى خادم أسرع وأقوى!</h1>
    <p class="sub-text">
        أعزائي الطلاب وأولياء الأمور، حرصاً على تقديم تجربة أسرع وأكثر استقراراً دون توقف،<br>
        تم نقل <b>بوابة إدارة ومتابعة الطلاب</b> إلى رابطها الرسمي الجديد.
    </p>
    <a href="https://onrender.com" target="_self" class="go-btn">
        ✨ اضغط هنا للدخول إلى المنصة الجديدة
    </a>
    <div class="note-box">
        💡 نصيحة: يرجى حفظ الرابط الجديد في المفضلة لديكم:<br>
        <span style="color:#2563EB; direction:ltr; display:inline-block; margin-top:4px;">https://onrender.com</span>
    </div>
</div>
""", unsafe_allow_html=True)
