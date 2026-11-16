
import streamlit as st

NEW_URL = "https://zi-edu.onrender.com/"

st.set_page_config(
    page_title="بوابة الطلاب - منصة زياد الذكية",
    page_icon="🎓",
    layout="centered"
)

# التحويل التلقائي
st.markdown(
    f'<meta http-equiv="refresh" content="3;url={NEW_URL}">',
    unsafe_allow_html=True
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');

header, footer, #MainMenu {
    display: none !important;
}

.stApp {
    background: #F1F5F9;
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}

.block-container {
    max-width: 520px;
    padding: 3rem 1rem;
}

.card {
    background: white;
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid #E2E8F0;
    box-shadow: 0 15px 40px rgba(15,23,42,.08);
    text-align: center;
}

.header {
    background: linear-gradient(135deg,#0F172A,#1D4ED8,#2563EB);
    padding: 35px 15px;
    color: white;
}

.icon {
    font-size: 43px;
    margin-bottom: 10px;
}

.header h1 {
    font-size: 23px;
    font-weight: 900;
    color: white;
    margin: 0 0 8px;
}

.header p {
    color: #DBEAFE;
    font-size: 13px;
    margin: 0;
}

.content {
    padding: 30px 22px;
}

.status {
    display: inline-block;
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
    border-radius: 30px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 800;
}

.content h2 {
    color: #0F172A;
    font-size: 21px;
    font-weight: 900;
    margin: 18px 0 10px;
}

.description {
    color: #64748B;
    font-size: 14px;
    line-height: 2;
    font-weight: 600;
    margin-bottom: 25px;
}

.enter {
    display: block;
    background: linear-gradient(135deg,#1E40AF,#2563EB);
    color: white !important;
    text-decoration: none !important;
    border-radius: 13px;
    padding: 15px;
    font-size: 16px;
    font-weight: 900;
}

.link {
    margin-top: 18px;
    background: #F8FAFC;
    border: 1px dashed #CBD5E1;
    border-radius: 12px;
    padding: 13px;
    color: #2563EB;
    font-size: 12px;
    direction: ltr;
    overflow-wrap: anywhere;
}

.footer {
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 15px;
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
}

@media(max-width:480px) {
    .block-container {padding: 1rem .5rem;}
    .content {padding: 24px 16px;}
}
</style>

<div class="card">
    <div class="header">
        <div class="icon">🎓</div>
        <h1>بوابة إدارة ومتابعة الطلاب</h1>
        <p>منصة زياد الذكية</p>
        <p style="margin-top:10px;color:#FDE68A">
            إشراف أ. زياد المعمري
        </p>
    </div>

    <div class="content">
        <span class="status">● تم تحديث المنصة بنجاح</span>

        <h2>أهلاً بكم في بوابتنا الجديدة</h2>

        <div class="description">
            تم نقل منصة الطلاب إلى رابط جديد
            لتقديم تجربة استخدام أفضل وأكثر استقراراً.
            <br>
            سيتم تحويلك تلقائياً خلال لحظات.
        </div>

        <a class="enter" href="https://zi-edu.onrender.com/">
            🚀 الدخول إلى المنصة الجديدة
        </a>

        <div class="link">
            https://zi-edu.onrender.com/
        </div>
    </div>

    <div class="footer">
        الدرجات • الاختبارات • الملاحظات • التواصل مع ولي الأمر
        <br>
        جميع الحقوق محفوظة © منصة زياد الذكية
    </div>
</div>
""", unsafe_allow_html=True)
