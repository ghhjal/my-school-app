import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials
import urllib.parse
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1- إعداد نظام تسجيل الأخطاء (للاستقرار والصيانة)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# 2- تحسين الاتصال وتقليل الضغط على Google Sheets باستخدام التخزين المؤقت
@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        logging.error(f"Error connecting to Sheets: {e}")
        return None

sh = get_client()

@st.cache_data(ttl=60) # تحديث البيانات كل دقيقة لتقليل الطلبات المتكررة
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        logging.error(f"Error fetching {worksheet_name}: {e}")
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) - كما هو تماماً بدون أي تغيير ---
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
    
    .contact-section { margin-top: 30px; text-align: center; padding: 20px; }
    .contact-icons { display: flex; justify-content: center; gap: 25px; margin-top: 15px; }
    .contact-icons a { text-decoration: none; color: #1e40af; font-size: 28px; transition: 0.3s; }
    .contact-icons a:hover { color: #3b82f6; transform: scale(1.15); }
    .footer-text { text-align: center; opacity: 0.8; font-size: 13px; margin-top: 30px; padding: 15px; border-top: 1px solid rgba(128, 128, 128, 0.1); }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام متابعة الطلاب والتواصل مع أولياء الأمور</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state:
    st.session_state.role = None

# --- صفحة الدخول ---
if st.session_state.role is None:
    st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #1e40af; margin-top: 0; font-weight: 700;">أهلًا بكم في منصة زياد الذكية</h4>
            <p style="color: inherit; font-size: 15px; margin-bottom: 0;">مبادرة تعليمية تهدف إلى تسهيل متابعة مستوى الطلاب أكاديمياً وسلوكياً.</p>
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

    st.markdown("""<div class="contact-section">...</div>""", unsafe_allow_html=True)
    st.stop()

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.markdown('<div style="background:linear-gradient(135deg,#1e40af,#3b82f6); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:10px;"><h1>👨‍🏫 لوحة تحكم المعلم</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 إدارة الطلاب", "📈 شاشة الدرجات", "🔍 البحث المطور", "🥇 رصد السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"
    ])

    # التبويب الأول: إدارة الطلاب
    with tab1:
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس ملف طالب جديد")
            with st.form("add_student_final_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("🔢 الرقم الأكاديمي")
                nname = c2.text_input("👤 الاسم الثلاثي")
                nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                c4, c5, c6 = st.columns(3)
                nyear = c4.text_input("🗓️ العام الدراسي", value="1447هـ")
                nstage = c5.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
                c7, c8 = st.columns(2)
                nmail = c7.text_input("📧 البريد الإلكتروني")
                nphone = c8.text_input("📱 جوال ولي الأمر (بدون 966)")

                if st.form_submit_button("✅ اعتماد وإضافة الطالب", use_container_width=True):
                    if nid and nname and nphone:
                        cp = nphone.strip()
                        if cp.startswith("0"): cp = cp[1:]
                        if not cp.startswith("966"): cp = "966" + cp
                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"]
                        try:
                            sh.worksheet("students").append_row(row)
                            st.success(f"✅ تم إضافة {nname} بنجاح")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                        except Exception as e:
                            logging.error(f"Add student error: {e}"); st.error("خطأ في الاتصال")

        with st.expander("📋 السجل الحالي للطلاب"):
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("🗑️ منطقة الحذف النهائي الشامل"):
            st.error("⚠️ سيتم حذف كافة بيانات الطالب بالاعتماد على الرقم الأكاديمي")
            if not df_st.empty:
                student_map = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0])) # اسم -> ID
                del_name = st.selectbox("🎯 اختر الطالب للحذف:", [""] + list(student_map.keys()))
                if st.button("🚨 تنفيذ الحذف النهائي الآن", use_container_width=True):
                    if del_name:
                        target_id = student_map[del_name]
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s)
                                df_temp = fetch_safe(s)
                                if not df_temp.empty:
                                    # الحذف يتم بالبحث عن الـ ID في العمود الأول
                                    row_idx = df_temp[df_temp.iloc[:, 0].astype(str) == str(target_id)].index
                                    if not row_idx.empty:
                                        ws.delete_rows(int(row_idx[0]) + 2)
                            except: pass
                        st.success("💥 تم المسح بنجاح"); st.cache_data.clear(); time.sleep(1); st.rerun()

    # التبويب الثاني: شاشة الدرجات (مطور للاعتماد على الـ ID)
    with tab2:
        st.markdown("### 📝 رصد درجات الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            student_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            with st.form("grades_integrated_form", clear_on_submit=True):
                sel_name = st.selectbox("👤 اختر الطالب:", options=list(student_dict.keys()), index=None)
                col_p1, col_p2, col_perf = st.columns(3)
                v_p1 = col_p1.number_input("⭐ المشاركة", min_value=0.0, max_value=20.0, step=0.5)
                v_p2 = col_p2.number_input("📚 الواجبات", min_value=0.0, max_value=20.0, step=0.5)
                v_perf = col_perf.number_input("📝 اختبارات", min_value=0.0, max_value=20.0, step=0.5)
                note = st.text_input("💬 ملاحظة المعلم")

                if st.form_submit_button("✅ حفظ الدرجات", use_container_width=True):
                    if sel_name:
                        s_id = student_dict[sel_name]
                        try:
                            ws_g = sh.worksheet("grades")
                            df_g_curr = fetch_safe("grades")
                            curr_date = datetime.datetime.now().strftime("%Y-%m-%d")
                            # التعديل: تخزين الـ ID بدلاً من الاسم لضمان الاستقرار
                            row_data = [s_id, v_p1, v_p2, v_perf, curr_date, note]
                            
                            if not df_g_curr.empty and str(s_id) in df_g_curr.iloc[:, 0].astype(str).values:
                                idx = df_g_curr[df_g_curr.iloc[:, 0].astype(str) == str(s_id)].index[0]
                                ws_g.update(f"B{idx+2}:F{idx+2}", [[v_p1, v_p2, v_perf, curr_date, note]])
                            else:
                                ws_g.append_row(row_data)
                            st.success("✅ تم الحفظ"); st.cache_data.clear(); time.sleep(1); st.rerun()
                        except: st.error("خطأ في النظام")

    # التبويب الثالث: البحث المطور
    with tab3:
        st.markdown("### 🔍 محرك البحث الذكي")
        df_st = fetch_safe("students")
        search_query = st.text_input("🔎 ابحث باسم الطالب أو الرقم الأكاديمي:")
        if search_query:
            results = df_st[df_st.iloc[:, 0].astype(str).str.contains(search_query) | df_st.iloc[:, 1].str.contains(search_query)]
            if not results.empty:
                for i in range(len(results)):
                    with st.container(border=True):
                        st.markdown(f"**👤 الاسم:** {results.iloc[i, 1]} | **🔢 الرقم:** {results.iloc[i, 0]}")
                        phone = results.iloc[i, 7]
                        st.markdown(f'<a href="https://wa.me/{phone}" target="_blank">💬 واتساب</a>', unsafe_allow_html=True)

    # التبويب الرابع: رصد السلوك (مطور للاعتماد على الـ ID)
    with tab4:
        st.subheader("🎭 رصد السلوك والتواصل الفوري")
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            b_name = st.selectbox("🎯 اختر الطالب:", [""] + list(st_dict.keys()), key="behavior_select")
            if b_name:
                s_id = st_dict[b_name]
                st_row = df_st[df_st.iloc[:, 0] == s_id].iloc[0]
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    b_type = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                    b_date = c2.date_input("📅 التاريخ")
                    b_note = st.text_area("📝 نص الملاحظة")
                    if st.button("💾 رصد وحفظ فقط", use_container_width=True):
                        try:
                            sh.worksheet("behavior").append_row([s_id, str(b_date), b_type, b_note])
                            # تحديث النقاط في شيت الطلاب
                            ws_st = sh.worksheet("students")
                            row_idx = df_st[df_st.iloc[:, 0] == s_id].index[0]
                            p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                            curr = int(st_row[8] if st_row[8] else 0)
                            ws_st.update_cell(row_idx + 2, 9, str(curr + p_map.get(b_type, 0)))
                            st.success("✅ تم الرصد"); st.cache_data.clear(); time.sleep(1); st.rerun()
                        except: st.error("فشل الحفظ")

    # التبويب الخامس: الاختبارات
    with tab5:
        st.markdown("### 📢 إدارة الاختبارات والتنبيهات")
        with st.form("ann_form"):
            c1, c2 = st.columns([1, 2])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = c2.text_input("📝 العنوان")
            a_date = st.date_input("📅 التاريخ")
            a_link = st.text_input("🔗 رابط إضافي")
            if st.form_submit_button("🚀 نشر الآن"):
                try:
                    sh.worksheet("exams").append_row([str(a_class), a_title, str(a_date), a_link])
                    st.success("✅ تم النشر"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("خطأ")

    # التبويب السادس: الإعدادات
    with tab6:
        st.markdown("### ⚙️ إعدادات المنصة")
        with st.expander("🔐 تغيير بيانات الحساب"):
            with st.form("auth_update"):
                new_u = st.text_input("اسم المستخدم الجديد")
                new_p = st.text_input("كلمة المرور الجديدة", type="password")
                if st.form_submit_button("💾 حفظ"):
                    h = hashlib.sha256(str.encode(new_p)).hexdigest()
                    try:
                        ws_u = sh.worksheet("users")
                        ws_u.update_cell(2, 1, new_u); ws_u.update_cell(2, 2, h)
                        st.success("✅ تم التحديث")
                    except: st.error("خطأ")

    with tab7:
        if st.button("تأكيد تسجيل الخروج"):
            st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (النسخة الكاملة بدون أي حذف)
# ==========================================
if st.session_state.role == "student":
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    df_beh = fetch_safe("behavior")
    df_ex = fetch_safe("exams")

    try:
        student_data = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        if not student_data.empty:
            s_row = student_data.iloc[0]
            s_name, s_class = s_row[1], s_row[2]
            val = str(s_row[8]).strip() if len(s_row) >= 9 else "0"
            s_points = int(float(val)) if val and val != "None" and val.replace('.','',1).isdigit() else 0
        else:
            st.error("⚠️ بيانات الطالب غير موجودة"); st.stop()
    except Exception as e:
        st.error(f"❌ خطأ: {e}"); st.stop()

    next_badge, points_to_next = "", 0
    if s_points < 10: next_badge, points_to_next = "البرونزي", 10 - s_points
    elif s_points < 50: next_badge, points_to_next = "الفضي", 50 - s_points
    elif s_points < 100: next_badge, points_to_next = "الذهبي", 100 - s_points

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 20px; text-align: center; border-radius: 15px; color: white;">
            <h2>🎯 إنجاز الطالب: {s_name}</h2>
            <b>🏫 {s_class}</b>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="opacity: {'1' if s_points >= 10 else '0.15'}">🥉<br><b>برونزي</b></div>
                <div style="opacity: {'1' if s_points >= 50 else '0.15'}">🥈<br><b>فضي</b></div>
                <div style="opacity: {'1' if s_points >= 100 else '0.15'}">🥇<br><b>ذهبي</b></div>
            </div>
            <div style="background: orange; color: white; padding: 15px; border-radius: 15px;">
                <b>رصيد النقاط: {s_points}</b>
                {f'<br><small>بقي {points_to_next} للوسام {next_badge}</small>' if points_to_next > 0 else ''}
            </div>
        </div>
    """, unsafe_allow_html=True)

    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "🏆 المتصدرون", "⚙️ الإعدادات"])

    with t_ex:
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.info(f"📢 {r[1]} | 📅 {r[2]}")

    with t_grade:
        # التعديل: البحث بالـ ID لضمان دقة درجات الطالب
        g_data = df_grades[df_grades.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        if not g_data.empty:
            p1, p2, perf = g_data.iloc[0][1], g_data.iloc[0][2], g_data.iloc[0][3]
            st.metric("المشاركة", p1)
            st.metric("الواجبات", p2)
            st.metric("الاختبارات", perf)
        else: st.write("لا توجد درجات مرصودة حالياً")

    with t_beh:
        # التعديل: البحث بالـ ID
        f_beh = df_beh[df_beh.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        for _, r in f_beh.iloc[::-1].iterrows():
            st.warning(f"{r[2]} | {r[3]} (📅 {r[1]})")

    with t_lead:
        try:
            leader_list = df_st.copy()
            leader_list[df_st.columns[8]] = pd.to_numeric(leader_list.iloc[:, 8], errors='coerce').fillna(0)
            leader_list = leader_list.sort_values(by=leader_list.columns[8], ascending=False).head(10)
            for i, row in leader_list.iterrows():
                st.write(f"🏆 {row[1]} - النقاط: {row[8]}")
        except: st.info("جاري التحديث...")

    with t_set:
        with st.form("set_f"):
            m = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            p = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ التعديلات"):
                try:
                    ws = sh.worksheet("students")
                    # البحث بالـ ID لمعرفة السطر الصحيح للتحديث
                    df_temp = fetch_safe("students")
                    idx = df_temp[df_temp.iloc[:, 0].astype(str) == str(st.session_state.sid)].index[0]
                    ws.update_cell(idx + 2, 7, m); ws.update_cell(idx + 2, 8, p)
                    st.cache_data.clear(); st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()
                except: st.error("خطأ في الاتصال")

    if st.button("🚗 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None; st.rerun()
