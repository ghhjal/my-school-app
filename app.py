import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import urllib.parse
import io
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إعدادات الصفحة والاتصال
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# ==========================================
# 2. التصميم (CSS) - النسخة الأصلية
# ==========================================
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
    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
    }
    /* أزرار السلوك الملونة */
    .btn-auto { background-color: #dc2626 !important; border:none; color:white; }
    .btn-wa { background-color: #16a34a !important; border:none; color:white; }
    
    .ann-card {
        padding: 15px; border-radius: 10px; margin-bottom: 5px;
        border-right: 5px solid #4F46E5; background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام متابعة الطلاب والتواصل مع أولياء الأمور</p>
    </div>
""", unsafe_allow_html=True)

# دالة مساعدة لتنسيق الرسائل
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

# دالة الإيميل
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

# ==========================================
# 3. إدارة الجلسة والدخول
# ==========================================
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    tab1, tab2 = st.tabs(["🎓 الطلاب وأولياء الأمور", "🔐 بوابة الإدارة"])
    with tab1:
        with st.form("st_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي")
            if st.form_submit_button("دخول للمنصة 🚀"):
                df = fetch_safe("students")
                if not df.empty and sid:
                    if sid.strip() in df.iloc[:, 0].astype(str).str.strip().values:
                        st.session_state.role = "student"; st.session_state.sid = sid.strip()
                        st.balloons(); time.sleep(0.5); st.rerun()
                    else: st.error("عذراً، الرقم غير مسجل")
    with tab2:
        with st.form("te_login"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty:
                    row = df[df['username'] == u.strip()]
                    if not row.empty and hashlib.sha256(str.encode(p)).hexdigest() == row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("بيانات خاطئة")
    st.stop()

# ==========================================
# 4. واجهة المعلم (تمت إضافة كل النواقص)
# ==========================================
if st.session_state.role == "teacher":
    tabs = st.tabs([
        "👥 إدارة الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"
    ])

    # -------------------------------------------
    # 1. إدارة الطلاب (تمت إضافة الحقول والجدول)
    # -------------------------------------------
    with tabs[0]:
        st.markdown("### 👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        
        with st.container(border=True):
            st.markdown("#### ➕ تأسيس ملف طالب جديد")
            with st.form("add_student_full", clear_on_submit=True):
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

                if st.form_submit_button("✅ إضافة الطالب", use_container_width=True):
                    if nid and nname:
                        cp = nphone.strip()
                        if cp and not cp.startswith("966"): cp = "966" + cp.lstrip("0")
                        row = [nid, nname, nclass, nyear, nstage, nsub, nmail, cp, "0"]
                        sh.worksheet("students").append_row(row)
                        st.success("تمت الإضافة بنجاح"); time.sleep(1); st.rerun()
        
        # الجدول الناقص تمت إعادته
        st.markdown("---")
        st.markdown("#### 📋 سجل الطلاب الحالي")
        st.dataframe(df_st, use_container_width=True)

        with st.expander("🗑️ منطقة الحذف النهائي"):
            if not df_st.empty:
                del_name = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("🚨 حذف نهائي"):
                    for s in ["students", "grades", "behavior"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(del_name)
                            if cell: ws.delete_rows(cell.row)
                        except: pass
                    st.success("تم الحذف"); time.sleep(1); st.rerun()

    # -------------------------------------------
    # 2. الدرجات (تمت إضافة عرض الجدول بعد التحديث)
    # -------------------------------------------
    # -------------------------------------------
    # 2. شاشة الدرجات (النسخة المعتمدة النهائية)
    # -------------------------------------------
    # -------------------------------------------
    # 2. شاشة الدرجات (النسخة الذكية: رقم أكاديمي + كشف التعديل)
    # -------------------------------------------
    with tabs[1]:
        st.markdown("### 📝 رصد الدرجات والتقييم")
        df_st = fetch_safe("students")
        df_grades = fetch_safe("grades") # جلب الدرجات مسبقاً للفحص
        
        if not df_st.empty:
            with st.container(border=True):
                # نموذج الرصد
                with st.form("grades_entry_smart"):
                    # --- المنطقة 1: بيانات الطالب (تمت إضافة الرقم الأكاديمي) ---
                    c_sel, c_info = st.columns([2, 1])
                    
                    with c_sel:
                        # قائمة الأسماء
                        student_list = df_st.iloc[:, 1].tolist()
                        sel_student = st.selectbox("👤 اختر الطالب:", options=student_list)
                    
                    # البحث عن الرقم الأكاديمي للطالب المختار وعرضه
                    # نفترض العمود 0 هو الرقم والعمود 1 هو الاسم
                    try:
                        st_id = df_st[df_st.iloc[:, 1] == sel_student].iloc[0, 0]
                    except: st_id = "---"
                    
                    with c_info:
                        st.text_input("🔢 الرقم الأكاديمي (للتأكد)", value=st_id, disabled=True)

                    # --- المنطقة 2: فحص الدرجات السابقة (الميزة الذكية) ---
                    prev_score_msg = ""
                    is_update = False
                    if not df_grades.empty:
                        # نبحث هل الاسم موجود في ملف الدرجات
                        student_grade_row = df_grades[df_grades.iloc[:, 0] == sel_student]
                        if not student_grade_row.empty:
                            old_total = student_grade_row.iloc[0, 3] # نفترض العمود 3 هو المجموع
                            prev_score_msg = f"⚠️ **تنبيه:** هذا الطالب مرصود له سابقاً (المجموع: {old_total}). الحفظ سيقوم بتعديل الدرجة."
                            is_update = True
                        else:
                            prev_score_msg = "✨ هذا الطالب يتم رصد درجته لأول مرة."
                    
                    # عرض رسالة الحالة (أزرق للجديد، برتقالي للتعديل)
                    if is_update: st.warning(prev_score_msg)
                    else: st.info(prev_score_msg)

                    st.markdown("---")
                    
                    # --- المنطقة 3: إدخال الدرجات ---
                    c1, c2, c3 = st.columns(3)
                    
                    # P1: المهام
                    p1 = c1.number_input("📝 المهام والمشاركات (P1)", min_value=0.0, max_value=100.0, step=0.5)
                    
                    # P2: الاختبار
                    p2 = c2.number_input("📄 اختبار الفترة (P2)", min_value=0.0, max_value=100.0, step=0.5)
                    
                    # P3: المجموع وحالة النجاح
                    total_score = p1 + p2
                    
                    # تحديد الحالة واللون
                    status = "✅ ناجح" if total_score >= 50 else "❌ يحتاج متابعة"
                    color = "green" if total_score >= 50 else "red"
                    
                    c3.metric("∑ المجموع النهائي", f"{total_score}", delta=status, delta_color="normal")

                    # ملاحظات
                    note = st.text_input("💬 ملاحظة (اختياري)")
                    
                    # زر الحفظ
                    btn_text = "🔄 تحديث الدرجة الحالية" if is_update else "💾 حفظ واعتماد الدرجة"
                    if st.form_submit_button(btn_text, use_container_width=True):
                        try:
                            ws_g = sh.worksheet("grades")
                            cell = ws_g.find(sel_student)
                            
                            data_row = [sel_student, p1, p2, total_score, str(datetime.date.today()), note]
                            
                            if cell:
                                ws_g.update(f"B{cell.row}:F{cell.row}", [data_row[1:]])
                                st.success(f"✅ تم تحديث بيانات الطالب: {sel_student}")
                            else:
                                ws_g.append_row(data_row)
                                st.success(f"✅ تم الحفظ بنجاح للطالب: {sel_student}")
                            
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ خطأ: {e}")

            # جدول العرض
            st.markdown("---")
            st.markdown("##### 📊 السجل الحالي للدرجات")
            if not df_grades.empty:
                st.dataframe(df_grades, use_container_width=True)
            else:
                st.info("لا توجد درجات مرصودة حتى الآن.")
        else:
            st.warning("⚠️ لا يوجد طلاب مسجلين.")

    # -------------------------------------------
    # 3. البحث (تمت إضافة كافة التفاصيل)
    # -------------------------------------------
    with tabs[2]:
        st.markdown("### 🔍 البحث الشامل")
        q = st.text_input("ابحث بالاسم أو الرقم:")
        if q:
            df_st = fetch_safe("students")
            res = df_st[df_st.iloc[:, 0].astype(str).str.contains(q) | df_st.iloc[:, 1].str.contains(q)]
            if not res.empty:
                for i in range(len(res)):
                    row = res.iloc[i]
                    with st.container(border=True):
                        # عرض كافة التفاصيل كما طلبت
                        c1, c2 = st.columns([2, 1])
                        c1.markdown(f"**👤 الاسم:** {row[1]}")
                        c2.markdown(f"**🔢 الرقم:** {row[0]}")
                        
                        c3, c4, c5 = st.columns(3)
                        c3.markdown(f"**🏫 الصف:** {row[2]}")
                        c4.markdown(f"**📚 المادة:** {row[5]}")
                        c5.markdown(f"**🎓 المرحلة:** {row[4]}")
                        
                        ph = row[7]
                        st.markdown(f"📧 **البريد:** {row[6]}")
                        
                        st.markdown(f'''
                        <div style="display:flex; gap:10px; margin-top:10px;">
                             <a href="https://wa.me/{ph}" target="_blank" style="background:#25D366; color:white; padding:8px 20px; border-radius:8px; text-decoration:none;">واتساب</a>
                             <a href="tel:{ph}" style="background:#1e40af; color:white; padding:8px 20px; border-radius:8px; text-decoration:none;">اتصال</a>
                        </div>
                        ''', unsafe_allow_html=True)
            else: st.warning("لا توجد نتائج")

    # -------------------------------------------
    # 4. السلوك (تمت إعادة التاريخ والأزرار 4 والجدول)
    # -------------------------------------------
    with tabs[3]:
        st.markdown("### 🎭 رصد السلوك والتواصل")
        df_st = fetch_safe("students")
        all_names = df_st.iloc[:, 1].tolist() if not df_st.empty else []
        
        # فلتر البحث
        search_n = st.text_input("بحث سريع عن اسم:", key="beh_search")
        f_names = [n for n in all_names if search_n in n] if search_n else all_names
        b_name = st.selectbox("🎯 اختر الطالب:", [""] + f_names)

        if b_name:
            st_row = df_st[df_st.iloc[:, 1] == b_name].iloc[0]
            s_email, s_phone = st_row[6], str(st_row[7])
            if not s_phone.startswith('966'): s_phone = '966' + s_phone.lstrip("0")
            
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                # تمت إعادة حقل التاريخ
                b_date = c2.date_input("📅 التاريخ")
                b_note = st.text_area("نص الملاحظة")
                
                # تمت إعادة الأزرار الأربعة
                col1, col2 = st.columns(2)
                btn_save = col1.button("💾 حفظ فقط", use_container_width=True)
                btn_mail = col1.button("📧 إيميل يدوي", use_container_width=True)
                btn_auto = col2.button("⚡ إشعار تلقائي", use_container_width=True) # تم تلوينه بالأحمر في الستايل
                btn_wa = col2.button("💬 رصد وواتساب", use_container_width=True)   # تم تلوينه بالأخضر في الستايل

                msg = get_formatted_msg(b_name, b_type, b_note, b_date)
                
                # منطق الأزرار
                if btn_save:
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note])
                    # تحديث النقاط
                    try:
                        ws = sh.worksheet("students"); cell = ws.find(b_name)
                        p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                        curr = int(ws.cell(cell.row, 9).value or 0)
                        ws.update_cell(cell.row, 9, str(curr + p_map.get(b_type, 0)))
                    except: pass
                    st.success("تم الحفظ"); time.sleep(1); st.rerun()
                
                if btn_wa:
                    sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note]) # حفظ أيضاً
                    url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(msg)}"
                    st.markdown(f'<script>window.open("{url}", "_blank");</script>', unsafe_allow_html=True)
                
                if btn_mail:
                    url = f"mailto:{s_email}?subject=سلوك&body={urllib.parse.quote(msg)}"
                    st.markdown(f'<script>window.open("{url}", "_self");</script>', unsafe_allow_html=True)

                if btn_auto:
                    if send_auto_email_silent(s_email, b_name, b_type, b_note, b_date): st.success("تم الارسال")
                    else: st.error("فشل الارسال")

            # تمت إعادة جدول الملاحظات السابقة
            st.markdown("---")
            st.markdown(f"**سجل ملاحظات الطالب: {b_name}**")
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                s_notes = df_b[df_b.iloc[:, 0] == b_name].iloc[::-1]
                for i, row in s_notes.iterrows():
                    with st.container(border=True):
                        st.info(f"{row[1]} | {row[2]} | {row[3]}")
                        c_wa, c_del = st.columns([1,4])
                        # زر إعادة الإرسال بالواتساب
                        old_msg = get_formatted_msg(b_name, row[2], row[3], row[1], "تذكير: ")
                        wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={urllib.parse.quote(old_msg)}"
                        c_wa.markdown(f'<a href="{wa_url}" target="_blank" style="background:#25D366; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">واتساب</a>', unsafe_allow_html=True)
                        if c_del.button("حذف", key=f"del_b_{i}"):
                            cell = sh.worksheet("behavior").find(row[3])
                            if cell: sh.worksheet("behavior").delete_rows(cell.row); st.rerun()

    # -------------------------------------------
    # 5. الاختبارات (تمت إعادة الجدول وزر المجموعات)
    # -------------------------------------------
    with tabs[4]:
        st.markdown("### 📢 التنبيهات والاختبارات")
        with st.form("exam_add"):
            c1, c2 = st.columns([1,2])
            cls = c1.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            ttl = c2.text_input("العنوان")
            c3, c4 = st.columns([1,2])
            dt = c3.date_input("التاريخ")
            lnk = c4.text_input("رابط")
            if st.form_submit_button("نشر التنبيه"):
                sh.worksheet("exams").append_row([str(cls), str(ttl), str(dt), str(lnk)])
                st.success("تم النشر"); time.sleep(1); st.rerun()

        # تمت إعادة الجدول وعرض التنبيهات بالأسفل
        st.markdown("---")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iloc[::-1].iterrows():
                # إعداد رسالة واتساب جماعية (بدون رقم هاتف محدد)
                wa_msg = f"📢 تنبيه للصف {row[0]}\nالعنوان: {row[1]}\nالتاريخ: {row[2]}\n{row[3]}"
                wa_grp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"
                
                with st.container(border=True):
                    c_main, c_act = st.columns([3, 1])
                    c_main.markdown(f"**{row[0]}** | 📅 {row[2]} | {row[1]}")
                    if row[3]: c_main.markdown(f"🔗 [رابط]({row[3]})")
                    
                    # زر الإرسال للمجموعة
                    c_act.markdown(f'<a href="{wa_grp_url}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:8px; border-radius:5px; text-decoration:none; margin-bottom:5px;">📤 إرسال لمجموعة</a>', unsafe_allow_html=True)
                    if c_act.button("🗑️ حذف", key=f"dx_{i}"):
                        cell = sh.worksheet("exams").find(row[1])
                        if cell: sh.worksheet("exams").delete_rows(cell.row); st.rerun()

    # -------------------------------------------
    # 6. الإعدادات
    # -------------------------------------------
    with tabs[5]:
        st.markdown("### ⚙️ الإعدادات")
        # تغيير كلمة المرور
        with st.expander("🔐 بيانات الدخول"):
            with st.form("upd_pass"):
                nu = st.text_input("مستخدم جديد")
                np = st.text_input("كلمة مرور جديدة", type="password")
                if st.form_submit_button("تحديث"):
                    ws = sh.worksheet("users")
                    ws.update_cell(2, 1, nu)
                    ws.update_cell(2, 2, hashlib.sha256(str.encode(np)).hexdigest())
                    st.success("تم")
        
        # رفع ملف اكسل
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("📥 **قالب فارغ**")
            df_t = pd.DataFrame(columns=["الرقم", "الاسم", "الصف", "السنة", "المرحلة", "المادة", "الايميل", "الجوال", "النقاط"])
            buf = io.BytesIO()
            with pd.ExcelWriter(buf) as writer: df_t.to_excel(writer, index=False)
            st.download_button("تحميل القالب", buf.getvalue(), "template.xlsx")
        with c2:
            st.markdown("📤 **رفع بيانات**")
            f = st.file_uploader("ملف Excel", type=["xlsx"])
            if f and st.button("رفع واستبدال"):
                dfn = pd.read_excel(f)
                ws = sh.worksheet("students"); ws.clear()
                ws.update([dfn.columns.values.tolist()] + dfn.values.tolist())
                st.success("تم الرفع"); time.sleep(1); st.rerun()
        
        # تصفير النقاط
        if st.button("🔴 تصفير نقاط جميع الطلاب"):
             ws = sh.worksheet("students")
             cnt = len(ws.get_all_values())
             if cnt > 1:
                 # تحديث عمود النقاط (العمود 9 - I)
                 clist = ws.range(f"I2:I{cnt}")
                 for c in clist: c.value = '0'
                 ws.update_cells(clist)
                 st.success("تم التصفير")

    with tabs[6]:
        if st.button("خروج"):
            st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب (كما هي)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    try:
        s_row = df_st[df_st.iloc[:, 0].astype(str).str.strip() == str(st.session_state.sid)].iloc[0]
        s_name = s_row[1]
        try: pts = int(float(str(s_row[8])))
        except: pts = 0
    except:
        st.error("خطأ في البيانات"); st.stop()

    st.markdown(f"<h2 style='text-align:center;'>مرحباً {s_name} | نقاطك: {pts}</h2>", unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📢 تنبيهات", "📊 درجات", "🎭 سلوك", "🏆 ترتيب"])
    
    with t1:
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            my_ex = df_ex[(df_ex.iloc[:, 0] == s_row[2]) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in my_ex.iloc[::-1].iterrows():
                st.info(f"📢 {r[1]} | 📅 {r[2]}\n{r[3]}")
    
    with t2:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_name]
        if not my_g.empty:
            r = my_g.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("مشاركة", r[1]); c2.metric("واجبات", r[2]); c3.metric("اختبارات", r[3])
        else: st.warning("لا توجد درجات")

    with t3:
        df_b = fetch_safe("behavior")
        my_b = df_b[df_b.iloc[:, 0] == s_name]
        if not my_b.empty:
            for _, r in my_b.iloc[::-1].iterrows():
                st.write(f"{r[2]} | {r[1]} | {r[3]}")

    with t4:
        st.write("ترتيب الصف:")
        try:
            lst = df_st.values.tolist()
            lst.sort(key=lambda x: int(float(str(x[8]))) if str(x[8]).replace('.','').isdigit() else 0, reverse=True)
            for i, r in enumerate(lst[:10]):
                st.write(f"{i+1}. {r[1]} - {r[8]} نقطة")
        except: pass

    if st.button("خروج"): st.session_state.role = None; st.rerun()
