
import streamlit as st
import streamlit.components.v1 as components

NEW_URL = "https://zi-edu.onrender.com/"

st.set_page_config(
    page_title="بوابة الطلاب | منصة زياد الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

header, footer, #MainMenu,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stBottom"] {
    display: none !important;
}

html, body, .stApp {
    direction: rtl !important;
    text-align: center !important;
    font-family: 'Cairo', sans-serif !important;
    background: #F1F5F9 !important;
}

.block-container {
    max-width: 570px !important;
    padding: 2rem 1rem !important;
}

.portal {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 15px 45px rgba(15,23,42,.09);
}

.header {
    background: linear-gradient(135deg,#0F172A,#1E40AF,#2563EB);
    padding: 32px 18px;
    color: white;
}

.logo {
    font-size: 42px;
    margin-bottom: 10px;
}

.heading {
    color: white !important;
    font-size: 24px !important;
    font-weight: 900 !important;
    margin: 0 0 8px !important;
}

.subtitle {
    color: #DBEAFE;
    font-size: 13px;
    font-weight: 700;
}

.brand {
    display: inline-block;
    background: rgba(255,255,255,.15);
    color: #FDE68A;
    border-radius: 30px;
    padding: 5px 15px;
    font-size: 12px;
    font-weight: 800;
    margin-top: 12px;
}

.body {
    padding: 30px 22px;
}

.status {
    display: inline-block;
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
    padding: 7px 15px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 17px;
}

.body-heading {
    color: #0F172A;
    font-size: 21px;
    font-weight: 900;
    margin-bottom: 12px;
}

.description {
    color: #64748B;
    font-size: 14px;
    font-weight: 600;
    line-height: 2;
    margin-bottom: 23px;
}

.launch {
    display: block;
    background: linear-gradient(135deg,#1E40AF,#2563EB);
    color: white !important;
    text-decoration: none !important;
    padding: 16px 12px;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 900;
    box-shadow: 0 7px 18px rgba(37,99,235,.23);
}

.url-box {
    margin-top: 18px;
    background: #F8FAFC;
    border: 1px dashed #CBD5E1;
    border-radius: 12px;
    padding: 13px;
}

.url-label {
    color: #64748B;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 7px;
}

.url {
    color: #2563EB !important;
    direction: ltr;
    font-size: 12px;
    font-weight: 800;
    overflow-wrap: anywhere;
    text-decoration: none;
}

.footer {
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    color: #64748B;
    padding: 16px 10px;
    font-size: 11px;
    font-weight: 700;
    line-height: 2;
}

@media(max-width:480px) {
    .block-container {
        padding: 1rem .6rem !important;
    }
    .header {
        padding: 27px 12px;
    }
    .heading {
        font-size: 21px !important;
    }
    .body {
        padding: 24px 16px;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="portal">

    <div class="header">
        <div class="logo">🎓</div>
        <h1 class="heading">بوابة إدارة ومتابعة الطلاب</h1>
        <div class="subtitle">منصة زياد الذكية</div>
        <div class="brand">إشراف أ. زياد المعمري</div>
    </div>

    <div class="body">

        <div class="status">● المنصة الجديدة أصبحت جاهزة</div>

        <div class="body-heading">
            نرحب بكم في بوابتنا الجديدة
        </div>

        <div class="description">
            تم نقل المنصة إلى استضافة جديدة لتوفير
            تجربة استخدام أسرع وأكثر استقراراً.
            <br>
            يمكنكم الآن الدخول مباشرة عبر الرابط الجديد.
        </div>

        <a class="launch" href="{NEW_URL}" target="_top">
            🚀 الدخول إلى بوابة الطلاب الجديدة
        </a>

        <div class="url-box">
            <div class="url-label">
                📌 يرجى حفظ الرابط الجديد
            </div>
            <a class="url" href="{NEW_URL}" target="_top">
                {NEW_URL}
            </a>
        </div>

    </div>

    <div class="footer">
        الدرجات • الاختبارات • الملاحظات • التواصل مع ولي الأمر
        <br>
        جميع الحقوق محفوظة © منصة زياد الذكية
    </div>

</div>
""", unsafe_allow_html=True)

# التحويل التلقائي
components.html(
    f"""
    <script>
        setTimeout(function() {{
            window.top.location.replace("{NEW_URL}");
        }}, 3000);
    </script>
    """,
    height=0,
)
