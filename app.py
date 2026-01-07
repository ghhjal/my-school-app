import streamlit as st
import pandas as pd
import gspread
import urllib.parse
import datetime
import hashlib
import io
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام والاستقرار الأساسية
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_gspread_client():
    """الاتصال الآمن بقاعدة بيانات Google Sheets"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return None

# تعريف العميل الأساسي
sh = get_gspread_client()

# ==========================================
# ⚙️ تأسيس النظام وتحميل الإعدادات
# ==========================================
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
        st.session_state.current_year = str(df_sett[df_sett['key'] == 'current_year']['value'].values[0])
        
        classes_raw = str(df_sett[df_sett['key'] == 'class_list']['value'].values[0])
        st.session_state.class_options = [c.strip() for c in classes_raw.split(',')]
        
        stages_raw = str(df_sett[df_sett['key'] == 'stage_list']['value'].values[0])
        st.session_state.stage_options = [s.strip() for s in stages_raw.split(',')]
        
    except Exception as e:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        st.session_state.class_options = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"]
        st.session_state.stage_options = ["ابتدائي", "متوسط", "ثانوي"]

if "role" not in st.session_state: st.session_state.role = None
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

# ==========================================
# 🧠 2. دوال معالجة البيانات الاحترافية
# ==========================================

@st.cache_data(ttl=20)
def fetch_safe(worksheet_name):
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

def clean_phone_number(phone):
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def safe_append_row(worksheet_name, data_dict):
    try:
        ws = sh.worksheet(worksheet_name)
        headers = ws.row_values(1)
        row_to_append = [data_dict.get(h, "") for h in headers]
        ws.append_row(row_to_append)
        return True
    except Exception as e:
        st.error(f"⚠️ خطأ في الكتابة لجدول {worksheet_name}: {e}")
        return False

def get_col_idx(df, col_name):
    try: return df.columns.get_loc(col_name) + 1
    except: return None

def get_professional_msg(name, b_type, b_desc, date):
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
# 🎨 3. التصميم البصري (تحديث نظام اللوجو والهوية)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; background-color: #f8fafc; }
    
    /* تنسيق الهيدر المطور (نظام اللوجو الجانبي) */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); /* تدرج ملكي */
        padding: 40px 30px;
        border-radius: 0 0 40px 40px;
        margin: -80px -20px 35px -20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        color: white;
    }
    
    .logo-icon {
        font-size: 5.5rem;
        margin-left: 30px;
        filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3));
        animation: float 3s ease-in-out infinite;
    }

    .header-text h1 {
        margin: 0;
        font-size: 2.8rem;
        font-weight: 900;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .header-text p {
        margin: 10px 0 0 0;
        font-size: 1.2rem;
        color: #dbeafe;
        font-weight: 700;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .stMetric { background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    .footer-text { text-align: center; color: #666; padding: 20px; font-size: 0.9em; }
    </style>
    
    <div class="header-container">
        <div class="logo-icon">🎓</div>
        <div class="header-text">
            <h1>منصة الأستاذ زياد الذكية</h1>
            <p>بوابة التعليم المتطورة والإدارة الشاملة - 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# دالة عرض قنوات التواصل والحقوق (تُستدعى في الواجهة الرئيسية)
def show_footer():
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #1e40af;'>📱 قنوات التواصل والدعم الفني</h3>", unsafe_allow_html=True)
    
    col_tele, col_wa, col_mail = st.columns(3)
    with col_tele:
        st.link_button("📢 قناة تليجرام", "https://t.me/YourUsername", use_container_width=True)
    with col_wa:
        # يرجى وضع رقمك الحقيقي هنا
        st.link_button("💬 واتساب الدعم", "https://wa.me/966500000000", use_container_width=True)
    with col_mail:
        st.link_button("📧 البريد الإلكتروني", "mailto:your-email@gmail.com", use_container_width=True)
    
    st.markdown("""
        <div class="footer-text">
            <hr style="border: 0.1px solid #eee;">
            <p><strong>© 2026 جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية</strong></p>
            <p>تم التطوير بكل فخر بواسطة الأستاذ زياد</p>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# استدعاء الحقوق والتواصل في الواجهة (تظهر للجميع قبل الدخول)
# ---------------------------------------------------------
if st.session_state.role is None:
    show_footer()
# ==========================================
# 🔐 4. نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    
    with t1:
        with st.form("st_log"):
            sid_in = st.text_input("🆔 الرقم الأكاديمي (بدون مسافات)").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                if sid_in:
                    df_st = fetch_safe("students")
                    if not df_st.empty:
                        # ✨ المطابق الذكي: تنظيف المدخلات والبيانات من أي .0 أو مسافات
                        search_id = sid_in.split('.')[0]
                        df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                        
                        if search_id in df_st['clean_id'].values:
                            # ✅ توحيد اسم المتغير ليكون 'username' في الحالتين
                            st.session_state.role = "student"
                            st.session_state.username = search_id 
                            st.success("تم تسجيل الدخول بنجاح")
                            st.rerun()
                        else: st.error("عذراً، الرقم الأكاديمي غير مسجل.")
                else: st.warning("يرجى إدخال الرقم الأكاديمي أولاً.")
                
    with t2:
        with st.form("admin_log"):
            u = st.text_input("👤 اسم المستخدم (الإدارة)").strip()
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    user_data = df_u[df_u['username'] == u].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role = "teacher"
                        st.session_state.username = u
                        st.rerun()
                st.error("بيانات الدخول غير صحيحة.")
    st.stop()
    
# ==========================================
# 👨‍🏫 واجهة المعلم الرئيسية (دمج شامل ومستقر)
# ==========================================
if st.session_state.role == "teacher":
    # 1. إنشاء التبويبات الخمسة (مُزاحة بـ Tab واحدة عن الـ if)
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # ---------------------------------------------------------
    # 👥 التبويب 0: إدارة الطلاب (النسخة الشاملة والمدمجة)
    # ---------------------------------------------------------
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        df_st = fetch_safe("students") # جلب البيانات بأمان
        
        if not df_st.empty:
            # 1. شريط الإحصائيات الذكي
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            c2.metric("🏫 عدد الفصول", len(df_st.iloc[:, 2].unique()) if len(df_st.columns) > 2 else 1)
            # معالجة النقاط كأرقام للحساب
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            
            st.divider()

            # 2. نموذج إضافة طالب جديد (7 حقول كاملة مع ربط ذكي وتنسيق جوال)
            with st.expander("➕ إضافة طالب جديد (تنسيق دولي + ربط أعمدة)"):
                with st.form("add_student_v2026_final", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    f_id = col1.text_input("🔢 الرقم الأكاديمي")
                    f_name = col2.text_input("👤 الاسم الثلاثي")
                    
                    col3, col4, col5 = st.columns(3)
                    f_stage = col3.selectbox("🎓 المرحلة", st.session_state.stage_options)
                    f_year = col4.text_input("🗓️ العام الدراسي", st.session_state.current_year)
                    f_class = col5.selectbox("🏫 الصف", st.session_state.class_options)
                    
                    col6, col7 = st.columns(2)
                    f_mail = col6.text_input("📧 الإيميل")
                    f_phone_raw = col7.text_input("📱 الجوال (مثال: 05xxxx)")
                    
                    if st.form_submit_button("✅ اعتماد وحفظ الطالب"):
                        if f_id and f_name:
                            f_phone = clean_phone_number(f_phone_raw) # تنسيق 966 آلياً
                            
                            # الخريطة الذكية لمنع إزاحة الأعمدة (Mapping)
                            st_map = {
                                "id": f_id.strip(),
                                "name": f_name.strip(),
                                "class": f_class,
                                "year": f_year,
                                "sem": f_stage, # ربط المرحلة بعمود sem
                                "الإيميل": f_mail,
                                "الجوال": f_phone,
                                "النقاط": "0"
                            }
                            
                            if safe_append_row("students", st_map): # الحفظ الآمن
                                st.success(f"✅ تم حفظ الطالب {f_name} بنجاح")
                                st.cache_data.clear() # تحديث البيانات فوراً
                                st.rerun()
                        else:
                            st.warning("⚠️ يرجى إدخال البيانات الأساسية (الاسم والرقم).")

            # 3. عرض الطلاب ومحرك البحث الذكي
            st.write("---")
            sq = st.text_input("🔍 محرك البحث الذكي (اكتب اسم الطالب أو رقمه):")
            mask = df_st.iloc[:, 0].str.contains(sq) | df_st.iloc[:, 1].str.contains(sq)
            st.dataframe(df_st[mask] if sq else df_st, use_container_width=True, hide_index=True)

            # 4. منطقة الحذف والإدارة النهائية (مدمجة)
            st.divider()
            with st.expander("🗑️ منطقة الحذف والإدارة النهائية"):
                st.warning("⚠️ تنبيه: حذف الطالب نهائي ولا يمكن التراجع عنه.")
                del_q = st.text_input("ابحث عن اسم الطالب الذي تود حذفه نهائياً:", key="del_search_tab")
                
                if del_q:
                    df_del = df_st[df_st.iloc[:, 0].str.contains(del_q) | df_st.iloc[:, 1].str.contains(del_q)]
                    if not df_del.empty:
                        for idx, row in df_del.iterrows():
                            ci, ca = st.columns([3, 1])
                            ci.write(f"👤 **{row.iloc[1]}** ({row.iloc[0]})")
                            if ca.button(f"🗑️ حذف", key=f"del_btn_{idx}"):
                                try:
                                    # حذف السطر من Google Sheets (Index + 2 لضمان السطر الصحيح)
                                    sh.worksheet("students").delete_rows(int(idx) + 2)
                                    st.success(f"✅ تم حذف {row.iloc[1]} بنجاح")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ خطأ أثناء الحذف: {e}")
                    else:
                        st.info("🔎 لم يتم العثور على طالب بهذا الاسم.")
        else:
            st.info("💡 لا يوجد طلاب حالياً في قاعدة البيانات، ابدأ بإضافة الطالب الأول.")

    # ---------------------------------------------------------
    # 📊 التبويب 1: التقييم والمتابعة (النسخة الشاملة + أزرار التواصل)
    # ---------------------------------------------------------
    with menu[1]:
        st.subheader("📊 مركز التقييم والمتابعة السلوكية")
        df_eval = fetch_safe("students")
        
        if not df_eval.empty:
            # 1. اختيار الطالب
            st_list = {f"{r.iloc[1]} ({r.iloc[0]})": r.iloc[0] for _, r in df_eval.iterrows()}
            sel = st.selectbox("🎯 اختر الطالب لبدء التقييم:", [""] + list(st_list.keys()), key="eval_select_v26")
            
            if sel:
                sid = st_list[sel]
                s_info = df_eval[df_eval.iloc[:, 0] == sid].iloc[0]
                s_name = s_info.iloc[1]
                
                # جلب بيانات التواصل وتنسيقها
                cl_p = clean_phone_number(s_info['الجوال'])
                s_mail = s_info['الإيميل']

                c_g, c_b = st.columns(2)

                # --- 📝 رصد الدرجات (مشاركة واختبار) ---
                with c_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_f_v26"):
                        v_t = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0, 100)
                        v_q = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0, 100)
                        if st.form_submit_button("💾 حفظ الدرجات"):
                            if v_t <= st.session_state.max_tasks and v_q <= st.session_state.max_quiz:
                                safe_append_row("grades", {"id": sid, "tasks": v_t, "quiz": v_q, "total": v_t+v_q, "date": str(datetime.date.today())})
                                st.success("✅ تم رصد الدرجات بنجاح")
                                st.cache_data.clear()

                # --- 🎭 رصد السلوك (7 حالات) ---
                with c_b:
                    st.markdown("##### 🎭 المتابعة السلوكية")
                    with st.form("beh_f_v26", clear_on_submit=True):
                        b_type = st.selectbox("نوع السلوك:", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص قلم (-5)", "🚫 سلبي (-10)"])
                        b_msg = st.text_area("الملاحظة")
                        if st.form_submit_button("💾 تسجيل السلوك"):
                            safe_append_row("behavior", {"id": sid, "date": str(datetime.date.today()), "type": b_type, "note": b_msg})
                            st.success("✅ تم تسجيل الملاحظة وتحديث النقاط")
                            st.cache_data.clear(); st.rerun()

                # --- 📜 السجل التاريخي مع أزرار (الواتساب + الإيميل) ---
                st.divider()
                st.markdown(f"#### 📜 سجل ملاحظات الطالب: {s_name}")
                df_beh = fetch_safe("behavior")
                my_beh = df_beh[df_beh.iloc[:, 0] == sid]
                
                if not my_beh.empty:
                    for _, r in my_beh.iloc[::-1].iterrows():
                        with st.container(border=True):
                            ct, cb = st.columns([3, 1.2]) # توزيع المساحة للأزرار
                            with ct:
                                st.write(f"📅 **{r.iloc[1]}** | **{r.iloc[2]}**")
                                if r.iloc[3]: st.caption(f"📝 {r.iloc[3]}")
                            
                            with cb:
                                # توليد وتشفير الرسالة الاحترافية
                                m_enc = get_professional_msg(s_name, r.iloc[2], r.iloc[3], r.iloc[1])
                                
                                # ✅ زر الواتساب
                                st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?phone={cl_p}&text={m_enc}", use_container_width=True)
                                
                                # ✅ زر الإيميل (الذي تمت إعادته)
                                st.link_button("📧 Email", f"mailto:{s_mail}?subject=تقرير متابعة: {s_name}&body={m_enc}", use_container_width=True)
                else:
                    st.info("💡 لا توجد ملاحظات سابقة لهذا الطالب.")
        else:
            st.info("💡 لا يوجد طلاب حالياً، يرجى إضافة طلاب من التبويب الأول.")

    # ---------------------------------------------------------
    # 📢 التبويب 2: التنبيهات (بث مجموعات + عرض رئيسي)
    # ---------------------------------------------------------
    with menu[2]:
        st.subheader("📢 إدارة التنبيهات والتعميمات العامة")
        
        # 1. نموذج نشر تنبيه جديد
        with st.form("announcement_form_v2026", clear_on_submit=True):
            a_title = st.text_input("📝 عنوان التنبيه / الإعلان")
            a_details = st.text_area("📄 تفاصيل التعميم")
            
            c1, c2 = st.columns(2)
            # المميزة 1: اختيار العرض في الشاشة الرئيسية
            is_urgent = c1.checkbox("🌟 عرض في الشاشة الرئيسية (تنبيه هام)")
            a_target = c2.selectbox("🎯 الفئة المستهدفة:", ["الكل", "أولياء الأمور", "الطلاب فقط"])
            
            if st.form_submit_button("📣 نشر وبث التنبيه"):
                if a_title and a_details:
                    # تحضير البيانات للحفظ في شيت (exams)
                    ann_data = {
                        "class": a_target,
                        "title": a_title,
                        "date": str(datetime.date.today()),
                        "details": a_details,
                        "urgent": "نعم" if is_urgent else "لا"
                    }
                    if safe_append_row("exams", ann_data):
                        st.success("✅ تم النشر بنجاح في قاعدة البيانات")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.warning("⚠️ يرجى كتابة العنوان والتفاصيل.")

        # 2. عرض سجل التنبيهات مع ميزات التواصل
        st.divider()
        st.markdown("#### 📜 سجل التعميمات المرسلة")
        df_ann = fetch_safe("exams")
        
        if not df_ann.empty:
            # عرض التنبيهات من الأحدث للأقدم
            for idx, row in df_ann.iloc[::-1].iterrows():
                # تلوين التنبيه الهام لتمييزه
                border_color = "red" if str(row.get('urgent', '')) == "نعم" else "gray"
                
                with st.container(border=True):
                    col_txt, col_btn = st.columns([3, 1])
                    
                    with col_txt:
                        prefix = "🚨 **[هام]** " if str(row.get('urgent', '')) == "نعم" else "📢 "
                        st.write(f"{prefix} **{row.iloc[1]}** | 📅 {row.iloc[2]}")
                        st.caption(f"📝 {row.iloc[3]}")
                    
                    with col_btn:
                        # المميزة 2: إرسال لمجموعة الواتساب
                        # يتم تشفير الرسالة لضمان عملها كـ "بث عام" للمجموعات
                        whatsapp_msg = urllib.parse.quote(f"📢 *تنبيه من منصة زياد*\n------------------\n📌 *{row.iloc[1]}*\n📝 {row.iloc[3]}\n------------------")
                        
                        # رابط الواتساب العام (بدون رقم) يفتح قائمة الدردشات لاختيار المجموعة
                        st.link_button("👥 بث للواتساب", f"https://api.whatsapp.com/send?text={whatsapp_msg}", use_container_width=True)
                        
                        # زر الحذف
                        if st.button("🗑️ حذف", key=f"del_ann_{idx}", use_container_width=True):
                            sh.worksheet("exams").delete_rows(int(idx) + 2)
                            st.cache_data.clear()
                            st.rerun()
        else:
            st.info("💡 لا توجد تنبيهات منشورة حالياً.")

    # ---------------------------------------------------------
    # ⚙️ التبويب 3: الإعدادات والتحكم الشامل (النسخة المكتملة 2026)
    # ---------------------------------------------------------
    with menu[3]:
        st.subheader("⚙️ غرفة التحكم المتقدمة")
        
        # 1. صيانة النظام وتحديث البيانات
        with st.expander("🛠️ صيانة النظام (تحديث البيانات)"):
            if st.button("🔄 تصفير الكاش (Clear Cache)"):
                st.cache_data.clear(); st.success("✅ تم تحديث البيانات من السحابة"); st.rerun()

        # 2. تحديث قيمة الدرجات (المشاركة والاختبار)
        with st.expander("⚖️ توزيع الدرجات (تحديث الحدود القصوى)"):
            c1, c2 = st.columns(2)
            mt = c1.number_input("حد المشاركة الحالي", 0, 100, st.session_state.max_tasks)
            mq = c2.number_input("حد الاختبار الحالي", 0, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ حدود الدرجات الجديدة"):
                ws_s = sh.worksheet("settings")
                # تحديث القيم في شيت settings (يفترض أنها في السطر 2 و 3)
                ws_s.update_cell(2, 2, mt)
                ws_s.update_cell(3, 2, mq)
                st.session_state.max_tasks, st.session_state.max_quiz = mt, mq
                st.success("✅ تم تحديث توزيع الدرجات بنجاح")

        # 3. إدارة العام والصفوف والمراحل
        with st.expander("🗓️ إدارة العام والصفوف والمراحل"):
            c1, c2, c3 = st.columns(3)
            ny = c1.text_input("تعديل العام الدراسي:", st.session_state.current_year)
            cl_s = c2.text_area("قائمة الصفوف (فاصلة):", ", ".join(st.session_state.class_options))
            st_s = c3.text_area("قائمة المراحل (فاصلة):", ", ".join(st.session_state.stage_options))
            if st.button("💾 حفظ الإعدادات العامة"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(4, 2, ny); ws_s.update_cell(5, 2, cl_s); ws_s.update_cell(6, 2, st_s)
                st.success("✅ تم حفظ إعدادات الفصول بنجاح")

        # 4. تغيير كلمة المرور للمستخدم الحالي
        with st.expander("🔑 تغيير كلمة المرور الخاصة بك"):
            with st.form("change_pass_form"):
                new_p = st.text_input("كلمة المرور الجديدة", type="password")
                conf_p = st.text_input("تأكيد كلمة المرور", type="password")
                if st.form_submit_button("💾 تحديث كلمة المرور"):
                    if new_p and new_p == conf_p:
                        h_p = hashlib.sha256(str.encode(new_p)).hexdigest()
                        df_u = fetch_safe("users")
                        user_idx = df_u[df_u['username'] == st.session_state.get('username', 'admin')].index
                        if not user_idx.empty:
                            sh.worksheet("users").update_cell(int(user_idx[0]) + 2, 2, h_p)
                            st.success("✅ تم تغيير كلمة المرور بنجاح")
                    else: st.error("⚠️ كلمتا المرور غير متطابقتين!")

        # 5. إدارة المستخدمين (إضافة مستخدم جديد)
        with st.expander("🔐 إضافة مستخدم جديد للقاعدة"):
            with st.form("u_v26", clear_on_submit=True):
                u_n = st.text_input("👤 اسم المستخدم الجديد")
                u_p = st.text_input("🔑 الباسوورد", type="password")
                if st.form_submit_button("➕ إضافة المستخدم"):
                    if u_n and u_p:
                        h_p = hashlib.sha256(str.encode(u_p)).hexdigest()
                        safe_append_row("users", {"username": u_n, "password_hash": h_p, "role": "teacher"})
                        st.success(f"✅ تم إضافة {u_n} كمعلم")
                    else: st.warning("⚠️ أكمل البيانات")

        # 6. النسخ الاحتياطي والقوالب (Excel)
        with st.expander("📂 النسخ الاحتياطي وقوالب الدرجات والطلاب"):
            col_t1, col_t2 = st.columns(2)
            buf_st = io.BytesIO()
            with pd.ExcelWriter(buf_st, engine='xlsxwriter') as wr:
                pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الإيميل", "الجوال", "النقاط"]).to_excel(wr, index=False)
            col_t1.download_button("📝 تحميل قالب الطلاب", data=buf_st.getvalue(), file_name="Students_Template.xlsx")
            
            buf_gr = io.BytesIO()
            with pd.ExcelWriter(buf_gr, engine='xlsxwriter') as wr:
                pd.DataFrame(columns=["id", "tasks", "quiz", "total", "date"]).to_excel(wr, index=False)
            col_t2.download_button("📊 تحميل قالب الدرجات", data=buf_gr.getvalue(), file_name="Grades_Template.xlsx")
            
            st.divider()
            if st.button("📊 توليد نسخة احتياطية كاملة (BackUp)"):
                df_bu = fetch_safe("students")
                buf_bu = io.BytesIO()
                with pd.ExcelWriter(buf_bu, engine='xlsxwriter') as wr: df_bu.to_excel(wr, index=False)
                st.download_button("📥 تنزيل ملف Backup الطلاب", data=buf_bu.getvalue(), file_name=f"Backup_Students_{datetime.date.today()}.xlsx")

        # 7. المزامنة الذكية (حل مشكلة التكرار، الأصفار، وغياب الرسائل)
        with st.expander("📤 مزامنة وتحديث البيانات (نظام الحماية والتحقق القصوى)"):
            st.markdown("### 🛠️ معالج المزامنة المطور")
            st.info("💡 سيقوم النظام بتحديث درجات الطلاب الحاليين ومنع تكرارهم، مع تجاهل الصفوف الفارغة.")
            
            up_file = st.file_uploader("اختر ملف الإكسل المحدث (p1, p2)", type=['xlsx'], key="smart_sync_final")
            target_sheet = st.radio("حدد الجدول المطلوب تحديثه:", ["students", "grades"], horizontal=True)
            
            if st.button("🚀 بدء المزامنة والتطهير الآن", key="run_master_sync"):
                if up_file:
                    try:
                        # 1. إظهار حالة المعالجة
                        with st.status("⏳ جاري تحليل البيانات وفلترة الأصفار...", expanded=True) as status:
                            # أ. قراءة الملف وتجاهل الصفوف الفارغة تماماً
                            df_up = pd.read_excel(up_file, engine='openpyxl').fillna("")
                            df_up = df_up.dropna(how='all')
                            
                            ws = sh.worksheet(target_sheet)
                            df_current = fetch_safe(target_sheet) # جلب البيانات الحالية للمقارنة
                            headers = ws.row_values(1) # جلب رؤوس الأعمدة من قوقل شيت
                            
                            up_count = 0; new_count = 0; skip_count = 0

                            for _, row in df_up.iterrows():
                                data_dict = row.to_dict()
                                
                                # ب. تحديد الرقم الأكاديمي وتطهيره من الـ (.0)
                                id_val = str(data_dict.get('student_id', data_dict.get('id', ""))).strip()
                                if "." in id_val: id_val = id_val.split(".")[0]
                                
                                # 🛡️ صمام الأمان: تجاهل الأرقام غير الصحيحة والأصفار (حل مشكلتك)
                                if id_val in ["0", "0.0", "", "nan", "None"]:
                                    skip_count += 1
                                    continue

                                # ج. معالجة الدرجات وحساب المجموع (perf) آلياً
                                if target_sheet == "grades":
                                    p1 = pd.to_numeric(data_dict.get('p1', 0), errors='coerce') or 0
                                    p2 = pd.to_numeric(data_dict.get('p2', 0), errors='coerce') or 0
                                    data_dict.update({
                                        "student_id": id_val,
                                        "p1": str(int(p1)), "p2": str(int(p2)),
                                        "perf": str(int(p1 + p2)), # تحديث عمود perf بدلاً من total
                                        "date": str(datetime.date.today())
                                    })
                                else:
                                    data_dict['id'] = id_val

                                # د. منطق المزامنة: تحديث سطر موجود أو إضافة سطر جديد
                                if not df_current.empty and id_val in df_current.iloc[:, 0].values:
                                    # تحديث السطر الموجود فعلياً في قوقل شيت لمنع التكرار
                                    row_idx = df_current[df_current.iloc[:, 0] == id_val].index[0] + 2
                                    updated_row = [str(data_dict.get(h, "")) for h in headers]
                                    ws.update(f"A{row_idx}", [updated_row])
                                    up_count += 1
                                else:
                                    # إضافة سجل جديد تماماً
                                    new_row = [str(data_dict.get(h, "")) for h in headers]
                                    ws.append_row(new_row)
                                    new_count += 1
                            
                            status.update(label="✅ اكتملت المزامنة بنجاح!", state="complete", expanded=False)

                        # 🌟 رسالة النجاح النهائية التي تظهر للمستخدم
                        st.success(f"""
                            🏁 **تقرير العملية النهائي:**
                            * ✅ تم تحديث **{up_count}** سجل (تحديث درجات موجودة).
                            * ➕ تم إضافة **{new_count}** سجل جديد.
                            * 🚫 تم تجاهل **{skip_count}** صف (أصفار أو صفوف فارغة).
                        """)
                        st.cache_data.clear(); st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ حدث خطأ تقني: {e}")
                else:
                    st.warning("⚠️ يرجى اختيار ملف الإكسل أولاً.")
    # ------------------------------------------
    # 🚗 التبويب 4: الخروج
    # ------------------------------------------
    with menu[4]:
        if st.button("🚪 تأكيد تسجيل الخروج"):
            st.session_state.role = None; st.rerun()
# ==========================================
# 👨‍🎓 6. واجهة الطالب (النسخة الذهبية المكتملة)
# ==========================================
if st.session_state.role == "student":
    # 1. استرجاع الرقم الأكاديمي وتطهيره (الحل النهائي لمشكلة الأقواس الفارغة)
    raw_user = str(st.session_state.get('username', '')).strip()
    # تحويل 1170.0 إلى 1170 لضمان المطابقة
    student_id = raw_user.split('.')[0] if raw_user and raw_user != "None" else ""

    if not student_id:
        st.warning("⚠️ يرجى تسجيل الدخول برقمك الأكاديمي أولاً.")
        if st.button("↩️ العودة لصفحة الدخول"):
            st.session_state.role = None
            st.rerun()
    else:
        # جلب البيانات
        df_st = fetch_safe("students")
        df_gr = fetch_safe("grades")

        # البحث الذكي عن الطالب
        if not df_st.empty:
            df_st['id_clean'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
            student_row = df_st[df_st['id_clean'] == student_id]
        else: student_row = pd.DataFrame()

        if not student_row.empty:
            s_data = student_row.iloc[0]
            s_name = s_data.get('name', 'طالبنا المتميز')
            s_points = int(pd.to_numeric(s_data.get('النقاط', 0), errors='coerce') or 0)
            
            # --- التصميم العصري (نظام البطاقات) ---
            st.markdown(f"""
                <style>
                .welcome-card {{ background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px rgba(0,0,0,0.05); margin-top: -50px; border-top: 8px solid #1e3a8a; }}
                .points-section {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; border-radius: 25px; text-align: center; margin: 20px 0; }}
                .badge-box {{ background: #f8fafc; padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #e2e8f0; }}
                </style>
                <div class="welcome-card">
                    <h2 style='margin:0; color:#1e3a8a;'>👋 أهلاً بك، {s_name}</h2>
                    <p style='margin:5px 0 0 0; color:#64748b;'>🏫 الصف: {s_data.get('class', 'عام')} | 🆔 الرقم: {student_id}</p>
                </div>
                <div class="points-section">
                    <p style='margin:0; opacity: 0.9;'>رصيد نقاط التميز السلوكي</p>
                    <h1 style='margin:0; font-size: 3.8rem; font-weight: 900;'>{s_points}</h1>
                </div>
            """, unsafe_allow_html=True)

            # قسم الأوسمة
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='badge-box'>🥇<br><b style='color:{'#f59e0b' if s_points >= 100 else '#cbd5e1'}'>ذهبي</b></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='badge-box'>🥈<br><b style='color:{'#94a3b8' if s_points >= 50 else '#cbd5e1'}'>فضي</b></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='badge-box'>🥉<br><b style='color:#b45309'>برونزي</b></div>", unsafe_allow_html=True)

            # --- التبويبات المطلوبة ---
            st.divider()
            tabs = st.tabs(["📢 التنبيهات", "📝 الملاحظات", "📊 درجاتي", "🏆 المتصدرين", "⚙️ الإعدادات"])

            with tabs[0]: # التنبيهات
                st.info(f"📅 لا توجد تنبيهات جديدة للفصل الحالي {st.session_state.current_year}")

            with tabs[1]: # سجل الملاحظات
                st.markdown("### 📝 سجل ملاحظات المعلم")
                df_beh = fetch_safe("behavior")
                if not df_beh.empty:
                    df_beh['id_clean'] = df_beh.iloc[:, 0].astype(str).str.split('.').str[0]
                    my_notes = df_beh[df_beh['id_clean'] == student_id]
                    if not my_notes.empty:
                        for _, n in my_notes.iterrows():
                            st.warning(f"📍 **{n.get('type', 'تنبيه')}:** {n.get('desc', '')} ({n.get('date', '')})")
                    else: st.success("🌟 سجلك خالي من الملاحظات، استمر في تفوقك!")

            if st.session_state.role == "student":
    # استرداد الرقم الأكاديمي
    student_id = str(st.session_state.get('username', '')).strip()
    
    df_st = fetch_safe("students")
    df_gr = fetch_safe("grades")

    # تنظيف وتجهيز البحث
    df_st['id_clean'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
    my_info = df_st[df_st['id_clean'] == student_id]

    if not my_info.empty:
        s_data = my_info.iloc[0]
        st.markdown(f"### 👋 أهلاً بك: {s_data['name']}")
        
        # التبويبات
        tabs = st.tabs(["📢 التنبيهات", "📝 الملاحظات", "📊 درجاتي", "🏆 المتصدرين", "⚙️ الإعدادات"])

        with tabs[2]: # تبويب درجاتي (تعديل المسميات)
            st.markdown("#### 📊 سجل النتائج الأكاديمية")
            if not df_gr.empty:
                df_gr['id_clean'] = df_gr.iloc[:, 0].astype(str).str.split('.').str[0]
                my_grades = df_gr[df_gr['id_clean'] == student_id]
                
                if not my_grades.empty:
                    g = my_grades.iloc[0]
                    
                    # عرض الدرجات بالمسميات العربية المطلوبة
                    st.markdown(f"""
                        <style>
                        .grade-card {{ background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
                        .grade-label {{ font-weight: bold; color: #1e3a8a; }}
                        .grade-value {{ font-size: 1.5rem; color: #333; }}
                        </style>
                        
                        <div class="grade-card">
                            <span class="grade-label">📝 المشاركة والمهام (p1)</span>
                            <span class="grade-value">{g.get('p1', 0)}</span>
                        </div>
                        
                        <div class="grade-card">
                            <span class="grade-label">✍️ اختبار قصير (p2)</span>
                            <span class="grade-value">{g.get('p2', 0)}</span>
                        </div>
                        
                        <div class="grade-card" style="border-right: 5px solid #10b981;">
                            <span class="grade-label">🏆 المجموع الكلي (perf)</span>
                            <span class="grade-value" style="color: #10b981; font-weight: bold;">{g.get('perf', 0)}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("⏳ جاري رصد الدرجات حالياً.")

            with tabs[3]: # المتصدرين
                st.markdown("### 🏆 لوحة شرف المتصدرين (Top 10)")
                if not df_st.empty:
                    # تحويل النقاط لرقم لضمان الترتيب الصحيح
                    df_st['pts_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
                    top_10 = df_st.sort_values(by="pts_num", ascending=False).head(10)
                    for i, (_, row) in enumerate(top_10.iterrows(), 1):
                        st.write(f"{i}. ⭐ **{row['name']}** - {int(row['pts_num'])} نقطة")

            with tabs[4]: # الإعدادات
                st.markdown("### ⚙️ تحديث بيانات التواصل")
                with st.form("update_info"):
                    n_mail = st.text_input("📧 البريد الإلكتروني", s_data.get('الإيميل', ''))
                    n_phone = st.text_input("📱 رقم الجوال", s_data.get('الجوال', ''))
                    if st.form_submit_button("💾 حفظ البيانات"):
                        try:
                            ws_st = sh.worksheet("students")
                            # تحديد السطر الصحيح في شيت قوقل
                            ids = [str(x).split('.')[0] for x in ws_st.col_values(1)]
                            if student_id in ids:
                                r_idx = ids.index(student_id) + 1
                                ws_st.update_cell(r_idx, 6, n_mail)
                                ws_st.update_cell(r_idx, 7, n_phone)
                                st.success("✅ تم تحديث بياناتك بنجاح!")
                                st.cache_data.clear()
                        except: st.error("❌ فشل التحديث، يرجى المحاولة لاحقاً.")
        else:
            st.error(f"⚠️ الرقم ({student_id}) غير مسجل في قاعدة البيانات.")

    show_footer() # إظهار الحقوق والتواصل في الأسفل
