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
# ==========================================
# 🔐 1. نظام تسجيل الدخول الموحد (إصدار زر العودة الذكي)
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    
    with t1:
        # قمنا بتعريف نموذج الدخول
        with st.form("st_log_v3", clear_on_submit=False):
            sid_in = st.text_input("🆔 الرقم الأكاديمي").strip()
            submit_btn = st.form_submit_button("دخول الطلاب 🚀")
            
            if submit_btn:
                if sid_in:
                    df_st = fetch_safe("students")
                    if not df_st.empty:
                        # تنظيف الرقم المكتوب
                        search_id = sid_in.split('.')[0]
                        df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                        
                        if search_id in df_st['clean_id'].values:
                            st.session_state.username = search_id
                            st.session_state.role = "student"
                            st.success("✅ جاري الدخول...")
                            st.rerun()
                        else:
                            # هنا الحل: رسالة الخطأ مع زر العودة
                            st.error(f"❌ الرقم ({sid_in}) غير مسجل في النظام.")
                            st.info("💡 تأكد من كتابة الرقم بشكل صحيح أو تواصل مع الإدارة.")
                else:
                    st.warning("⚠️ يرجى إدخال الرقم الأكاديمي أولاً.")

        # زر العودة يظهر خارج الفورم عند الحاجة لتحديث الحالة
        if not st.session_state.role:
             if st.button("🔄 تحديث الشاشة / محاولة مرة أخرى", use_container_width=True):
                 st.rerun()

    with t2:
        with st.form("admin_log_v3"):
            u = st.text_input("👤 اسم المستخدم (الإدارة)")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("دخول الإدارة 🛠️"):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    user_data = df_u[df_u['username']==u].iloc[0]
                    import hashlib
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role = "teacher"
                        st.session_state.username = u
                        st.rerun()
                st.error("❌ بيانات الدخول غير صحيحة.")
    st.stop()
    
# ==========================================
# 👨‍🏫 واجهة المعلم الرئيسية (دمج شامل ومستقر)
# ==========================================
if st.session_state.role == "teacher":
    # 1. إنشاء التبويبات الخمسة (مُزاحة بـ Tab واحدة عن الـ if)
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    
    # ---------------------------------------------------------
    # 👥 التبويب 0: إدارة قاعدة بيانات الطلاب (الإصدار المصحح 2026)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 👥 التبويب 0: إدارة قاعدة بيانات الطلاب (الإصدار الديناميكي المرتبط بالإعدادات)
    # ---------------------------------------------------------
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        df_st = fetch_safe("students") 
        
        if not df_st.empty:
            # 🛡️ تنظيف معرف الطالب للمطابقة
            df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
            
            # 1. شريط الإحصائيات
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            unique_classes = len(df_st.iloc[:, 2].unique()) if len(df_st.columns) > 2 else 0
            c2.metric("🏫 الفصول النشطة", unique_classes)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            
            st.divider()
    
            # 2. نموذج إضافة طالب جديد (ديناميكي بالكامل)
            with st.expander("➕ إضافة طالب جديد (يرتبط بإعدادات النظام)", expanded=True):
                with st.form("add_student_dynamic_v2026", clear_on_submit=True):
                    # الصف الأول: البيانات الأساسية
                    c1, c2 = st.columns(2)
                    f_id = c1.text_input("🔢 الرقم الأكاديمي (id)")
                    f_name = c2.text_input("👤 الاسم الثلاثي (name)")
                    
                    # الصف الثاني: البيانات الأكاديمية (تتحدث تلقائياً من الإعدادات)
                    c3, c4, c5 = st.columns(3)
                    
                    # ✅ 1. ربط قائمة الصفوف بالإعدادات
                    # إذا كانت القائمة فارغة، نضع قيمة افتراضية لتجنب الخطأ
                    classes_list = st.session_state.get('class_options', ['الأول'])
                    f_class = c3.selectbox("🏫 الصف الدراسي", classes_list)
                    
                    # ✅ 2. ربط قائمة المراحل بالإعدادات (كانت ثابتة سابقاً)
                    stages_list = st.session_state.get('stage_options', ['ابتدائي'])
                    f_stage = c4.selectbox("🎓 المرحلة الدراسية", stages_list)
                    
                    # ✅ 3. ربط العام الدراسي بالإعدادات
                    current_yr = st.session_state.get('current_year', '1447هـ')
                    f_year = c5.text_input("🗓️ العام الدراسي", value=current_yr)
                    
                    # الصف الثالث: بيانات التواصل (مطلوبة)
                    c6, c7 = st.columns(2)
                    f_phone = c6.text_input("📱 رقم الجوال")
                    f_mail = c7.text_input("📧 البريد الإلكتروني")

                    if st.form_submit_button("✅ اعتماد وحفظ في القاعدة"):
                        if f_id and f_name:
                            # تنظيف البيانات
                            clean_phone = clean_phone_number(f_phone) if f_phone else ""
                            
                            # تجهيز القاموس للحفظ (مطابق لأعمدة ملف الإكسل)
                            st_map = {
                                "id": f_id.strip(),
                                "name": f_name.strip(),
                                "class": f_class, # القيمة المختارة من القائمة الديناميكية
                                "year": f_year,   # القيمة القادمة من الإعدادات
                                "sem": f_stage,   # القيمة المختارة من القائمة الديناميكية
                                "الجوال": clean_phone,
                                "الإيميل": f_mail.strip(),
                                "النقاط": "0"
                            }
                            
                            if safe_append_row("students", st_map):
                                st.success(f"✅ تم حفظ الطالب: {f_name} في {f_class}")
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.warning("⚠️ يرجى تعبئة الرقم والاسم على الأقل.")
    
            # 3. عرض الجدول والبحث
            st.write("---")
            sq = st.text_input("🔍 بحث سريع:")
            if sq:
                mask = df_st.iloc[:, 0].astype(str).str.contains(sq) | df_st.iloc[:, 1].astype(str).str.contains(sq)
                st.dataframe(df_st[mask], use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
    
            # 4. الحذف
            with st.expander("🗑️ إدارة الحذف"):
                del_q = st.text_input("ابحث للحذف:", key="del_search")
                if del_q:
                    df_del = df_st[df_st.iloc[:, 0].astype(str).str.contains(del_q) | df_st.iloc[:, 1].astype(str).str.contains(del_q)]
                    for idx, row in df_del.iterrows():
                        ci, ca = st.columns([3, 1])
                        ci.write(f"{row.iloc[1]} - {row.iloc[0]}")
                        if ca.button("حذف نهائي", key=f"d_{idx}"):
                            sh.worksheet("students").delete_rows(int(idx) + 2)
                            st.success("تم الحذف"); st.cache_data.clear(); st.rerun()
        else:
            st.info("💡 القاعدة فارغة. أضف طلاباً من النموذج أعلاه.")
            # نموذج احتياطي للإضافة الأولى
            with st.form("first_add"):
                id_1 = st.text_input("الرقم"); nm_1 = st.text_input("الاسم")
                if st.form_submit_button("إضافة"):
                    safe_append_row("students", {"id": id_1, "name": nm_1, "النقاط": "0"})
                    st.rerun()
    # ---------------------------------------------------------
    # 📊 التبويب 1: التقييم والمتابعة (الإصدار المصحح والمتطابق مع الشيت)
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
                # جلب بيانات الطالب بدقة
                s_info = df_eval[df_eval.iloc[:, 0] == sid].iloc[0]
                s_name = s_info['name'] # استخدام اسم العمود 'name' بدلاً من الفهرس
                
                # جلب وتجهيز بيانات التواصل
                cl_p = clean_phone_number(s_info.get('الجوال', ''))
                s_mail = s_info.get('الإيميل', '')

                c_g, c_b = st.columns(2)

                # --- 📝 رصد الدرجات (مشاركة واختبار) ---
                with c_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_f_v26"):
                        v_t = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0, 100)
                        v_q = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0, 100)
                        if st.form_submit_button("💾 حفظ الدرجات"):
                            if v_t <= st.session_state.max_tasks and v_q <= st.session_state.max_quiz:
                                # مفاتيح الدرجات: student_id, p1, p2, perf, date
                                grade_data = {
                                    "student_id": sid, 
                                    "p1": str(v_t), 
                                    "p2": str(v_q), 
                                    "perf": str(v_t+v_q), 
                                    "date": str(datetime.date.today())
                                }
                                if safe_append_row("grades", grade_data):
                                    st.success("✅ تم رصد الدرجات بنجاح")
                                    st.cache_data.clear()
                            else:
                                st.error("⚠️ الدرجة المدخلة تتجاوز الحد المسموح.")

                # --- 🎭 رصد السلوك (تصحيح أسماء الحقول) ---
                with c_b:
                    st.markdown("##### 🎭 المتابعة السلوكية")
                    with st.form("beh_f_v26", clear_on_submit=True):
                        b_type = st.selectbox("نوع السلوك:", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص قلم (-5)", "🚫 سلبي (-10)"])
                        b_msg = st.text_area("الملاحظة")
                        if st.form_submit_button("💾 تسجيل السلوك"):
                            # ✅ التصحيح: استخدام المفاتيح المطابقة لملف الإكسل (student_id, date, type, note)
                            beh_data = {
                                "student_id": sid, 
                                "date": str(datetime.date.today()), 
                                "type": b_type, 
                                "note": b_msg
                            }
                            if safe_append_row("behavior", beh_data):
                                st.success("✅ تم تسجيل الملاحظة بنجاح")
                                st.cache_data.clear(); st.rerun()

                # --- 📜 السجل التاريخي (تصحيح العرض) ---
                st.divider()
                st.markdown(f"#### 📜 سجل ملاحظات الطالب: {s_name}")
                df_beh = fetch_safe("behavior")
                
                # تصفية الملاحظات الخاصة بالطالب المحدد
                if not df_beh.empty:
                    # التأكد من اسم عمود المعرف في جدول السلوك (student_id)
                    beh_id_col = 'student_id' if 'student_id' in df_beh.columns else df_beh.columns[0]
                    my_beh = df_beh[df_beh[beh_id_col].astype(str) == str(sid)]
                else:
                    my_beh = pd.DataFrame()
                
                if not my_beh.empty:
                    for _, r in my_beh.iloc[::-1].iterrows():
                        with st.container(border=True):
                            ct, cb = st.columns([3, 1.2]) 
                            with ct:
                                # عرض التاريخ والنوع والملاحظة بناءً على أسماء الأعمدة الصحيحة
                                date_val = r.get('date', '')
                                type_val = r.get('type', '')
                                note_val = r.get('note', '')
                                
                                st.write(f"📅 **{date_val}** | **{type_val}**")
                                if note_val: st.caption(f"📝 {note_val}")
                            
                            with cb:
                                # توليد وتشفير الرسالة الاحترافية
                                m_enc = get_professional_msg(s_name, type_val, note_val, date_val)
                                
                                # أزرار التواصل تعمل الآن ببيانات صحيحة
                                st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?phone={cl_p}&text={m_enc}", use_container_width=True)
                                st.link_button("📧 Email", f"mailto:{s_mail}?subject=تقرير متابعة: {s_name}&body={m_enc}", use_container_width=True)
                else:
                    st.info("💡 لا توجد ملاحظات سابقة لهذا الطالب.")
        else:
            st.info("💡 لا يوجد طلاب حالياً، يرجى إضافة طلاب من التبويب الأول.")

    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 📢 التبويب 2: إدارة التنبيهات (النسخة الكاملة والمطورة 2026)
    # ---------------------------------------------------------
    with menu[2]:
        st.subheader("📢 إدارة التنبيهات والتعميمات العامة")
        
        # 1. نموذج نشر تنبيه جديد (ربط ذكي مع الشاشة الرئيسية)
        with st.form("admin_announcement_final_v2026", clear_on_submit=True):
            a_title = st.text_input("📝 عنوان التنبيه / الإعلان")
            a_details = st.text_area("📄 تفاصيل التعميم (تظهر للطالب)")
            
            c1, c2 = st.columns(2)
            # ميزة العرض في الشاشة الرئيسية
            is_urgent = c1.checkbox("🌟 عرض في الشاشة الرئيسية (تنبيه عاجل)")
            
            # جلب قائمة الصفوف ديناميكياً من الإعدادات
            target_list = ["الكل"] + st.session_state.get('class_options', ["الصف الأول", "الصف الثاني"])
            a_target = c2.selectbox("🎯 الفئة المستهدفة:", target_list)
            
            if st.form_submit_button("📣 نشر وبث التنبيه الآن"):
                if a_title and a_details:
                    # تحضير البيانات لضمان عدم حدوث IndexError (الربط بأسماء الحقول)
                    ann_data = {
                        "الصف": a_target,
                        "عاجل": "نعم" if is_urgent else "لا",
                        "العنوان": a_title,
                        "التاريخ": str(datetime.date.today()),
                        "الرابط": a_details # حقل التفاصيل
                    }
                    
                    if safe_append_row("exams", ann_data):
                        st.success(f"✅ تم النشر بنجاح لـ {a_target}")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.warning("⚠️ يرجى كتابة العنوان والتفاصيل قبل النشر.")
    
        st.divider()
        
        # 2. سجل التعميمات المرسلة وإدارة البث والحذف
        st.markdown("#### 📜 سجل التعميمات المرسلة وإدارة البث")
        df_ann = fetch_safe("exams")
        
        if not df_ann.empty:
            # عرض التنبيهات من الأحدث للأقدم
            for idx, row in df_ann.iloc[::-1].iterrows():
                with st.container(border=True):
                    col_txt, col_btn = st.columns([3, 1])
                    
                    with col_txt:
                        # تمييز التنبيه العاجل بصرياً
                        is_urgent_val = str(row.get('عاجل', 'لا')).strip()
                        pfx = "🚨 [هام جداً] " if is_urgent_val == "نعم" else "📢 "
                        
                        st.markdown(f"<b style='color:#1e3a8a; font-size:1.1rem;'>{pfx} {row.get('العنوان', '')}</b>", unsafe_allow_html=True)
                        st.caption(f"🎯 لـ: {row.get('الصف', 'الكل')} | 📅 {row.get('التاريخ', '')}")
                        st.write(f"📝 {row.get('الرابط', row.get('details', ''))}")
                    
                    with col_btn:
                        # ✅ ميزة بث الواتساب (تجهيز رسالة احترافية للمجموعات)
                        w_msg = urllib.parse.quote(
                            f"📢 *تنبيه من منصة زياد الذكية*\n"
                            f"------------------\n"
                            f"📌 *{row.get('العنوان')}*\n"
                            f"📝 {row.get('الرابط')}\n"
                            f"------------------"
                        )
                        st.link_button("👥 بث للواتساب", f"https://api.whatsapp.com/send?text={w_msg}", use_container_width=True)
                        
                        # ✅ ميزة الحذف النهائي من قوقل شيت
                        if st.button("🗑️ حذف التنبيه", key=f"del_ann_{idx}", use_container_width=True):
                            try:
                                # حذف السطر (المؤشر + 2 لتعويض الترويسة وبدء الفهرس من 0)
                                sh.worksheet("exams").delete_rows(int(idx) + 2)
                                st.success("✅ تم الحذف بنجاح")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ فشل الحذف: {e}")
        else:
            st.info("💡 لا توجد تنبيهات منشورة حالياً في قاعدة البيانات.")
    # ---------------------------------------------------------
    # ⚙️ التبويب 3: الإعدادات والتحكم الشامل (النسخة النهائية 2026)
    # ---------------------------------------------------------
    with menu[3]:
        st.subheader("⚙️ غرفة التحكم وإعدادات النظام")
        
        # 1. صيانة النظام وتحديث البيانات
        with st.expander("🛠️ صيانة النظام والبيانات", expanded=True):
            c1, c2 = st.columns(2)
            if c1.button("🔄 تحديث النظام (Clear Cache)", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ تم تحديث البيانات من السحابة بنجاح")
                st.rerun()
            
            # زر تصفير النقاط (تحديث العمود I في شيت الطلاب)
            if c2.button("🧹 تصفير نقاط جميع الطلاب", type="primary", use_container_width=True):
                try:
                    ws_st = sh.worksheet("students")
                    # جلب كل البيانات لحساب عدد الصفوف
                    all_data = ws_st.get_all_values()
                    if len(all_data) > 1:
                        row_count = len(all_data)
                        # تجهيز قائمة من الأصفار لتغطية المجال من I2 إلى آخر صف
                        zero_fill = [[0]] * (row_count - 1)
                        # التحديث دفعة واحدة (Batch Update) لتوفير الموارد
                        ws_st.update(range_name=f"I2:I{row_count}", values=zero_fill)
                        st.success("✅ تم تصفير نقاط جميع الطلاب بنجاح!")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.warning("⚠️ لا يوجد طلاب لتصفير نقاطهم.")
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء التصفير: {e}")

        # 2. إدارة الثوابت (القوائم والدرجات) - تحديث فوري
        with st.expander("📝 تحديث القوائم والدرجات (ديناميكي)"):
            st.info("💡 التعديلات هنا تنعكس فوراً على نموذج 'إضافة طالب' و 'رصد الدرجات'.")
            
            # أخذ القيم الحالية من الذاكرة
            c_y = st.text_input("🗓️ العام الدراسي الحالي:", st.session_state.current_year)
            
            c_cls, c_stg = st.columns(2)
            # تحويل القوائم لنصوص للعرض في text_area
            cls_txt = c_cls.text_area("🏫 قائمة الصفوف (افصل بفاصلة):", ", ".join(st.session_state.class_options))
            stg_txt = c_stg.text_area("🎓 قائمة المراحل (افصل بفاصلة):", ", ".join(st.session_state.stage_options))
            
            c_mk, c_mq = st.columns(2)
            n_mt = c_mk.number_input("درجة المشاركة القصوى:", 0, 100, st.session_state.max_tasks)
            n_mq = c_mq.number_input("درجة الاختبار القصوى:", 0, 100, st.session_state.max_quiz)
            
            if st.button("💾 حفظ الإعدادات وتحديث النظام"):
                try:
                    ws_s = sh.worksheet("settings")
                    # تحديث الخلايا في شيت الإعدادات (B2, B3, B4, B5, B6)
                    batch_updates = [
                        {'range': 'B2', 'values': [[n_mt]]},
                        {'range': 'B3', 'values': [[n_mq]]},
                        {'range': 'B4', 'values': [[c_y]]},
                        {'range': 'B5', 'values': [[cls_txt]]},
                        {'range': 'B6', 'values': [[stg_txt]]}
                    ]
                    ws_s.batch_update(batch_updates)
                    
                    # ✅ تحديث الذاكرة الحية (Session State) فوراً
                    st.session_state.max_tasks = n_mt
                    st.session_state.max_quiz = n_mq
                    st.session_state.current_year = c_y
                    st.session_state.class_options = [x.strip() for x in cls_txt.split(',') if x.strip()]
                    st.session_state.stage_options = [x.strip() for x in stg_txt.split(',') if x.strip()]
                    
                    st.success("✅ تم الحفظ! القوائم والدرجات محدثة الآن.")
                    st.cache_data.clear() # مسح الكاش لضمان التحميل القادم
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ خطأ في الحفظ: {e}")

        # 3. المزامنة الذكية (Smart Sync) - المعالجة المتقدمة
        with st.expander("📤 المزامنة الذكية (رفع ملفات Excel)"):
            st.warning("⚠️ هذا الإجراء يقوم بتحديث البيانات الموجودة وإضافة الجديدة.")
            up_file = st.file_uploader("اختر ملف الإكسل (xlsx)", type=['xlsx'])
            target_sheet = st.radio("الجدول المستهدف:", ["students", "grades"], horizontal=True)
            
            if st.button("🚀 بدء المزامنة"):
                if up_file:
                    try:
                        with st.status("⏳ جاري قراءة الملف ومعالجة البيانات...", expanded=True) as status:
                            # قراءة الملف وتجاهل الصفوف الفارغة
                            df_up = pd.read_excel(up_file, engine='openpyxl').fillna("")
                            df_up = df_up.dropna(how='all')
                            
                            ws = sh.worksheet(target_sheet)
                            # جلب البيانات الحالية للمقارنة
                            current_data = ws.get_all_records()
                            current_ids = [str(row.get('id', row.get('student_id', ''))) for row in current_data]
                            headers = ws.row_values(1)
                            
                            up_c = 0; new_c = 0; skip_c = 0
                            
                            for _, row in df_up.iterrows():
                                d = row.to_dict()
                                # توحيد اسم المعرف (id أو student_id)
                                raw_id = str(d.get('student_id', d.get('id', ''))).strip()
                                # إزالة الفواصل العشرية من الرقم الأكاديمي
                                id_v = raw_id.split('.')[0]
                                
                                if not id_v or id_v == '0':
                                    skip_c += 1; continue
                                
                                # تجهيز البيانات حسب الجدول
                                if target_sheet == "grades":
                                    p1 = int(pd.to_numeric(d.get('p1', 0), errors='coerce') or 0)
                                    p2 = int(pd.to_numeric(d.get('p2', 0), errors='coerce') or 0)
                                    d.update({"student_id": id_v, "p1": p1, "p2": p2, "perf": p1+p2, "date": str(datetime.date.today())})
                                    # إزالة أي مفاتيح غير ضرورية
                                    if 'id' in d: del d['id']
                                else:
                                    d['id'] = id_v
                                    if 'الجوال' in d: d['الجوال'] = clean_phone_number(d['الجوال'])

                                # التحقق والتحديث
                                if id_v in current_ids:
                                    # تحديث (نبحث عن رقم الصف - تذكر أن البيانات تبدأ من الصف 2)
                                    row_idx = current_ids.index(id_v) + 2 
                                    # بناء الصف بنفس ترتيب الأعمدة في الشيت
                                    row_values = [str(d.get(h, "")) for h in headers]
                                    ws.update(range_name=f"A{row_idx}", values=[row_values])
                                    up_c += 1
                                else:
                                    # إضافة جديد
                                    row_values = [str(d.get(h, "")) for h in headers]
                                    ws.append_row(row_values)
                                    new_c += 1
                            
                            status.update(label="✅ تمت المزامنة!", state="complete", expanded=False)
                        st.success(f"النتيجة: ✅ تحديث {up_c} | ➕ إضافة {new_c} | ⚠️ تجاهل {skip_c}")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error(f"❌ حدث خطأ: {e}")

        # 4. الأمان والنسخ الاحتياطي
        with st.expander("🔐 الأمان والنسخ الاحتياطي"):
            t1, t2 = st.tabs(["تغيير الباسوورد", "تنزيل القوالب"])
            
            with t1:
                with st.form("chg_pwd"):
                    np = st.text_input("كلمة المرور الجديدة", type="password")
                    if st.form_submit_button("تحديث"):
                        if np:
                            hp = hashlib.sha256(str.encode(np)).hexdigest()
                            # تحديث الباسوورد للمستخدم الحالي فقط
                            # (يتطلب منطق بحث عن المستخدم، هنا مثال مبسط)
                            st.info("⚠️ هذه الميزة تتطلب صلاحيات خاصة")
            
            with t2:
                # توليد قوالب الإكسل
                b1 = io.BytesIO()
                pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل"]).to_excel(b1, index=False)
                st.download_button("📥 قالب الطلاب", b1.getvalue(), "students_template.xlsx")
                
                b2 = io.BytesIO()
                pd.DataFrame(columns=["student_id", "p1", "p2"]).to_excel(b2, index=False)
                st.download_button("📥 قالب الدرجات", b2.getvalue(), "grades_template.xlsx")
    # ------------------------------------------
    # 🚗 التبويب 4: الخروج
    # ------------------------------------------
    with menu[4]:
        if st.button("🚪 تأكيد تسجيل الخروج"):
            st.session_state.role = None; st.rerun()
# ==========================================
# 👨‍🎓 6. واجهة الطالب (النسخة الذهبية المكتملة والمطورة)
# ==========================================
# ==========================================
# 👨‍🎓 2. واجهة الطالب (إصدار الاستقرار والتباين العالي المدمج)
# ==========================================
if st.session_state.role == "student":
    # 1. استرجاع وتطهير الرقم الأكاديمي لضمان المطابقة
    student_id = str(st.session_state.get('username', '')).strip()
    
    # تحميل كافة الجداول الحقيقية من قوقل شيت
    df_st = fetch_safe("students")
    df_gr = fetch_safe("grades")
    df_beh = fetch_safe("behavior")
    df_ann = fetch_safe("exams") # شيت التنبيهات المربوط بلوحة الإدارة

    # 🛠️ البحث الدقيق عن بيانات الطالب وتجنب KeyError
    if not df_st.empty:
        # إنشاء عمود منظف للمعرف لتجنب أخطاء المطابقة (مثل .0)
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
        
        # 🎨 تنسيق التباين العالي للجوال والأوسمة الأفقية (CSS المطور)
        st.markdown(f"""
            <style>
            .app-header {{ background: #ffffff; padding: 20px; border-radius: 15px; border-right: 10px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: -50px; text-align: right; border: 1px solid #ddd; }}
            .medal-flex {{ display: flex; justify-content: space-between; gap: 8px; margin: 15px 0; }}
            .m-card {{ flex: 1; background: #ffffff; padding: 15px 5px; border-radius: 15px; text-align: center; border: 2px solid #f1f5f9; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.3s; }}
            .m-active {{ border-color: #f59e0b !important; background: #fffbeb !important; box-shadow: 0 4px 8px rgba(245,158,11,0.2) !important; }}
            .points-banner {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 6px 12px rgba(217, 119, 6, 0.2); }}
            
            /* تباين عالي: نصوص سوداء عريضة جداً للجوال لضمان الوضوح */
            .mobile-card {{ background: #ffffff; color: #000000 !important; padding: 18px; border-radius: 12px; border: 1.5px solid #000; margin-bottom: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-right: 8px solid #1e3a8a; font-size: 1.1rem; }}
            .urgent-msg {{ background: #fff5f5; border: 2px solid #e53e3e; color: #c53030 !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; font-weight: 900; box-shadow: 0 4px 10px rgba(229, 62, 62, 0.1); }}
            </style>
            
            <div class="app-header">
                <h2 style='margin:0; color:#1e3a8a;'>👋 مرحباً بك: {s_name}</h2>
                <p style='margin:5px 0 0 0; color:#000; font-weight:900;'>🏫 الصف الدراسي: {s_class} | 🆔 الرقم: {student_id}</p>
            </div>
        """, unsafe_allow_html=True)

        # --- 🚨 [موقع الشاشة الرئيسية] التنبيه العاجل (مفلتر بالصف وبالحالة) ---
        if not df_ann.empty:
            # التحقق من وجود الحقول لتجنب KeyError
            if 'عاجل' in df_ann.columns and 'الصف' in df_ann.columns:
                df_ann['عاجل'] = df_ann['عاجل'].astype(str).str.strip()
                df_ann['الصف'] = df_ann['الصف'].astype(str).str.strip()
                
                # فلترة ذكية: يظهر التنبيه العاجل (نعم) الموجه لصف الطالب أو للكل
                urgent = df_ann[(df_ann['عاجل'] == 'نعم') & (df_ann['الصف'].isin(['الكل', s_class]))]
                if not urgent.empty:
                    u = urgent.tail(1).iloc[0] # عرض أحدث تنبيه عاجل
                    st.markdown(f"""
                        <div class="urgent-msg">
                            🌟 تنبيه هام لـ {s_class}: {u.get('العنوان', 'تنبيه جديد')} <br>
                            <small style="font-weight:normal;">{u.get('الرابط', u.get('التفاصيل', ''))}</small>
                        </div>
                    """, unsafe_allow_html=True)

        # 🏅 2. الأوسمة الأفقية ورصيد النقاط
        st.markdown(f"""
            <div class="medal-flex">
                <div class="m-card {'m-active' if s_points >= 100 else ''}">🥇<br><b style='color:#000;'>ذهبي</b></div>
                <div class="m-card {'m-active' if s_points >= 50 else ''}">🥈<br><b style='color:#000;'>فضي</b></div>
                <div class="m-card m-active">🥉<br><b style='color:#000;'>برونزي</b></div>
            </div>
            <div class="points-banner">
                <p style='margin:0; font-size: 1rem; opacity:0.9; font-weight:bold;'>رصيد نقاط التميز</p>
                <h1 style='margin:0; font-size: 4rem; font-weight: 900;'>{s_points}</h1>
            </div>
        """, unsafe_allow_html=True)

        # 📱 3. التبويبات المدمجة (نظام الفلترة المطور بأسماء الحقول)
        tabs = st.tabs(["📢 التنبيهات", "📝 الملاحظات", "📊 درجاتي", "🏆 المتصدرين", "⚙️ الإعدادات"])

        # --- تبويب التنبيهات (الفلترة بناءً على حقل الصف - الربط بالأسماء) ---
        with tabs[0]:
            st.markdown(f"#### 📢 سجل تعميمات {s_class}")
            if not df_ann.empty and 'الصف' in df_ann.columns:
                # يظهر للطالب التنبيهات الموجهة لصفه المسجل فقط أو للكل
                student_ann = df_ann[df_ann['الصف'].astype(str).str.strip().isin(['الكل', s_class])]
                if not student_ann.empty:
                    # عرض التعميمات من الأحدث للأقدم
                    for _, row in student_ann.iloc[::-1].iterrows(): 
                        st.markdown(f"""
                            <div class="mobile-card">
                                📢 {row.get('العنوان', 'تعميم جديد')} <br> 
                                <small style='color:#555; font-weight:normal;'>📅 {row.get('التاريخ', '')}</small> <br> 
                                <div style='margin-top:5px; font-weight:normal; font-size:0.95rem;'>{row.get('الرابط', row.get('التفاصيل', ''))}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else: 
                    st.info(f"💡 لا توجد تنبيهات جديدة لـ {s_class} حالياً.")
            else: 
                st.info("💡 سجل التنبيهات فارغ حالياً.")

        # --- تبويب الملاحظات (تباين عالي للجوال) ---
        with tabs[1]:
            st.markdown("#### 📝 ملاحظات المعلم")
            if not df_beh.empty:
                df_beh['clean_id'] = df_beh.iloc[:, 0].astype(str).str.split('.').str[0]
                my_notes = df_beh[df_beh['clean_id'] == student_id]
                if not my_notes.empty:
                    for _, n in my_notes.iterrows():
                        st.markdown(f"""
                            <div class="mobile-card" style="border-right-color:#e53e3e;">
                                📌 {n.get('type', 'تنبيه')}: {n.get('desc', '')} <br> 
                                <small style="font-weight:normal;">📅 {n.get('date', '')}</small>
                            </div>
                        """, unsafe_allow_html=True)
                else: 
                    st.success("🌟 سجلّك مثالي وخالٍ من الملاحظات السلبية.")

        # --- تبويب درجاتي (المسميات العربية الصافية) ---
        with tabs[2]:
            st.markdown("#### 📊 نتائج الاختبارات والمهام")
            if not df_gr.empty:
                df_gr['clean_id'] = df_gr.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                my_gr = df_gr[df_gr['clean_id'] == student_id]
                if not my_gr.empty:
                    g = my_gr.iloc[0]
                    st.markdown(f"""
                        <div class="mobile-card">📝 المشاركة والمهام: {g.get('p1', 0)}</div>
                        <div class="mobile-card">✍️ اختبار قصير: {g.get('p2', 0)}</div>
                        <div class="mobile-card" style="background:#f0fdf4; border-right-color:#10b981; border-width:2px;">
                            🏆 المجموع الكلي: <span style='font-size:1.3rem;'>{g.get('perf', 0)}</span>
                        </div>
                    """, unsafe_allow_html=True)

        # --- تبويب المتصدرين (بطاقات تنافسية) ---
        with tabs[3]:
            st.markdown("#### 🏆 لوحة الشرف (أفضل 10 طلاب)")
            df_st['pts_num'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            top_10 = df_st.sort_values(by="pts_num", ascending=False).head(10)
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
                is_me_style = "border: 2px solid #1e3a8a; background: #eff6ff;" if str(row['clean_id']) == student_id else ""
                st.markdown(f"""
                    <div class="mobile-card" style="{is_me_style}">
                        <span style='font-size:1.2rem;'>{icon}</span> {row['name']} 
                        <span style='float:left; color:#f59e0b;'>{int(row['pts_num'])} ن</span>
                    </div>
                """, unsafe_allow_html=True)

        # --- تبويب الإعدادات (تحديث الملف + الخروج) ---
        with tabs[4]:
            st.markdown("#### ⚙️ إعدادات الحساب")
            with st.form("up_info_final_merged"):
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
                        st.error("❌ فشل التحديث حالياً، يرجى المحاولة لاحقاً.")
            
            st.divider()
            if st.button("🚪 تسجيل الخروج الآمن من المنصة", type="primary", use_container_width=True):
                st.session_state.role = None; st.session_state.username = None; st.rerun()

    else: 
        # رسالة الخطأ عند عدم العثور على الطالب
        st.error(f"⚠️ عذراً، الرقم الأكاديمي ({student_id}) غير مسجل في النظام.")
        if st.button("🔄 العودة لمحاولة الدخول برقم آخر"): 
            st.rerun()

    show_footer() # إظهار الحقوق والتواصل في أسفل الصفحة
