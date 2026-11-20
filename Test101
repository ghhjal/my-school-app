import streamlit as st
import streamlit.components.v1 as components

NEW_URL = "https://zi-edu.onrender.com"

st.set_page_config(
    page_title="منصة زياد الذكية — الانتقال للإصدار الجديد",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <meta http-equiv="refresh" content="3;url={NEW_URL}">
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800;900&display=swap');
      #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] {{
        visibility: hidden !important;
        display: none !important;
      }}
      html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, #EEF4FB 0%, #F7FAFE 55%, #EFF5FC 100%) !important;
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: center;
      }}
      .redirect-card {{
        max-width: 520px;
        margin: 48px auto 0;
        background: #FFFFFF;
        border: 1.5px solid #D5E2F0;
        border-radius: 24px;
        padding: 34px 26px;
        box-shadow: 0 18px 40px -14px rgba(15, 23, 42, 0.14);
        text-align: center;
        font-family: 'Cairo', sans-serif;
      }}
      .badge-top {{
        display: inline-block;
        background: linear-gradient(135deg, #0B1F3A 0%, #0F3D75 55%, #0284C7 100%);
        color: #FEF08A;
        padding: 6px 20px;
        border-radius: 999px;
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 16px;
      }}
      .r-title {{
        margin: 0 0 10px;
        font-size: 24px;
        font-weight: 900;
        color: #0F172A;
        line-height: 1.4;
      }}
      .r-desc {{
        margin: 0 0 22px;
        font-size: 15px;
        font-weight: 600;
        color: #475569;
        line-height: 1.7;
      }}
      .go-btn {{
        display: inline-block;
        width: 100%;
        padding: 14px 22px;
        border-radius: 999px;
        background: linear-gradient(135deg, #0F3D75 0%, #0284C7 100%);
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-size: 17px;
        font-weight: 900;
        box-shadow: 0 10px 24px -6px rgba(2, 132, 199, 0.50);
        transition: transform 0.15s ease;
      }}
      .go-btn:hover {{
        transform: translateY(-2px);
      }}
      .url-note {{
        margin-top: 16px;
        font-size: 13px;
        font-weight: 700;
        color: #64748B;
        direction: ltr;
      }}
      .teacher-sig {{
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid #E2E8F0;
        font-size: 13px;
        font-weight: 800;
        color: #334155;
      }}
    </style>
    <div class="redirect-card">
      <div class="badge-top">🎓 منصة زياد الذكية</div>
      <h1 class="r-title">تمت ترقية المنصة إلى الإصدار الجديد</h1>
      <p class="r-desc">
        سيتم تحويلك تلقائياً خلال ثوانٍ إلى البوابة الجديدة الأسرع مع دعم إشعارات الجوال.<br>
        إذا لم يتم التحويل تلقائياً، اضغط الزر أدناه:
      </p>
      <a class="go-btn" href="{NEW_URL}" target="_top">الانتقال إلى المنصة الجديدة الآن</a>
      <div class="url-note">{NEW_URL}</div>
      <div class="teacher-sig">إشراف المعلم: أ. زياد المعمري</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Attempt top-level automatic redirect after 2.5 seconds (works outside sandboxed iframe when allowed)
components.html(
    f"""
    <script>
      setTimeout(function() {{
        try {{
          window.top.location.replace("{NEW_URL}");
        }} catch (e) {{
          window.location.replace("{NEW_URL}");
        }}
      }}, 2500);
    </script>
    """,
    height=0,
)
