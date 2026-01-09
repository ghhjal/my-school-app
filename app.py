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

# --- [دوال الخدمات الأساسية - التعريف في القمة لمنع الأخطاء] ---

def clean_phone_number(phone):
    """تجهيز رقم الجوال بصيغة دولية"""
    p = str(phone).strip().replace(" ", "")
    if p.startswith("0"): p = p[1:]
    if not p.startswith("966") and p != "": p = "966" + p
    return p

def get_professional_msg(name, b_type, b_desc, date):
    """توليد رسالة الواتساب الاحترافية"""
    msg = (f"🔔 *إشعار من منصة الأستاذ زياد*\n"
            f"------------------\n"
            f"👤 *الطالب:* {name}\n"
            f"📍 *الملاحظة:* {b_type}\n"
            f"📝 *التفاصيل:* {b_desc if b_desc else 'متابعة دورية'}\n"
            f"📅 *التاريخ:* {date}\n"
            f"------------------\n"
            f"🏛️ *منصة زياد الذكية*")
    return urllib.parse.quote(msg)

def show_footer():
    """دالة الفوتر الموحدة"""
    st.markdown("<br><h3 style='text-align:center; color:#1e40af;'>📱 قنوات التواصل والدعم الفني</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown('<a href="#" class="contact-btn">📢 تليجرام الإدارة 👉</a>', unsafe_allow_html=True)
    c2.markdown('<a href="#" class="contact-btn">💬 واتساب المعلم 👉</a>', unsafe_allow_html=True)
    c3.markdown('<a href="#" class="contact-btn">📧 البريد الإلكتروني 👉</a>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:0.8rem; margin-top:20px;'>© 2026 جميع الحقوق محفوظة لمنصة الأستاذ زياد الذكية</p>", unsafe_allow_html=True)

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}"); return None

sh = get_gspread_client()

@st.cache_data(ttl=10) # كاش قصير لضمان تحديث الإعدادات
def fetch_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name); data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty: df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def safe_append_row(worksheet_name, data_dict):
    try:
        ws = sh.worksheet(worksheet_name); headers = ws.row_values(1)
        row_to_append = [data_dict.get(h, "") for h in headers]
        ws.append_row(row_to_append); return True
    except: return False

# --- [تحميل الإعدادات (نظام الثبات القوي)] ---
# هذا الجزء يضمن تحميل الإعدادات من الشيت مباشرة عند كل تشغيل
if "class_options" not in st.session_state:
    try:
        # جلب البيانات وتحويلها إلى قاموس لسهولة الوصول
        sett_data = sh.worksheet("settings").get_all_records()
        settings_map = {row['key']: row['value'] for row in sett_data}

        st.session_state.max_tasks = int(settings_map.get('max_tasks', 60))
        st.session_state.max_quiz = int(settings_map.get('max_quiz', 40))
        st.session_state.current_year = str(settings_map.get('current_year', '1447هـ'))
        
        # معالجة القوائم النصية
        classes_str = str(settings_map.get('class_list', 'الأول, الثاني'))
        st.session_state.class_options = [c.strip() for c in classes_str.split(',') if c.strip()]
        
        stages_str = str(settings_map.get('stage_list', 'ابتدائي'))
        st.session_state.stage_options = [s.strip() for s in stages_str.split(',') if s.strip()]
        
    except Exception as e:
        # قيم افتراضية للطوارئ فقط
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40
        st.session_state.current_year = "1447هـ"
        st.session_state.class_options = ["الأول", "الثاني"]
        st.session_state.stage_options = ["ابتدائي"]

if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = None

# ==========================================
# 🎨 2. التصميم البصري الموحد (إصدار الأزرق الملكي والموقع الصحيح)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; background-color: #f8fafc; }
    
    .block-container { padding-top: 0rem; padding-bottom: 5rem; }
    
    /* --- تنسيق الهيدر (رأس الصفحة) --- */
    .header-container {
        display: flex;
        flex-direction: row-reverse; 
        align-items: center;
        justify-content: center;
        /* ✅ العودة للون الأزرق الملكي الصافي */
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        
        /* ✅ زيادة الحشوة العلوية لإنزال المحتوى للأسفل */
        padding-top: 80px; 
        padding-bottom: 40px;
        padding-left: 20px;
        padding-right: 20px;
        
        border-radius: 0 0 35px 35px;
        margin-top: -60px; 
        margin-left: -5rem; 
        margin-right: -5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        color: white;
        text-align: center;
    }

    .logo-icon {
        font-size: 6rem;
        margin-right: 25px;
        /* ✅ إنزال القبعة أكثر لتكون في المنتصف */
        margin-top: 15px; 
        filter: drop-shadow(0px 5px 10px rgba(0,0,0,0.3));
        animation: float 3s ease-in-out infinite;
    }

    .header-text h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 900;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        line-height: 1.2;
    }

    .header-text p {
        margin: 5px 0 0 0;
        color: #dbeafe; /* لون سماوي فاتح جداً للنص الفرعي */
        font-size: 1.2rem;
        font-weight: bold;
    }

    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

    /* --- تحسينات الجوال --- */
    @media (max-width: 768px) {
        .header-container {
            flex-direction: column;
            /* ✅ مسافة أكبر في الجوال لمنع الاختفاء في الأعلى */
            padding-top: 100px; 
            padding-bottom: 30px;
        }
        .logo-icon {
            font-size: 5rem;
            margin-right: 0;
            margin-top: 0;
            margin-bottom: 10px;
        }
        .header-text h1 {
            font-size: 2.2rem;
        }
    }

    /* --- بقية التنسيقات --- */
    div[data-baseweb="input"] { 
        background-color: #f0f9ff !important; 
        border: 2px solid #3b82f6 !important; 
        border-radius: 12px !important; 
        height: 50px;
    }
    input { color: #1e3a8a !important; font-weight: bold !important; font-size: 1.1rem !important; }

    .contact-btn { 
        display: block; 
        padding: 12px; 
        background: white; 
        border: 2px solid #e2e8f0; 
        border-radius: 12px; 
        color: #1e3a8a !important; 
        text-decoration: none; 
        font-weight: bold; 
        text-align: center; 
        margin-bottom: 10px;
        transition: 0.3s; 
    }
    .contact-btn:hover { background: #eff6ff; border-color: #3b82f6; transform: translateY(-2px); }
    </style>

    <div class="header-container">
        <div class="logo-icon">🎓</div>
        <div class="header-text">
            <h1>منصة الأستاذ زياد الذكية</h1>
            <p>بوابة التعليم المتطورة والإدارة الشاملة - 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 3. نظام الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "👨‍💼 بوابة المعلم"])
    with t1:
        with st.form("st_log_v26"):
            sid_in = st.text_input("🆔 الرقم الأكاديمي الموحد").strip()
            if st.form_submit_button("انطلق للمنصة 🚀", use_container_width=True):
                df_st = fetch_safe("students")
                if not df_st.empty:
                    df_st['clean_id'] = df_st.iloc[:, 0].astype(str).str.strip().str.split('.').str[0]
                    if sid_in.split('.')[0] in df_st['clean_id'].values:
                        st.session_state.username, st.session_state.role = sid_in.split('.')[0], "student"; st.rerun()
                    else: st.error("❌ الرقم غير مسجل. تواصل مع معلمك.")
    with t2:
        with st.form("admin_log_v26"):
            u = st.text_input("👤 اسم المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة 🛠️", use_container_width=True):
                df_u = fetch_safe("users")
                if not df_u.empty and u in df_u['username'].values:
                    user_data = df_u[df_u['username']==u].iloc[0]
                    if hashlib.sha256(str.encode(p)).hexdigest() == user_data['password_hash']:
                        st.session_state.role, st.session_state.username = "teacher", u; st.rerun()
                st.error("❌ بيانات خاطئة.")
    show_footer()
    
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
    # 📊 التبويب 1: التقييم والمتابعة (الإصدار المطور: تحديث + حذف + عرض)
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
                s_name = s_info['name'] 
                
                # بيانات التواصل
                cl_p = clean_phone_number(s_info.get('الجوال', ''))
                s_mail = s_info.get('الإيميل', '')

                c_g, c_b = st.columns(2)

                # ==========================================
                # 📝 القسم الأيمن: رصد وتحديث الدرجات
                # ==========================================
                with c_g:
                    st.markdown("##### 📝 رصد وتحديث الدرجات")
                    
                    # جلب الدرجات الحالية لعرضها في النموذج (اختياري، هنا نبدأ من الصفر أو نعرض القيمة)
                    df_grades_curr = fetch_safe("grades")
                    curr_p1 = 0; curr_p2 = 0
                    if not df_grades_curr.empty:
                        # البحث عن درجات الطالب
                        g_row = df_grades_curr[df_grades_curr.iloc[:, 0] == sid]
                        if not g_row.empty:
                            curr_p1 = int(pd.to_numeric(g_row.iloc[0]['p1'], errors='coerce') or 0)
                            curr_p2 = int(pd.to_numeric(g_row.iloc[0]['p2'], errors='coerce') or 0)

                    with st.form("grade_f_v26"):
                        # عرض الدرجات الحالية كقيم افتراضية
                        v_t = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0, st.session_state.max_tasks, value=curr_p1)
                        v_q = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0, st.session_state.max_quiz, value=curr_p2)
                        
                        if st.form_submit_button("💾 تحديث الدرجات"):
                            try:
                                ws_gr = sh.worksheet("grades")
                                cell = ws_gr.find(sid) # البحث عن الطالب
                                
                                total_perf = v_t + v_q
                                # إذا وجدنا الطالب -> نحدث الصف
                                if cell:
                                    # نفترض ترتيب الأعمدة: student_id, p1, p2, perf, date
                                    ws_gr.update_cell(cell.row, 2, v_t)      # p1
                                    ws_gr.update_cell(cell.row, 3, v_q)      # p2
                                    ws_gr.update_cell(cell.row, 4, total_perf) # perf
                                    ws_gr.update_cell(cell.row, 5, str(datetime.date.today())) # date
                                    st.success("✅ تم تحديث درجات الطالب بنجاح")
                                else:
                                    # إذا لم نجده -> نضيف صف جديد
                                    new_row = [sid, v_t, v_q, total_perf, str(datetime.date.today())]
                                    ws_gr.append_row(new_row)
                                    st.success("✅ تم رصد الدرجات لأول مرة")
                                
                                st.cache_data.clear() # مسح الكاش لتحديث الجدول بالأسفل
                            except Exception as e:
                                st.error(f"❌ حدث خطأ: {e}")

                    # 📊 عرض جدول الدرجات الحالي للطالب (للتأكد)
                    st.caption("📋 الدرجات الحالية المسجلة في النظام:")
                    if not df_grades_curr.empty:
                        my_g_view = df_grades_curr[df_grades_curr.iloc[:, 0] == sid]
                        if not my_g_view.empty:
                            # عرض أنيق للدرجات
                            g_data = my_g_view.iloc[0]
                            st.info(f"📌 **المشاركة:** {g_data.get('p1')} | **الاختبار:** {g_data.get('p2')} | **المجموع:** {g_data.get('perf')}")
                        else:
                            st.warning("لم يتم رصد درجات لهذا الطالب بعد.")

                # ==========================================
                # 🎭 القسم الأيسر: سلوكيات + تحديث نقاط
                # ==========================================
                with c_b:
                    st.markdown("##### 🎭 المتابعة السلوكية")
                    with st.form("beh_f_v26_auto", clear_on_submit=True):
                        b_type = st.selectbox("نوع السلوك:", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "📚 نقص كتاب (-5)", "✍️ نقص واجب (-5)", "🖊️ نقص قلم (-5)", "🚫 سلبي (-10)"])
                        b_msg = st.text_area("الملاحظة")
                        
                        if st.form_submit_button("💾 تسجيل وتحديث النقاط"):
                            # 1. تسجيل الملاحظة
                            beh_data = {
                                "student_id": sid, 
                                "date": str(datetime.date.today()), 
                                "type": b_type, 
                                "note": b_msg
                            }
                            if safe_append_row("behavior", beh_data):
                                # 2. تحديث النقاط تلقائياً
                                try:
                                    import re
                                    score_match = re.search(r'\(([\+\-]?\d+)\)', b_type)
                                    score_change = int(score_match.group(1)) if score_match else 0
                                    
                                    if score_change != 0:
                                        ws_st = sh.worksheet("students")
                                        cell = ws_st.find(sid)
                                        if cell:
                                            headers = ws_st.row_values(1)
                                            if 'النقاط' in headers:
                                                col_idx = headers.index('النقاط') + 1
                                                current_val = ws_st.cell(cell.row, col_idx).value
                                                current_points = int(current_val) if current_val and str(current_val).isdigit() else 0
                                                new_total = current_points + score_change
                                                ws_st.update_cell(cell.row, col_idx, new_total)
                                                st.toast(f"📈 الرصيد الجديد: {new_total}")
                                except Exception as e:
                                    st.warning(f"تم التسجيل، خطأ في النقاط: {e}")

                                st.success("✅ تم الحفظ")
                                st.cache_data.clear(); st.rerun()

                # ==========================================
                # 📜 السجل التاريخي (مع زر الحذف)
                # ==========================================
                st.divider()
                st.markdown(f"#### 📜 سجل ملاحظات الطالب: {s_name}")
                df_beh = fetch_safe("behavior")
                
                if not df_beh.empty:
                    # فلترة ملاحظات الطالب
                    col_id = 'student_id' if 'student_id' in df_beh.columns else df_beh.columns[0]
                    # نحتفظ بالـ index الأصلي للحذف
                    my_beh = df_beh[df_beh[col_id].astype(str) == str(sid)]
                else:
                    my_beh = pd.DataFrame()
                
                if not my_beh.empty:
                    # التكرار مع الحفاظ على الفهرس (idx) لحذفه من الشيت
                    for idx, r in my_beh.iterrows():
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 1, 0.5]) 
                            
                            with c1:
                                d_val = r.get('date', '')
                                t_val = r.get('type', '')
                                n_val = r.get('note', '')
                                st.markdown(f"**{t_val}** | 📅 {d_val}")
                                if n_val: st.caption(f"📝 {n_val}")
                            
                            with c2:
                                # أزرار التواصل
                                m_enc = get_professional_msg(s_name, t_val, n_val, d_val)
                                st.link_button("واتساب", f"https://api.whatsapp.com/send?phone={cl_p}&text={m_enc}", use_container_width=True)
                            
                            with c3:
                                # 🗑️ زر الحذف (جديد)
                                if st.button("🗑️", key=f"del_beh_{idx}"):
                                    try:
                                        # حذف الصف من الشيت (index + 2 لأن أول صف عناوين و index يبدأ من 0)
                                        sh.worksheet("behavior").delete_rows(int(idx) + 2)
                                        st.success("حُذفت")
                                        st.cache_data.clear(); st.rerun()
                                    except Exception as e:
                                        st.error("خطأ")
                else:
                    st.info("💡 لا توجد ملاحظات مسجلة.")
        else:
            st.info("💡 لا يوجد طلاب في قاعدة البيانات.")
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
    # ⚙️ التبويب 3: الإعدادات والتحكم الشامل (النسخة النهائية الكاملة 2026)
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
                    all_data = ws_st.get_all_values()
                    if len(all_data) > 1:
                        row_count = len(all_data)
                        zero_fill = [[0]] * (row_count - 1)
                        ws_st.update(range_name=f"I2:I{row_count}", values=zero_fill)
                        st.success("✅ تم تصفير نقاط جميع الطلاب بنجاح!")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.warning("⚠️ لا يوجد طلاب لتصفير نقاطهم.")
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء التصفير: {e}")

        # 2. تحديث القوائم والدرجات (ديناميكي)
        with st.expander("📝 تحديث القوائم والدرجات (ديناميكي)"):
            st.info("💡 التعديلات هنا تنعكس فوراً على النظام.")
            
            c_y = st.text_input("🗓️ العام الدراسي الحالي:", st.session_state.current_year)
            
            c_cls, c_stg = st.columns(2)
            cls_txt = c_cls.text_area("🏫 الصفوف (افصل بفاصلة):", ", ".join(st.session_state.class_options))
            stg_txt = c_stg.text_area("🎓 المراحل (افصل بفاصلة):", ", ".join(st.session_state.stage_options))
            
            c_mk, c_mq = st.columns(2)
            n_mt = c_mk.number_input("درجة المشاركة القصوى:", 0, 100, st.session_state.max_tasks)
            n_mq = c_mq.number_input("درجة الاختبار القصوى:", 0, 100, st.session_state.max_quiz)
            
            if st.button("💾 حفظ الإعدادات وتحديث النظام"):
                try:
                    ws_s = sh.worksheet("settings")
                    # تحديث الخلايا دفعة واحدة
                    batch_updates = [
                        {'range': 'B2', 'values': [[n_mt]]}, {'range': 'B3', 'values': [[n_mq]]},
                        {'range': 'B4', 'values': [[c_y]]}, {'range': 'B5', 'values': [[cls_txt]]},
                        {'range': 'B6', 'values': [[stg_txt]]}
                    ]
                    ws_s.batch_update(batch_updates)
                    
                    # تحديث الذاكرة الحية
                    st.session_state.max_tasks = n_mt
                    st.session_state.max_quiz = n_mq
                    st.session_state.current_year = c_y
                    st.session_state.class_options = [x.strip() for x in cls_txt.split(',') if x.strip()]
                    st.session_state.stage_options = [x.strip() for x in stg_txt.split(',') if x.strip()]
                    
                    st.success("✅ تم الحفظ وتحديث النظام بنجاح."); st.cache_data.clear(); st.rerun()
                except Exception as e:
                    st.error(f"❌ خطأ في الحفظ: {e}")

        # 3. المزامنة الذكية (الكود المطور والمدمج)
        with st.expander("📤 المزامنة الذكية (رفع ملفات Excel)"):
            st.info("💡 سيقوم النظام بتحديث البيانات وتجاهل الصفوف الفارغة.")
            up_file = st.file_uploader("اختر ملف الإكسل (xlsx)", type=['xlsx'])
            target_sheet = st.radio("الجدول المستهدف:", ["students", "grades"], horizontal=True)
            
            if st.button("🚀 بدء المزامنة"):
                if up_file:
                    try:
                        with st.status("⏳ جاري المعالجة...", expanded=True) as status:
                            # قراءة الملف وتنظيفه
                            df_up = pd.read_excel(up_file, engine='openpyxl').fillna("")
                            df_up = df_up.dropna(how='all')
                            
                            ws = sh.worksheet(target_sheet)
                            # جلب المعرفات الحالية للمقارنة
                            current_data = ws.get_all_records()
                            current_ids = [str(row.get('id', row.get('student_id', ''))) for row in current_data]
                            headers = ws.row_values(1)
                            
                            up_c = 0; new_c = 0; skip_c = 0
                            
                            for _, row in df_up.iterrows():
                                d = row.to_dict()
                                # توحيد اسم المعرف
                                raw_id = str(d.get('student_id', d.get('id', ''))).strip()
                                id_v = raw_id.split('.')[0] # إزالة الفواصل العشرية
                                
                                if not id_v or id_v == '0':
                                    skip_c += 1; continue
                                
                                # تجهيز البيانات حسب نوع الجدول
                                if target_sheet == "grades":
                                    p1 = int(pd.to_numeric(d.get('p1', 0), errors='coerce') or 0)
                                    p2 = int(pd.to_numeric(d.get('p2', 0), errors='coerce') or 0)
                                    d.update({"student_id": id_v, "p1": p1, "p2": p2, "perf": p1+p2, "date": str(datetime.date.today())})
                                    if 'id' in d: del d['id']
                                else:
                                    d['id'] = id_v
                                    if 'الجوال' in d: d['الجوال'] = clean_phone_number(d['الجوال'])
                                    # ضمان وجود قيمة للنقاط
                                    if 'النقاط' not in d or str(d.get('النقاط', '')).strip() == "": d['النقاط'] = 0

                                # التحديث أو الإضافة
                                if id_v in current_ids:
                                    row_idx = current_ids.index(id_v) + 2 
                                    row_vals = [str(d.get(h, "")) for h in headers]
                                    ws.update(range_name=f"A{row_idx}", values=[row_vals])
                                    up_c += 1
                                else:
                                    row_vals = [str(d.get(h, "")) for h in headers]
                                    ws.append_row(row_vals)
                                    new_c += 1
                            
                            status.update(label="✅ تمت العملية!", state="complete", expanded=False)
                        st.success(f"النتيجة: ✅ تحديث {up_c} | ➕ إضافة {new_c} | ⚠️ تجاهل {skip_c}")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")

        # 4. إدارة المستخدمين (تمت إعادة الميزة المفقودة)
        with st.expander("🔐 إدارة المستخدمين (إضافة معلم/إداري)"):
            with st.form("add_user_v26_final", clear_on_submit=True):
                st.write("إضافة مستخدم جديد للنظام:")
                new_u = st.text_input("👤 اسم المستخدم")
                new_p = st.text_input("🔑 كلمة المرور", type="password")
                
                if st.form_submit_button("➕ إضافة المستخدم"):
                    if new_u and new_p:
                        # تشفير كلمة المرور قبل الحفظ
                        h_p = hashlib.sha256(str.encode(new_p)).hexdigest()
                        # الإضافة لجدول المستخدمين
                        if safe_append_row("users", {"username": new_u, "password_hash": h_p, "role": "teacher"}):
                            st.success(f"✅ تم إضافة المستخدم {new_u} بنجاح")
                            st.cache_data.clear()
                    else:
                        st.warning("⚠️ يرجى إدخال الاسم وكلمة المرور")

        # 5. الأمان والنسخ الاحتياطي
        with st.expander("📂 النسخ الاحتياطي والقوالب"):
            t1, t2 = st.tabs(["تغيير الباسوورد", "تنزيل القوالب"])
            
            with t1:
                with st.form("chg_pwd_main"):
                    np = st.text_input("كلمة المرور الجديدة", type="password")
                    if st.form_submit_button("تحديث"):
                        if np:
                            hp = hashlib.sha256(str.encode(np)).hexdigest()
                            # تحديث للمستخدم الحالي (Admin كمثال)
                            df_u = fetch_safe("users")
                            curr_user = st.session_state.get('username', 'admin')
                            if curr_user in df_u['username'].values:
                                u_idx = df_u[df_u['username'] == curr_user].index[0] + 2
                                sh.worksheet("users").update_cell(u_idx, 2, hp)
                                st.success("✅ تم التغيير")
                            else: st.error("المستخدم غير موجود")
            
            with t2:
                b1 = io.BytesIO()
                pd.DataFrame(columns=["id", "name", "class", "year", "sem", "الجوال", "الإيميل", "النقاط"]).to_excel(b1, index=False)
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

        # ---------------------------------------------------------
        # ⚙️ تبويب 4: إعدادات الحساب (تحديث البيانات الشخصية)
        # ---------------------------------------------------------
        with tabs[4]:
            st.markdown("#### ⚙️ تحديث بيانات التواصل")
            with st.form("up_info_student_v26"):
                # عرض البيانات الحالية
                current_mail = s_data.get('الإيميل', '')
                current_phone = s_data.get('الجوال', '')
                
                new_mail = st.text_input("📧 البريد الإلكتروني", value=current_mail)
                new_phone = st.text_input("📱 رقم الجوال", value=current_phone)
                
                if st.form_submit_button("💾 حفظ التعديلات"):
                    try:
                        # ✅ خطوة التصحيح: تنظيف الرقم وتنسيقه (966) قبل الحفظ
                        final_phone = clean_phone_number(new_phone) if new_phone else ""

                        ws_st = sh.worksheet("students")
                        # البحث عن رقم السطر باستخدام المعرف
                        cell = ws_st.find(student_id)
                        if cell:
                            # تحديد أرقام أعمدة الجوال والإيميل ديناميكياً
                            headers = ws_st.row_values(1)
                            
                            # البحث عن موقع عمود 'الإيميل' و 'الجوال'
                            if 'الإيميل' in headers and 'الجوال' in headers:
                                col_mail = headers.index('الإيميل') + 1
                                col_phone = headers.index('الجوال') + 1
                                
                                # التحديث في الخلايا الصحيحة
                                ws_st.update_cell(cell.row, col_mail, new_mail)
                                ws_st.update_cell(cell.row, col_phone, final_phone) # تم استخدام الرقم المنسق
                                
                                st.success("✅ تم تحديث بياناتك بنجاح!")
                                st.cache_data.clear() # مسح الكاش لرؤية التغيير
                            else:
                                st.error("⚠️ لم يتم العثور على أعمدة 'الجوال' أو 'الإيميل' في الجدول.")
                        else:
                            st.error("❌ لم يتم العثور على سجلك في قاعدة البيانات.")
                    except Exception as e: 
                        st.error(f"❌ حدث خطأ: {e}")
            
            st.divider()
            if st.button("🚪 تسجيل الخروج الآمن", type="primary", use_container_width=True):
                st.session_state.role = None
                st.session_state.username = None
                st.rerun()
    else: 
        # رسالة الخطأ عند عدم العثور على الطالب
        st.error(f"⚠️ عذراً، الرقم الأكاديمي ({student_id}) غير مسجل في النظام.")
        if st.button("🔄 العودة لمحاولة الدخول برقم آخر"): 
            st.rerun()

    show_footer() # إظهار الحقوق والتواصل في أسفل الصفحة
