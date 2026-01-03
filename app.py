import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة والتصميم العام (Logo & Header)
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

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
        <h1 style="margin:0; font-size: 24px;">منصة زياد الذكية</h1>
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
# 🛠️ واجهة المعلم - النسخة الشاملة (البحث + الإدارة + التنسيقات)
# ==========================================
if st.session_state.role == "teacher":
    
    # 1. إعدادات CSS (إخفاء السايدبار + تنسيق التبويبات)
    st.markdown("""
        <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
            .stTabs [data-baseweb="tab-list"] { gap: 5px; justify-content: space-around; }
            .stTabs [data-baseweb="tab"] {
                background-color: #f8fafc; border-radius: 8px;
                padding: 10px; font-weight: bold; font-size: 0.85rem;
            }
            .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
            .stButton button { border-radius: 8px; height: 3em; font-weight: bold; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

    # 2. إنشاء التبويبات (أضفنا تبويب البحث الذكي)
    t_search, t_students, t_grades, t_behavior, t_exams, t_logout = st.tabs([
        "🔍 البحث الذكي", "👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات", "🚗 خروج"
    ])

    # --- 🔍 تبويب: البحث الذكي (كامل البيانات) ---
    with t_search:
        st.markdown("### 🔍 استعلام سريع عن طالب")
        df_st = fetch_safe("students")
        if df_st is not None and not df_st.empty:
            search_query = st.text_input("اكتب اسم الطالب للبحث السريع...")
            if search_query:
                res = df_st[df_st.iloc[:, 1].str.contains(search_query, na=False)]
                if not res.empty:
                    for _, row in res.iterrows():
                        with st.container(border=True):
                            st.markdown(f"**👤 الطالب:** {row[1]} | **🏫 الصف:** {row[2]}")
                            st.markdown(f"**🔢 الرقم:** {row[0]} | **📚 المادة:** {row[5]} | **⭐ النقاط:** {row[8]}")
                else:
                    st.warning("لم يتم العثور على نتائج.")

    # --- 👥 تبويب: إدارة الطلاب (بكامل الحقول) ---
    with t_students:
        st.markdown('<div style="background:linear-gradient(90deg,#1E3A8A,#3B82F6);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>👥 إدارة الطلاب</h1></div>', unsafe_allow_html=True)
        df_st = fetch_safe("students")
        st.write("")
        st.dataframe(df_st, use_container_width=True, hide_index=True)

        with st.form("add_student_final", clear_on_submit=True):
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
                    sh.worksheet("students").append_row([nid, nname, nclass, nyear, nstage, nsub, nmail, nphone, "0"])
                    st.success(f"✅ تم إضافة {nname} بنجاح"); time.sleep(1); st.rerun()

        st.divider()
        with st.expander("🗑️ منطقة الحذف النهائي (حذف شامل)"):
            if df_st is not None and not df_st.empty:
                del_name = st.selectbox("🎯 اختر الطالب للحذف:", [""] + df_st.iloc[:, 1].tolist(), key="del_list")
                if st.button("🚨 تنفيذ الحذف من كافة السجلات"):
                    if del_name:
                        for sheet_n in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(sheet_n)
                                cell = ws.find(del_name)
                                if cell: ws.delete_rows(cell.row)
                            except: pass
                        st.success(f"💥 تم حذف {del_name} نهائياً"); time.sleep(1); st.rerun()

    # --- 📝 تبويب: رصد الدرجات ---
    with t_grades:
        st.markdown('<div style="background:linear-gradient(90deg,#6366f1,#4338ca);padding:20px;border-radius:15px;color:white;text-align:center;"><h1>📝 رصد الدرجات</h1></div>', unsafe_allow_html=True)
        if df_st is not None and not df_st.empty:
            target_g = st.selectbox("🎯 اختر الطالب للرصد", [""] + df_st.iloc[:, 1].tolist(), key="gr_sel")
            if target_g:
                df_g = fetch_safe("grades")
                curr = df_g[df_g.iloc[:, 0] == target_g] if not df_g.empty else pd.DataFrame()
                v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
                v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
                v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
                with st.form("grade_form_pro"):
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.number_input("📉 الفترة الأولى", 0, 100, value=v1)
                    p2 = c2.number_input("📉 الفترة الثانية", 0, 100, value=v2)
                    part = c3.number_input("⭐ المشاركة", 0, 100, value=v3)
                    if st.form_submit_button("💾 حفظ الدرجات"):
                        ws = sh.worksheet("grades")
                        try:
                            cell = ws.find(target_g)
                            ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                        except: ws.append_row([target_g, p1, p2, part])
                        st.success("✅ تم تحديث الدرجات"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True, hide_index=True)

    # --- 🎭 تبويب: رصد السلوك (تنسيق الرسالة المطول) ---
   # --- القسم الثالث: رصد السلوك (النسخة الأصلية الكاملة) ---
    with t_behavior:
        import smtplib, time, urllib.parse
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # 1. دالة إرسال الإيميل التلقائي (Silent Email) كما في كودك
        def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date):
            try:
                email_set = st.secrets["email_settings"]
                msg = MIMEMultipart()
                msg['From'] = email_set["sender_email"]
                msg['To'] = to_email
                msg['Subject'] = f"🔔 إشعار سلوكي: {student_name}"
                body = (
                    f"تحية طيبة، تم رصد ملاحظة للطالب: {student_name}\n"
                    f"نوع السلوك: {b_type}\n"
                    f"الملاحظة: {b_note}\n"
                    f"التاريخ: {b_date}"
                )
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_set["sender_email"], email_set["sender_password"])
                server.send_message(msg)
                server.quit()
                return True
            except:
                return False

        st.subheader("🎭 رصد السلوك والتواصل الفوري")
        df_st = fetch_safe("students")
        all_names = df_st.iloc[:, 1].tolist()
        
        # البحث والفلترة
        search_term = st.text_input("🔍 ابحث عن اسم الطالب", key="beh_search_input")
        filtered_names = [n for n in all_names if search_term in n] if search_term else all_names
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + filtered_names, key="beh_target_select")

        if b_name:
            student_info = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email = student_info[6]
            s_phone = str(student_info[7]).split('.')[0]
            
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("🏷️ نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("📅 التاريخ", key="beh_date_pick")
                b_note = st.text_area("📝 نص الملاحظة السلوكية")
                
                # تنسيق الرسالة الموحد
                full_msg = (
                    f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {b_name}\n"
                    f"----------------------------------------\n"
                    f"🏷️ نوع السلوك: {b_type}\n"
                    f"📝 الملاحظة: {b_note}\n"
                    f"📅 التاريخ: {b_date}\n"
                    f"----------------------------------------\n"
                    f"🏛️ منصة الأستاذ زياد الذكية"
                )

                # 💡 توزيع الأزرار الأربعة كما في تصميمك الأصلي
                col1, col2 = st.columns(2)
                
                # الزر 1: حفظ فقط
                if col1.button("💾 رصد وحفظ فقط", use_container_width=True):
                    if b_note:
                        sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                        try:
                            ws_st = sh.worksheet("students")
                            cell = ws_st.find(b_name)
                            p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                            current_p = int(ws_st.cell(cell.row, 9).value or 0)
                            ws_st.update_cell(cell.row, 9, str(current_p + p_map.get(b_type, 0)))
                        except: pass
                        st.success("✅ تم الحفظ وتحديث النقاط"); time.sleep(1); st.rerun()

                # الزر 2: إشعار تلقائي صامت
                if col2.button("⚡ إشعار تلقائي (فوري)", use_container_width=True):
                    if s_email:
                        with st.spinner("جاري الإرسال..."):
                            if send_auto_email_silent(s_email, b_name, b_type, b_note, b_date):
                                st.success("✅ تم إرسال الإيميل التلقائي بنجاح")
                            else:
                                st.error("❌ فشل الإرسال التلقائي")

                # الزر 3: إيميل يدوي (Mailto)
                if col1.button("📧 إيميل منظم (يدوي)", use_container_width=True):
                    if s_email:
                        mail_url = f"mailto:{s_email}?subject=إشعار سلوكي&body={urllib.parse.quote(full_msg)}"
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={mail_url}">', unsafe_allow_html=True)

                # الزر 4: واتساب
                if col2.button("💬 رصد وواتساب", use_container_width=True):
                    wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(full_msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:8px;text-align:center;font-weight:bold;">💬 فتح واتساب</div></a>', unsafe_allow_html=True)

        # 📋 الجدول السفلي لعرض السجل (موجود كما طلبت)
        st.divider()
        df_b = fetch_safe("behavior")
        if df_b is not None and not df_b.empty:
            if b_name:
                st.markdown(f"**📋 سجل ملاحظات الطالب: {b_name}**")
                filtered_b = df_b[df_b.iloc[:, 0] == b_name].iloc[::-1, :4]
                st.dataframe(filtered_b, use_container_width=True, hide_index=True)
            else:
                st.markdown("**📋 آخر الملاحظات السلوكية العامة**")
                st.dataframe(df_b.iloc[::-1, :4].head(10), use_container_width=True, hide_index=True)
    # --- 📢 تبويب: الاختبارات ---
    with t_exams:
        st.markdown("### 📢 مركز التنبيهات")
        with st.form("exam_form_f"):
            c1, c2, c3 = st.columns([1,2,1])
            e_class = c1.selectbox("🏫 الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_title = c2.text_input("📝 عنوان التنبيه")
            e_date = c3.date_input("📅 الموعد")
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_class, e_title, str(e_date)])
                st.balloons(); st.rerun()
        
        df_ex = fetch_safe("exams")
        if df_ex is not None:
            for i, row in df_ex.iloc[::-1].iterrows():
                st.info(f"📍 {row[0]} | {row[1]} | 📅 {row[2]}")
                wa_msg_ex = f"📢 *تنبيه من منصة الأستاذ زياد*\nالصف: {row[0]}\nالموضوع: {row[1]}\nالموعد: {row[2]}"
                wa_url_ex = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg_ex)}"
                st.markdown(f'<a href="{wa_url_ex}" target="_blank" style="color:#25D366;text-decoration:none;font-weight:bold;">🔗 مشاركة عبر واتساب</a>', unsafe_allow_html=True)
                if st.button("🗑️ حذف التنبيه", key=f"del_ex_{i}"):
                    sh.worksheet("exams").delete_rows(int(i)+2); st.rerun()

    # --- 🚗 تبويب: تسجيل الخروج ---
    with t_logout:
        if st.button("🚗 تسجيل الخروج الآن"):
            st.session_state.clear(); st.rerun()
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
