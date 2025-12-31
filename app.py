import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. الإعدادات الأساسية وتنسيق الجوال ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; height: 60px; border-radius: 15px; font-size: 18px !important; font-weight: bold; margin-top: 10px; }
    .stTextInput>div>div>input { height: 55px; border-radius: 12px; text-align: center; font-size: 20px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. دالة الاتصال بقاعدة البيانات (تم تحسين الـ ttl للاستقرار) ---
@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # سيقوم الكود تلقائياً بجلب البيانات من Secrets التي وضعتها
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db()

# دالة جلب البيانات الآمنة
def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            return pd.DataFrame(data[1:], columns=headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# دالة إرسال الإيميل (تستخدم البيانات التي أرسلتها في Secrets)
def send_email_notification(to_email, subject, body):
    try:
        email_set = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = email_set["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_set["sender_email"], email_set["sender_password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"خطأ في إرسال الإيميل: {e}")
        return False
# أضف هذا المتغير في بداية قسم "إدارة الجلسة" (Session State)
if 'email_count' not in st.session_state:
    st.session_state.email_count = 0

# --- تعديل دالة إرسال الإيميل لتزيد العداد ---
def send_email_notification(to_email, subject, body):
    try:
        email_set = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = email_set["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_set["sender_email"], email_set["sender_password"])
        server.send_message(msg)
        server.quit()
        
        # زيادة العداد عند نجاح الإرسال
        st.session_state.email_count += 1
        return True
    except Exception as e:
        st.error(f"خطأ في إرسال الإيميل: {e}")
        return False

# --- إضافة العداد في شريط جانبي أو أسفل شاشة السلوك ---
if menu == "🎭 رصد السلوك":
    # (كود الرصد السابق هنا...)
    
    # العداد الذكي في القائمة الجانبية أو أسفل الصفحة
    with st.sidebar:
        st.divider()
        st.markdown("### 📊 مراقب الإرسال اليومي")
        count = st.session_state.email_count
        limit = 500
        
        # تغيير اللون حسب العدد
        color = "green" if count < 300 else "orange" if count < 450 else "red"
        
        st.markdown(f"""
            <div style="padding:10px; border-radius:10px; background-color:#f0f2f6; border-right: 5px solid {color};">
                <small>الإيميلات المرسلة الآن:</small><br>
                <b style="font-size:1.2rem; color:{color};">{count} / {limit}</b>
            </div>
        """, unsafe_allow_html=True)
        
        if count >= 450:
            st.warning("⚠️ اقتربت من الحد اليومي لـ Gmail (500 إيميل).")
# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown('<div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 35px; border-radius: 20px; text-align: center; color: white; margin-bottom: 25px;"><h1>🌟 منصة الأستاذ زياد العمري</h1><p>تميز، إبداع، لغة إنجليزية</p></div>', unsafe_allow_html=True)
    
    t_st, t_tea = st.tabs(["🎓 دخول الطالب", "👨‍🏫 منطقة المعلم"])
    
    with t_st:
        sid_in = st.text_input("أدخل الرقم الأكاديمي", key="st_login")
        if st.button("🚀 دخول الطالب", type="primary"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("عذراً، الرقم غير مسجل")

    with t_tea:
        t_pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("🔓 دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
            else: st.error("كلمة المرور خاطئة")
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))

    if menu == "🎭 رصد السلوك":
        st.markdown('<div style="background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;"><h1>🎭 رصد السلوك والتواصل الفوري</h1></div>', unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        search = st.text_input("🔍 ابحث عن اسم الطالب")
        filtered = [n for n in df_st.iloc[:,1].tolist() if search in n]
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + filtered)

        if b_name:
            s_info = df_st[df_st.iloc[:,1] == b_name].iloc[0]
            s_email = s_info[6]
            s_phone = str(s_info[7]).split('.')[0]

            with st.form("beh_form_v2", clear_on_submit=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 الملاحظة")
                
                col1, col2, col3 = st.columns(3)
                btn_save = col1.form_submit_button("💾 حفظ فقط")
                btn_mail = col2.form_submit_button("📧 إرسال إيميل")
                btn_wa = col3.form_submit_button("💬 إرسال واتساب")

                if btn_save or btn_mail or btn_wa:
                    if b_note:
                        # تحديث جوجل شيت
                        sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                        # تحديث النقاط تلقائياً
                        try:
                            ws_st = sh.worksheet("students"); cell = ws_st.find(b_name)
                            p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                            curr_p = int(ws_st.cell(cell.row, 9).value or 0)
                            ws_st.update_cell(cell.row, 9, str(curr_p + p_map.get(b_type, 0)))
                        except: pass

                        # تنسيق الرسالة المطلوب
                        wa_msg = (
                            f"📢 *تنبيه من منصة الأستاذ زياد الذكية*\n"
                            f"----------------------------------\n"
                            f"🏫 *الطالب:* {b_name}\n"
                            f"🏷️ *السلوك:* {b_type}\n"
                            f"📝 *الملاحظة:* {b_note}\n"
                            f"📅 *التاريخ:* {b_date}\n"
                            f"----------------------------------\n"
                            f"يرجى العلم والمتابعة. مع تمنياتي لكم بالتوفيق 🌟"
                        )

                        if btn_mail and s_email:
                            send_email_notification(s_email, "تقرير سلوك", wa_msg)
                            st.success("📧 تم إرسال الإيميل بنجاح")
                        
                        if btn_wa and s_phone:
                            wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(wa_msg)}"
                            st.markdown(f'<a href="{wa_url}" target="_blank">✅ اضغط هنا لفتح واتساب</a>', unsafe_allow_html=True)
                        
                        st.success("✅ تم الحفظ بنجاح")
                    else: st.error("يرجى كتابة ملاحظة")

            st.divider()
            st.subheader(f"📋 سجل: {b_name}")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                st.dataframe(df_b[df_b.iloc[:,0] == b_name].iloc[::-1], use_container_width=True, hide_index=True)

    # (بقية الأقسام: إدارة الطلاب، الدرجات، الاختبارات تبقى بنفس منطق كودك الأصلي مع استدعاء sh و fetch_safe)
    elif menu == "📢 شاشة الاختبارات":
        st.header("📢 شاشة الاختبارات")
        with st.form("exam_form"):
            e_cls = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = st.text_input("الموضوع")
            e_dt = st.date_input("الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                wa_msg = (
                    f"📢 *تنبيه من منصة الأستاذ زياد الذكية*\n"
                    f"----------------------------------\n"
                    f"🏫 *الصف:* {e_cls}\n"
                    f"📝 *الموضوع:* {e_ttl}\n"
                    f"📅 *الموعد:* {e_dt}\n"
                    f"----------------------------------\n"
                    f"يرجى العلم والاستعداد. بالتوفيق 🌟"
                )
                st.markdown(f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}" target="_blank">💬 انشر عبر واتساب</a>', unsafe_allow_html=True)
                st.rerun()

# --- واجهة الطالب (نفس التصميم الجذاب بالأوسمة) ---
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    s_points = int(s_row[8]) if s_row[8] else 0
    
    st.markdown(f'<div style="background:#1e3a8a; padding:15px; color:white; text-align:center; border-radius:15px;"><h3>🎯 الطالب: {s_row[1]} | النقاط: {s_points}</h3></div>', unsafe_allow_html=True)
    
    # عرض الأوسمة
    c1, c2, c3 = st.columns(3)
    c1.metric("🥉 برونزي", "10 نقاط", delta="مفعل" if s_points >= 10 else "قيد الإنجاز")
    c2.metric("🥈 فضي", "50 نقطة", delta="مفعل" if s_points >= 50 else "قيد الإنجاز")
    c3.metric("🥇 ذهبي", "100 نقطة", delta="مفعل" if s_points >= 100 else "قيد الإنجاز")
    
    st.divider()
    if st.button("🚗 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
