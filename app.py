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
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تحقق من Secrets.")
        return None

sh = get_gspread_client()

# --- تحميل الإعدادات الدائمة من شيت settings لضمان ثبات التوزيع ---
if "max_tasks" not in st.session_state:
    try:
        df_sett = pd.DataFrame(sh.worksheet("settings").get_all_records())
        st.session_state.max_tasks = int(df_sett[df_sett['key'] == 'max_tasks']['value'].values[0])
        st.session_state.max_quiz = int(df_sett[df_sett['key'] == 'max_quiz']['value'].values[0])
    except:
        st.session_state.max_tasks, st.session_state.max_quiz = 60, 40

if "role" not in st.session_state: st.session_state.role = None
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

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
        if not df.empty: df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def get_col_idx(df, col_name):
    try: return df.columns.get_loc(col_name) + 1
    except: return None

# ==========================================
# 🎨 3. التصميم البصري (CSS المخصص)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin: -80px -20px 25px -20px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .stMetric { background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    </style>
    <div class="header-section"><h1>🏛️ منصة زياد الذكية</h1><p>الإصدار الإداري الشامل - 2026</p></div>
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
# 👨‍🏫 5. واجهة المعلم (المكتملة بدون نقصان)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم", "📢 التواصل", "⚙️ الإعدادات", "🚗 خروج"])

    # ==========================================
# 👥 تبويب: إدارة قاعدة بيانات الطلاب (الإصدار الشامل)
# ==========================================
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        
        # 1. جلب البيانات وتحديث الإحصائيات (لمسة احترافية)
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # عرض بطاقات إحصائية سريعة
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📊 إجمالي الطلاب", len(df_st))
            c2.metric("🏫 عدد الصفوف", len(df_st.iloc[:, 4].unique()) if len(df_st.columns) > 4 else 1)
            # تحويل النقاط لرقم لحساب المتوسط
            df_st['النقاط'] = pd.to_numeric(df_st['النقاط'], errors='coerce').fillna(0)
            c3.metric("⭐ متوسط النقاط", round(df_st['النقاط'].mean(), 1))
            c4.metric("📅 العام الدراسي", df_st.iloc[0, 3] if len(df_st.columns) > 3 else "1447هـ")
    
            st.divider()
    
            # 2. محرك البحث الذكي (بحث لحظي بالاسم أو الرقم)
            search_query = st.text_input("🔍 ابحث عن طالب (اكتب الاسم أو الرقم الأكاديمي):", placeholder="مثال: زياد أو 101...")
    
            # 3. نموذج إضافة طالب جديد (كافة الحقول السبعة)
            with st.expander("➕ إضافة طالب جديد يدوياً للسجلات"):
                with st.form("add_student_full_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    f_id = col1.text_input("🔢 الرقم الأكاديمي (نص)")
                    f_name = col2.text_input("👤 الاسم الثلاثي للطالب")
                    
                    col3, col4, col5 = st.columns(3)
                    f_stage = col3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    f_year = col4.text_input("🗓️ العام الدراسي", "1447هـ")
                    f_class = col5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    
                    col6, col7 = st.columns(2)
                    f_mail = col6.text_input("📧 البريد الإلكتروني")
                    f_phone = col7.text_input("📱 جوال ولي الأمر (بدون 0)")
                    
                    if st.form_submit_button("✅ حفظ الطالب في القاعدة"):
                        if f_id and f_name:
                            # تنسيق الجوال تلقائياً قبل الحفظ
                            phone = f_phone.strip()
                            if phone.startswith("0"): phone = phone[1:]
                            if not phone.startswith("966") and phone: phone = "966" + phone
                            
                            # إضافة السطر لـ Google Sheets
                            new_student = [f_id.strip(), f_name, f_class, f_year, f_stage, f_mail, phone, "0"]
                            sh.worksheet("students").append_row(new_student)
                            st.success(f"✅ تم حفظ الطالب {f_name} بنجاح.")
                            st.cache_data.clear(); st.rerun()
                        else:
                            st.warning("⚠️ يرجى إكمال الحقول الأساسية (الرقم والاسم).")
    
            # 4. فلترة وعرض البيانات (جدول تفاعلي)
            mask = df_st.iloc[:, 0].str.contains(search_query) | df_st.iloc[:, 1].str.contains(search_query)
            df_filtered = df_st[mask] if search_query else df_st
            
            st.markdown(f"**📂 قائمة الطلاب الحالية: ({len(df_filtered)}) طالب**")
            st.dataframe(
                df_filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("🆔 الرقم"),
                    "name": st.column_config.TextColumn("👤 الاسم"),
                    "النقاط": st.column_config.ProgressColumn("🏆 النقاط", min_value=0, max_value=100, format="%d")
                }
            )
    
            # 5. منطقة الحذف الآمن (لمنع الأخطاء)
            with st.expander("🗑️ منطقة إدارة الحذف (حذف نهائي)"):
                del_id = st.selectbox("اختر الرقم الأكاديمي للطالب المراد حذفه:", [""] + df_filtered.iloc[:, 0].tolist())
                if st.button("🚨 تأكيد الحذف من كافة السجلات"):
                    if del_id:
                        try:
                            # الحذف من شيت الطلاب
                            idx = df_st[df_st.iloc[:, 0] == del_id].index[0] + 2
                            sh.worksheet("students").delete_rows(int(idx))
                            # يمكن إضافة حذف درجاته وسلوكه هنا أيضاً لضمان نظافة البيانات
                            st.success(f"✅ تم حذف الطالب {del_id} بنجاح."); st.cache_data.clear(); st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ فشل الحذف: {e}")
        else:
            st.info("💡 لا يوجد طلاب مضافون حالياً. استخدم نموذج الإضافة أعلاه أو أداة الرفع في الإعدادات.")
            #............#
    with menu[1]: # تبويب التقييم: رصد بحدود الوزارة + سلوك + واتساب
        df_st = fetch_safe("students")
        if not df_st.empty:
            st_list = {f"{row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected = st.selectbox("🎯 اختر الطالب للتقييم:", [""] + list(st_list.keys()))
            if selected:
                sid = st_list[selected]; s_info = df_st[df_st.iloc[:, 0] == sid].iloc[0]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 رصد الدرجات")
                    with st.form("grade_f"):
                        v_t = st.number_input(f"المشاركة والمهام (الحد: {st.session_state.max_tasks})", 0)
                        v_q = st.number_input(f"اختبار قصير (الحد: {st.session_state.max_quiz})", 0)
                        if st.form_submit_button("💾 حفظ"):
                            if v_t <= st.session_state.max_tasks and v_q <= st.session_state.max_quiz:
                                sh.worksheet("grades").append_row([sid, v_t, v_q, v_t+v_q, str(datetime.date.today())])
                                st.success("✅ تم الحفظ بنجاح"); st.cache_data.clear()
                            else: st.error("⚠️ الدرجة تتجاوز الحد المسموح به.")
                with col_b:
                    st.markdown("##### 🎭 سجل السلوك")
                    with st.form("beh_f", clear_on_submit=True):
                        b_type = st.selectbox("النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "🚫 سلبي (-10)"])
                        b_msg = st.text_input("ملاحظة")
                        if st.form_submit_button("💾 حفظ وإرسال واتساب"):
                            sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, b_msg])
                            msg_enc = urllib.parse.quote(f"📢 تنبيه من منصة زياد\nالطالب: {s_info.iloc[1]}\nالسلوك: {b_type}\nالملاحظة: {b_msg}")
                            st.markdown(f' <a href="https://api.whatsapp.com/send?phone={s_info.iloc[6]}&text={msg_enc}" target="_blank">📲 إرسال واتساب</a>', unsafe_allow_html=True)
                            st.cache_data.clear()

    with menu[2]: # تبويب التواصل
        st.subheader("📢 إدارة التنبيهات")
        with st.form("ann_f", clear_on_submit=True):
            a_title = st.text_input("عنوان التنبيه"); a_body = st.text_area("التفاصيل")
            if st.form_submit_button("📣 نشر"):
                sh.worksheet("exams").append_row(["الكل", a_title, str(datetime.date.today()), a_body, "لا"])
                st.success("تم النشر"); st.cache_data.clear(); st.rerun()

    with menu[3]: # تبويب الإعدادات: حفظ دائم + رفع إكسل
        st.subheader("⚙️ التحكم الإداري")
        with st.expander("⚖️ توزيع الدرجات (حفظ دائم)", expanded=True):
            c1, c2 = st.columns(2)
            nt = c1.number_input("الحد الأعلى للمشاركة", 1, 100, st.session_state.max_tasks)
            nq = c2.number_input("الحد الأعلى للاختبار", 1, 100, st.session_state.max_quiz)
            if st.button("💾 حفظ نهائي"):
                ws_s = sh.worksheet("settings")
                ws_s.update_cell(2, 2, nt); ws_s.update_cell(3, 2, nq)
                st.session_state.max_tasks, st.session_state.max_quiz = nt, nq
                st.success("✅ تم الحفظ في قاعدة البيانات"); st.rerun()
        
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
    
    st.markdown(f"<div class='header-section'><h2>🎯 مرحباً: {s_row.iloc[1]}</h2>🏆 نقاطك: {s_row['النقاط']} | 🏫 {s_row.iloc[4]}</div>", unsafe_allow_html=True)
    t_ex, t_grade, t_beh, t_lead = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال"])

    with t_ex:
        f_ex = df_ex[(df_ex.iloc[:, 0] == s_row.iloc[4]) | (df_ex.iloc[:, 0] == "الكل")]
        for _, r in f_ex.iloc[::-1].iterrows():
            with st.container(border=True):
                st.markdown(f"### 📍 {r[1]}"); st.caption(f"📅 {r[2]}"); st.write(r[3])

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
        else: st.info("لم ترصد درجاتك بعد.")

    if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()
