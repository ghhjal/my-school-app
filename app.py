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

if st.session_state.role == "teacher":
    st.markdown('<div style="...">لوحة تحكم المعلم</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 إدارة الطلاب",
        "📈 شاشة الدرجات",
        "🔍 البحث",
        "🥇 السلوك",
        "📢 الاختبارات",
        "⚙️ الإعدادات",
        "🚪 خروج"
    ])

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
                        if cp.startswith('0'): cp = cp[1:]
                        if not cp.startswith('966'): cp = '966' + cp
                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"]
                        sh.worksheet("students").append_row(row)
                        st.success(f"✅ تم إضافة {nname} بنجاح"); time.sleep(1); st.rerun()

        with st.expander("📋 السجل الحالي للطلاب"):
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("🗑️ منطقة الحذف النهائي الشامل"):
            st.error("⚠️ سيتم حذف كافة بيانات الطالب من جميع الجداول")
            if not df_st.empty:
                del_name = st.selectbox("🎯 اختر الطالب للحذف:", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 تنفيذ الحذف النهائي الآن", use_container_width=True):
                    if del_name:
                        for s in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(s); cell = ws.find(del_name)
                                if cell: ws.delete_rows(cell.row)
                            except: pass
                        st.success("💥 تم المسح بنجاح"); time.sleep(1); st.rerun()

    with tba2:
    st.markdown("### 📝 رصد درجات الطلاب (النظام المتكامل)")
    df_st = fetch_safe("students")
    
    if not df_st.empty:
        with st.container(border=True):
            st.markdown("#### 🎯 إدخال درجات الطالب")
            with st.form("grades_integrated_form", clear_on_submit=True):
                # 1. حقل اختيار الطالب مع خاصية البحث
                # استخراج الأسماء من عمود الاسم (B) في شيت الطلاب
                student_list = df_st.iloc[:, 1].tolist()
                selected_student = st.selectbox("👤 اختر الطالب (يمكنك كتابة الاسم للبحث):", 
                                               options=student_list, 
                                               index=None, 
                                               placeholder="ابحث عن اسم الطالب هنا...")
                
                # 2. الحقول الثلاثة متطابقة مع أعمدة الجدول (p1, p2, perf)
                st.markdown("---")
                col_p1, col_p2, col_perf = st.columns(3)
                
                val_p1 = col_p1.number_input("⭐ المشاركة التفاعلية (p1)", min_value=0.0, max_value=20.0, step=0.5)
                val_p2 = col_p2.number_input("📚 إنجاز الواجبات (p2)", min_value=0.0, max_value=20.0, step=0.5)
                val_perf = col_perf.number_input("📝 اختبارات قصيرة (perf)", min_value=0.0, max_value=20.0, step=0.5)
                
                # حقل الملاحظة الإضافي
                teacher_note = st.text_input("💬 ملاحظة المعلم (اختياري)")
                
                if st.form_submit_button("✅ حفظ الدرجات في الجدول", use_container_width=True):
                    if selected_student:
                        try:
                            # البحث عن الرقم الأكاديمي للطالب المختار
                            student_row = df_st[df_st.iloc[:, 1] == selected_student].iloc[0]
                            s_id = student_row[0] # student_id من عمود A
                            
                            # ترتيب الأعمدة للمطابقة مع شيت grades:
                            # A: student_id, B: p1, C: p2, D: perf, E: date, F: notes
                            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                            grade_row = [s_id, val_p1, val_p2, val_perf, current_date, teacher_note]
                            
                            sh.worksheet("grades").append_row(grade_row)
                            st.success(f"✅ تم رصد درجات الطالب {selected_student} بنجاح")
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"خطأ في التوصيل: {e}")
                    else:
                        st.warning("⚠️ يرجى اختيار اسم الطالب أولاً.")

        # عرض جدول الدرجات الحالي للمراجعة (مطابق لصورة الجدول المرفقة)
        st.markdown("---")
        st.markdown("##### 📊 مراجعة سجل الدرجات الحالي (grades)")
        df_grades = fetch_safe("grades")
        if not df_grades.empty:
            # تجميل العرض ليطابق student_id, p1, p2, perf
            st.dataframe(df_grades, use_container_width=True, hide_index=True)

    with tab3:
        ...

    with tab4:
        ...

    with tab5:
        ...

    with tab6:
        ...

    with tab7:
        ...

# ==========================================
# 🛑 قسم الطالب (معزول 100٪)
# ==========================================

# ==========================================
# 👨‍🎓 واجهة الطالب (النسخة المتكاملة: أوسمة + خطوط واضحة)
# ==========================================
elif st.session_state.role == "student":
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
            st.error("⚠️ بيانات الطالب غير موجودة")
            st.stop()
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        st.stop()

    # حساب المتبقي للوسام التالي
    next_badge, points_to_next = "", 0
    if s_points < 10: next_badge, points_to_next = "البرونزي", 10 - s_points
    elif s_points < 50: next_badge, points_to_next = "الفضي", 50 - s_points
    elif s_points < 100: next_badge, points_to_next = "الذهبي", 100 - s_points

    # --- 📢 العنوان العلوي (الاسم والفصل) ---
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

    # --- 👤 نظام الأوسمة والنقاط (تمت إعادتها وتوضيحها) ---
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="border: 2px solid #cd7f32; padding: 10px; border-radius: 15px; width: 30%; background: #fffcf9; opacity: {'1' if s_points >= 10 else '0.15'}; transform: {'scale(1.1)' if 10 <= s_points < 50 else 'scale(1)'}; border-width: {'3px' if 10 <= s_points < 50 else '1px'};">
                    <div style="font-size: 2rem;">🥉</div><b style="color: #cd7f32; font-size: 0.8rem;">برونزي</b>
                </div>
                <div style="border: 2px solid #c0c0c0; padding: 10px; border-radius: 15px; width: 30%; background: #f8f9fa; opacity: {'1' if s_points >= 50 else '0.15'}; transform: {'scale(1.1)' if 50 <= s_points < 100 else 'scale(1)'}; border-width: {'3px' if 50 <= s_points < 100 else '1px'};">
                    <div style="font-size: 2rem;">🥈</div><b style="color: #7f8c8d; font-size: 0.8rem;">فضي</b>
                </div>
                <div style="border: 2px solid #ffd700; padding: 10px; border-radius: 15px; width: 30%; background: #fffdf0; opacity: {'1' if s_points >= 100 else '0.15'}; transform: {'scale(1.1)' if s_points >= 100 else 'scale(1)'}; border-width: {'3px' if s_points >= 100 else '1px'};">
                    <div style="font-size: 2rem;">🥇</div><b style="color: #d4af37; font-size: 0.8rem;">ذهبي</b>
                </div>
            </div>
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px;">
                <b style="font-size: 1.1rem; display: block;">رصيد النقاط السلوكية</b>
                <b style="font-size: 3.5rem; line-height: 1.1;">{s_points}</b>
                {f'<div style="font-size: 0.9rem; margin-top:8px; background: rgba(255,255,255,0.2); border-radius: 10px; padding: 5px; font-weight: bold;">🚀 بقي لك {points_to_next} نقطة للوسام {next_badge}</div>' if points_to_next > 0 else ''}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات (خطوط كبيرة واضحة) ---
    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "🏆 المتصدرون", "⚙️ الإعدادات"])

    with t_ex:
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.markdown(f'<div style="background: #002347; padding: 15px; border-radius: 12px; border-right: 8px solid #f59e0b; margin-bottom: 10px;"><b style="color: #ffd700; font-size: 1.2rem;">📢 {r[1]}</b><br><b style="color: white; font-size: 1rem;">📅 {r[2]}</b></div>', unsafe_allow_html=True)

    with t_grade:
        st.markdown('<h3 style="text-align:right; color:#1e3a8a; font-size: 1.3rem;">📊 السجل الأكاديمي</h3>', unsafe_allow_html=True)
        try:
            g_data = df_grades[df_grades.iloc[:, 0].astype(str) == s_name]
            p1, p2, perf = (g_data.iloc[0][1], g_data.iloc[0][2], g_data.iloc[0][3]) if not g_data.empty else ("-", "-", "-")
        except: p1, p2, perf = "-", "-", "-"
        
        def gc(t, v, c): return f'<div style="background: #ffffff; padding: 15px; border-radius: 12px; border: 2px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><b style="font-size: 1.1rem; color: #1e293b;">{t}</b><b style="font-size: 1.7rem; color: {c};">{v}</b></div>'
        st.markdown(gc("المشاركة التفاعلية", p1, "#3b82f6"), unsafe_allow_html=True)
        st.markdown(gc("إنجاز الواجبات", p2, "#10b981"), unsafe_allow_html=True)
        st.markdown(gc("الاختبارات القصيرة", perf, "#f59e0b"), unsafe_allow_html=True)

    with t_beh:
        st.markdown('<h3 style="text-align:right; color:#1e3a8a; font-size: 1.3rem;">🎭 سجل الانضباط</h3>', unsafe_allow_html=True)
        if not df_beh.empty:
            f_beh = df_beh[df_beh.iloc[:, 0] == s_name]
            for _, r in f_beh.iloc[::-1].iterrows():
                is_pos = any(x in str(r[2]) for x in ["+", "🌟", "✅"])
                color = "#065f46" if is_pos else "#991b1b"
                st.markdown(f'<div style="background: {"#f0fdf4" if is_pos else "#fef2f2"}; padding: 15px; border-radius: 12px; border-right: 8px solid {color}; margin-bottom: 10px;"><div style="display: flex; justify-content: space-between;"><b style="font-size: 1.1rem; color: {color};">{"✅" if is_pos else "⚠️"} {r[2]}</b><b style="font-size: 0.9rem; color: #64748b;">{r[1]}</b></div><div style="font-size: 1.1rem; color: #1e293b; margin-top:5px; font-weight: bold;">{r[3]}</div></div>', unsafe_allow_html=True)

    with t_lead:
        st.markdown('<h3 style="text-align:right; color:#1e3a8a; font-size: 1.3rem;">🏆 أبطال الصف</h3>', unsafe_allow_html=True)
        try:
            leader_list = df_st.values.tolist()
            def get_p(x):
                try: return int(float(str(x[8])))
                except: return 0
            leader_list.sort(key=get_p, reverse=True)
            for rank_idx, l_row in enumerate(leader_list[:10]):
                rank = rank_idx + 1
                is_me = (str(l_row[1]) == str(s_name))
                icon, col = ("👑", "#ffd700") if rank==1 else (("🥈", "#94a3b8") if rank==2 else (("🥉", "#cd7f32") if rank==3 else (f"#{rank}", "#64748b")))
                st.markdown(f'<div style="background: {"#eff6ff" if is_me else "white"}; padding: 12px; border-radius: 12px; border: {"3px solid #1e3a8a" if is_me else "1px solid #e2e8f0"}; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"><div style="display: flex; align-items: center;"><b style="width: 40px; font-size: 1.3rem; color: {col}; text-align: center;">{icon}</b><b style="font-size: 1.1rem; color: #1e293b;">{l_row[1]} {" (أنت)" if is_me else ""}</b></div><b style="background: {col}; color: white; padding: 5px 15px; border-radius: 10px; font-size: 1.1rem; font-weight: bold;">{get_p(l_row)}</b></div>', unsafe_allow_html=True)
        except: st.info("جاري التحديث...")

    with t_set:
        with st.form("set_f"):
            st.markdown("<b>⚙️ تحديث البيانات</b>", unsafe_allow_html=True)
            m = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            p = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            if st.form_submit_button("✅ حفظ التعديلات", use_container_width=True):
                ws = sh.worksheet("students")
                cell = ws.find(st.session_state.sid)
                ws.update_cell(cell.row, 7, m); ws.update_cell(cell.row, 8, p)
                st.cache_data.clear(); st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()
    
    if st.button("🚗 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None; st.rerun()
