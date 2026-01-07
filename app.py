import streamlit as st
import pandas as pd
import gspread
import urllib.parse
import datetime
import hashlib
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام والاستقرار الأساسية
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من Secrets.")
        return None

sh = get_gspread_client()

# ==========================================
# ⚙️ تأسيس النظام وتحميل الإعدادات (حل مشكلة اللاق)
# ==========================================
if "max_tasks" not in st.session_state:
    try:
        # قراءة ورقة الإعدادات مرة واحدة لضمان السرعة
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        
        # 1. تحميل توزيع الدرجات
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
        
        # 2. تحميل العام الدراسي الحالي
        st.session_state.current_year = str(df_sett[df_sett['key'] == 'current_year']['value'].values[0])
        
        # 3. تحميل قائمة الصفوف الديناميكية
        classes_raw = str(df_sett[df_sett['key'] == 'class_list']['value'].values[0])
        st.session_state.class_options = [c.strip() for c in classes_raw.split(',')]
        
        # 4. تحميل قائمة المراحل الدراسية
        stages_raw = str(df_sett[df_sett['key'] == 'stage_list']['value'].values[0])
        st.session_state.stage_options = [s.strip() for s in stages_raw.split(',')]
        
    except Exception as e:
        # صمام أمان: تفعيل القيم الافتراضية في حال تعطل الربط
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        st.session_state.class_options = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"]
        st.session_state.stage_options = ["ابتدائي", "متوسط", "ثانوي"]

# تهيئة متغيرات الجلسة الأساسية
if "role" not in st.session_state: st.session_state.role = None
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

# ==========================================
# 🧠 2. دوال معالجة البيانات الاحترافية
# ==========================================

@st.cache_data(ttl=20)
def fetch_safe(worksheet_name):
    """جلب البيانات مع ضمان تحويل المعرف (ID) لنص لمنع الانهيار"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty: 
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: 
        return pd.DataFrame()

# 📱 دالة تنظيف وتنسيق رقم الجوال (966)
def clean_phone_number(phone):
    """تنظيف رقم الجوال: إزالة الصفر، المسافات، وإضافة 966"""
    p = str(phone).strip().replace(" ", "")
    # إزالة الصفر من البداية إن وجد
    if p.startswith("0"):
        p = p[1:]
    # إضافة 966 إذا لم تكن موجودة وكان الحقل غير فارغ
    if not p.startswith("966") and p != "":
        p = "966" + p
    return p

# 🌟 الدالة الأهم: منع إزاحة الأعمدة (Mapping System)
def safe_append_row(worksheet_name, data_dict):
    """تضمن إرسال كل بيان للعمود الصحيح بناءً على اسمه في الإكسل"""
    try:
        ws = sh.worksheet(worksheet_name)
        headers = ws.row_values(1) # قراءة الرؤوس الفعلية من ملفك
        # بناء السطر بترتيب يطابق الملف تماماً لمنع الإزاحة
        row_to_append = [data_dict.get(h, "") for h in headers]
        ws.append_row(row_to_append)
        return True
    except Exception as e:
        st.error(f"⚠️ خطأ في جدول {worksheet_name}: {e}")
        return False

def get_col_idx(df, col_name):
    """إيجاد رقم العمود ديناميكياً بناءً على اسمه"""
    try: 
        return df.columns.get_loc(col_name) + 1
    except: 
        return None

def get_professional_msg(name, b_type, b_desc, date):
    """تنسيق رسالة الواتساب بترميز آمن لضمان سلامة اللغة العربية"""
    msg = (f"🔔 *إشعار من منصة الأستاذ زياد*\n"
           f"------------------\n"
           f"👤 *الطالب:* {name}\n"
           f"📍 *الملاحظة:* {b_type}\n"
           f"📝 *التفاصيل:* {b_desc if b_desc else 'متابعة دورية'}\n"
           f"📅 *التاريخ:* {date}\n"
           f"------------------\n"
           f"🏛️ *منصة زياد الذكية*")
    return urllib.parse.quote(msg)
# ==========================================
# 🎨 3. التصميم البصري (RTL + Cairo Font)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin: -80px -20px 25px -20px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .stMetric { background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    </style>
    <div class="header-section"><h1>🏛️ منصة زياد الذكية</h1><p>الإصدار الإداري الشامل والمستقر - 2026</p></div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 4. نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    with t1:
        with st.form("st_log"):
            sid_in = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid_in in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid_in; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل.")
    with t2:
        with st.form("admin_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    user_data = df_u[df_u['username']==u.strip()].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role = "teacher"; st.session_state.username = u.strip(); st.rerun()
                st.error("بيانات الدخول غير صحيحة.")
    st.stop()

# ==========================================
# 👨‍🏫 5. واجهة المعلم (المكتملة بدون نقصان)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # ==========================================
# 👥 الوحدة 2: تبويب إدارة الطلاب (الإصدار الشامل)
# ==========================================
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # 1. شريط الإحصائيات الذكي
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            c2.metric("🏫 عدد الفصول", len(df_st.iloc[:, 2].unique()) if len(df_st.columns) > 2 else 1)
            # تحويل النقاط لرقم لضمان دقة المتوسط
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            
            st.divider()
    
            with st.expander("➕ إضافة طالب جديد (تنسيق الجوال آلي)"):
                with st.form("add_st_final_v5", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    f_id = col1.text_input("🔢 الرقم الأكاديمي")
                    f_name = col2.text_input("👤 الاسم الثلاثي")
                    col3, col4, col5 = st.columns(3)
                    f_stage = col3.selectbox("🎓 المرحلة", st.session_state.stage_options)
                    f_year = col4.text_input("🗓️ العام", st.session_state.current_year)
                    f_class = col5.selectbox("🏫 الصف", st.session_state.class_options)
                    f_mail = st.text_input("📧 الإيميل")
                    f_phone_raw = st.text_input("📱 الجوال (مثال: 05xxxx)")
                    
                    if st.form_submit_button("✅ حفظ"):
                        # ✅ تنظيف الرقم قبل الحفظ
                        f_phone = clean_phone_number(f_phone_raw)
                        st_data = {
                            "id": f_id.strip(), "name": f_name.strip(), 
                            "class": f_class, "year": f_year, "sem": f_stage, 
                            "الإيميل": f_mail, "الجوال": f_phone, "النقاط": "0"
                        }
                        if safe_append_row("students", st_data):
                            st.success(f"✅ تم الحفظ بالرقم الدولي: {f_phone}")
                            st.cache_data.clear(); st.rerun()

    # 3. محرك البحث الذكي (الاسم أو الرقم)
    sq = st.text_input("🔍 ابحث عن طالب محدد:")
    df_disp = df_st[df_st.iloc[:, 0].str.contains(sq) | df_st.iloc[:, 1].str.contains(sq)] if sq else df_st
    
    # عرض الجدول بشكل احترافي
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
else:
    st.info("💡 لا يوجد طلاب حالياً، ابدأ بإضافة الطالب الأول.")

    # ==========================================
    # 📊 تبويب: التقييم والمتابعة (الإصدار الشامل والمصحح)
    # ==========================================
    with menu[1]:
        st.subheader("📊 مركز التقييم والمتابعة السلوكية")
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # 1. اختيار الطالب
            st_list = {f"{row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected_label = st.selectbox("🎯 اختر الطالب لبدء التقييم:", [""] + list(st_list.keys()))
            
            if selected_label:
                sid = st_list[selected_label]
                s_info = df_st[df_st.iloc[:, 0] == sid].iloc[0]
                s_name = s_info.iloc[1]
                
                # تنظيف رقم الجوال فوراً لاستخدامه في الروابط
                clean_p = clean_phone_number(s_info['الجوال'])
                s_email = s_info['الإيميل']
    
                col_grades, col_behavior = st.columns(2)
    
                # --- 📝 رصد الدرجات (مقيد بالحدود الدائمة) ---
                with col_grades:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_form_vFinal"):
                        v_tasks = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0, 100)
                        v_quiz = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0, 100)
                        if st.form_submit_button("💾 حفظ"):
                            if v_tasks <= st.session_state.max_tasks and v_quiz <= st.session_state.max_quiz:
                                safe_append_row("grades", {"id": sid, "tasks": v_tasks, "quiz": v_quiz, "total": v_tasks+v_quiz, "date": str(datetime.date.today())})
                                st.success("✅ تم الحفظ"); st.cache_data.clear()
                            else: st.error("⚠️ تجاوزت الحد المسموح!")
    
                # --- 🎭 رصد السلوك (القائمة الكاملة 7 حالات) ---
                with col_behavior:
                    st.markdown("##### 🎭 المتابعة السلوكية")
                    with st.form("beh_form_vFinal", clear_on_submit=True):
                        b_date = st.date_input("🗓️ التاريخ", datetime.date.today())
                        b_type = st.selectbox("نوع السلوك:", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص قلم (-5)", "🚫 سلبي (-10)"])
                        b_desc = st.text_area("الملاحظة")
                        if st.form_submit_button("💾 تسجيل وتحديث النقاط"):
                            safe_append_row("behavior", {"id": sid, "date": str(b_date), "type": b_type, "note": b_desc})
                            # تحديث النقاط في شيت الطلاب تلقائياً
                            p_map = {"متميز": 10, "إيجابي": 5, "كتاب": -5, "واجب": -5, "قلم": -5, "سلبي": -10}
                            change = next((v for k, v in p_map.items() if k in b_type), 0)
                            row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                            sh.worksheet("students").update_cell(row_idx, df_st.columns.get_loc("النقاط")+1, str(int(float(s_info['النقاط'])) + change))
                            st.success("✅ تم التسجيل"); st.cache_data.clear(); st.rerun()
    
                # --- 📜 السجل التاريخي (هذا هو الكود الذي سألت عنه مدمجاً بالأزرار) ---
                st.divider()
                st.markdown(f"#### 📜 سجل ملاحظات الطالب: {s_name}")
                df_beh = fetch_safe("behavior")
                my_beh = df_beh[df_beh.iloc[:, 0] == sid]
                
                if not my_beh.empty:
                    for idx, r in my_beh.iloc[::-1].iterrows():
                        with st.container(border=True):
                            c_info, c_actions = st.columns([3, 1])
                            with c_info:
                                st.write(f"📅 **{r.iloc[1]}** | **{r.iloc[2]}**")
                                if r.iloc[3]: st.caption(f"📝 {r.iloc[3]}")
                            
                            with c_actions:
                                # توليد الرسالة المشفرة لكل سطر بناءً على ملاحظته
                                msg_enc = get_professional_msg(s_name, r.iloc[2], r.iloc[3], r.iloc[1])
                                st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?phone={clean_p}&text={msg_enc}", use_container_width=True)
                                st.link_button("📧 Email", f"mailto:{s_email}?subject=تقرير&body={msg_enc}", use_container_width=True)
                else:
                    st.info("💡 لا توجد ملاحظات مسجلة لهذا الطالب.")
                    #...........#
    with menu[2]: # 📢 تبويب التنبيهات (الذي سقط سهواً - عاد بكامل ميزاته)
        st.subheader("📢 إدارة وبث التنبيهات")
        with st.expander("🚀 نشر تنبيه جديد", expanded=True):
            with st.form("ann_form_complete", clear_on_submit=True):
                a_title = st.text_input("📝 عنوان التنبيه")
                a_target = st.selectbox("🎯 الفئة", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                a_body = st.text_area("📄 التفاصيل / الروابط")
                a_home = st.checkbox("🌟 عرض في الرئيسية؟")
                if st.form_submit_button("📣 نشر الآن للمنصة"):
                    if a_title:
                        sh.worksheet("exams").append_row([a_target, a_title, str(datetime.date.today()), a_body, "نعم" if a_home else "لا"])
                        st.success("✅ تم النشر"); st.cache_data.clear(); st.rerun()

        st.divider()
        st.markdown("##### 📜 سجل التنبيهات المنشورة")
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for idx, row in df_ex.iloc[::-1].iterrows():
                with st.container(border=True):
                    st.write(f"**[{row.iloc[0]}]** - **{row.iloc[1]}**")
                    msg_wa = urllib.parse.quote(f"📢 *تنبيه من منصة الأستاذ زياد*\n📝 {row.iloc[1]}\n📍 {row.iloc[3]}")
                    c_wa, c_del = st.columns([3, 1])
                    c_wa.link_button("👥 إرسال لمجموعة واتساب", f"https://api.whatsapp.com/send?text={msg_wa}", use_container_width=True)
                    if c_del.button("🗑️ حذف", key=f"del_{idx}"):
                        sh.worksheet("exams").delete_rows(int(idx) + 2)
                        st.cache_data.clear(); st.rerun()

    with menu[3]:
        st.subheader("⚙️ مركز التحكم وإدارة النظام")
        
        # 1. إدارة توزيع الدرجات (حفظ دائم)
        with st.expander("⚖️ توزيع الدرجات السنوي", expanded=False):
            c1, c2 = st.columns(2)
            nt = c1.number_input("حد المشاركة والمهام", 1, 100, st.session_state.max_tasks)
            nq = c2.number_input("حد الاختبار القصير", 1, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ توزيع الدرجات نهائياً"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, nt); ws_s.update_cell(3, 2, nq)
                st.session_state.max_tasks, st.session_state.max_quiz = nt, nq
                st.success("✅ تم تحديث توزيع الدرجات في القاعدة.")
    
        # 2. إدارة العام والصفوف والمراحل
        with st.expander("🗓️ إدارة العام الدراسي والصفوف والمراحل"):
            c1, c2, c3 = st.columns(3)
            new_year = c1.text_input("العام الدراسي الحالي:", st.session_state.current_year)
            
            # تعديل القوائم عبر نص مفصول بفاصلة
            classes_str = c2.text_area("قائمة الصفوف (افصل بفاصلة):", ", ".join(st.session_state.class_options))
            stages_str = c3.text_area("قائمة المراحل (افصل بفاصلة):", ", ".join(st.session_state.stage_options))
            
            if st.button("💾 حفظ إعدادات القوائم"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(4, 2, new_year) # current_year
                ws_s.update_cell(5, 2, classes_str) # class_list
                ws_s.update_cell(6, 2, stages_str) # stage_list
                st.success("✅ تم تحديث القوائم بنجاح. (يرجى إعادة تحميل الصفحة)")
    
        # 3. إدارة المستخدمين (إضافة مع تشفير الباسوورد)
        with st.expander("🔐 إدارة الوصول (إضافة مستخدم جديد)"):
            with st.form("add_user_form", clear_on_submit=True):
                new_u = st.text_input("👤 اسم المستخدم الجديد")
                new_p = st.text_input("🔑 كلمة المرور", type="password")
                u_role = st.selectbox("📌 الصلاحية", ["teacher", "admin"])
                if st.form_submit_button("➕ إضافة المستخدم للقاعدة"):
                    if new_u and new_p:
                        # تشفير كلمة المرور قبل الحفظ للأمان
                        h_pass = hashlib.sha256(str.encode(new_p)).hexdigest()
                        if safe_append_row("users", {"username": new_u, "password_hash": h_pass, "role": u_role}):
                            st.success(f"✅ تم إضافة المستخدم {new_u} بنجاح.")
                    else: st.warning("⚠️ يرجى تعبئة كافة الحقول.")
    
        # 4. إدارة البيانات (نسخ احتياطي + قوالب فارغة)
        with st.expander("📂 إدارة البيانات (إكسل)"):
            st.write("📥 **تحميل قوالب إكسل فارغة (للرفع الجديد):**")
            # إنشاء ملف إكسل فارغ في الذاكرة
            buffer_tpl = io.BytesIO()
            with pd.ExcelWriter(buffer_tpl, engine='xlsxwriter') as writer:
                pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الإيميل", "الجوال", "النقاط"]).to_excel(writer, index=False)
            st.download_button("📝 تحميل قالب بيانات الطلاب", data=buffer_tpl.getvalue(), file_name="students_template.xlsx", mime="application/vnd.ms-excel")
    
            st.divider()
            st.write("📤 **نسخة احتياطية من البيانات الحالية:**")
            if st.button("📊 توليد ملف النسخة الاحتياطية (BackUp)"):
                df_backup = fetch_safe("students")
                buffer_bu = io.BytesIO()
                with pd.ExcelWriter(buffer_bu, engine='xlsxwriter') as writer:
                    df_backup.to_excel(writer, index=False)
                st.download_button("📥 تنزيل سجل الطلاب الحالي", data=buffer_bu.getvalue(), file_name=f"Backup_Students_{datetime.date.today()}.xlsx")
    
        # 5. صيانة النظام (تصفير الكاش)
        with st.expander("🛠️ صيانة النظام"):
            st.warning("تصفير الكاش سيقوم بإعادة جلب كافة البيانات من Google Sheets (يحل مشكلة عدم ظهور التحديثات).")
            if st.button("🔄 تصفير الكاش وتحديث البيانات (Clear Cache)"):
                st.cache_data.clear()
                st.success("✅ تم تصفير الكاش بنجاح!")
                st.rerun()

    with menu[4]:
        if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 6. واجهة الطالب (النسخة الذهبية المكتملة)
# ==========================================
if st.session_state.role == "student":
    df_s = fetch_safe("students"); df_g = fetch_safe("grades")
    df_ex = fetch_safe("exams"); s_id = st.session_state.sid
    s_row = df_s[df_s.iloc[:, 0] == s_id].iloc[0]
    
    st.markdown(f"<div class='header-section'><h2>🎯 مرحباً: {s_row.iloc[1]}</h2>🏆 نقاطك: {s_row['النقاط']} | 🏫 {s_row.iloc[4]}</div>", unsafe_allow_html=True)
    t_ex, t_grade, t_beh, t_lead = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال"])

    with t_ex: # التنبيهات المفلترة
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_row.iloc[4]) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            with st.container(border=True):
                st.markdown(f"### 📍 {r[1]}"); st.write(r[3])

    with t_grade: # الترتيب والدرجات
        my_g = df_g[df_g.iloc[:, 0] == s_id]
        if not my_g.empty:
            df_rank = df_g.copy(); df_rank.iloc[:, 3] = pd.to_numeric(df_rank.iloc[:, 3], errors='coerce').fillna(0)
            df_sorted = df_rank.sort_values(by=df_rank.columns[3], ascending=False).reset_index(drop=True)
            rank = df_sorted[df_sorted.iloc[:, 0] == s_id].index[0] + 1
            c1, c2, c3 = st.columns(3)
            c1.metric("📚 المشاركة", f"{my_g.iloc[0, 1]} / {st.session_state.max_tasks}")
            c2.metric("📝 الاختبار", f"{my_g.iloc[0, 2]} / {st.session_state.max_quiz}")
            c3.metric("🏆 المجموع", f"{my_g.iloc[0, 3]} / 100")
            st.success(f"🥇 ترتيبك: {rank} من {len(df_sorted)}")

    if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()
