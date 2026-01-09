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

# تعريف الدوال الأساسية في البداية لتجنب أخطاء NameError
def clean_phone_number(phone):
    """تجهيز رقم الجوال للتواصل"""
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def show_footer():
    """عرض قنوات التواصل والحقوق في أسفل الصفحة"""
    st.markdown("<br><h3 style='text-align:center; color:#1e40af;'>📱 قنوات التواصل والدعم الفني</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown('<a href="#" class="contact-btn">📢 تليجرام الإدارة 👉</a>', unsafe_allow_html=True)
    c2.markdown('<a href="#" class="contact-btn">💬 واتساب المعلم 👉</a>', unsafe_allow_html=True)
    c3.markdown('<a href="#" class="contact-btn">📧 البريد الإلكتروني 👉</a>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:0.8rem; margin-top:20px;'>© 2026 جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية</p>", unsafe_allow_html=True)

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_gspread_client()

# تحميل الإعدادات وتأسيس الـ Session State
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
        st.session_state.current_year = str(df_sett[df_sett['key'] == 'current_year']['value'].values[0])
        st.session_state.class_options = [c.strip() for c in str(df_sett[df_sett['key'] == 'class_list']['value'].values[0]).split(',')]
        st.session_state.stage_options = [s.strip() for s in str(df_sett[df_sett['key'] == 'stage_list']['value'].values[0]).split(',')]
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year, st.session_state.class_options, st.session_state.stage_options = "1447هـ", ["الأول", "الثاني"], ["ابتدائي"]

if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = None

# ==========================================
# 🧠 2. دوال معالجة البيانات
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
    except: return pd.DataFrame()

def safe_append_row(worksheet_name, data_dict):
    try:
        ws = sh.worksheet(worksheet_name)
        headers = ws.row_values(1)
        ws.append_row([data_dict.get(h, "") for h in headers])
        return True
    except: return False

# ==========================================
# 🎨 3. التصميم البصري (تصحيح الهيدر والحقول)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; background-color: #f8fafc; }
    
    .block-container { padding-top: 1rem; }

    /* ✅ تحسين موقع القبعة: إنزال الهيدر قليلاً لتظهر بوضوح */
    .header-container {
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px 20px; border-radius: 0 0 40px 40px; 
        margin: -20px -20px 25px -20px; 
        box-shadow: 0 15px 20px rgba(0,0,0,0.15); color: white;
    }
    .logo-icon { 
        font-size: 5rem; margin-left: 20px; 
        filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3));
        animation: float 3s ease-in-out infinite; 
    }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

    /* ✅ تمييز مكان إدخال البيانات والباسوورد بلون سماوي واضح */
    div[data-baseweb="input"] {
        background-color: #e0f2fe !important; 
        border: 2px solid #0284c7 !important; 
        border-radius: 12px !important;
    }
    input { color: #0c4a6e !important; font-weight: bold !important; }

    /* أزرار التواصل والحقوق */
    .contact-btn { display: inline-block; padding: 12px; background: white; border: 2px solid #e2e8f0; border-radius: 12px; color: #1e3a8a !important; text-decoration: none; font-weight: bold; text-align: center; width: 100%; transition: 0.3s; }
    .contact-btn:hover { background: #eff6ff; border-color: #3b82f6; transform: translateY(-3px); }
    </style>

    <div class="header-container">
        <div class="logo-icon">🎓</div>
        <div class="header-text" style="text-align:right;">
            <h1 style="margin:0; font-size:2.4rem; font-weight:900;">منصة الأستاذ زياد الذكية</h1>
            <p style="margin:5px 0 0 0; color:#dbeafe; font-size:1.1rem;">بوابة التعليم المتطورة والإدارة الشاملة - 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 4. نظام تسجيل الدخول الموحد
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 لوحة تحكم المعلم"])
    with t1:
        st.markdown("<h4 style='text-align:center; color:#1e3a8a;'>أهلاً بك يا بطل.. سجل دخولك برقمك الأكاديمي</h4>", unsafe_allow_html=True)
        with st.form("st_log_v2026"):
            sid_in = st.text_input("🔢 الرقم الأكاديمي الموحد").strip()
            if st.form_submit_button("انطلق للمنصة 🚀", use_container_width=True):
                df_st = fetch_safe("students")
                if not df_st.empty:
                    df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                    if sid_in.split('.')[0] in df_st['clean_id'].values:
                        st.session_state.username = sid_in.split('.')[0]; st.session_state.role = "student"; st.rerun()
                    else: st.error("❌ الرقم غير مسجل. تواصل مع معلمك.")
    with t2:
        st.markdown("<h4 style='text-align:center; color:#1e3a8a;'>🔐 تسجيل دخول الإدارة</h4>", unsafe_allow_html=True)
        with st.form("admin_log_v2026"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("دخول الإدارة 🛠️", use_container_width=True):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    user_data = df_u[df_u['username']==u].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role = "teacher"; st.session_state.username = u; st.rerun()
                st.error("❌ بيانات الدخول خاطئة.")
    show_footer()

# (هنا يتم دمج واجهة الطالب والمعلم كما في الأكواد السابقة...)
    
# ==========================================
# 👨‍🏫 واجهة المعلم الرئيسية (دمج شامل ومستقر)
# ==========================================
if st.session_state.role == "teacher":
    # 1. إنشاء التبويبات الخمسة (مُزاحة بـ Tab واحدة عن الـ if)
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])
         
    # ---------------------------------------------------------
    # 👥 التبويب 0: إدارة قاعدة بيانات الطلاب (الإصدار المصحح والمستقر)
    # ---------------------------------------------------------
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        df_st = fetch_safe("students") 
        
        if not df_st.empty:
            # 🛡️ ضمان وجود عمود التطهير لتجنب KeyError
            df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
            
            # 1. شريط الإحصائيات الذكي
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            unique_classes = len(df_st.iloc[:, 2].unique()) if len(df_st.columns) > 2 else 1
            c2.metric("🏫 عدد الفصول النشطة", unique_classes)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            
            st.divider()
    
            # 2. نموذج إضافة طالب جديد (الربط الديناميكي)
            with st.expander("➕ إضافة طالب جديد (تنسيق ديناميكي)"):
                with st.form("add_student_v2026_final", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    f_id = col1.text_input("🔢 الرقم الأكاديمي")
                    f_name = col2.text_input("👤 الاسم الثلاثي")
                    
                    col3, col4, col5 = st.columns(3)
                    f_stage = col3.selectbox("🎓 المرحلة", st.session_state.get('stage_options', ['ابتدائي']))
                    f_year = col4.text_input("🗓️ العام الدراسي", st.session_state.get('current_year', '1447هـ'))
                    f_class = col5.selectbox("🏫 الصف", st.session_state.get('class_options', ['الأول']))
                    
                    if st.form_submit_button("✅ اعتماد وحفظ الطالب"):
                        if f_id and f_name:
                            f_phone = clean_phone_number(st.text_input("📱 الجوال")) 
                            st_map = {"id": f_id.strip(), "name": f_name.strip(), "class": f_class, "year": f_year, "sem": f_stage, "النقاط": "0"}
                            if safe_append_row("students", st_map):
                                st.success(f"✅ تم إضافة {f_name}")
                                st.cache_data.clear(); st.rerun()
                        else: st.warning("⚠️ يرجى إكمال الاسم والرقم.")
    
            # 3. عرض الطلاب ومحرك البحث الذكي (يجب أن يكون داخل الـ IF)
            st.write("---")
            sq = st.text_input("🔍 محرك البحث الذكي (اكتب اسم الطالب أو رقمه):")
            mask = df_st.iloc[:, 0].astype(str).str.contains(sq) | df_st.iloc[:, 1].astype(str).str.contains(sq)
            st.dataframe(df_st[mask] if sq else df_st, use_container_width=True, hide_index=True)
    
            # 4. منطقة الحذف والإدارة
            with st.expander("🗑️ منطقة الحذف والإدارة النهائية"):
                st.warning("⚠️ تنبيه: الحذف نهائي.")
                del_q = st.text_input("ابحث عن الطالب لحذفه:", key="del_search_main")
                if del_q:
                    df_del = df_st[df_st.iloc[:, 0].astype(str).str.contains(del_q) | df_st.iloc[:, 1].astype(str).str.contains(del_q)]
                    for idx, row in df_del.iterrows():
                        ci, ca = st.columns([3, 1])
                        ci.write(f"👤 {row.iloc[1]} ({row.iloc[0]})")
                        if ca.button(f"🗑️ حذف", key=f"del_final_{idx}"):
                            sh.worksheet("students").delete_rows(int(idx) + 2)
                            st.cache_data.clear(); st.rerun()
    
        # 🏁 سطر الـ else متموضع بشكل صحيح الآن في نهاية التبويب
        else:
            st.warning("⚠️ قاعدة بيانات الطلاب فارغة حالياً.")
            if st.button("🔄 تحديث الشاشة"): st.rerun()
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
# ==========================================
# 👨‍💼 6. واجهة المعلم (الإدارة والتحكم الشامل)
# ==========================================
elif st.session_state.role == "teacher":
    # تعريف التبويبات (يجب أن يتم تعريفها مرة واحدة فقط)
    menu = st.tabs(["👥 الطلاب", "📊 الدرجات", "📢 التنبيهات", "⚙️ الإعدادات"])
    
    # --- التبويب 0: إدارة الطلاب (سيتم دمج كودك هنا لاحقاً) ---
    with menu[0]:
        st.info("👥 قسم إدارة بيانات الطلاب - قيد التشغيل")
        # ضع كود الطلاب هنا

    # --- التبويب 1: رصد الدرجات (سيتم دمج كودك هنا لاحقاً) ---
    with menu[1]:
        st.info("📊 قسم رصد وإدارة الدرجات - قيد التشغيل")
        # ضع كود الدرجات هنا

    # --- التبويب 2: إدارة التنبيهات (تم إصلاح الربط) ---
    with menu[2]:
        st.subheader("📢 إدارة التنبيهات والتعميمات العامة")
        
        with st.form("admin_announcement_v2026", clear_on_submit=True):
            a_title = st.text_input("📝 عنوان التنبيه / الإعلان")
            a_details = st.text_area("📄 تفاصيل التعميم (تظهر للطالب)")
            
            c1, c2 = st.columns(2)
            is_urgent = c1.checkbox("🌟 عاجل (يظهر في قمة شاشة الطالب)")
            # جلب الخيارات من session_state لضمان عدم حدوث KeyError
            target_list = ["الكل"] + st.session_state.get('class_options', ["الأول", "الثاني"])
            target = c2.selectbox("🎯 الفئة المستهدفة:", target_list)
            
            if st.form_submit_button("📣 نشر وتعميم وبث الآن"):
                if a_title and a_details:
                    ann_data = {
                        "الصف": target,
                        "عاجل": "نعم" if is_urgent else "لا",
                        "العنوان": a_title,
                        "التاريخ": str(datetime.date.today()),
                        "الرابط": a_details
                    }
                    if safe_append_row("exams", ann_data):
                        st.success(f"✅ تم نشر التعميم لـ {target}")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.warning("⚠️ أكمل العنوان والتفاصيل.")

        st.divider()
        
        # سجل التنبيهات المحدث
        st.markdown("#### 📜 سجل التعميمات وإدارة البث")
        df_ann = fetch_safe("exams")
        if not df_ann.empty:
            for idx, row in df_ann.iloc[::-1].iterrows():
                with st.container(border=True):
                    col_txt, col_btn = st.columns([3, 1])
                    with col_txt:
                        pfx = "🚨 [عاجل] " if str(row.get('عاجل', 'لا')).strip() == "نعم" else "📢 "
                        st.markdown(f"<b style='color:#1e3a8a; font-size:1.1rem;'>{pfx}{row.get('العنوان', 'عنوان')}</b>", unsafe_allow_html=True)
                        st.caption(f"🎯 لـ: {row.get('الصف', 'الكل')} | 📅 {row.get('التاريخ', '')}")
                        st.write(f"📝 {row.get('الرابط', '')}")
                    
                    with col_btn:
                        # ✅ ميزة بث الواتساب الاحترافي
                        w_msg = urllib.parse.quote(f"📢 *تنبيه من منصة زياد*\n📌 *{row.get('العنوان')}*\n📝 {row.get('الرابط')}")
                        st.link_button("👥 بث واتساب", f"https://api.whatsapp.com/send?text={w_msg}", use_container_width=True)
                        
                        # ✅ ميزة الحذف النهائي
                        if st.button("🗑️ حذف", key=f"del_ann_{idx}", use_container_width=True):
                            sh.worksheet("exams").delete_rows(int(idx) + 2)
                            st.success("✅ تم الحذف")
                            st.cache_data.clear()
                            st.rerun()
        else:
            st.info("💡 لا توجد تعميمات في السجل حالياً.")

    # --- التبويب 3: الإعدادات والخروج ---
    with menu[3]:
        st.subheader("⚙️ إعدادات الإدارة")
        st.info(f"🗓️ العام الدراسي الحالي: {st.session_state.get('current_year', '1447هـ')}")
        
        st.divider()
        if st.button("🚪 تسجيل خروج الإدارة", type="primary", use_container_width=True):
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()

    # زر الخروج الجانبي (لضمان الوصول السريع)
    if st.sidebar.button("🚪 تسجيل الخروج الآمن", key="admin_side_logout"):
        st.session_state.role = None
        st.rerun()
    # ---------------------------------------------------------
    # ⚙️ التبويب 3: الإعدادات والتحكم الشامل (النسخة المكتملة والمدمجة 2026)
    # ---------------------------------------------------------
    with menu[3]:
        st.subheader("⚙️ غرفة التحكم المتقدمة")
        
        # 1. صيانة النظام وتحديث البيانات
        with st.expander("🛠️ صيانة النظام (تحديث البيانات)"):
            c1, c2 = st.columns(2)
            if c1.button("🔄 تصفير الكاش (Clear Cache)", use_container_width=True):
                st.cache_data.clear(); st.success("✅ تم تحديث البيانات من السحابة"); st.rerun()
            
            # 🔥 الميزة الجديدة: تصفير نقاط التميز السلوكي (إجراء حساس)
            if c2.button("🧹 تصفير نقاط كافة الطلاب", type="secondary", use_container_width=True):
                try:
                    ws_st = sh.worksheet("students")
                    df_st = fetch_safe("students")
                    if not df_st.empty:
                        # تحديث عمود "النقاط" (يفترض أنه العمود رقم 8) لجميع الصفوف
                        row_count = len(df_st) + 1
                        # إرسال قائمة من الأصفار لتغطية كافة الطلاب بضغطة واحدة
                        zero_fill = [[0]] * (row_count - 1)
                        ws_st.update(f"I2:I{row_count}", zero_fill) # تحديث العمود I (النقاط)
                        st.success("✅ تم تصفير نقاط جميع الطلاب بنجاح!")
                        st.cache_data.clear(); st.rerun()
                except Exception as e:
                    st.error(f"❌ فشل التصفير: {e}")

        # 2. تحديث قيمة الدرجات (المشاركة والاختبار)
        with st.expander("⚖️ توزيع الدرجات (تحديث الحدود القصوى)"):
            c1, c2 = st.columns(2)
            mt = c1.number_input("حد المشاركة الحالي", 0, 100, st.session_state.max_tasks)
            mq = c2.number_input("حد الاختبار الحالي", 0, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ حدود الدرجات الجديدة"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, mt)
                ws_s.update_cell(3, 2, mq)
                st.session_state.max_tasks, st.session_state.max_quiz = mt, mq
                st.success("✅ تم تحديث توزيع الدرجات بنجاح")

        # 3. إدارة العام والصفوف والمراحل (الربط الديناميكي المصلح)
        with st.expander("🗓️ إدارة العام والصفوف والمراحل"):
            st.info("💡 ملاحظة: التعديل هنا سيغير الخيارات في 'نموذج إضافة طالب جديد' فوراً.")
            c1, c2, c3 = st.columns(3)
            ny = c1.text_input("تعديل العام الدراسي:", st.session_state.current_year)
            cl_s = c2.text_area("قائمة الصفوف (فاصلة):", ", ".join(st.session_state.class_options))
            st_s = c3.text_area("قائمة المراحل (فاصلة):", ", ".join(st.session_state.stage_options))
            
            if st.button("💾 حفظ الإعدادات العامة وتحديث القوائم"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(4, 2, ny) # العام الدراسي
                ws_s.update_cell(5, 2, cl_s) # قائمة الصفوف
                ws_s.update_cell(6, 2, st_s) # قائمة المراحل
                
                # تحديث الذاكرة الحالية (Session State) لضمان التغيير الفوري في النماذج
                st.session_state.current_year = ny
                st.session_state.class_options = [x.strip() for x in cl_s.split(',')]
                st.session_state.stage_options = [x.strip() for x in st_s.split(',')]
                
                st.success("✅ تم حفظ الإعدادات وتحديث قوائم الاختيار بنجاح")
                st.cache_data.clear(); st.rerun()

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
            col_t1.download_button("📝 تحميل قالب الطلاب", data=buf_st.getvalue(), file_name="Students_Template.xlsx", use_container_width=True)
            
            buf_gr = io.BytesIO()
            with pd.ExcelWriter(buf_gr, engine='xlsxwriter') as wr:
                pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(wr, index=False)
            col_t2.download_button("📊 تحميل قالب الدرجات المطور", data=buf_gr.getvalue(), file_name="Smart_Grades_Template.xlsx", use_container_width=True)
            
            st.divider()
            if st.button("📊 توليد نسخة احتياطية كاملة (BackUp)", use_container_width=True):
                df_bu = fetch_safe("students")
                buf_bu = io.BytesIO()
                with pd.ExcelWriter(buf_bu, engine='xlsxwriter') as wr: df_bu.to_excel(wr, index=False)
                st.download_button("📥 تنزيل ملف Backup الطلاب", data=buf_bu.getvalue(), file_name=f"Backup_Students_{datetime.date.today()}.xlsx")

        # 7. المزامنة الذكية (المعالجة المتقدمة)
        with st.expander("📤 مزامنة وتحديث البيانات (نظام الحماية والتحقق القصوى)"):
            st.markdown("### 🛠️ معالج المزامنة المطور")
            st.info("💡 سيقوم النظام بتحديث درجات الطلاب الحاليين ومنع تكرارهم.")
            
            up_file = st.file_uploader("اختر ملف الإكسل المحدث (p1, p2)", type=['xlsx'], key="smart_sync_final")
            target_sheet = st.radio("حدد الجدول المطلوب تحديثه:", ["students", "grades"], horizontal=True)
            
            if st.button("🚀 بدء المزامنة والتطهير الآن", key="run_master_sync"):
                if up_file:
                    try:
                        with st.status("⏳ جاري تحليل البيانات وفلترة الأصفار...", expanded=True) as status:
                            df_up = pd.read_excel(up_file, engine='openpyxl').fillna("")
                            df_up = df_up.dropna(how='all')
                            
                            ws = sh.worksheet(target_sheet)
                            df_current = fetch_safe(target_sheet)
                            headers = ws.row_values(1)
                            
                            up_count = 0; new_count = 0; skip_count = 0

                            for _, row in df_up.iterrows():
                                data_dict = row.to_dict()
                                id_val = str(data_dict.get('student_id', data_dict.get('id', ""))).strip()
                                if "." in id_val: id_val = id_val.split(".")[0]
                                
                                # 🛡️ صمام الأمان: تجاهل الأرقام غير الصحيحة
                                if id_val in ["0", "0.0", "", "nan", "None"]:
                                    skip_count += 1
                                    continue

                                if target_sheet == "grades":
                                    p1 = pd.to_numeric(data_dict.get('p1', 0), errors='coerce') or 0
                                    p2 = pd.to_numeric(data_dict.get('p2', 0), errors='coerce') or 0
                                    data_dict.update({
                                        "student_id": id_val,
                                        "p1": str(int(p1)), "p2": str(int(p2)),
                                        "perf": str(int(p1 + p2)), 
                                        "date": str(datetime.date.today())
                                    })
                                else:
                                    data_dict['id'] = id_val

                                if not df_current.empty and id_val in df_current.iloc[:, 0].values:
                                    row_idx = df_current[df_current.iloc[:, 0] == id_val].index[0] + 2
                                    updated_row = [str(data_dict.get(h, "")) for h in headers]
                                    ws.update(f"A{row_idx}", [updated_row])
                                    up_count += 1
                                else:
                                    new_row = [str(data_dict.get(h, "")) for h in headers]
                                    ws.append_row(new_row)
                                    new_count += 1
                            
                            status.update(label="✅ اكتملت المزامنة بنجاح!", state="complete", expanded=False)

                        st.success(f"🏁 التقرير: تحديث {up_count} | إضافة {new_count} | تجاهل {skip_count}")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")
    # ------------------------------------------
    # 🚗 التبويب 4: الخروج
    # ------------------------------------------
    with menu[4]:
        if st.button("🚪 تأكيد تسجيل الخروج"):
            st.session_state.role = None; st.rerun()
# ==========================================
# 👨‍🎓 5. واجهة الطالب (النسخة الكاملة والمصلحة برمجياً)
# ==========================================
elif st.session_state.role == "student":
    student_id = str(st.session_state.get('username', '')).strip()
    df_st = fetch_safe("students")
    df_gr = fetch_safe("grades")
    df_beh = fetch_safe("behavior")
    df_ann = fetch_safe("exams")

    if not df_st.empty:
        # إنشاء عمود منظف للمعرف لضمان المطابقة
        df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
        my_info = df_st[df_st['clean_id'] == student_id]
    else: 
        my_info = pd.DataFrame()

    if not my_info.empty:
        s_data = my_info.iloc[0]
        s_name = s_data.get('name', 'طالبنا المتميز')
        # 🎯 ربط الصف: جلب الصف من حقل class بجدول الطلاب
        s_class = str(s_data.get('class', 'غير محدد')).strip() 
        s_points = int(pd.to_numeric(s_data.get('النقاط', 0), errors='coerce') or 0)

        # الهيدر الشخصي
        st.markdown(f"""
            <div class="app-header">
                <h2 style='margin:0; color:#1e3a8a;'>👋 مرحباً بك: {s_name}</h2>
                <p style='margin:5px 0 0 0; color:#000; font-weight:900;'>🏫 الصف الدراسي: {s_class} | 🆔 الرقم: {student_id}</p>
            </div>
        """, unsafe_allow_html=True)

        # 🚨 1. شريط الأخبار المتحرك (Marquee) - مع حماية من KeyError
        if not df_ann.empty and 'الصف' in df_ann.columns:
            scrolling_filter = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_class])].tail(3)
            if not scrolling_filter.empty:
                news_ticker = " 🌟 | ".join(scrolling_filter['العنوان'].tolist())
                st.markdown(f'<div class="marquee-container"><div class="marquee-text">📢 آخر الأخبار لـ {s_class}: {news_ticker} 🌟</div></div>', unsafe_allow_html=True)

        # 🚨 2. الإعلان العاجل الثابت (مع حماية مضاعفة)
        if not df_ann.empty:
            if 'عاجل' in df_ann.columns and 'الصف' in df_ann.columns:
                urgent_news = df_ann[(df_ann['عاجل'].astype(str).str.strip() == "نعم") & 
                                    (df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_class]))]
                if not urgent_news.empty:
                    u = urgent_news.tail(1).iloc[0]
                    st.markdown(f"""
                        <div class="urgent-msg">
                            🌟 تنبيه هام لـ {s_class}: {u.get('العنوان', 'تنبيه جديد')} <br>
                            <small style="font-weight:normal;">{u.get('الرابط', u.get('التفاصيل', ''))}</small>
                        </div>
                    """, unsafe_allow_html=True)

        # 🏅 3. الأوسمة الأفقية ورصيد النقاط العملاق
        st.markdown(f"""
            <div class="medal-flex">
                <div class="m-card {'m-active' if s_points >= 100 else ''}">🥇<br><b style='color:#000;'>ذهبي</b></div>
                <div class="m-card {'m-active' if s_points >= 50 else ''}">🥈<br><b style='color:#000;'>فضي</b></div>
                <div class="m-card m-active">🥉<br><b style='color:#000;'>برونزي</b></div>
            </div>
            <div class="points-banner">
                <p style='margin:0; font-size: 1.1rem; opacity:0.9; font-weight:bold;'>رصيد نقاط التميز السلوكي</p>
                <h1 style='margin:0; font-size: 4.5rem; font-weight: 900;'>{s_points}</h1>
            </div>
        """, unsafe_allow_html=True)

        # 📱 5. التبويبات المدمجة
        tabs = st.tabs(["📢 التنبيهات", "📝 الملاحظات", "📊 درجاتي", "🏆 المتصدرين", "⚙️ الإعدادات"])

        with tabs[0]:
            st.markdown(f"#### 📢 سجل تعميمات {s_class}")
            if not df_ann.empty and 'الصف' in df_ann.columns:
                student_ann = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_class])]
                if not student_ann.empty:
                    for _, row in student_ann.iloc[::-1].iterrows(): 
                        st.markdown(f"""
                            <div class="mobile-card">
                                📢 {row.get('العنوان', 'تعميم')} <br> 
                                <small style='color:#555; font-weight:normal;'>📅 {row.get('التاريخ', '')}</small> <br> 
                                <div style='margin-top:5px; font-weight:normal; font-size:0.95rem;'>{row.get('الرابط', row.get('التفاصيل', ''))}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else: 
                    st.info(f"💡 لا توجد تنبيهات جديدة لـ {s_class}.")
            else:
                st.info("💡 سجل التنبيهات غير متاح حالياً.")

        with tabs[1]:
            st.markdown("#### 📝 ملاحظات المعلم")
            if not df_beh.empty:
                df_beh['clean_id'] = df_beh.iloc[:, 0].astype(str).str.split('.').str[0]
                my_notes = df_beh[df_beh['clean_id'] == student_id]
                if not my_notes.empty:
                    for _, n in my_notes.iterrows():
                        st.markdown(f'<div class="mobile-card" style="border-right-color:#e53e3e;">📌 {n.get("type", "تنبيه")}: {n.get("desc", "")} <br> <small style="font-weight:normal;">📅 {n.get("date", "")}</small></div>', unsafe_allow_html=True)
                else: 
                    st.success("🌟 سجلّك مثالي وخالٍ من الملاحظات.")

        # --- تبويب درجاتي (إصدار التفاصيل الكاملة) ---
        with tabs[2]:
            st.markdown("#### 📊 نتائج الاختبارات والمهام")
            if not df_gr.empty:
                # التأكد من تطهير المعرف لضمان جلب الدرجة الصحيحة
                df_gr['clean_id'] = df_gr.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                my_gr = df_gr[df_gr['clean_id'] == student_id]
                
                if not my_gr.empty:
                    g = my_gr.iloc[0]
                    # عرض الدرجات بشكل مفصل ببطاقات عالية التباين
                    st.markdown(f"""
                        <div class="mobile-card">
                            📝 المشاركة والمهام: <span style='float:left;'>{g.get('p1', 0)}</span>
                        </div>
                        <div class="mobile-card">
                            ✍️ اختبار قصير: <span style='float:left;'>{g.get('p2', 0)}</span>
                        </div>
                        <div class="mobile-card" style="background:#f0fdf4; border-right-color:#10b981; border-width:2px;">
                            🏆 المجموع الكلي: <span style='float:left; font-size:1.3rem;'>{g.get('perf', 0)}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("💡 لم يتم رصد درجاتك في النظام بعد.")
            else:
                st.warning("⚠️ جدول الدرجات غير متاح حالياً.")

        with tabs[3]:
            st.markdown("#### 🏆 لوحة الشرف (أفضل 10 طلاب)")
            df_st['pts_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            top_10 = df_st.sort_values(by="pts_num", ascending=False).head(10)
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
                is_me_style = "border: 2px solid #1e3a8a; background: #eff6ff;" if str(row['clean_id']) == student_id else ""
                st.markdown(f"""<div class="mobile-card" style="{is_me_style}"><span style='font-size:1.2rem;'>{icon}</span> {row['name']} <span style='float:left; color:#f59e0b;'>{int(row['pts_num'])} ن</span></div>""", unsafe_allow_html=True)

        with tabs[4]:
            st.markdown("#### ⚙️ إعدادات الحساب")
            with st.form("up_info_final"):
                new_mail = st.text_input("📧 البريد الإلكتروني", s_data.get('الإيميل', ''))
                new_phone = st.text_input("📱 رقم الجوال", s_data.get('الجوال', ''))
                if st.form_submit_button("💾 حفظ البيانات المحدثة"):
                    try:
                        ws_st = sh.worksheet("students")
                        ids = [str(x).split('.')[0] for x in ws_st.col_values(1)]
                        if student_id in ids:
                            r_idx = ids.index(student_id) + 1
                            ws_st.update_cell(r_idx, 6, new_mail); ws_st.update_cell(r_idx, 7, new_phone)
                            st.success("✅ تم تحديث بياناتك بنجاح!"); st.cache_data.clear()
                    except: 
                        st.error("❌ فشل التحديث حالياً.")
            st.divider()
            if st.button("🚪 تسجيل الخروج الآمن من المنصة", type="primary", use_container_width=True):
                st.session_state.role = None; st.session_state.username = None; st.rerun()

    else: 
        st.error(f"⚠️ عذراً، الرقم الأكاديمي ({student_id}) غير مسجل في النظام.")
        if st.button("🔄 العودة لمحاولة الدخول برقم آخر"): st.rerun()

    # استدعاء دالة الفوتر بأمان
    try:
        show_footer()
    except NameError:
        pass
