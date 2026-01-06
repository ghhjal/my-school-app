import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import logging
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات النظام والاستقرار ---
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

# الاتصال بـ Google Sheets
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من Secrets.")
        return None

sh = get_gspread_client()

# --- 2. دوال معالجة البيانات (الذكاء البرمجي) ---

@st.cache_data(ttl=30)
def fetch_safe(worksheet_name):
    """جلب البيانات مع ضمان تحويل المعرف (ID) لنص لمنع انهيار البرنامج"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        if not df.empty:
            # الاعتماد على المعرف كـ نص لمنع فقدان الأصفار
            df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def get_col_idx(df, col_name):
    """إيجاد رقم العمود بناءً على اسمه لضمان عدم تأثر الكود بتغيير الترتيب في الشيت"""
    try:
        return df.columns.get_loc(col_name) + 1
    except:
        return None

def dynamic_append_student(f_id, f_name, f_stage, f_year, f_class, f_email, f_phone):
    """إضافة طالب بناءً على أسماء الأعمدة الفعلية لتجنب مشكلة إزاحة البيانات"""
    try:
        ws = sh.worksheet("students")
        headers = ws.row_values(1)
        data_map = {
            "id": str(f_id).strip(),
            "name": f_name,
            "class": f_class,
            "year": f_year,
            "sem": f_stage,
            "الإيميل": f_email,
            "الجوال": str(f_phone),
            "النقاط": "0"
        }
        # بناء السطر بناءً على الترتيب الحقيقي للأعمدة في ملفك
        new_row = [data_map.get(h, "") for h in headers]
        ws.append_row(new_row)
        return True
    except:
        return False

# --- 3. التصميم البصري (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .header-section { background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 40px; border-radius: 0 0 30px 30px; color: white; text-align: center; margin: -80px -20px 20px -20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 12px !important; font-weight: bold; width: 100%; height: 3.5em; }
    div[data-testid="stForm"] { border-radius: 20px !important; padding: 25px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    </style>
    <div class="header-section">
        <h1>منصة زياد الذكية</h1>
        <p>الإصدار الإداري المتكامل - 2026</p>
    </div>
""", unsafe_allow_html=True)

if "role" not in st.session_state: st.session_state.role = None

# ==========================================
# 🔐 نظام الدخول الموحد
# ==========================================
if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 دخول الإدارة"])
    with t1:
        with st.form("st_log"):
            sid_input = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول الطلاب 🚀"):
                df_st = fetch_safe("students")
                if not df_st.empty and sid_input in df_st.iloc[:, 0].values:
                    st.session_state.role = "student"; st.session_state.sid = sid_input; st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")
    with t2:
        with st.form("te_log"):
            u = st.text_input("👤 المستخدم"); p = st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty and u.strip() in df_u['username'].values:
                    if hashlib.sha256(str.encode(p)).hexdigest() == df_u[df_u['username']==u.strip()].iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("كلمة المرور خاطئة")
    st.stop()

# ==========================================
# 👨‍🏫 واجهة المعلم (التقسيم المدمج المطور)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 الطلاب", "📊 التقييم والمتابعة", "📢 التواصل والتنبيهات", "⚙️ الإعدادات", "🚗 خروج"])

    with menu[0]: # تبويب الطلاب
        st.subheader("👥 إدارة قاعدة بيانات الطلاب")
        with st.expander("➕ إضافة طالب جديد (الحقول السبعة)", expanded=False):
            with st.form("add_st_full", clear_on_submit=True):
                c1, c2 = st.columns(2)
                f_id = c1.text_input("🔢 الرقم الأكاديمي (نص)")
                f_name = c2.text_input("👤 الاسم الثلاثي")
                c3, c4, c5 = st.columns(3)
                f_stage = c3.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                f_year = c4.text_input("🗓️ العام", "1447هـ")
                f_class = c5.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                f_mail = st.text_input("📧 البريد الإلكتروني")
                f_phone = st.text_input("📱 الجوال (بدون 0)")
                if st.form_submit_button("✅ اعتماد وحفظ"):
                    df_cur = fetch_safe("students")
                    if f_id.strip() in df_cur.iloc[:, 0].values:
                        st.error(f"⚠️ الرقم {f_id} مسجل مسبقاً")
                    elif f_id and f_name:
                        # تنسيق الجوال تلقائياً
                        phone = f_phone.strip()
                        if phone.startswith("0"): phone = phone[1:]
                        if not phone.startswith("966"): phone = "966" + phone
                        if dynamic_append_student(f_id.strip(), f_name, f_stage, f_year, f_class, f_mail, phone):
                            st.success(f"تمت إضافة {f_name} بنجاح"); st.cache_data.clear(); st.rerun()

        st.divider()
        df_st = fetch_safe("students")
        if not df_st.empty:
            c_s, c_d = st.columns([2, 1])
            with c_s: q = st.text_input("🔍 ابحث (اسم/رقم):")
            with c_d:
                st.markdown("##### 🗑️ الحذف الآمن")
                t_del = st.selectbox("اختر الرقم للحذف:", [""] + df_st.iloc[:, 0].tolist())
                if t_del:
                    st.warning(f"⚠️ هل أنت متأكد من حذف {t_del}؟")
                    if st.button("🚨 نعم، حذف نهائي من كافة الجداول"):
                        for s in ["students", "grades", "behavior"]:
                            ws = sh.worksheet(s); df_t = fetch_safe(s)
                            if not df_t.empty and str(t_del) in df_t.iloc[:, 0].values:
                                idx = df_t[df_t.iloc[:, 0] == str(t_del)].index[0]
                                ws.delete_rows(int(idx) + 2)
                        st.success("تم الحذف بنجاح"); st.cache_data.clear(); st.rerun()
            
            # عرض الجدول مع إخفاء المادة كما طلبت
            cols_hide = ["لغة إنجليزية", "المادة", "sem"]
            df_disp = df_st.drop(columns=[c for c in cols_hide if c in df_st.columns], errors='ignore')
            if q: df_disp = df_disp[df_disp.iloc[:, 0].str.contains(q) | df_disp.iloc[:, 1].str.contains(q)]
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
    #
    # ==========================================
    # 📊 تبويب: التقييم والمتابعة (الإصدار الاحترافي الصامد)
    # ==========================================
    with menu[1]:
        st.subheader("📈 التقييم والمتابعة الشاملة")
        
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # 1. اختيار الطالب (تجنب الإزاحة عبر الربط بالأسماء)
            st_list = {f"{row['name'] if 'name' in row else row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected_label = st.selectbox("🎯 اختر الطالب للتقييم:", [""] + list(st_list.keys()))
            
            if selected_label:
                sid = st_list[selected_label]
                student_info = df_st[df_st.iloc[:, 0] == sid].iloc[0]
                s_name = student_info['name'] if 'name' in student_info else student_info.iloc[1]
                s_phone = student_info['الجوال'] if 'الجوال' in student_info else ""
                s_email = student_info['الإيميل'] if 'الإيميل' in student_info else ""
    
                # --- 💡 دالة التنسيق الموحد مع الترميز الآمن ---
                def get_safe_whatsapp_link(phone, name, b_type, b_desc, b_date):
                    # نص الرسالة الاحترافي (تنسيق موحد)
                    message = (
                        f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {name}\n"
                        f"---------------------------------------\n"
                        f"📍 نوع السلوك: {b_type}\n"
                        f"📝 الملاحظة: {b_desc if b_desc else 'لا يوجد ملاحظات إضافية'}\n"
                        f"📅 التاريخ: {b_date}\n"
                        f"---------------------------------------\n"
                        f"🏛️ منصة الأستاذ زياد الذكية"
                    )
                    # استخدام quote_plus لضمان تشفير الرموز التعبيرية والمسافات بشكل صحيح
                    encoded_msg = urllib.parse.quote(message)
                    return f"https://wa.me/{phone}?text={encoded_msg}", message
    
                # --- 📝 القسم الأول: الرصد الأكاديمي (الآلة الحاسبة) ---
                st.markdown("#### 📝 الرصد الأكاديمي")
                with st.form("grade_calc_v2"):
                    c1, c2, c3 = st.columns(3)
                    v_tasks = c1.number_input("المشاركة والمهام (60)", 0, 60)
                    v_quiz = c2.number_input("اختبار قصير (40)", 0, 40)
                    
                    # الحساب التلقائي للمجموع
                    total_sum = v_tasks + v_quiz
                    c3.metric("المجموع الكلي", f"{total_sum} / 100")
                    
                    if st.form_submit_button("💾 حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        df_g = fetch_safe("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v_tasks)
                            ws_g.update_cell(idx, 3, v_quiz)
                            ws_g.update_cell(idx, 4, total_sum)
                        else:
                            ws_g.append_row([sid, v_tasks, v_quiz, total_sum, str(datetime.date.today()), ""])
                        st.success(f"✅ تم حفظ الدرجة ({total_sum})")
                        st.cache_data.clear()
    
                st.divider()
    
                # --- 🎭 القسم الثاني: السلوك والتواصل ---
                st.markdown("#### 🎭 سجل السلوك والتواصل الفوري")
                with st.expander("🆕 رصد ملاحظة جديدة", expanded=True):
                    with st.form("behavior_v2", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        b_date = c1.date_input("التاريخ", datetime.date.today())
                        b_type = c2.selectbox("نوع السلوك", [
                            "🌟 متميز (+10)", "✅ مشاركة إيجابية (+5)", 
                            "📚 لم يحضر الكتاب (-5)", "✍️ لم يحل الواجب (-5)", 
                            "🖊️ لم يحضر القلم (-5)", "⚠️ تنبيه شفوي (0)"
                        ])
                        b_desc = st.text_input("ملاحظات إضافية")
                        
                        if st.form_submit_button("💾 حفظ السلوك"):
                            sh.worksheet("behavior").append_row([sid, str(b_date), b_type, b_desc])
                            # تحديث النقاط (تجنب الإزاحة)
                            p_idx = get_col_idx(df_st, "النقاط")
                            row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                            p_map = {"متميز": 10, "إيجابية": 5, "الكتاب": -5, "الواجب": -5, "القلم": -5}
                            change = next((v for k, v in p_map.items() if k in b_type), 0)
                            old_p = int(student_info["النقاط"] or 0)
                            sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + change))
                            st.success("✅ تم الحفظ وتحديث النقاط")
                            st.cache_data.clear()
    
                # 📜 سجل الملاحظات السابقة مع أزرار الإرسال الموحدة
                st.markdown("##### 📜 سجل الملاحظات وإرسال التقارير")
                df_beh = fetch_safe("behavior")
                my_beh = df_beh[df_beh.iloc[:, 0] == sid]
                
                if not my_beh.empty:
                    for _, row in my_beh.iloc[::-1].iterrows():
                        with st.container(border=True):
                            st.write(f"📅 **التاريخ:** {row[1]} | **النوع:** {row[2]}")
                            
                            # توليد الرابط والرسالة بشكل آمن
                            wa_url, clean_msg = get_safe_whatsapp_link(s_phone, s_name, row[2], row[3], row[1])
                            
                            col_wa, col_mail = st.columns(2)
                            col_wa.link_button("📲 إرسال عبر واتساب", wa_url, use_container_width=True)
                            
                            # ترميز الإيميل بشكل منفصل لضمان التوافق
                            mail_body = urllib.parse.quote(clean_msg)
                            mail_url = f"mailto:{s_email}?subject=تقرير سلوكي: {s_name}&body={mail_body}"
                            col_mail.link_button("📧 إرسال عبر الإيميل", mail_url, use_container_width=True)
                else:
                    st.info("لا توجد ملاحظات سابقة لهذا الطالب.")
        else:
            st.warning("⚠️ يرجى إضافة طلاب أولاً.")
    
    
    with menu[2]: # التواصل والتنبيهات
        st.subheader("📢 التواصل والتنبيهات")
        with st.form("exam_comm"):
            e_t = st.text_input("موضوع التنبيه")
            e_c = st.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("🚀 نشر الإعلان"):
                sh.worksheet("exams").append_row([e_c, e_t, str(datetime.date.today()), ""])
                st.success("تم النشر")

    with menu[3]: # الإعدادات
        st.subheader("⚙️ أدوات التحكم المتقدمة")
        c_excel, c_auth = st.columns(2)
        with c_excel:
            st.info("📥 استيراد قاعدة بيانات الطلاب")
            up = st.file_uploader("ارفع ملف Excel", type="xlsx")
            if up and st.button("تأكيد الاستبدال النهائي"):
                new_df = pd.read_excel(up)
                sh.worksheet("students").update([new_df.columns.values.tolist()] + new_df.values.tolist())
                st.success("تم تحديث البيانات"); st.cache_data.clear(); st.rerun()
        with c_auth:
            if st.button("🧹 تصفير الكاش (تحديث فوري للمنصة)"): st.cache_data.clear(); st.rerun()

    with menu[4]:
        if st.button("🚪 تسجيل الخروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (الملف الشخصي المتكامل)
# ==========================================
if st.session_state.role == "student":
    # 1. جلب البيانات (محدثة بالـ ID النصي)
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    df_beh = fetch_safe("behavior")
    df_ex = fetch_safe("exams")

    # 2. تحديد بيانات الطالب الحالي (البحث بالـ ID)
    s_id = str(st.session_state.sid)
    try:
        # البحث عن سطر الطالب
        s_data = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
        
        # 💡 تقنية الربط بالأسماء (لتفادي مشكلة الإزاحة التي ظهرت في صورك)
        # الكود يبحث عن اسم العمود ويأخذ ما تحته مباشرة
        s_name = s_data['class'] if 'class' in s_data else s_data.iloc[1]
        s_class = s_data['year'] if 'year' in s_data else s_data.iloc[2]
        s_phone = s_data['الجوال'] if 'الجوال' in s_data else "غير مسجل"
        
        # جلب النقاط من عمود "النقاط" حصراً (لضمان عدم ظهور الجوال مكانه)
        p_col = "النقاط"
        raw_p = str(s_data[p_col]).strip() if p_col in s_data else "0"
        s_points = int(float(raw_p)) if raw_p.replace('.','',1).isdigit() else 0
        
    except Exception as e:
        st.error(f"⚠️ خطأ في تحميل ملفك الشخصي: {e}")
        st.stop()

    # --- 📢 هيدر الطالب الجمالي ---
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 30px; border-radius: 25px; color: white; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-size: 1.8rem;">🎯 أهلاً بك يا بطل: <span style="color: #ffd700;">{s_name}</span></h2>
            <div style="margin-top: 10px; opacity: 0.9; font-weight: bold;">🏫 {s_class} | الرقم الأكاديمي: {s_id}</div>
        </div>
    """, unsafe_allow_html=True)

    # --- 🏆 رصيد النقاط والأوسمة ---
    st.markdown(f"""
        <div style="background: white; border-radius: 20px; padding: 25px; border: 1px solid #e2e8f0; text-align: center; margin-top: 20px;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 25px;">
                <div style="opacity: {'1' if s_points >= 10 else '0.2'}">🥉<br><b>برونزي</b></div>
                <div style="opacity: {'1' if s_points >= 50 else '0.2'}">🥈<br><b>فضي</b></div>
                <div style="opacity: {'1' if s_points >= 100 else '0.2'}">🥇<br><b>ذهبي</b></div>
            </div>
            <div style="background: #f59e0b; color: white; padding: 20px; border-radius: 15px; font-size: 24px; font-weight: bold;">
                رصيد النقاط السلوكية: {s_points}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات الطلابية (كاملة المحتوى) ---
    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأبطال", "⚙️ الإعدادات"])

    with t_ex: # 1. التنبيهات
        st.markdown("##### 📢 آخر التعميمات والاختبارات")
        if not df_ex.empty:
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            for _, r in f_ex.iloc[::-1].iterrows():
                st.info(f"📍 {r[1]} | 📅 {r[2]}")
        else: st.info("لا توجد تنبيهات جديدة.")

    with t_grade: # 2. الدرجات
        st.markdown("##### 📊 مستواي الأكاديمي")
        my_g = df_grades[df_grades.iloc[:, 0].astype(str) == s_id]
        if not my_g.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("⭐ المشاركة", my_g.iloc[0, 1])
            c2.metric("📚 الواجبات", my_g.iloc[0, 2])
            c3.metric("📝 الاختبارات", my_g.iloc[0, 3])
        else: st.info("لم يتم رصد درجات لك بعد.")

    with t_beh: # 3. السلوك
        st.markdown("##### 🎭 سجل الانضباط")
        my_b = df_beh[df_beh.iloc[:, 0].astype(str) == s_id]
        if not my_b.empty:
            for _, r in my_b.iloc[::-1].iterrows():
                st.warning(f"🏷️ {r[2]} | {r[3]} (📅 {r[1]})")
        else: st.success("سجلك نظيف ومتميز! واصل العمل الرائع. ✨")

    with t_lead: # 4. الأبطال
        st.markdown("##### 🏆 لوحة المتصدرين (أعلى 10)")
        if p_col in df_st.columns:
            df_st[p_col] = pd.to_numeric(df_st[p_col], errors='coerce').fillna(0)
            top_10 = df_st.sort_values(by=p_col, ascending=False).head(10)
            for i, row in top_10.iterrows():
                is_me = str(row.iloc[0]) == s_id
                d_name = row['class'] if 'class' in row else row.iloc[1]
                st.markdown(f"""
                    <div style="padding:10px; border:{"2px solid #1e3a8a" if is_me else "1px solid #ddd"}; border-radius:10px; margin-bottom:5px; display:flex; justify-content:space-between;">
                        <span>{'⭐' if is_me else '👤'} {d_name}</span>
                        <b style="color: #1e3a8a;">{int(row[p_col])} نقطة</b>
                    </div>
                """, unsafe_allow_html=True)

    with t_set: # 5. الإعدادات
        st.markdown("##### ⚙️ تحديث بيانات التواصل")
        with st.form("st_update_form"):
            new_mail = st.text_input("📧 البريد الإلكتروني")
            new_phone = st.text_input("📱 جوال ولي الأمر", value=str(s_phone))
            if st.form_submit_button("✅ حفظ التعديلات"):
                ws = sh.worksheet("students")
                row_idx = df_st[df_st.iloc[:, 0].astype(str) == s_id].index[0] + 2
                col_phone_idx = get_col_idx(df_st, "الجوال")
                if col_phone_idx:
                    ws.update_cell(row_idx, col_phone_idx, new_phone)
                    st.success("✅ تم تحديث الجوال بنجاح!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.role = None; st.rerun()
