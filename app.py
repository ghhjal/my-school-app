import streamlit as st
import gspread
import pandas as pd
def draw_professional_student_ui():
    # تصميم واجهة الطالب - الهوية البصرية
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 2rem;
            border-radius: 1rem;
            border-right: 8px solid #38bdf8;
            color: white;
            margin-bottom: 2rem;
            text-align: right;
        }
        </style>
        <div class="main-header">
            <h1 style='margin:0; font-size: 2rem;'>بوابة الطالب المتميزة 🌟</h1>
            <p style='opacity:0.8;'>مرحباً بك في نظامك الأكاديمي المتكامل</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        # جلب البيانات
        df_st = fetch_safe("students")
        student_data = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        
        if not student_data.empty:
            s_row = student_data.iloc[0]
            # عرض الإحصائيات في كروت جذابة
            c1, c2, c3 = st.columns(3)
            with c1:
                val = str(s_row[8]).strip() if len(s_row) >= 9 else "0"
                points = int(float(val)) if val.replace('.','',1).isdigit() else 0
                st.metric("🎯 رصيد النقاط", points)
            with c2:
                st.metric("🏅 المستوى", "متفوق")
            with c3:
                st.metric("👤 الطالب", s_row[1])

            st.divider()
            
            # حل مشكلة NameError: ننشئ تبويبات جديدة تماماً للطالب هنا
            st_tabs = st.tabs(["📊 كشف الدرجات", "📜 سجل السلوك", "📝 الاختبارات"])
            
            with st_tabs[0]:
                st.dataframe(fetch_safe("grades"), use_container_width=True)
            with st_tabs[1]:
                st.info("سجلك الدراسي حافل بالإنجازات، استمر!")
            with st_tabs[2]:
                st.success("جميع اختباراتك ستظهر هنا فور جدولتها")
        else:
            st.error("بياناتك غير موجودة، يرجى مراجعة الإدارة")
    except Exception as e:
        st.error(f"عذراً، حدث خطأ: {e}")
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def render_student_portal():
    # تصميم الواجهة الاحترافية (Dark Mode Friendly)
    st.markdown("""
        <style>
        .student-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 25px;
            border-radius: 15px;
            border-left: 10px solid #3b82f6;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        # جلب البيانات بشكل معزول
        df_st = fetch_safe("students")
        student_data = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        
        if not student_data.empty:
            s_row = student_data.iloc[0]
            s_name, s_class = s_row[1], s_row[2]
            
            # عرض الترويسة
            st.markdown(f"""<div class="student-card">
                <h1 style='margin:0;'>مرحباً، {s_name} ✨</h1>
                <p style='opacity:0.8;'>الصف: {s_class} | لوحة متابعة الطالب الذكية</p>
            </div>""", unsafe_allow_html=True)

            # عرض الإحصائيات (Metrics)
            val = str(s_row[8]).strip() if len(s_row) >= 9 else "0"
            s_points = int(float(val)) if val.replace('.','',1).isdigit() else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🎯 نقاطك", s_points, delta="مستوى ممتاز")
            c2.metric("🏆 الأوسمة", "🥇 ذهبي")
            c3.metric("📅 الحضور", "100%")

            # التبويبات (بديلة لـ tab2 التي تسبب خطأ NameError)
            st.divider()
            t1, t2, t3 = st.tabs(["📊 كشف الدرجات", "🌟 سجل التميز", "📝 الاختبارات"])
            
            with t1:
                st.dataframe(fetch_safe("grades"), use_container_width=True)
            with t2:
                st.info("سيتم عرض ملاحظات المعلمين هنا قريباً")
            with t3:
                st.success("لا توجد اختبارات مجدولة لليوم")
        else:
            st.error("لم يتم العثور على بياناتك. راجع الإدارة.")
    except Exception as e:
        st.error(f"عذراً، حدث خطأ فني: {e}")

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

# --- واجهة المعلم ---
if st.session_state.role == "teacher":
    st.markdown('<div style="background:linear-gradient(135deg,#1e40af,#3b82f6); padding:20px; border-radius:15px; color:white; text-align:center; margin-bottom:10px;"><h1>👨‍🏫 لوحة تحكم المعلم</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 إدارة الطلاب", 
        "📈 شاشة الدرجات", 
        "🔍 البحث المطور", 
        "🥇 رصد السلوك", 
        "📢 الاختبارات", 
        "⚙️ الإعدادات", 
        "🚗 خروج"
    ])

    with tab7:
        if st.button("تأكيد تسجيل الخروج"):
            st.session_state.role = None
            st.rerun()

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

    # --- التبويب الثاني: شاشة الدرجات (تطوير شامل لمطابقة الجدول) ---
with tab2:
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

    # --- التبويب الثالث: البحث المطور (تصميم ذكي للجوال) ---
with tab3:
    st.markdown("### 🔍 محرك البحث الذكي")
    df_st = fetch_safe("students")
    
    # حقل البحث
    search_query = st.text_input("🔎 ابحث باسم الطالب أو الرقم الأكاديمي:", placeholder="اكتب هنا للبحث...")
    
    if search_query:
        # البحث في عمود الرقم الأكاديمي (A) وعمود الاسم (B)
        results = df_st[
            df_st.iloc[:, 0].astype(str).str.contains(search_query) | 
            df_st.iloc[:, 1].str.contains(search_query)
        ]
        
        if not results.empty:
            st.success(f"✅ تم العثور على {len(results)} طالب")
            
            # عرض النتائج في بطاقات بدلاً من جدول
            for i in range(len(results)):
                with st.container(border=True):
                    # سطر الاسم والرقم
                    c1, c2 = st.columns([2, 1])
                    c1.markdown(f"**👤 الاسم:** {results.iloc[i, 1]}")
                    c2.markdown(f"**🔢 الرقم:** {results.iloc[i, 0]}")
                    
                    # سطر الصف والمادة
                    c3, c4 = st.columns(2)
                    c3.markdown(f"**🏫 الصف:** {results.iloc[i, 2]}")
                    c4.markdown(f"**📚 المادة:** {results.iloc[i, 5]}")
                    
                    # أزرار التواصل السريع (تستفيد من مفتاح 966)
                    phone = results.iloc[i, 7]
                    st.markdown(f'''
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <a href="https://wa.me/{phone}" target="_blank" style="flex: 1; text-decoration: none;">
                                <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                                    <i class="bi bi-whatsapp"></i> واتساب ولي الأمر
                                </div>
                            </a>
                            <a href="tel:{phone}" style="flex: 1; text-decoration: none;">
                                <div style="background-color: #1e40af; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                                    📱 اتصال هاتفي
                                </div>
                            </a>
                        </div>
                    ''', unsafe_allow_html=True)
        else:
            st.error("❌ لا توجد نتائج مطابقة.")
    else:
        st.info("💡 نصيحة: يمكنك البحث بجزء من الاسم (مثلاً: اكتب 'أحمد' فقط).")

    # --- التبويب الرابع: رصد السلوك (الإصدار النهائي المكتمل 100%) ---
with tab4:
    import smtplib
    import time
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import urllib.parse 

    # 1. كود التنسيق CSS (تثبيت الألوان: الأحمر للتلقائي والحذف، الأخضر للواتساب)
    st.markdown("""
        <style>
            .stButton button { border-radius: 10px; height: 3.5em; font-weight: bold; transition: 0.3s; }
            
            /* زر الإشعار التلقائي -> أحمر فاقع */
            div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stVerticalBlock"] > div:nth-child(1) button {
                background-color: #FF0000 !important;
                color: white !important;
                border: none !important;
            }
            
            /* زر الواتساب الرئيسي -> أخضر واتساب */
            div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stVerticalBlock"] > div:nth-child(2) button {
                background-color: #25D366 !important;
                color: white !important;
                border: none !important;
            }

            /* أزرار الحذف في السجل السفلي -> أحمر */
            .stButton button[key*="del_"] {
                background-color: #FF0000 !important;
                color: white !important;
            }
            
            .stTextArea textarea { border: 1px solid #1e40af; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # دالة الرسالة الموحدة
    def get_formatted_msg(name, b_type, b_note, b_date, prefix=""):
        return (
            f"{prefix}تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {name}\n"
            f"----------------------------------------\n"
            f"🏷️ نوع السلوك: {b_type}\n"
            f"📝 الملاحظة: {b_note}\n"
            f"📅 التاريخ: {b_date}\n"
            f"----------------------------------------\n"
            f"🏛️ منصة الأستاذ زياد الذكية"
        )

    # دالة الإيميل الصامت
    def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date):
        try:
            email_set = st.secrets["email_settings"]
            msg = MIMEMultipart()
            msg['From'] = email_set["sender_email"]; msg['To'] = to_email
            msg['Subject'] = f"🔔 إشعار سلوكي: {student_name}"
            body = get_formatted_msg(student_name, b_type, b_note, b_date)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
            server.login(email_set["sender_email"], email_set["sender_password"])
            server.send_message(msg); server.quit()
            return True
        except: return False

    st.subheader("🎭 رصد السلوك والتواصل الفوري")

    df_st = fetch_safe("students")
    all_names = df_st.iloc[:, 1].tolist() if not df_st.empty else []
    search_term = st.text_input("🔍 ابحث عن اسم الطالب لفلترة القائمة:", placeholder="اكتب اسم الطالب هنا...")
    f_names = [n for n in all_names if search_term in n] if search_term else all_names
    b_name = st.selectbox("🎯 اختر الطالب من القائمة:", [""] + f_names, key="behavior_select")

    if b_name:
        st_row = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
        s_email, s_phone = st_row[6], str(st_row[7]).split('.')[0]
        if not s_phone.startswith('966'): s_phone = '966' + s_phone
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            b_type = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
            b_date = c2.date_input("📅 التاريخ")
            b_note = st.text_area("📝 نص الملاحظة السلوكية الجديدة")
            
            st.write("✨ **خيارات الحفظ والتواصل:**")
            col1, col2 = st.columns(2)
            
            btn_save = col1.button("💾 رصد وحفظ فقط", use_container_width=True)
            btn_mail = col1.button("📧 إيميل منظم (يدوي)", use_container_width=True)
            
            btn_auto = col2.button("⚡ إشعار تلقائي (فوري)", use_container_width=True) 
            btn_wa = col2.button("💬 رصد وواتساب", use_container_width=True)     

            current_msg = get_formatted_msg(b_name, b_type, b_note, b_date)

            # منطق الحفظ
            if btn_save:
                if b_note:
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    try:
                        ws_st = sh.worksheet("students"); cell = ws_st.find(b_name)
                        p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                        curr = int(ws_st.cell(cell.row, 9).value or 0)
                        ws_st.update_cell(cell.row, 9, str(curr + p_map.get(b_type, 0)))
                    except: pass
                    st.success("✅ تم الحفظ وتحديث النقاط"); time.sleep(1); st.rerun()
                else: st.error("⚠️ يرجى كتابة نص الملاحظة أولاً")

            # منطق الواتساب
            if btn_wa and b_note:
                wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(current_msg)}"
                st.markdown(f'<script>window.open("{wa_url}", "_blank");</script>', unsafe_allow_html=True)
                st.link_button("🚀 اضغط لفتح واتساب", wa_url, use_container_width=True)

            # منطق الإيميل اليدوي
            if btn_mail and b_note and s_email:
                mail_url = f"mailto:{s_email}?subject=تقرير سلوك&body={urllib.parse.quote(current_msg)}"
                st.markdown(f'<script>window.open("{mail_url}", "_self");</script>', unsafe_allow_html=True)
                st.link_button("📧 اضغط لفتح تطبيق الإيميل يدوياً", mail_url, use_container_width=True)

            # إشعار الإيميل التلقائي
            if btn_auto and b_note and s_email:
                if send_auto_email_silent(s_email, b_name, b_type, b_note, b_date): st.success("✅ تم الإرسال")
                else: st.error("❌ فشل الإرسال")

        # --- سجل الملاحظات السابقة ---
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            st.markdown("---")
            st.markdown(f"🗓️ **سجل ملاحظات الطالب: {b_name}**")
            s_notes = df_b[df_b.iloc[:, 0] == b_name].iloc[::-1]
            for idx, row in s_notes.iterrows():
                with st.container(border=True):
                    st.markdown(f"**📅 {row[1]}** | **🏷️ {row[2]}**")
                    st.info(f"📝 {row[3]}")
                    bc1, bc2 = st.columns(2)
                    
                    old_msg = get_formatted_msg(b_name, row[2], row[3], row[1], prefix="📢 تذكير بملاحظة سابقة\n")
                    wa_old = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(old_msg)}"
                    bc1.markdown(f'<a href="{wa_old}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">💬 واتساب</div></a>', unsafe_allow_html=True)
                    
                    if bc2.button(f"🗑️ حذف الملاحظة", key=f"del_{idx}"):
                        ws_b = sh.worksheet("behavior"); cell = ws_b.find(row[3])
                        if cell: ws_b.delete_rows(cell.row); st.success("💥 تم الحذف"); time.sleep(0.5); st.rerun()

    # --- التبويب الخامس: شاشة الاختبارات (إصدار حل مشكلة العمود الرابع) ---
with tab5:
    import urllib.parse
    import time

    # 1. تثبيت تنسيقات الألوان (الأحمر للحذف)
    st.markdown("""
        <style>
            div.stButton > button[key*="del_ex_"] {
                background-color: #FF0000 !important;
                color: white !important;
                border: none !important;
            }
            .wa-btn {
                background-color: #25D366; color: white; padding: 10px;
                border-radius: 8px; text-align: center; font-weight: bold;
                text-decoration: none; display: block; width: 100%;
            }
            .link-btn {
                background-color: #4F46E5; color: white; padding: 10px;
                border-radius: 8px; text-align: center; font-weight: bold;
                text-decoration: none; display: block; width: 100%;
            }
            .ann-card {
                padding: 15px; border-radius: 10px; margin-bottom: 5px;
                border-right: 5px solid #4F46E5; background-color: #F8FAFC;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. نموذج الإضافة مع معالجة محسنة للرابط
    with st.expander("➕ إضافة تنبيه أو موعد جديد", expanded=True):
        with st.form("ann_form_final_fixed", clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            a_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            a_title = c2.text_input("📝 عنوان التنبيه / الاختبار")
            
            c3, c4 = st.columns([1, 2])
            a_date = c3.date_input("📅 التاريخ")
            a_link = c4.text_input("🔗 رابط إضافي (اختياري)", placeholder="https://example.com")
            
            btn_post = st.form_submit_button("🚀 نشر التنبيه الآن")
            
            if btn_post and a_title:
                try:
                    # إرسال البيانات كقائمة صريحة لضمان تعبئة الأعمدة الأربعة A, B, C, D
                    row_to_add = [str(a_class), str(a_title), str(a_date), str(a_link)]
                    sh.worksheet("exams").append_row(row_to_add)
                    
                    st.balloons()
                    st.success("✅ تم النشر بنجاح")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ خطأ فني: تأكد أن الشيت يحتوي على 4 أعمدة على الأقل")

    # 3. عرض التنبيهات المنشورة
    df_ann = fetch_safe("exams")
    if df_ann is not None and not df_ann.empty:
        # تحويل البيانات لنص لضمان عدم حدوث خطأ في الروابط الفارغة
        df_ann = df_ann.astype(str)
        reversed_df = df_ann.iloc[::-1]

        for index, row in reversed_df.iterrows():
            r_class, r_title, r_date = row[0], row[1], row[2]
            # التحقق من وجود العمود الرابع للرابط
            r_link = row[3] if len(row) > 3 and row[3] != 'nan' else ""
            
            # رسالة الواتساب
            link_wa = f"\n🔗 *الرابط:* {r_link}" if r_link else ""
            wa_msg = f"📢 *تنبيه من الأستاذ زياد*\n---\n🏫 *الصف:* {r_class}\n📝 *الموضوع:* {r_title}\n📅 *التاريخ:* {r_date}{link_wa}\n---\nبالتوفيق 🌟"
            encoded_msg = urllib.parse.quote(wa_msg)
            wa_url = f"https://api.whatsapp.com/send?text={encoded_msg}"

            st.markdown(f"""
                <div class="ann-card">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #666;">
                        <span>📅 {r_date}</span>
                        <span><b>{r_class}</b></span>
                    </div>
                    <h4 style="margin: 10px 0;">{r_title}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col_del, col_link, col_wa = st.columns([1, 2, 3])
            with col_del:
                if st.button("🗑️", key=f"del_ex_{index}"):
                    ws_ex = sh.worksheet("exams")
                    cell = ws_ex.find(r_title)
                    if cell:
                        ws_ex.delete_rows(cell.row)
                        st.rerun()
            
            with col_link:
                if r_link and r_link.strip():
                    st.markdown(f'<a href="{r_link}" target="_blank" class="link-btn">🔗 فتح الرابط</a>', unsafe_allow_html=True)
                else:
                    st.button("🔗 لا يوجد", disabled=True, key=f"no_lnk_{index}")
            
            with col_wa:
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

    # --- التبويب السادس: الإعدادات وإدارة البيانات ---
with tab6:
    import pandas as pd
    import io

    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
            <h2 style="margin:0;">⚙️ إعدادات المنصة المتقدمة</h2>
            <p style="margin:5px 0 0 0; opacity: 0.8;">إدارة الحساب ورفع بيانات الطلاب - الأستاذ زياد</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. قسم تغيير بيانات الدخول
    with st.expander("🔐 تغيير بيانات الحساب"):
        st.info("سيتم تحديث هذه البيانات في شيت 'users' الخاص بالدخول.")
        with st.form("update_auth_v1"):
            new_user = st.text_input("اسم المستخدم الجديد")
            new_pass = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("💾 حفظ البيانات الجديدة"):
                try:
                    ws_u = sh.worksheet("users")
                    ws_u.update_cell(2, 1, new_user)
                    ws_u.update_cell(2, 2, new_pass)
                    st.success("✅ تم تحديث بيانات الدخول. سيتم العمل بها في الدخول القادم.")
                except:
                    st.error("❌ فشل التحديث، تأكد من وجود شيت 'users'")

    # 2. قسم رفع بيانات الطلاب
    st.markdown("### 📥 إدارة بيانات الطلاب")
    col_down, col_up = st.columns(2)
    
    with col_down:
        st.markdown("#### الخطوة 1: تحميل القالب")
        st.write("حمل القالب لتعبئة بيانات الطلاب بنفس تنسيق المنصة.")
        # إنشاء قالب Excel في الذاكرة
        template_df = pd.DataFrame(columns=["الاسم", "الصف", "رقم ولي الأمر", "ملاحظات", "النقاط"])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            template_df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(
            label="📥 تحميل قالب Excel فارغ",
            data=buffer.getvalue(),
            file_name="students_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_up:
        st.markdown("#### الخطوة 2: رفع البيانات")
        st.write("ارفع ملف Excel بعد تعبئته لاستبدال قائمة الطلاب الحالية.")
        up_file = st.file_uploader("اختر ملف الطلاب", type=["xlsx"])
        
        if up_file:
            try:
                new_st_df = pd.read_excel(up_file)
                st.write("📊 معاينة أول 5 طلاب:")
                st.dataframe(new_st_df.head())
                
                if st.button("🚀 تأكيد الرفع والاستبدال"):
                    with st.spinner("جاري التحديث..."):
                        ws_st = sh.worksheet("students")
                        ws_st.clear()
                        # رفع البيانات الجديدة مع العناوين
                        ws_st.update([new_st_df.columns.values.tolist()] + new_st_df.values.tolist())
                        st.balloons()
                        st.success(f"✅ تم رفع {len(new_st_df)} طالب بنجاح!")
                        time.sleep(2)
                        st.rerun()
            except Exception as e:
                st.error(f"❌ خطأ في تنسيق الملف: {e}")

    # 3. مساحة الإجراءات السريعة
    st.markdown("---")
    with st.expander("🗑️ منطقة التحكم السريع"):
        c1, c2 = st.columns(2)
        if c1.button("🧹 مسح سجل الإعلانات"):
            sh.worksheet("exams").clear()
            sh.worksheet("exams").append_row(["الصف", "العنوان", "التاريخ", "الرابط"])
            st.success("تم تصفير شيت الإعلانات")
        
        if c2.button("🎯 تصفير نقاط جميع الطلاب"):
            # هذا الزر يحتاج حذر، سيقوم بجعل العمود التاسع (I) صفراً لكل الطلاب
            ws_st = sh.worksheet("students")
            all_data = ws_st.get_all_values()
            for i in range(2, len(all_data) + 1):
                ws_st.update_cell(i, 9, "0")
            st.warning("تم تصفير جميع النقاط")

# =========================================================
# الحل الجوهري: واجهة الطالب المعزولة والمحمية
# =========================================================

# --- بداية واجهة الطالب المدمجة والاحترافية ---
# تأكد أن السطر التالي يبدأ من أقصى اليسار تماماً
if st.session_state.get('role') == "student":
    # 1. تصميم الواجهة بهوية بصرية حديثة
    st.markdown("""
        <style>
        .student-portal {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 25px; border-radius: 15px; border-right: 10px solid #3b82f6;
            color: white; margin-bottom: 25px; box-shadow: 0 10px 15px rgba(0,0,0,0.3);
            text-align: right;
        }
        </style>
        <div class="student-portal">
            <h1 style='margin:0; font-family:Cairo; font-size:26px;'>لوحة المتابعة الذكية 🎓</h1>
            <p style='opacity:0.8;'>مرحباً بك في بوابتك التعليمية المتكاملة</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        # 2. جلب البيانات بشكل معزول وآمن
        df_students = fetch_safe("students")
        student_info = df_students[df_students.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        
        if not student_info.empty:
            s_row = student_info.iloc[0]
            s_name, s_class = s_row[1], s_row[2]
            
            # معالجة النقاط (العمود التاسع)
            raw_val = str(s_row[8]).strip() if len(s_row) >= 9 else "0"
            pts = int(float(raw_val)) if raw_val.replace('.','',1).isdigit() else 0
            
            # 3. عرض كروت الإحصائيات (Metrics)
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("🎯 مجموع نقاطك", f"{pts} نقطة")
            with c2: st.metric("🏆 رتبة الطالب", "متميز")
            with c3: st.metric("👤 الطالب", s_name)

            st.divider()
            
            # 4. حل مشكلة NameError: ننشئ تبويبات (Tabs) خاصة للطالب فقط
            # هذه التبويبات مستقلة تماماً عن متغير tab2 المسبب للخطأ
            st_tabs = st.tabs(["📊 سجل الدرجات", "🛡️ سجل السلوك", "📝 الاختبارات"])
            
            with st_tabs[0]:
                st.subheader("كشف الدرجات الأكاديمي")
                st.dataframe(fetch_safe("grades"), use_container_width=True)
            
            with st_tabs[1]:
                st.info("سجلك الدراسي حافل بالإنجازات، استمر في تميزك!")
                
            with st_tabs[2]:
                st.success("سيتم عرض روابط الاختبارات القادمة هنا فور جدولتها")
        else:
            st.error("⚠️ لم نتمكن من العثور على بياناتك، يرجى مراجعة إدارة المدرسة.")
            
    except Exception as e:
        st.error(f"حدث خطأ تقني أثناء تحميل الواجهة: {e}")

    # 5. الأمر السحري الذي يحمي تطبيقك من أي أخطاء متبقية في أسفل الملف
    st.stop()
