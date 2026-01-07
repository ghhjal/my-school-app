import streamlit as st
import gspread
import pandas as pd
import hashlib
import datetime
import urllib.parse
import io
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 1. إعدادات النظام والاستقرار الأساسية
# ==========================================
# يجب أن يكون أول أمر Streamlit لضمان عمل الواجهة
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# الاتصال بـ Google Sheets عبر نظام Secrets
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من إعدادات Secrets.")
        return None

sh = get_gspread_client()

# تهيئة الذاكرة المؤقتة (Session State)
if "role" not in st.session_state: st.session_state.role = None
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

# تحميل الإعدادات الدائمة من شيت settings لضمان ثبات التوزيع
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40

# ==========================================
# 🧠 2. دوال معالجة البيانات الاحترافية
# ==========================================
@st.cache_data(ttl=30)
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

def get_col_idx(df, col_name):
    try: return df.columns.get_loc(col_name) + 1
    except: return None

# ==========================================
# 🎨 3. التصميم البصري (RTL + Cairo Font)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin: -80px -20px 25px -20px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .stMetric { background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    div[data-testid="stForm"] { border-radius: 15px !important; border: 1px solid #eee !important; }
    </style>
    <div class="header-section">
        <h1>🏛️ منصة زياد الذكية</h1>
        <p>الإصدار الإداري الشامل والمستقر - 2026</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 4. نظام الدخول والحماية
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
# 👨‍🏫 5. واجهة المعلم (المكتملة بجميع المميزات)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- تبويب الطلاب (إحصائيات + بحث + إضافة كاملة + حذف) ---
    with menu[0]:
        st.subheader("👥 إدارة قاعدة الطلاب")
        df_st = fetch_safe("students")
        if not df_st.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            c2.metric("🏫 الصفوف", len(df_st.iloc[:, 4].unique()) if len(df_st.columns) > 4 else 1)
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            c4.metric("🗓️ العام", df_st.iloc[0, 3] if len(df_st.columns) > 3 else "1447هـ")
            
            st.divider()
            search_q = st.text_input("🔍 محرك البحث الذكي (الاسم أو الرقم):")
            
            with st.expander("➕ إضافة طالب جديد يدوياً بكافة الحقول"):
                with st.form("add_st_full", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    f_id = col1.text_input("🔢 الرقم الأكاديمي")
                    f_name = col2.text_input("👤 الاسم الثلاثي")
                    col3, col4, col5 = st.columns(3)
                    f_stage = col3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    f_year = col4.text_input("🗓️ العام", "1447هـ")
                    f_class = col5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    f_mail = st.text_input("📧 الإيميل")
                    f_phone = st.text_input("📱 الجوال (966...)")
                    if st.form_submit_button("✅ اعتماد وحفظ"):
                        sh.worksheet("students").append_row([f_id, f_name, f_class, f_year, f_stage, f_mail, f_phone, "0"])
                        st.success("تمت الإضافة"); st.cache_data.clear(); st.rerun()

            df_disp = df_st[df_st.iloc[:, 0].str.contains(search_q) | df_st.iloc[:, 1].str.contains(search_q)] if search_q else df_st
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

    # ==========================================
    # 📊 تبويب: التقييم والمتابعة (الإصدار الشامل - 2026)
    # ==========================================
    with menu[1]:
        st.subheader("📊 مركز تقييم الطلاب والمتابعة السلوكية")
        
        # 1. جلب البيانات الأساسية للعمل
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # نظام اختيار الطالب الذكي
            st_list = {f"{row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected_label = st.selectbox("🎯 اختر الطالب لبدء التقييم:", [""] + list(st_list.keys()), key="eval_select_box")
            
            if selected_label:
                sid = st_list[selected_label]
                # جلب تفاصيل الطالب المختار بدقة
                student_info = df_st[df_st.iloc[:, 0] == sid].iloc[0]
                s_name = student_info.iloc[1]
                s_phone = student_info['الجوال'] if 'الجوال' in student_info else ""
                s_email = student_info['الإيميل'] if 'الإيميل' in student_info else ""
    
                # --- 💡 دالة التنسيق الاحترافي (لضمان سلامة اللغة العربية وتنسيق الواتساب) ---
                def get_professional_msg(name, b_type, b_desc, date):
                    msg = (
                        f"🔔 *إشعار من منصة الأستاذ زياد الذكية*\n"
                        f"---------------------------------------\n"
                        f"👤 *الطالب:* {name}\n"
                        f"📍 *الملاحظة:* {b_type}\n"
                        f"📝 *التفاصيل:* {b_desc if b_desc else 'متابعة روتينية'}\n"
                        f"📅 *التاريخ:* {date}\n"
                        f"---------------------------------------\n"
                        f"🏛️ *منصة زياد الذكية - 2026*"
                    )
                    return urllib.parse.quote(msg)
    
                # تقسيم الشاشة لجزئين: درجات وسلوك
                col_grades, col_behavior = st.columns(2)
    
                # --- 📝 1. رصد وتحرير الدرجات (بصمام أمان الإعدادات) ---
                with col_grades:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_form_final", clear_on_submit=False):
                        v_tasks = st.number_input(f"المشاركة (الحد: {st.session_state.max_tasks})", 0, 100, 0)
                        v_quiz = st.number_input(f"الاختبار (الحد: {st.session_state.max_quiz})", 0, 100, 0)
                        total = v_tasks + v_quiz
                        
                        if st.form_submit_button("💾 حفظ الدرجات"):
                            if v_tasks <= st.session_state.max_tasks and v_quiz <= st.session_state.max_quiz:
                                ws_g = sh.worksheet("grades")
                                # تحديث الإكسل
                                ws_g.append_row([sid, v_tasks, v_quiz, total, str(datetime.date.today())])
                                st.success(f"✅ تم رصد درجات الطالب: {s_name}")
                                st.cache_data.clear()
                            else:
                                st.error(f"⚠️ تجاوزت الحد المسموح به في الإعدادات!")
    
                # --- 🎭 2. سجل السلوك والنقاط (مع حقل التاريخ المفقود) ---
                with col_behavior:
                    st.markdown("##### 🎭 سجل السلوك وتحديث النقاط")
                    with st.form("behavior_form_final", clear_on_submit=True):
                        # إرجاع حقل التاريخ المطلوب
                        b_date = st.date_input("📅 تاريخ الملاحظة", datetime.date.today())
                        
                        b_type = st.selectbox("نوع السلوك المرصود:", [
                            "🌟 متميز (+10)", "✅ مشاركة إيجابية (+5)", "⚠️ تنبيه شفوي (0)", 
                            "📚 لم يحضر الكتاب (-5)", "✍️ لم يحل الواجب (-5)", 
                            "🖊️ لم يحضر القلم (-5)", "🚫 سلوك غير لائق (-10)"
                        ])
                        b_desc = st.text_area("تفاصيل الملاحظة:")
                        
                        if st.form_submit_button("💾 تسجيل الملاحظة وتحديث النقاط"):
                            try:
                                # 1. حفظ في شيت behavior
                                sh.worksheet("behavior").append_row([sid, str(b_date), b_type, b_desc])
                                
                                # 2. تحديث رصيد النقاط تلقائياً في شيت الطلاب
                                p_map = {"متميز": 10, "إيجابية": 5, "الكتاب": -5, "الواجب": -5, "القلم": -5, "غير لائق": -10}
                                change = next((v for k, v in p_map.items() if k in b_type), 0)
                                
                                current_p = int(pd.to_numeric(student_info['النقاط'], errors='coerce') or 0)
                                row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                                col_p_idx = df_st.columns.get_loc("النقاط") + 1
                                sh.worksheet("students").update_cell(row_idx, col_p_idx, str(current_p + change))
                                
                                st.success("✅ تم التسجيل وتحديث نقاط الطالب بنجاح!")
                                st.cache_data.clear(); st.rerun()
                            except Exception as e:
                                st.error(f"⚠️ خطأ أثناء الحفظ: {e}")
    
                st.divider()
    
                # --- 📜 3. السجل التاريخي وقنوات التواصل (استعادة التنسيق) ---
                st.markdown(f"#### 📜 متابعة وتواصل: {s_name}")
                t_log, t_msg = st.tabs(["📝 الملاحظات السابقة", "📲 التواصل مع ولي الأمر"])
                
                with t_log:
                    df_beh = fetch_safe("behavior")
                    my_beh = df_beh[df_beh.iloc[:, 0] == sid]
                    if not my_beh.empty:
                        # عرض التاريخ والنوع والملاحظة بوضوح
                        for _, row in my_beh.iloc[::-1].iterrows():
                            with st.container(border=True):
                                st.write(f"📅 **التاريخ:** {row.iloc[1]} | **النوع:** {row.iloc[2]}")
                                if row.iloc[3]: st.info(f"📝 {row.iloc[3]}")
                    else:
                        st.info("لا توجد ملاحظات مسجلة مسبقاً لهذا الطالب.")
    
                with t_msg:
                    st.write("📢 إرسال تقرير فوري ومنسق لولي الأمر:")
                    
                    # إعداد الرسالة المنسقة والمشفرة
                    # نأخذ بيانات آخر ملاحظة تم تسجيلها أو متابعة عامة
                    current_type = b_type if 'b_type' in locals() else "متابعة دورية"
                    current_desc = b_desc if 'b_desc' in locals() else ""
                    current_date = str(b_date) if 'b_date' in locals() else str(datetime.date.today())
                    
                    encoded_msg = get_professional_msg(s_name, current_type, current_desc, current_date)
                    
                    c_wa, c_ml = st.columns(2)
                    # رابط الواتساب المنسق (يعمل بكفاءة)
                    c_wa.link_button("📲 إرسال عبر WhatsApp", f"https://api.whatsapp.com/send?phone={s_phone}&text={encoded_msg}", use_container_width=True)
                    # رابط الإيميل المنسق (يعمل بكفاءة)
                    c_ml.link_button("📧 إرسال عبر البريد", f"mailto:{s_email}?subject=تقرير متابعة الطالب&body={encoded_msg}", use_container_width=True)
    
        else:
            st.warning("⚠️ لا يوجد طلاب في القاعدة. يرجى إضافة طلاب أولاً.")

    # --- تبويب الإعدادات (توزيع الدرجات الدائم + باسوورد + رفع إكسل) ---
    with menu[3]:
        st.subheader("⚙️ أدوات التحكم المتقدمة")
        with st.expander("⚖️ توزيع الدرجات (حفظ دائم)", expanded=True):
            c1, c2 = st.columns(2)
            nt = c1.number_input("حد المشاركة", 1, 100, st.session_state.max_tasks)
            nq = c2.number_input("حد الاختبار", 1, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ في القاعدة"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, nt); ws_s.update_cell(3, 2, nq)
                st.session_state.max_tasks, st.session_state.max_quiz = nt, nq
                st.success("✅ تم الحفظ الدائم"); st.rerun()
        
        with st.expander("🔐 تغيير كلمة المرور"):
            df_u = fetch_safe("users")
            user_fix = st.selectbox("المستخدم:", df_u['username'].tolist() if not df_u.empty else [])
            new_p = st.text_input("الكلمة الجديدة", type="password")
            if st.button("تحديث"):
                u_hash = hashlib.sha256(str.encode(new_p)).hexdigest()
                row_idx = df_u[df_u['username'] == user_fix].index[0] + 2
                sh.worksheet("users").update_cell(row_idx, 2, u_hash); st.success("تم التحديث")

        with st.expander("📤 رفع بيانات الطلاب من Excel"):
            up_f = st.file_uploader("اختر ملف إكسل", type=["xlsx"])
            if up_f and st.button("🚀 بدء الرفع"):
                df_up = pd.read_excel(up_f).fillna("")
                sh.worksheet("students").append_rows(df_up.values.tolist())
                st.success("✅ تم الرفع بنجاح"); st.cache_data.clear()

    with menu[4]:
        if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 6. واجهة الطالب (الترتيب + النقاط + التنبيهات)
# ==========================================
if st.session_state.role == "student":
    df_s = fetch_safe("students"); df_g = fetch_safe("grades")
    df_ex = fetch_safe("exams"); s_id = st.session_state.sid
    s_row = df_s[df_s.iloc[:, 0] == s_id].iloc[0]
    
    st.markdown(f"<div class='header-section'><h2>🎯 مرحباً: {s_row.iloc[1]}</h2>🏆 نقاطك: {s_row['النقاط']} | 🏫 {s_row.iloc[2]}</div>", unsafe_allow_html=True)
    t_ex, t_grade, t_beh, t_lead = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال"])

    with t_grade:
        my_g = df_g[df_g.iloc[:, 0] == s_id]
        if not my_g.empty:
            df_rank = df_g.copy(); df_rank.iloc[:, 3] = pd.to_numeric(df_rank.iloc[:, 3], errors='coerce').fillna(0)
            df_sorted = df_rank.sort_values(by=df_rank.columns[3], ascending=False).reset_index(drop=True)
            rank = df_sorted[df_sorted.iloc[:, 0] == s_id].index[0] + 1
            c1, c2, c3 = st.columns(3)
            c1.metric("📚 المشاركة", f"{my_g.iloc[0, 1]} / {st.session_state.max_tasks}")
            c2.metric("📝 الاختبار", f"{my_g.iloc[0, 2]} / {st.session_state.max_quiz}")
            c3.metric("🏆 المجموع", f"{my_g.iloc[0, 3]} / 100")
            st.success(f"🥇 ترتيبك الحالي: {rank} من {len(df_sorted)}")
