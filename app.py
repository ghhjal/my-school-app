import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة والتصميم العام (Logo & Header)
st.set_page_config(page_title="منصة الأستاذ زياد التعليمية", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { 
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; 
    }
    .header-box { 
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); 
        padding: 35px; border-radius: 0 0 35px 35px; color: white; text-align: center; 
        margin: -65px -20px 25px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); 
    }
    .logo-box { 
        background: rgba(255, 255, 255, 0.2); width: 65px; height: 65px; border-radius: 18px; 
        margin: 0 auto 10px auto; display: flex; justify-content: center; align-items: center; 
        border: 1px solid rgba(255, 255, 255, 0.3); 
    }
    .logo-box i { font-size: 32px; color: white; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; }
    </style>
    <div class="header-box">
        <div class="logo-box"><i class="bi bi-graph-up-arrow"></i></div>
        <h1 style="margin:0; font-size: 24px;">منصة الأستاذ زياد</h1>
        <p style="opacity: 0.8; font-size: 14px;">نظام الإدارة المدرسية المتكامل</p>
    </div>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال والبيانات
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
        
        # تحويل البيانات إلى DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # 1. حذف الأعمدة التي ليس لها اسم (تظهر كأعمدة فارغة في الإكسل)
        df = df.loc[:, df.columns != '']
        
        # 2. التعامل مع الأسماء المكررة إن وجدت بإضافة رقم بجانبها
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                cols[i] = f"{col}_{i}"
        df.columns = cols
        
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات من {worksheet_name}: {e}")
        return pd.DataFrame()

# 3. نظام الجلسات والتحقق
if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.sid = None  # لتخزين رقم الطالب الحالي

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["👨‍🎓 دخول الطالب", "👨‍🏫 دخول المعلم"])
    
    with tab1:
        sid_input = st.text_input("الرقم الأكاديمي", placeholder="ادخل رقم الهوية")
        if st.button("دخول الطالب 🚀"):
            df_st = fetch_safe("students")
            if not df_st.empty:
                df_st['id'] = df_st['id'].astype(str).str.strip()
                match = df_st[df_st['id'] == str(sid_input).strip()]
                if not match.empty:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid_input).strip()
                    st.rerun()
                else: st.error("❌ عذراً، رقم الهوية غير مسجل")

    with tab2:
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم 🔐"):
            u_df = fetch_safe("users")
            if not u_df.empty:
                user_row = u_df[u_df['username'] == u_name.strip()]
                if not user_row.empty:
                    hashed = hashlib.sha256(str.encode(u_pass)).hexdigest()
                    if hashed == user_row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"
                        st.rerun()
                    else: st.error("❌ كلمة المرور خطأ")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (كودك الأصلي)
# ==========================================
if st.session_state.role == "teacher":
    # 1. القائمة الجانبية الموحدة
    st.sidebar.markdown("### 👨‍🏫 لوحة التحكم")
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])
    st.sidebar.divider()
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))

    # --- القسم الأول: إدارة الطلاب (المطور مع خاصية الحذف الشامل) ---
    if menu == "👥 إدارة الطلاب":
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        st.write("")
        with st.container(border=True):
            st.subheader("📋 السجل الحالي للطلاب")
            st.dataframe(df_st, use_container_width=True, hide_index=True)

        # 1. نموذج إضافة طالب جديد (بالترتيب الصحيح للأعمدة)
        with st.form("add_student_pro_v3", clear_on_submit=True):
            st.markdown("### ➕ تأسيس طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            
            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة (sem)", ["ابتدائي", "متوسط", "ثانوي"])
            nsub = c5.text_input("📚 المادة (عمود F)", value="لغة إنجليزية")
            nyear = c6.text_input("🗓️ العام", value="1447هـ")
            
            c7, c8 = st.columns(2)
            nmail = c7.text_input("📧 البريد الإلكتروني")
            nphone = c8.text_input("📱 جوال ولي الأمر")
            
            if st.form_submit_button("✅ اعتماد التأسيس"):
                if nid and nname:
                    # الترتيب: ID, Name, Class, Year, Stage, Subject, Email, Phone, Points
                    row_to_add = [nid, nname, nclass, nyear, nstage, nsub, nmail, nphone, "0"]
                    sh.worksheet("students").append_row(row_to_add)
                    st.success(f"✅ تم إضافة {nname} بنجاح"); time.sleep(1); st.rerun()

        # 2. زر الحذف النهائي (الميزة الجديدة)
        st.divider()
        with st.expander("🗑️ منطقة الحذف النهائي (حذف من كافة السجلات)", expanded=False):
            st.error("⚠️ تحذير: سيتم حذف الطالب نهائياً من قائمة الطلاب والدرجات وسجل السلوك.")
            del_name = st.selectbox("🎯 اختر الطالب المراد حذفه نهائياً:", [""] + df_st.iloc[:, 1].tolist(), key="delete_list")
            
            if st.button("🚨 تنفيذ الحذف النهائي الآن"):
                if del_name:
                    try:
                        with st.spinner(f'جاري مسح كافة سجلات {del_name}...'):
                            # أ. الحذف من شيت الطلاب (students)
                            ws_st = sh.worksheet("students")
                            c_st = ws_st.find(del_name)
                            if c_st: ws_st.delete_rows(c_st.row)
                            
                            # ب. الحذف من شيت الدرجات (grades)
                            try:
                                ws_gr = sh.worksheet("grades")
                                c_gr = ws_gr.find(del_name)
                                if c_gr: ws_gr.delete_rows(c_gr.row)
                            except: pass # في حال لم تكن له درجات بعد
                            
                            # ج. الحذف من شيت السلوك (behavior) - حذف كافة الأسطر المرتبطة به
                            try:
                                ws_bh = sh.worksheet("behavior")
                                matches = ws_bh.findall(del_name)
                                # الحذف من الأسفل للأعلى لضمان عدم تغير أرقام الصفوف أثناء المسح
                                for m in reversed(matches):
                                    if m.col == 1: # التأكد أنه في عمود الاسم
                                        ws_bh.delete_rows(m.row)
                            except: pass
                            
                            st.success(f"💥 تم حذف الطالب {del_name} وكافة بياناته من جميع الجداول")
                            time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
                else:
                    st.warning("يرجى اختيار اسم الطالب أولاً")

    # --- القسم الثاني: شاشة الدرجات (تم إصلاح الخطأ هنا) ---
    elif menu == "📝 شاشة الدرجات":
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        
        df_st = fetch_safe("students")
        target = st.selectbox("🎯 اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            
            with st.form("grade_pro_form"):
                st.markdown(f"**تحديث درجات الطالب: {target}**")
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("📉 الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                
                if st.form_submit_button("💾 حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except:
                        ws.append_row([target, p1, p2, part])
                    st.success("تم الحفظ"); st.rerun()

        st.divider()
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    # --- باقي الأقسام تتبع نفس الهيكل ---
# --- القسم الثالث: رصد السلوك (إصدار الأزرار الاحترافية المستقرة) ---
    elif menu == "🎭 رصد السلوك":
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import urllib.parse 

        # دالة الإرسال التلقائي الصامت
        def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date):
            try:
                email_set = st.secrets["email_settings"]
                msg = MIMEMultipart()
                msg['From'] = email_set["sender_email"]
                msg['To'] = to_email
                msg['Subject'] = f"🔔 إشعار سلوكي فوري: {student_name}"
                
                # التنسيق المعتمد كما في الصور
                body = (
                    f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {student_name}\n"
                    f"----------------------------------------\n"
                    f"🏷️ نوع السلوك: {b_type}\n"
                    f"📝 الملاحظة: {b_note}\n"
                    f"📅 التاريخ: {b_date}\n"
                    f"----------------------------------------\n"
                    f"🏛️ منصة الأستاذ زياد الذكية"
                )
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_set["sender_email"], email_set["sender_password"])
                server.send_message(msg)
                server.quit()
                return True
            except: return False

        # عنوان الشاشة البسيط بدون بنر أزرق
        st.subheader("🎭 رصد السلوك والتواصل الفوري")

        df_st = fetch_safe("students")
        
        # محرك البحث
        search_term = st.text_input("🔍 ابحث عن اسم الطالب", placeholder="اكتب الاسم للفلترة...")
        all_names = df_st.iloc[:, 1].tolist()
        filtered_names = [name for name in all_names if search_term in name] if search_term else all_names
        b_name = st.selectbox("🎯 اختر الطالب المطلوب:", [""] + filtered_names)

        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6] 
            s_phone = str(student_info[7]).split('.')[0]
            
            # منطقة المدخلات
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("📝 نص الملاحظة السلوكية")
                
                st.markdown("---")
                st.write("✨ **خيارات الحفظ والتواصل الاحترافية:**")
                
                # تنظيم الأزرار بشكل احترافي في صفين
                col1, col2 = st.columns(2)
                
                # الصف الأول من الأزرار
                btn_save = col1.button("💾 رصد وحفظ فقط", use_container_width=True)
                btn_auto = col2.button("⚡ إشعار تلقائي (فوري)", use_container_width=True)
                
                # الصف الثاني من الأزرار
                btn_mail = col1.button("📧 إيميل منظم (يدوي)", use_container_width=True)
                btn_wa = col2.button("💬 رصد وواتساب", use_container_width=True)

                if btn_save or btn_auto or btn_mail or btn_wa:
                    if b_note:
                        # 1. عملية الحفظ (تنفذ مع أي زر)
                        sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                        try:
                            ws_st = sh.worksheet("students")
                            cell = ws_st.find(b_name)
                            p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                            current_p = int(ws_st.cell(cell.row, 9).value or 0)
                            ws_st.update_cell(cell.row, 9, str(current_p + p_map.get(b_type, 0)))
                        except: pass

                        # تنسيق الرسائل الموحد
                        full_msg = (
                            f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\n"
                            f"----------------------------------------\n"
                            f"🏷️ نوع السلوك: {b_type}\n"
                            f"📝 الملاحظة: {b_note}\n"
                            f"📅 التاريخ: {b_date}\n"
                            f"----------------------------------------\n"
                            f"🏛️ منصة الأستاذ زياد الذكية"
                        )

                        # تنفيذ الإجراءات بناءً على الزر المضغوط
                        if btn_auto:
                            if s_email:
                                with st.spinner("جاري الإرسال التلقائي..."):
                                    if send_auto_email_silent(s_email, b_name, b_type, b_note, b_date):
                                        st.success(f"✅ تم الإرسال التلقائي إلى {s_email}")
                                    else: st.error("❌ فشل الإرسال الصامت")
                            else: st.warning("⚠️ لا يوجد بريد مسجل لهذا الطالب")

                        if btn_mail and s_email:
                            mail_url = f"mailto:{s_email}?subject=تقرير سلوك: {b_name}&body={urllib.parse.quote(full_msg)}"
                            st.markdown(f'<meta http-equiv="refresh" content="0;url={mail_url}">', unsafe_allow_html=True)
                        
                        if btn_wa and s_phone:
                            encoded_msg = urllib.parse.quote(full_msg)
                            wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={encoded_msg}"
                            st.markdown(f"""
                                <div style="background-color: #f0fff4; border: 1px solid #25D366; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px;">
                                    <p style="color: #155724; font-weight: bold;">✅ تم الحفظ بنجاح</p>
                                    <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                                        <div style="background-color: #25D366; color: white; padding: 10px 20px; display: inline-block; border-radius: 8px; font-weight: bold;">
                                            💬 اضغط هنا لفتح واتساب الآن
                                        </div>
                                    </a>
                                </div>
                            """, unsafe_allow_html=True)

                        if btn_save:
                            st.success("✅ تم حفظ الملاحظة في السجل")
                    else:
                        st.error("⚠️ يرجى كتابة نص الملاحظة أولاً")

            # عرض السجل التاريخي المصغر
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                st.dataframe(df_b[df_b.iloc[:, 0] == b_name].iloc[::-1, :4], use_container_width=True, hide_index=True)

# ==========================================
# 👨‍🎓 واجهة الطالب (تم تصحيح جلب النقاط فقط)
# ==========================================
elif st.session_state.role == "student":
    # 1. جلب البيانات
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    
    # تأكد من أن البحث يتم بشكل صحيح عن الطالب
    try:
        # نبحث عن السطر الذي يحتوي على رقم الطالب في العمود الأول
        student_data = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)]
        if not student_data.empty:
            s_row = student_data.iloc[0]
            s_name, s_class = s_row[1], s_row[2]
            
            # --- الحل النهائي لمشكلة النقاط (العمود I هو فهرس 8) ---
            # نستخدم .get() أو الوصول المباشر مع التأكد من طول الصف
            if len(s_row) >= 9:
                val = str(s_row[8]).strip()
                # تحويل آمن: إذا كانت القيمة فارغة أو نصية تصبح 0
                s_points = int(float(val)) if val and val != "None" and val.replace('.','',1).isdigit() else 0
            else:
                s_points = 0
        else:
            st.error("لم يتم العثور على بيانات الطالب")
            st.stop()
    except Exception as e:
        st.error(f"خطأ في الوصول للبيانات: {e}")
        st.stop()

    # --- بقية الكود (تصميمك الأصلي للأوسمة والتبويبات) يبقى كما هو تماماً ---
    # --------------------------------------------------------

    # جلب الدرجات الأكاديمية من ورقة grades
    try:
        g_row = df_grades[df_grades.iloc[:, 0].astype(str) == s_name].iloc[0]
        p1, p2, perf = g_row[1], g_row[2], g_row[3]
    except:
        p1, p2, perf = "-", "-", "-"

    # --- 📢 شريط الإعلانات العلوي ---
    st.markdown(f"""
        <div style="background: #1e3a8a; padding: 12px; margin: -1rem -1rem 1rem -1rem; border-bottom: 5px solid #f59e0b; text-align: center;">
            <h3 style="color: white; margin: 0; font-family: 'Cairo', sans-serif;">🎯 لوحة إنجاز الطالب: {s_name}</h3>
        </div>
    """, unsafe_allow_html=True)

    # --- 👤 بطاقة الأوسمة والنقاط ---
    st.markdown(f"""
        <div style="background: white; border-radius: 15px; padding: 20px; border: 2px solid #e2e8f0; text-align: center; margin-top: 15px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                <div style="border: 3px solid #cd7f32; padding: 10px; border-radius: 15px; width: 30%; background: #fffcf9; opacity: {'1' if s_points >= 10 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥉</div><div style="font-weight: bold; color: #cd7f32; font-size: 0.8rem;">برونزي</div>
                </div>
                <div style="border: 3px solid #c0c0c0; padding: 10px; border-radius: 15px; width: 30%; background: #f8f9fa; opacity: {'1' if s_points >= 50 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥈</div><div style="font-weight: bold; color: #7f8c8d; font-size: 0.8rem;">فضي</div>
                </div>
                <div style="border: 3px solid #ffd700; padding: 10px; border-radius: 15px; width: 30%; background: #fffdf0; opacity: {'1' if s_points >= 100 else '0.2'};">
                    <div style="font-size: 1.8rem;">🥇</div><div style="font-weight: bold; color: #d4af37; font-size: 0.8rem;">ذهبي</div>
                </div>
            </div>
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); color: white; padding: 15px; border-radius: 15px;">
                <small style="font-size: 1rem;">رصيد النقاط السلوكية</small><br>
                <b style="font-size: 2.5rem;">{s_points}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات الرئيسية ---
    t_ex, t_grade, t_beh, t_set = st.tabs(["📢 التنبيهات", "📊 درجاتي", "🎭 السلوك", "⚙️ الإعدادات"])

    with t_ex:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.markdown(f"""
                    <div style="background: #002347; padding: 15px; border-radius: 12px; border-right: 8px solid #f59e0b; margin-bottom: 10px;">
                        <b style="color: #ffd700; font-size: 1.1rem;">📢 {r[1]}</b><br>
                        <span style="color: white; font-size: 0.9rem;">📅 الموعد: {r[2]}</span>
                    </div>
                """, unsafe_allow_html=True)

    with t_grade:
        st.markdown(f"""<h4 style="text-align:right; color:#1e3a8a; margin-top:10px;">📊 سجل الدرجات (p1, p2, perf)</h4>""", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">درجة المشاركة (p1)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{p1}</b>
                </div>
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">درجة الواجبات (p2)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{p2}</b>
                </div>
                <div style="background: #f0f4f8; padding: 15px; border-radius: 10px; border: 1px solid #1e3a8a; display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #1e3a8a;">الاختبارات القصيرة (perf)</b>
                    <b style="font-size: 1.3rem; color: #d97706;">{perf}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with t_beh:
        st.markdown(f"""<h4 style="text-align:right; color:#1e3a8a; margin-top:10px;">🎭 ملاحظات السلوك والانضباط</h4>""", unsafe_allow_html=True)
        df_beh = fetch_safe("behavior")
        if not df_beh.empty:
            f_beh = df_beh[df_beh.iloc[:, 0] == s_name]
            for _, r in f_beh.iloc[::-1].iterrows():
                is_pos = "+" in str(r[2])
                bg = "#f0fdf4" if is_pos else "#fef2f2"
                text_color = "#166534" if is_pos else "#991b1b"
                icon = "✅" if is_pos else "⚠️"
                
                st.markdown(f"""
                    <div style="background: {bg}; padding: 15px; border-radius: 12px; border: 1px solid {text_color}44; border-right: 8px solid {text_color}; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b style="color: {text_color};">{icon} {r[2]}</b>
                            <small style="color: #64748b;">{r[1]}</small>
                        </div>
                        <div style="margin-top: 5px; color: #475569; font-size: 0.95rem;">{r[3]}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("سجلك السلوكي نظيف حالياً")

    with t_set:
        with st.form("st_settings_final"):
            # عرض البيانات الحالية
            new_mail = st.text_input("📧 البريد الإلكتروني", value=str(s_row[6]))
            new_phone = st.text_input("📱 جوال ولي الأمر", value=str(s_row[7]))
            
            if st.form_submit_button("✅ حفظ البيانات", use_container_width=True):
                with st.spinner("جاري تحديث البيانات..."):
                    # 1. التحديث في جوجل شيت (العمود G هو 7 والعمود H هو 8)
                    ws = sh.worksheet("students")
                    cell = ws.find(st.session_state.sid)
                    ws.update_cell(cell.row, 7, new_mail)
                    ws.update_cell(cell.row, 8, new_phone)
                    
                    # 2. السر هنا: تنظيف الذاكرة المؤقتة لكي يضطر التطبيق لجلب البيانات الجديدة فوراً
                    st.cache_data.clear() 
                    
                    st.success("✅ تم تحديث بياناتك بنجاح!")
                    time.sleep(1)
                    st.rerun() # إعادة تشغيل الصفحة لعرض البيانات الجديدة

        if st.button("🚗 تسجيل الخروج", use_container_width=True):
            st.session_state.role = None
            st.rerun()
