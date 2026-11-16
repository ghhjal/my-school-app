
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
NEW_URL = "https://zi-edu.onrender.com/"
REDIRECT_SECONDS = 3

st.set_page_config(
    page_title="بوابة الطلاب | منصة زياد الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None
    }
)

# ==========================================
# 2. التصميم الاحترافي
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

:root {
    --primary: #1D4ED8;
    --dark: #0F172A;
    --muted: #64748B;
    --bg: #F1F5F9;
}

header, footer, #MainMenu,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stBottom"],
[data-testid="manage-app-button"] {
    display: none !important;
}

html, body, .stApp,
[data-testid="stAppViewContainer"] {
    direction: rtl !important;
    text-align: center !important;
    font-family: 'Cairo', sans-serif !important;
    background: var(--bg) !important;
    color: var(--dark) !important;
}

.block-container {
    max-width: 570px !important;
    padding: 3rem 1rem 2rem !important;
}

.portal-shell {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 26px;
    overflow: hidden;
    box-shadow: 0 18px 55px rgba(15,23,42,.09);
}

/* Header */
.portal-header {
    background: linear-gradient(135deg,#0F172A 0%,#1E40AF 60%,#2563EB 100%);
    padding: 35px 20px 30px;
    position: relative;
    overflow: hidden;
}

.portal-header:before {
    content: "";
    position: absolute;
    width: 190px;
    height: 190px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 50%;
    top: -100px;
    right: -65px;
}

.portal-header:after {
    content: "";
    position: absolute;
    width: 150px;
    height: 150px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 50%;
    bottom: -100px;
    left: -45px;
}

.logo-box {
    width: 70px;
    height: 70px;
    background: rgba(255,255,255,.14);
    border: 1px solid rgba(255,255,255,.30);
    border-radius: 21px;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 auto 15px;
    font-size: 36px;
    position: relative;
    z-index: 1;
}

.portal-title {
    color: #FFFFFF !important;
    font-size: 25px !important;
    font-weight: 900 !important;
    margin: 0 0 8px !important;
    position: relative;
    z-index: 1;
}

.portal-subtitle {
    color: #DBEAFE !important;
    font-size: 13px;
    font-weight: 700;
    margin: 0;
    position: relative;
    z-index: 1;
}

.brand-label {
    display: inline-block;
    background: rgba(255,255,255,.13);
    border: 1px solid rgba(255,255,255,.22);
    border-radius: 30px;
    padding: 5px 15px;
    margin-top: 14px;
    color: #FDE68A;
    font-size: 12px;
    font-weight: 800;
}

/* Body */
.portal-body {
    padding: 30px 25px 27px;
}

.status {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
    border-radius: 30px;
    padding: 6px 15px;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 19px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #10B981;
    border-radius: 50%;
}

.body-title {
    font-size: 21px;
    font-weight: 900;
    color: #0F172A;
    line-height: 1.7;
    margin: 0 0 10px;
}

.body-description {
    color: #64748B;
    font-size: 14px;
    font-weight: 600;
    line-height: 2;
    margin: 0 0 23px;
}

/* Redirect */
.redirect-panel {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 16px;
    padding: 17px 12px;
    margin-bottom: 20px;
}

.redirect-text {
    color: #1E40AF;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 7px;
}

.countdown {
    color: #1D4ED8;
    font-size: 34px;
    font-weight: 900;
    direction: ltr;
    line-height: 1.3;
}

.countdown-caption {
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    margin-top: 4px;
}

/* Button */
.launch-btn {
    display: block;
    width: 100%;
    box-sizing: border-box;
    background: linear-gradient(135deg,#1E40AF,#2563EB);
    color: #FFFFFF !important;
    text-decoration: none !important;
    padding: 16px 15px;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 900;
    box-shadow: 0 7px 18px rgba(37,99,235,.23);
    transition: .2s ease;
}

.launch-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(37,99,235,.30);
}

.link-section {
    margin-top: 19px;
    background: #F8FAFC;
    border: 1px dashed #CBD5E1;
    border-radius: 13px;
    padding: 13px;
}

.link-label {
    font-size: 12px;
    color: #64748B;
    font-weight: 700;
    margin-bottom: 7px;
}

.new-url {
    color: #1D4ED8;
    font-size: 12px;
    font-weight: 800;
    direction: ltr;
    word-break: break-all;
    text-decoration: none;
}

/* Footer */
.portal-footer {
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 17px 12px;
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    line-height: 2;
}

.footer-services {
    color: #475569;
    margin-bottom: 5px;
}

/* Mobile */
@media (max-width: 480px) {
    .block-container {
        padding: 1.3rem .7rem 1rem !important;
    }

    .portal-header {
        padding: 28px 15px 25px;
    }

    .portal-title {
        font-size: 21px !important;
    }

    .portal-body {
        padding: 24px 17px;
    }

    .body-title {
        font-size: 19px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        transition: none !important;
        animation: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. واجهة البوابة
# ==========================================
st.markdown(f"""
<div class="portal-shell">

    <div class="portal-header">
        <div class="logo-box">🎓</div>

        <h1 class="portal-title">
            بوابة إدارة ومتابعة الطلاب
        </h1>

        <p class="portal-subtitle">
            منصة زياد الذكية
        </p>

        <div class="brand-label">
            إشراف أ. زياد المعمري
        </div>
    </div>

    <div class="portal-body">

        <div class="status">
            <span class="status-dot"></span>
            المنصة الجديدة أصبحت جاهزة
        </div>

        <h2 class="body-title">
            نرحب بكم في بوابتنا الجديدة
        </h2>

        <p class="body-description">
            تم تطوير المنصة ونقلها إلى استضافة جديدة
            لتوفير تجربة استخدام أسرع وأكثر استقراراً.
            <br>
            يرجى استخدام الرابط الجديد للدخول ومتابعة
            الدرجات والاختبارات والملاحظات.
        </p>

        <div class="redirect-panel">
            <div class="redirect-text">
                🚀 سيتم تحويلك تلقائياً إلى المنصة الجديدة
            </div>

            <div class="countdown" id="countdown">
                03
            </div>

            <div class="countdown-caption">
                ثانية حتى الانتقال
            </div>
        </div>

        <a href="{NEW_URL}" target="_top" class="launch-btn">
            الدخول إلى بوابة الطلاب الجديدة ←
        </a>

        <div class="link-section">
            <div class="link-label">
                📌 رابط المنصة الجديد - يرجى حفظه
            </div>

            <a href="{NEW_URL}" target="_top" class="new-url">
                {NEW_URL}
            </a>
        </div>

    </div>

    <div class="portal-footer">
        <div class="footer-services">
            الدرجات • الاختبارات • الملاحظات • التواصل مع ولي الأمر
        </div>
        جميع الحقوق محفوظة © منصة زياد الذكية
    </div>

</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. التحويل التلقائي والعد التنازلي
# ==========================================
components.html(f"""
<script>
(function() {{
    const target = "{NEW_URL}";
    let remaining = {REDIRECT_SECONDS};

    const timer = setInterval(function() {{
        remaining--;

        try {{
            const frame = window.frameElement;
            if (frame && frame.parentElement) {{
                const doc = window.parent.document;
                const counter = doc.getElementById("countdown");
                if (counter) {{
                    counter.textContent = String(
                        Math.max(remaining, 0)
                    ).padStart(2, "0");
                }}
            }}
        }} catch(e) {{}}

        if (remaining <= 0) {{
            clearInterval(timer);

            try {{
                window.top.location.replace(target);
            }} catch(e) {{
                window.location.replace(target);
            }}
        }}
    }}, 1000);
}})();
</script>
""", height=0)
