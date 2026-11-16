import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="بوابة إدارة ومتابعة الطلاب | منصة زياد الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.markdown("""
<style>
@import url('https://googleapis.com');

header,
header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer,
[data-testid="stFooter"],
[data-testid="stBottom"],
[data-testid="manage-app-button"],
[class*="viewerBadge"],
a[href*="streamlit.io"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Cairo', sans-serif !important;
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    direction: rtl !important;
    text-align: center !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1.5rem !important;
    max-width: 650px !important;
}

.portal-shell {
    background: #FFFFFF;
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 20px 45px -15px rgba(15, 23, 42, 0.14);
    border: 1.5px solid #E2E8F0;
}

.portal-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E40AF 50%, #2563EB 100%);
    padding: 28px 20px 24px 20px;
    color: #FFFFFF;
    position: relative;
}

.cap-badge {
    width: 64px;
    height: 64px;
    margin: 0 auto 12px auto;
    background: rgba(255, 255, 255, 0.15);
    border: 2px solid rgba(255, 255, 255, 0.35);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.banner-title {
    font-size: 24px;
    font-weight: 900;
    margin: 0 0 6px 0;
    color: #FFFFFF !important;
}

.banner-pill {
    display: inline-block;
    background: rgba(15, 23, 42, 0.38);
    border: 1px solid rgba(255, 255, 255, 0.28);
    color: #FDE68A !important;
    padding: 4px 16px;
    border-radius: 999px;
    font-size: 13.5px;
    font-weight: 800;
}

.portal-body {
    padding: 28px 24px 24px 24px;
}

.status-tag {
    display: inline-block;
    background: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 14px;
}

.body-heading {
    font-size: 21px;
    font-weight: 900;
    color: #0F172A;
    margin: 0 0 10px 0;
}

.body-desc {
    font-size: 15px;
    font-weight: 600;
    color: #475569;
    line-height: 1.75;
    margin: 0 0 22px 0;
}

.launch-btn {
    display: block;
    width: 100%;
    background: linear-gradient(135deg, #0F172A 0%, #1E40AF 50%, #2563EB 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    padding: 15px 20px;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 800;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.32);
    transition: all 0.2s ease;
    box-sizing: border-box;
}

.launch-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.42);
}

.url-box {
    margin-top: 18px;
    background: #F1F5F9;
    border: 1.5px dashed #CBD5E1;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13.5px;
    font-weight: 700;
    color: #334155;
}

.url-link {
    display: block;
    margin-top: 4px;
    color: #2563EB !important;
    font-weight: 800;
    direction: ltr;
    text-decoration: none !important;
}

.portal-footer {
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 14px 20px;
    font-size: 12.5px;
    font-weight: 700;
    color: #64748B;
}
</style>

<div class="portal-shell">
    <div class="portal-banner">
        <div class="cap-badge">🎓</div>
        <h1 class="banner-title">بوابة إدارة ومتابعة الطلاب</h1>
        <span class="banner-pill">منصة زياد الذكية • إشراف أ. زياد المعمري</span>
    </div>
    <div class="portal-body">
        <div class="status-tag">⚡ تحديث مهم للطلاب وأولياء الأمور</div>
        <h2 class="body-heading">تمت ترقية المنصة ونقلها إلى رابطها الرسمي الجديد</h2>
        <p class="body-desc">
            حرصاً على سرعة التصفح واستقرار الخدمة دون توقف، تم نقل البوابة بالكامل.<br>
            سيتم نقلك تلقائياً خلال ثوانٍ، أو يمكنك الدخول مباشرة عبر الزر أدناه:
        </p>
        <a href="https://zi-edu.onrender.com/" target="_top" class="launch-btn">
            🚀 الدخول إلى بوابة الطلاب الجديدة الآن
        </a>
        <div class="url-box">
            📌 يرجى حفظ الرابط الجديد في المفضلة لديكم:
            <a href="https://zi-edu.onrender.com/" target="_top" class="url-link">https://zi-edu.onrender.com/</a>
        </div>
    </div>
    <div class="portal-footer">
        الدرجات • الاختبارات • الملاحظات • التواصل مع ولي الأمر
    </div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
setTimeout(function() {
    try {
        window.top.location.href = "https://zi-edu.onrender.com/";
    } catch (e) {
        window.location.href = "https://zi-edu.onrender.com/";
    }
}, 4000);
</script>
""", height=0)
