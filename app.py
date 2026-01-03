import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame()

st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 45px 20px;
        border-radius: 0 0 40px 40px;
        color: white;
        text-align: center;
        margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; 
        justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .welcome-card {
        background: rgba(30, 64, 175, 0.05);
        border-right: 5px solid #1e40af;
        padding: 20px;
        border-radius: 12px;
        margin: 25px 0;
        text-align: justify;
        line-height: 1.8;
    }
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 25px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        padding: 30px !important;
    }
    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    
    .contact-section {
        margin-top: 30px;
        text-align: center;
        padding: 20px;
    }
    .contact-icons {
        display: flex;
        justify-content: center;
        gap: 25px;
        margin-top: 15px;
    }
    .contact-icons a {
        text-decoration: none;
        color: #1e40af;
        font-size: 28px;
        transition: 0.3s;
    }
    .contact-icons a:hover {
        color: #3b82f6;
        transform: scale(1.15);
    }
    .footer-text {
        text-align: center;
        opacity: 0.8;
        font-size: 13px;
        margin-top: 30px;
        padding: 15px;
        border-top: 1px solid rgba(128, 128, 128, 0.1);
    }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام متابعة الطلاب والتواصل مع أولياء الأمور</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #1e40af; margin-top: 0; font-weight: 700;">أهلًا بكم في منصة زياد الذكية</h4>
            <p style="color: inherit; font-size: 15px; margin-bottom: 0;">
                مبادرة تعليمية تهدف إلى تسهيل متابعة مستوى الطلاب أكاديمياً وسلوكياً، وتعزيز التواصل السريع والفعّال مع أولياء الأمور.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_form"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية للمتابعة")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df = fetch_safe("students")
                if not df.empty and sid:
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    if sid.strip() in df.iloc[:, 0].values:
                        st.session_state.role = "student"; st.session_state.sid = sid.strip()
                        st.balloons(); time.sleep(1); st.rerun()
                    else: st.error("عذراً، الرقم غير مسجل في النظام")
    with tab2:
        with st.form("te_form"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u.strip()]
                    if not row.empty:
                        hashed = hashlib.sha256(str.encode(p)).hexdigest()
                        if hashed == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"; st.rerun()
                        else: st.error("كلمة المرور غير صحيحة")
                    else: st.error("المستخدم غير موجود")

    # قنوات التواصل الأربعة (مكتملة الآن)
    st.markdown("""
        <div class="contact-section">
            <p style="font-weight: 700; color: #1e40af; margin-bottom: 10px;">قنوات التواصل المباشرة</p>
            <div class="contact-icons">
                <a href="mailto:info@example.com" title="البريد الإلكتروني"><i class="bi bi-envelope-at-fill"></i></a>
                <a href="https://wa.me/966XXXXXXXXX" target="_blank" title="واتساب"><i class="bi bi-whatsapp"></i></a>
                <a href="https://t.me/YourUser" target="_blank" title="تليجرام"><i class="bi bi-telegram"></i></a>
                <a href="https://www.snapchat.com/add/YourUser" target="_blank" title="سناب شات"><i class="bi bi-snapchat"></i></a>
            </div>
        </div>
        <div class="footer-text">© منصة زياد الذكية – مبادرة تعليمية بإشراف الأستاذ زياد</div>
    """, unsafe_allow_html=True)
    st.stop()

if st.session_state.role:
    st.success("تم تسجيل الدخول بنجاح!")
    if st.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
# ==========================================
# 🛠️ واجهة المعلم (بعد الدمج الاحترافي)
# ==========================================
if st.session_state.role == "teacher":
    # 1. التنسيق الجمالي للقائمة الجانبية
    st.sidebar.markdown(f"""
        <div style="text-align:center; padding:10px;">
            <i class="bi bi-person-badge" style="font-size:50px; color:#1e40af;"></i>
            <h3 style="margin-top:10px;">الأستاذ زياد</h3>
            <p style="font-size:12px; opacity:0.7;">مدير المنصة</p>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.sidebar.selectbox("🏠 القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    
    st.sidebar.divider()
    if st.sidebar.button("🚗 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None
        st.rerun()

    # --- القسم الأول: إدارة الطلاب (كودك الأصلي مع لمسات جمالية) ---
    if menu == "👥 إدارة الطلاب":
        st.markdown("""
            <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); padding:25px; border-radius:20px; color:white; text-align:center; margin-bottom:25px;">
                <h1 style="margin:0; font-size:24px;">👥 إدارة سجلات الطلاب</h1>
                <p style="margin:5px 0 0 0; opacity:0.9;">إضافة، تعديل، وحذف بيانات الطلاب من النظام</p>
            </div>
        """, unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        
        # عرض البيانات بشكل أنيق
        with st.expander("📋 عرض السجل الحالي للطلاب", expanded=True):
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
            else:
                st.info("لا يوجد طلاب مسجلين حالياً")

        # 1. نموذج إضافة طالب جديد
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس ملف طالب جديد")
            with st.form("add_student_pro_v3", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("🔢 الرقم الأكاديمي")
                nname = c2.text_input("👤 الاسم الثلاثي")
                nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                
                c4, c5, c6 = st.columns(3)
                nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nsub = c5.text_input("📚 المادة", value="لغة إنجليزية")
                nyear = c6.text_input("🗓️ العام الدراسي", value="1447هـ")
                
                c7, c8 = st.columns(2)
                nmail = c7.text_input("📧 البريد الإلكتروني")
                nphone = c8.text_input("📱 جوال ولي الأمر")
                
                submit = st.form_submit_button("✅ اعتماد وإضافة الطالب")
                if submit:
                    if nid and nname:
                        row_to_add = [nid, nname, nclass, nyear, nstage, nsub, nmail, nphone, "0"]
                        try:
                            sh.worksheet("students").append_row(row_to_add)
                            st.success(f"✅ تم إضافة الطالب {nname} بنجاح")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ في الاتصال: {e}")
                    else:
                        st.warning("يرجى ملء البيانات الأساسية (الرقم والاسم)")

        # 2. زر الحذف النهائي (الميزة الاحترافية التي أضفتها أنت)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🗑️ منطقة الحذف النهائي والمخاطر", expanded=False):
            st.markdown("""
                <div style="background-color:#fee2e2; padding:15px; border-radius:10px; border-right:5px solid #ef4444; color:#991b1b;">
                    <strong>⚠️ تنبيه أمني:</strong> سيتم حذف الطالب نهائياً من كافة السجلات (الطلاب، الدرجات، السلوك). هذا الإجراء لا يمكن التراجع عنه.
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            del_name = st.selectbox("🎯 اختر الطالب المراد حذفه نهائياً:", [""] + df_st.iloc[:, 1].tolist() if not df_st.empty else [""])
            
            if st.button("🚨 تنفيذ الحذف الشامل الآن", use_container_width=True):
                if del_name and del_name != "":
                    try:
                        with st.spinner(f'جاري تنظيف كافة السجلات المرتبطة بـ {del_name}...'):
                            # أ. الحذف من شيت الطلاب
                            ws_st = sh.worksheet("students")
                            c_st = ws_st.find(del_name)
                            if c_st: ws_st.delete_rows(c_st.row)
                            
                            # ب. الحذف من شيت الدرجات
                            try:
                                ws_gr = sh.worksheet("grades")
                                c_gr = ws_gr.find(del_name)
                                if c_gr: ws_gr.delete_rows(c_gr.row)
                            except: pass
                            
                            # ج. الحذف من شيت السلوك
                            try:
                                ws_bh = sh.worksheet("behavior")
                                matches = ws_bh.findall(del_name)
                                for m in reversed(matches):
                                    if m.col == 1: ws_bh.delete_rows(m.row)
                            except: pass
                            
                            st.success(f"💥 تم مسح سجلات {del_name} بنجاح من جميع الجداول")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الحذف: {e}")
                else:
                    st.warning("يرجى اختيار اسم الطالب أولاً")        
