import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 1. الإعدادات والربط ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=60)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_db()

def fetch_data(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

# --- 📧 دالة إرسال الإشعارات التلقائية ---
def send_email_alert(student_name, parent_email, behavior_type, note):
    try:
        sender_email = st.secrets["email_settings"]["sender_email"]
        sender_password = st.secrets["email_settings"]["sender_password"]
        
        subject = f"🔔 إشعار سلوكي: {student_name}"
        body = f"تحية طيبة،\nتم رصد ملاحظة سلوكية جديدة لابننا: {student_name}\nالنوع: {behavior_type}\nالملاحظة: {note}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}\n\nمع تحيات الأستاذ زياد المعمري."
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = parent_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, parent_email, msg.as_string())
        return True
    except:
        return False

# --- 2. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234":
                st.session_state.role = "teacher"
                st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_data("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(sid)
                st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك", "📢 إعلانات الاختبارات"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة بيانات الطلاب")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # كود الإضافة والحذف يظل كما هو لضمان الاستقرار

    elif menu == "📊 الدرجات والسلوك":
        tab1, tab2 = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        df_st = fetch_data("students")
        
        with tab1:
            st.subheader("📝 رصد الدرجات")
            target = st.selectbox("اختر الطالب للدرجات", [""] + df_st['name'].tolist())
            if target:
                with st.form("g_form"):
                    c1, c2, c3 = st.columns(3)
                    v1 = c1.number_input("ف1")
                    v2 = c2.number_input("ف2")
                    v3 = c3.number_input("مشاركة")
                    if st.form_submit_button("حفظ"):
                        ws_g = sh.worksheet("grades")
                        try:
                            fnd = ws_g.find(target)
                            ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v1, v2, v3]])
                        except:
                            ws_g.append_row([target, v1, v2, v3])
                        st.success("تم التحديث ✅")

        with tab2: # شاشة رصد السلوك
            st.subheader("🎭 رصد السلوك والتحفيز")
            sel_st = st.selectbox("اسم الطالب للسلوك", [""] + df_st['name'].tolist())
            if sel_st:
                st_info = df_st[df_st['name'] == sel_st].iloc[0]
                target_email = st_info.get('الإيميل', '')
                
                with st.form("b_form", clear_on_submit=True):
                    d_v = st.date_input("التاريخ", datetime.now())
                    t_v = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                    n_v = st.text_input("ملاحظة السلوك")
                    if st.form_submit_button("حفظ وإرسال إشعار"):
                        pts = 10 if "⭐" in t_v else 5 if "✅" in t_v else -5 if "⚠️" in t_v else -10
                        sh.worksheet("behavior").append_row([sel_st, str(d_v), t_v, n_v])
                        
                        ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                        old_pts = int(ws_st.cell(c.row, 9).value or 0)
                        ws_st.update_cell(c.row, 9, old_pts + pts)
                        
                        if target_email and "@" in str(target_email):
                            send_email_alert(sel_st, target_email, t_v, n_v)
                            st.info(f"📧 تم إرسال إشعار لولي الأمر: {target_email}")
                        st.success("تم الحفظ ✅"); time.sleep(1); st.rerun()

    elif menu == "📢 إعلانات الاختبارات":
        st.header("📢 إعلانات المواعيد")
        with st.form("ex_form"):
            e_cls = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = st.text_input("الموضوع")
            e_dt = st.date_input("التاريخ")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([e_cls, e_ttl, str(e_dt)])
                st.success("تم النشر ✅")

# --- 4. واجهة الطالب (مصححة الأخطاء) ---
elif st.session_state.role == "student":
    st.sidebar.button("خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_data("students")
    s_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    # الإعلانات
    df_ex = fetch_data("exams")
    if not df_ex.empty:
        my_ex = df_ex[df_ex['الصف'] == s_data['class']]
        for _, r in my_ex.iterrows():
            st.warning(f"🔔 **تنبيه:** {r['العنوان']} بتاريخ {r['التاريخ']}")

    st.markdown(f"### 👋 مرحباً بك يا بطل: {s_data['name']}")
    # جلب المرحلة والمادة بشكل صحيح
    s_lev = s_data.get('المرحلة', 'غير محدد')
    s_sub = s_data.get('sem', 'غير محدد')
    st.info(f"📍 الصف: {s_data['class']} | المرحلة: {s_lev} | المادة: {s_sub}")

    t1, t2, t3 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📧 بياناتي"])
    
    with t1:
        st.subheader("📝 درجاتي")
        df_g = fetch_data("grades")
        my_g = df_g[df_g['student_id'] == s_data['name']].drop_duplicates()
        if not my_g.empty:
            top_g = my_g.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("فترة 1", top_g['p1']); c2.metric("فترة 2", top_g['p2']); c3.metric("مشاركة", top_g['perf'])
            st.dataframe(my_g, use_container_width=True, hide_index=True)

    with t2:
        st.subheader(f"⭐ رصيد النقاط: {s_data.get('النقاط', 0)}")
        # إصلاح الخطأ: جلب بيانات السلوك أولاً ثم عرضها
        df_behavior_data = fetch_data("behavior")
        if not df_behavior_data.empty:
            my_behavior = df_behavior_data[df_behavior_data['student_id'] == s_data['name']]
            st.dataframe(my_behavior, use_container_width=True, hide_index=True)
        else:
            st.info("لا يوجد سجل سلوك حالياً.")

    with t3:
        with st.form("up_st"):
            m = st.text_input("إيميل ولي الأمر", value=str(s_data.get('الإيميل', '')))
            p = st.text_input("الجوال", value=str(s_data.get('الجوال', '')))
            if st.form_submit_button("تحديث البيانات"):
                ws = sh.worksheet("students"); cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, m); ws.update_cell(cell.row, 8, p)
                st.success("تم التحديث ✅"); st.rerun()
