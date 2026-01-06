import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

sh = get_client()

@st.cache_data(ttl=30)
def fetch_data(name):
    try:
        ws = sh.worksheet(name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # تحويل المعرف (ID) دائماً إلى نص لضمان الاستقرار
        if not df.empty and df.columns[0]:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """إيجاد رقم العمود بناءً على اسمه لضمان المرونة"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

# --- 2. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 35px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; height: 3.2em; }
    div[data-testid="stForm"] { border-radius: 20px !important; padding: 20px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>الإصدار الإداري المتكامل والآمن - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 بوابة تسجيل الدخول
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_log"):
            sid = st.text_input("🆔 الرقم الأكاديمي (نص)").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_st = fetch_data("students")
                if not df_st.empty and sid in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("te_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_data("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (الهيكلية المدمجة الكاملة)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1️⃣ تبويب: الطلاب (إضافة + بحث + حذف ذكي) ---
    with menu[0]:
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        
        # كود إضافة الطالب (تمت إعادته بالكامل مع منع التكرار وتنسيق الهاتف)
        with st.expander("➕ إضافة طالب جديد (الحقول السبعة)", expanded=False):
            with st.form("full_add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                f_id = c1.text_input("🔢 الرقم الأكاديمي (ID نص)")
                f_name = c2.text_input("👤 الاسم الثلاثي")
                
                c3, c4, c5 = st.columns(3)
                f_stage = c3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                f_year = c4.text_input("🗓️ العام الدراسي", "1447هـ")
                f_class = c5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                
                c6, c7 = st.columns(2)
                f_email = c6.text_input("📧 البريد الإلكتروني")
                f_phone = c7.text_input("📱 الجوال (سيتم تنسيقه تلقائياً)")
                
                if st.form_submit_button("✅ اعتماد وحفظ"):
                    df_check = fetch_data("students")
                    if f_id.strip() in df_check.iloc[:, 0].values:
                        st.error(f"⚠️ الرقم ({f_id}) مسجل مسبقاً باسم: {df_check[df_check.iloc[:,0]==f_id.strip()].iloc[0,1]}")
                    elif f_id and f_name:
                        # تنسيق الهاتف
                        phone = f_phone.strip()
                        if phone.startswith("0"): phone = phone[1:]
                        if not phone.startswith("966"): phone = "966" + phone
                        
                        sh.worksheet("students").append_row([f_id.strip(), f_name, f_stage, f_year, f_class, f_email, phone, "0"])
                        st.success(f"تمت إضافة {f_name} بنجاح"); st.cache_data.clear(); st.rerun()
                    else:
                        st.warning("يرجى ملء الحقول الأساسية (الاسم والرقم)")

        st.divider()
        df_st = fetch_data("students")
        
        if not df_st.empty:
            c_search, c_del = st.columns([2, 1])
            with c_search:
                q = st.text_input("🔍 ابحث عن طالب (اسم/رقم):")
            with c_del:
                st.markdown("##### 🗑️ الحذف الآمن")
                target_del = st.selectbox("اختر الرقم:", [""] + df_st.iloc[:, 0].tolist(), key="del_sel")
                if target_del:
                    st.warning(f"⚠️ حذف الطالب ({target_del})؟")
                    if st.button("🚨 نعم، حذف نهائي"):
                        for s in ["students", "grades", "behavior"]:
                            ws_del = sh.worksheet(s); df_del = fetch_data(s)
                            if not df_del.empty and str(target_del) in df_del.iloc[:,0].values:
                                idx_del = df_del[df_del.iloc[:,0] == str(target_del)].index[0]
                                ws_del.delete_rows(int(idx_del) + 2)
                        st.success("💥 تم الحذف بنجاح"); st.cache_data.clear(); time.sleep(1); st.rerun()

            # عرض الجدول مع إخفاء المادة
            st.markdown("##### 📋 سجل الطلاب")
            cols_to_hide = ["لغة إنجليزية", "المادة", "sem"]
            df_display = df_st.drop(columns=[c for c in cols_to_hide if c in df_st.columns], errors='ignore')
            if q:
                df_display = df_display[df_display.iloc[:, 0].str.contains(q) | df_display.iloc[:, 1].str.contains(q)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- 2️⃣ تبويب: التقييم والمتابعة ---
    with menu[1]:
        st.subheader("📊 رصد الأداء")
        if not df_st.empty:
            st_dict = dict(zip(df_st.iloc[:, 1], df_st.iloc[:, 0]))
            sel_st = st.selectbox("🎯 اختر الطالب:", [""] + list(st_dict.keys()))
            if sel_st:
                sid = st_dict[sel_st]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.markdown("##### 📝 الدرجات")
                    v1 = st.number_input("المشاركة", 0, 20); v2 = st.number_input("الواجبات", 0, 20)
                    if st.button("💾 حفظ الدرجة"):
                        ws_g = sh.worksheet("grades"); df_g = fetch_data("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v1); ws_g.update_cell(idx, 3, v2)
                        else: ws_g.append_row([sid, v1, v2, "0", str(datetime.date.today()), ""])
                        st.success("تم الحفظ")
                with col_b:
                    st.markdown("##### 🥇 السلوك")
                    b_type = st.selectbox("النوع", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "❌ سلبي (-5)"])
                    if st.button("💾 تحديث النقاط"):
                        sh.worksheet("behavior").append_row([sid, str(datetime.date.today()), b_type, ""])
                        p_idx = get_col_idx(df_st, "النقاط")
                        row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                        points = 10 if "+" in b_type else (5 if "إيجابي" in b_type else -5)
                        old_p = int(df_st[df_st.iloc[:, 0] == sid].iloc[0]["النقاط"] or 0)
                        sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + points))
                        st.success("تم التحديث"); st.cache_data.clear()

    # --- 3️⃣ تبويب: التواصل ---
    with menu[2]:
        st.subheader("📢 التنبيهات")
        with st.form("comm"):
            e_t = st.text_input("عنوان التنبيه")
            e_c = st.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("🚀 نشر"):
                sh.worksheet("exams").append_row([e_c, e_t, str(datetime.date.today()), ""])
                st.success("تم النشر")

    # --- 4️⃣ تبويب: الإعدادات ---
    with menu[3]:
        st.subheader("⚙️ التحكم")
        if st.button("🧹 تصفير الكاش (تحديث البيانات)"): st.cache_data.clear(); st.rerun()

    with menu[4]:
        if st.button("🚪 خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الملف الشخصي المتكامل)
# ==========================================
if st.session_state.role == "student":
    # 1. جلب البيانات (محدثة بالـ ID النصي)
    df_st = fetch_data("students")
    df_grades = fetch_data("grades") 
    df_beh = fetch_data("behavior")
    df_ex = fetch_data("exams")

    # 2. تحديد بيانات الطالب الحالي بدقة (البحث بالـ ID النصي)
    s_id = st.session_state.sid
    try:
        # البحث في العمود الأول (الرقم الأكاديمي)
        s_data = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].iloc[0]
        
        # توزيع البيانات بناءً على الترتيب الجديد (7 حقول + النقاط)
        s_name = s_data.iloc[1]       # الاسم
        s_stage = s_data.iloc[2]      # المرحلة
        s_year = s_data.iloc[3]       # العام
        s_class = s_data.iloc[4]      # الصف
        s_email = s_data.iloc[5]      # البريد
        s_phone = s_data.iloc[6]      # الجوال
        # جلب النقاط (العمود الثامن - index 7) مع معالجة القيم الفارغة
        p_val = str(s_data.iloc[7]).strip() if len(s_data) >= 8 else "0"
        s_points = int(float(p_val)) if p_val.replace('.','',1).isdigit() else 0
        
    except Exception as e:
        st.error(f"⚠️ خطأ في تحميل ملفك الشخصي: {e}")
        st.stop()

    # 3. حساب الأوسمة والمتبقي
    next_badge, points_to_next = "", 0
    if s_points < 10: next_badge, points_to_next = "البرونزي", 10 - s_points
    elif s_points < 50: next_badge, points_to_next = "الفضي", 50 - s_points
    elif s_points < 100: next_badge, points_to_next = "الذهبي", 100 - s_points

    # --- 📢 هيدر الطالب الجمالي ---
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 30px; border-radius: 25px; color: white; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-size: 1.8rem;">🎯 أهلاً بك يا بطل: <span style="color: #ffd700;">{s_name}</span></h2>
            <div style="margin-top: 10px; opacity: 0.9; font-weight: bold;">
                🏫 {s_class} | {s_stage} | {s_year}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 🏆 نظام الأوسمة والنقاط ---
    st.markdown(f"""
        <div style="background: white; border-radius: 20px; padding: 25px; border: 1px solid #e2e8f0; text-align: center; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-around; margin-bottom: 25px;">
                <div style="opacity: {'1' if s_points >= 10 else '0.2'}; filter: {'grayscale(0%)' if s_points >= 10 else 'grayscale(100%)'};">
                    <div style="font-size: 2.5rem;">🥉</div><b style="color: #cd7f32;">برونزي</b>
                </div>
                <div style="opacity: {'1' if s_points >= 50 else '0.2'}; filter: {'grayscale(0%)' if s_points >= 50 else 'grayscale(100%)'};">
                    <div style="font-size: 2.5rem;">🥈</div><b style="color: #7f8c8d;">فضي</b>
                </div>
                <div style="opacity: {'1' if s_points >= 100 else '0.2'}; filter: {'grayscale(0%)' if s_points >= 100 else 'grayscale(100%)'};">
                    <div style="font-size: 2.5rem;">🥇</div><b style="color: #d4af37;">ذهبي</b>
                </div>
            </div>
            <div style="background: #f59e0b; color: white; padding: 20px; border-radius: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                <b style="font-size: 1.2rem; display: block; margin-bottom: 5px;">رصيد النقاط السلوكية</b>
                <b style="font-size: 3.5rem; line-height: 1;">{s_points}</b>
                {f'<div style="font-size: 0.9rem; margin-top:10px; background: rgba(255,255,255,0.2); padding: 5px; border-radius: 8px;">🚀 بقي لك {points_to_next} نقطة للوسام {next_badge}</div>' if points_to_next > 0 else ''}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات الطلابية ---
    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال", "⚙️ الإعدادات"])

    with t_ex: # التنبيهات
        st.markdown("##### 📢 آخر التعميمات والاختبارات")
        if not df_ex.empty:
            # عرض التنبيهات الخاصة بصف الطالب أو الموجهة للكل
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            if not f_ex.empty:
                for _, r in f_ex.iloc[::-1].iterrows():
                    st.markdown(f"""
                        <div style="background: #f0f7ff; padding: 15px; border-radius: 12px; border-right: 5px solid #1e40af; margin-bottom: 10px;">
                            <b style="color: #1e40af; font-size: 1.1rem;">📝 {r[1]}</b><br>
                            <small style="color: #64748b;">📅 تاريخ النشر: {r[2]}</small>
                        </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد تنبيهات جديدة لصفك حالياً.")

    with t_grade: # الدرجات
        st.markdown("##### 📊 مستواي الأكاديمي")
        my_g = df_grades[df_grades.iloc[:, 0].astype(str) == str(s_id)]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            # عرض الدرجات (بافتراض ترتيبها: ID, مشاركة, واجبات, اختبار)
            c1.metric("المشاركة", my_g.iloc[0, 1])
            c2.metric("الواجبات", my_g.iloc[0, 2])
            c3.metric("الاختبارات", my_g.iloc[0, 3])
            if len(my_g.columns) > 5:
                st.success(f"💬 ملاحظة المعلم: {my_g.iloc[0, 5]}")
        else: st.info("لم يتم رصد درجات لك بعد.")

    with t_beh: # السلوك
        st.markdown("##### 🎭 سجل الانضباط")
        my_b = df_beh[df_beh.iloc[:, 0].astype(str) == str(s_id)]
        if not my_b.empty:
            for _, r in my_b.iloc[::-1].iterrows():
                is_pos = "+" in str(r[2])
                st.markdown(f"""
                    <div style="background: {'#f0fdf4' if is_pos else '#fef2f2'}; padding: 15px; border-radius: 12px; border-right: 5px solid {'#16a34a' if is_pos else '#dc2626'}; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <b style="color: {'#16a34a' if is_pos else '#dc2626'};">{r[2]}</b>
                            <small>{r[1]}</small>
                        </div>
                        <div style="margin-top: 5px;">{r[3]}</div>
                    </div>
                """, unsafe_allow_html=True)
        else: st.success("سجلك نظيف ومتميز! واصل العمل الرائع. ✨")

    with t_lead: # الأبطال
        st.markdown("##### 🏆 لوحة المتصدرين (أعلى 10)")
        df_st.iloc[:, 7] = pd.to_numeric(df_st.iloc[:, 7], errors='coerce').fillna(0)
        top_students = df_st.sort_values(by=df_st.columns[7], ascending=False).head(10)
        for i, row in top_students.iterrows():
            is_me = str(row[0]) == str(s_id)
            st.markdown(f"""
                <div style="background: {'#eff6ff' if is_me else 'white'}; padding: 12px; border-radius: 12px; border: {'2px solid #1e40af' if is_me else '1px solid #e2e8f0'}; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span>{'👑' if i==top_students.index[0] else '⭐'} <b>{row[1]}</b> {'(أنت)' if is_me else ''}</span>
                    <b style="background: #1e40af; color: white; padding: 4px 12px; border-radius: 8px;">{int(row[7])}</b>
                </div>
            """, unsafe_allow_html=True)

    with t_set: # الإعدادات (تحديث البيانات)
        st.markdown("##### ⚙️ تحديث بيانات التواصل")
        with st.form("st_update_form"):
            new_mail = st.text_input("📧 البريد الإلكتروني", value=str(s_email))
            new_phone = st.text_input("📱 جوال ولي الأمر (بدون 966)", value=str(s_phone).replace('966', ''))
            if st.form_submit_button("✅ حفظ التعديلات"):
                # تنسيق الهاتف تلقائياً قبل الحفظ
                phone = new_phone.strip()
                if phone.startswith("0"): phone = phone[1:]
                if not phone.startswith("966") and phone: phone = "966" + phone
                
                try:
                    ws = sh.worksheet("students")
                    # إيجاد رقم السطر بالـ ID النصي
                    row_idx = df_st[df_st.iloc[:, 0].astype(str) == str(s_id)].index[0] + 2
                    ws.update_cell(row_idx, 6, new_mail) # تحديث البريد
                    ws.update_cell(row_idx, 7, phone)    # تحديث الجوال
                    st.success("✅ تم تحديث بياناتك بنجاح!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("فشل في تحديث البيانات")

    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None; st.rerun()
