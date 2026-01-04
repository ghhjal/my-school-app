import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# --- التصميم الاحترافي (CSS) ---
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

# ======================================================
# 👨‍🏫 واجهة المعلم – النسخة الكاملة المصححة
# ======================================================
if st.session_state.role == "teacher":

    st.markdown(
        '<div style="background:#1e3a8a;padding:15px;border-radius:12px;color:white;font-size:26px;font-weight:bold;text-align:center;">'
        '👨‍🏫 لوحة تحكم المعلم'
        '</div>',
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 إدارة الطلاب",
        "📈 شاشة الدرجات",
        "🔍 البحث",
        "🥇 السلوك",
        "📢 الاختبارات",
        "⚙️ الإعدادات",
        "🚪 خروج"
    ])

    # ======================================================
    # 👥 إدارة الطلاب
    # ======================================================
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
                        phone = nphone.strip()
                        if phone.startswith("0"):
                            phone = phone[1:]
                        if not phone.startswith("966"):
                            phone = "966" + phone

                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, phone, "0"]
                        sh.worksheet("students").append_row(row)

                        st.success(f"✅ تم إضافة الطالب {nname}")
                        time.sleep(1)
                        st.rerun()

        with st.expander("📋 السجل الحالي للطلاب"):
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.markdown("---")

        with st.expander("🗑️ منطقة الحذف النهائي"):
            st.error("⚠️ سيتم حذف الطالب من جميع الجداول")
            if not df_st.empty:
                del_name = st.selectbox("اختر الطالب:", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 حذف نهائي", use_container_width=True):
                    if del_name:
                        for sheet in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(sheet)
                                cell = ws.find(del_name)
                                ws.delete_rows(cell.row)
                            except:
                                pass
                        st.success("✅ تم الحذف")
                        time.sleep(1)
                        st.rerun()

    # ======================================================
    # 📈 شاشة الدرجات
    # ======================================================
    with tab2:
        st.markdown("### 📝 رصد درجات الطلاب (النظام المتكامل)")
        df_st = fetch_safe("students")

        if not df_st.empty:
            with st.container(border=True):
                with st.form("grades_integrated_form", clear_on_submit=True):
                    students = df_st.iloc[:, 1].tolist()
                    selected_student = st.selectbox(
                        "👤 اختر الطالب",
                        options=students,
                        index=None,
                        placeholder="اكتب اسم الطالب..."
                    )

                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("⭐ المشاركة", 0.0, 20.0, step=0.5)
                    p2 = c2.number_input("📚 الواجبات", 0.0, 20.0, step=0.5)
                    perf = c3.number_input("📝 الاختبارات", 0.0, 20.0, step=0.5)

                    note = st.text_input("💬 ملاحظة المعلم")

                    if st.form_submit_button("✅ حفظ الدرجات", use_container_width=True):
                        if selected_student:
                            row = df_st[df_st.iloc[:, 1] == selected_student].iloc[0]
                            sid = row[0]
                            date = datetime.datetime.now().strftime("%Y-%m-%d")
                            sh.worksheet("grades").append_row([sid, p1, p2, perf, date, note])
                            st.success("✅ تم حفظ الدرجات")
                            time.sleep(1)
                            st.rerun()

        st.markdown("---")
        df_gr = fetch_safe("grades")
        if not df_gr.empty:
            st.dataframe(df_gr, use_container_width=True, hide_index=True)

    # ======================================================
    # 🔍 البحث
    # ======================================================
    with tab3:
        st.markdown("### 🔍 البحث عن طالب")
        q = st.text_input("اكتب اسم الطالب")
        if q:
            df = fetch_safe("students")
            res = df[df.iloc[:, 1].str.contains(q, na=False)]
            st.dataframe(res, use_container_width=True, hide_index=True)

    # ======================================================
    # 🥇 السلوك
    # ======================================================
    with tab4:
        st.markdown("### 🥇 سجل السلوك")
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            st.dataframe(df_b, use_container_width=True, hide_index=True)

    # ======================================================
    # 📢 الاختبارات
    # ======================================================
    with tab5:
        st.markdown("### 📢 إدارة الاختبارات")
        st.info("واجهة الاختبارات جاهزة للربط")

    # ======================================================
    # ⚙️ الإعدادات
    # ======================================================
    with tab6:
        st.markdown("### ⚙️ إعدادات الحساب")
        with st.form("settings_form"):
            new_user = st.text_input("اسم المستخدم الجديد")
            new_pass = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("💾 حفظ"):
                ws = sh.worksheet("users")
                ws.update_cell(2, 1, new_user)
                ws.update_cell(2, 2, new_pass)
                st.success("✅ تم التحديث")

    # ======================================================
    # 🚪 خروج
    # ======================================================
    with tab7:
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# ==========================================
# 👨‍🎓 واجهة الطالب (النسخة الأصلية المصححة)
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
            s_points = int(float(val)) if val and val != "None" and val.replace('.', '', 1).isdigit() else 0
        else:
            st.error("⚠️ بيانات الطالب غير موجودة")
            st.stop()
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        st.stop()

    # -----------------------------
    # 🎖️ حساب الوسام التالي
    # -----------------------------
    next_badge, points_to_next = "", 0
    if s_points < 10:
        next_badge, points_to_next = "البرونزي", 10 - s_points
    elif s_points < 50:
        next_badge, points_to_next = "الفضي", 50 - s_points
    elif s_points < 100:
        next_badge, points_to_next = "الذهبي", 100 - s_points

    # -----------------------------
    # 📢 العنوان العلوي
    # -----------------------------
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 20px; margin: -1rem -1rem 1rem -1rem; border-bottom: 5px solid #f59e0b; text-align: center;">
            <h2 style="color: white; margin: 0; font-family: 'Cairo', sans-serif; font-size: 1.5rem;">
                🎯 إنجاز الطالب: <span style="color: #ffd700;">{s_name}</span>
            </h2>
            <div style="background: rgba(0,0,0,0.2); display: inline-block; padding: 5px 20px; border-radius: 10px; margin-top: 10px;">
                <b style="color: white; font-size: 1.1rem;">🏫 {s_class}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # -----------------------------
    # 👤 نظام الأوسمة والنقاط
    # -----------------------------
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="border: 2px solid #cd7f32; padding: 10px; border-radius: 15px; width: 30%; background: #fffcf9; opacity: {'1' if s_points >= 10 else '0.15'};">
                    <div style="font-size: 2rem;">🥉</div><b style="color: #cd7f32; font-size: 0.8rem;">برونزي</b>
                </div>
                <div style="border: 2px solid #c0c0c0; padding: 10px; border-radius: 15px; width: 30%; background: #f8f9fa; opacity: {'1' if s_points >= 50 else '0.15'};">
                    <div style="font-size: 2rem;">🥈</div><b style="color: #7f8c8d; font-size: 0.8rem;">فضي</b>
                </div>
                <div style="border: 2px solid #ffd700; padding: 10px; border-radius: 15px; width: 30%; background: #fffdf0; opacity: {'1' if s_points >= 100 else '0.15'};">
                    <div style="font-size: 2rem;">🥇</div><b style="color: #d4af37; font-size: 0.8rem;">ذهبي</b>
                </div>
            </div>
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px;">
                <b style="font-size: 1.1rem;">رصيد النقاط السلوكية</b>
                <div style="font-size: 3.5rem;">{s_points}</div>
                {f'<div style="font-size: 0.9rem;">🚀 بقي لك {points_to_next} نقطة للوسام {next_badge}</div>' if points_to_next > 0 else ''}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # -----------------------------
    # 📊 التبويبات
    # -----------------------------
    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(
        ["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "🏆 المتصدرون", "⚙️ الإعدادات"]
    )

    # --- التنبيهات ---
    with t_ex:
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.markdown(
                    f'<div style="background:#002347;padding:15px;border-radius:12px;border-right:8px solid #f59e0b;margin-bottom:10px;">'
                    f'<b style="color:#ffd700;">📢 {r[1]}</b><br>'
                    f'<b style="color:white;">📅 {r[2]}</b></div>',
                    unsafe_allow_html=True
                )

    # --- الدرجات ---
    with t_grade:
        try:
            g_data = df_grades[df_grades.iloc[:, 0].astype(str) == str(s_name)]
            p1, p2, perf = g_data.iloc[0][1:4] if not g_data.empty else ("-", "-", "-")
        except:
            p1, p2, perf = "-", "-", "-"

        def box(t, v, c):
            return f'<div style="background:white;padding:15px;border-radius:12px;border:2px solid #e2e8f0;margin-bottom:10px;"><b>{t}</b><b style="float:left;color:{c};font-size:1.7rem;">{v}</b></div>'

        st.markdown(box("المشاركة التفاعلية", p1, "#3b82f6"), unsafe_allow_html=True)
        st.markdown(box("إنجاز الواجبات", p2, "#10b981"), unsafe_allow_html=True)
        st.markdown(box("الاختبارات القصيرة", perf, "#f59e0b"), unsafe_allow_html=True)

    # --- السلوك ---
    with t_beh:
        if not df_beh.empty:
            f_beh = df_beh[df_beh.iloc[:, 0] == s_name]
            for _, r in f_beh.iloc[::-1].iterrows():
                st.markdown(
                    f'<div style="background:#f8fafc;padding:15px;border-radius:12px;border-right:6px solid #1e3a8a;margin-bottom:10px;">'
                    f'<b>{r[2]}</b><br><small>{r[3]}</small></div>',
                    unsafe_allow_html=True
                )

    # --- المتصدرون ---
    with t_lead:
        try:
            leader_list = df_st.values.tolist()

            def pts(x):
                try:
                    return int(float(x[8]))
                except:
                    return 0

            leader_list.sort(key=pts, reverse=True)
            for i, r in enumerate(leader_list[:10]):
                st.markdown(
                    f'<div style="padding:10px;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:8px;">'
                    f'<b>{i+1}. {r[1]}</b>'
                    f'<span style="float:left;background:#1e3a8a;color:white;padding:4px 12px;border-radius:8px;">{pts(r)}</span></div>',
                    unsafe_allow_html=True
                )
        except:
            st.info("جاري التحديث...")

    # --- الإعدادات ---
    with t_set:
        with st.form("set_f"):
            m = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            p = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ التعديلات", use_container_width=True):
                ws = sh.worksheet("students")
                cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, m)
                ws.update_cell(cell.row, 8, p)
                st.cache_data.clear()
                st.success("تم الحفظ")
                st.rerun()

    # -----------------------------
    # 🚪 تسجيل الخروج
    # -----------------------------
    if st.button("🚗 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None
        st.rerun()
