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
# --- كود الإعلان البارز في الصفحة الرئيسية ---
df_ex = fetch_safe("exams")
if not df_ex.empty:
    # جلب آخر إعلان موجه لـ "الكل"
    latest_global = df_ex[df_ex.iloc[:, 0] == "الكل"].iloc[-1:]
    if not latest_global.empty:
        st.markdown(f"""
            <div style="background: #fff5f5; border: 2px solid #feb2b2; padding: 15px; border-radius: 15px; margin-bottom: 20px; border-right: 10px solid #f56565;">
                <h4 style="color: #c53030; margin: 0;">📢 إعلان هام وعاجل: {latest_global.iloc[0, 1]}</h4>
                <p style="color: #4a5568; margin: 10px 0 0 0;">{latest_global.iloc[0, 3] if len(latest_global.columns) > 3 else ''}</p>
                <small style="color: #a0aec0;">📅 تاريخ النشر: {latest_global.iloc[0, 2]}</small>
            </div>
        """, unsafe_allow_html=True)
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
    # 📊 تبويب: التقييم والمتابعة (الإصدار المصفح برمجياً)
    # ==========================================
    with menu[1]:
        st.subheader("📈 التقييم والمتابعة الاحترافية")
        
        df_st = fetch_safe("students")
        
        if not df_st.empty:
            # 1. اختيار الطالب (حل مشكلة الإزاحة بالاعتماد على أسماء الأعمدة)
            st_list = {f"{row['name'] if 'name' in row else row.iloc[1]} ({row.iloc[0]})": row.iloc[0] for _, row in df_st.iterrows()}
            selected_label = st.selectbox("🎯 اختر الطالب المراد تقييمه:", [""] + list(st_list.keys()))
            
            if selected_label:
                sid = st_list[selected_label]
                student_info = df_st[df_st.iloc[:, 0] == sid].iloc[0]
                s_name = student_info['name'] if 'name' in student_info else student_info.iloc[1]
                s_phone = student_info['الجوال'] if 'الجوال' in student_info else ""
                s_email = student_info['الإيميل'] if 'الإيميل' in student_info else ""
    
                # --- 💡 دالة التشفير العميق (الحل النهائي لعلامات الاستفهام) ---
                def safe_encode_msg(name, b_type, b_desc, b_date):
                    msg = (
                        f"تحية طيبة، تم رصد ملاحظة سلوكية للطالب: {name}\n"
                        f"---------------------------------------\n"
                        f"📍 نوع السلوك: {b_type}\n"
                        f"📝 الملاحظة: {b_desc if b_desc else 'لا يوجد ملاحظات إضافية'}\n"
                        f"📅 التاريخ: {b_date}\n"
                        f"---------------------------------------\n"
                        f"🏛️ منصة الأستاذ زياد الذكية"
                    )
                    # استخدام quote لترميز كل حرف غير آمن بما في ذلك الرموز التعبيرية
                    return urllib.parse.quote(msg)
    
                # --- 📝 رصد الدرجات (المعادلة الحسابية) ---
                st.markdown("#### 📝 رصد الدرجات الأكاديمية")
                with st.form("grade_calc_stable"):
                    c1, c2, c3 = st.columns(3)
                    v_tasks = c1.number_input("المشاركة والمهام (60)", 0, 60)
                    v_quiz = c2.number_input("اختبار قصير (40)", 0, 40)
                    total = v_tasks + v_quiz
                    c3.metric("المجموع الكلي", f"{total} / 100")
                    
                    if st.form_submit_button("💾 حفظ الدرجات"):
                        ws_g = sh.worksheet("grades")
                        df_g = fetch_safe("grades")
                        if not df_g.empty and str(sid) in df_g.iloc[:, 0].values:
                            idx = df_g[df_g.iloc[:, 0] == str(sid)].index[0] + 2
                            ws_g.update_cell(idx, 2, v_tasks); ws_g.update_cell(idx, 3, v_quiz); ws_g.update_cell(idx, 4, total)
                        else:
                            ws_g.append_row([sid, v_tasks, v_quiz, total, str(datetime.date.today()), ""])
                        st.success("✅ تم حفظ الدرجات بنجاح"); st.cache_data.clear()
    
                st.divider()
    
                # --- 🎭 السلوك (استعادة القائمة الكاملة) ---
                st.markdown("#### 🎭 سجل السلوك والتواصل الفوري")
                with st.expander("🆕 رصد ملاحظة سلوكية جديدة", expanded=True):
                    with st.form("behavior_full_v3", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        b_date = c1.date_input("تاريخ تسجيل الملاحظة", datetime.date.today())
                        # 🌟 استعادة القائمة الكاملة كما طلبت
                        b_type = c2.selectbox("نوع السلوك المرصود", [
                            "🌟 متميز (+10)", 
                            "✅ مشاركة إيجابية (+5)", 
                            "📚 لم يحضر الكتاب (-5)", 
                            "✍️ لم يحل الواجب (-5)", 
                            "🖊️ لم يحضر القلم (-5)", 
                            "⚠️ تنبيه شفوي (0)",
                            "🚫 سلوك غير لائق (-10)"
                        ])
                        b_desc = st.text_input("تفاصيل إضافية للملاحظة")
                        
                        if st.form_submit_button("💾 حفظ وإرسال الملاحظة"):
                            sh.worksheet("behavior").append_row([sid, str(b_date), b_type, b_desc])
                            
                            # تحديث النقاط (ديناميكياً عبر الاسم)
                            p_idx = get_col_idx(df_st, "النقاط")
                            row_idx = df_st[df_st.iloc[:, 0] == sid].index[0] + 2
                            p_map = {"متميز": 10, "إيجابية": 5, "الكتاب": -5, "الواجب": -5, "القلم": -5, "غير لائق": -10}
                            change = next((v for k, v in p_map.items() if k in b_type), 0)
                            
                            old_p = int(student_info["النقاط"] or 0)
                            sh.worksheet("students").update_cell(row_idx, p_idx, str(old_p + change))
                            st.success(f"✅ تم الحفظ وتحديث النقاط بمقدار ({change})")
                            st.cache_data.clear()
    
                # --- 📜 السجل التاريخي وإرسال الواتساب (التشفير المضمون) ---
                st.markdown("##### 📜 السجل التاريخي وقنوات التواصل")
                df_beh = fetch_safe("behavior")
                my_beh = df_beh[df_beh.iloc[:, 0] == sid]
                
                if not my_beh.empty:
                    for _, row in my_beh.iloc[::-1].iterrows():
                        with st.container(border=True):
                            st.write(f"📅 **التاريخ:** {row[1]} | **النوع:** {row[2]}")
                            
                            # التشفير الآمن للرسالة بالكامل
                            encoded_text = safe_encode_msg(s_name, row[2], row[3], row[1])
                            
                            c1, c2 = st.columns(2)
                            # رابط الواتساب (استخدام api.whatsapp.com لضمان جودة الترميز)
                            wa_url = f"https://api.whatsapp.com/send?phone={s_phone}&text={encoded_text}"
                            c1.link_button("📲 إرسال واتساب (ترميز آمن)", wa_url, use_container_width=True)
                            
                            # رابط الإيميل
                            mail_url = f"mailto:{s_email}?subject=تقرير سلوكي&body={encoded_text}"
                            c2.link_button("📧 إرسال إيميل", mail_url, use_container_width=True)
                else:
                    st.info("لا توجد ملاحظات سابقة لهذا الطالب.")
        else:
            st.warning("⚠️ يرجى إضافة طلاب أولاً لبدء عملية التقييم.")
    
    
    # ==========================================
    # 📢 تبويب: التواصل والتنبيهات (إصدار الإرسال الجماعي)
    # ==========================================
    with menu[2]:
        st.subheader("📢 مركز التواصل وبث التنبيهات")
        
        # --- 1️⃣ قسم نشر تنبيه جديد (كودك المدمج) ---
        with st.expander("🚀 نشر إعلان أو موعد اختبار جديد", expanded=True):
            with st.form("new_announcement_form", clear_on_submit=True):
                c1, c2 = st.columns([2, 1])
                ann_title = c1.text_input("📝 عنوان التنبيه (مثال: اختبار لغتي القصير)")
                ann_target = c2.selectbox("🎯 الفئة المستهدفة", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                
                ann_details = st.text_area("📄 تفاصيل الإعلان أو التعليمات (يمكنك وضع روابط هنا)")
                ann_date = st.date_input("🗓️ تاريخ النشر/الفعالية", datetime.date.today())
                
                if st.form_submit_button("📣 نشر الآن للمنصة"):
                    if ann_title:
                        try:
                            sh.worksheet("exams").append_row([
                                ann_target, 
                                ann_title, 
                                str(ann_date), 
                                ann_details
                            ])
                            st.success(f"✅ تم نشر التنبيه بنجاح لطلاب الصف: {ann_target}")
                            st.cache_data.clear()
                            st.rerun()
                        except:
                            st.error("⚠️ حدث خطأ أثناء الاتصال بقاعدة البيانات.")
                    else:
                        st.warning("⚠️ يرجى كتابة عنوان للتنبيه أولاً.")
        
        st.divider()
    
        # --- 2️⃣ سجل التنبيهات مع ميزة إرسال المجموعات (احترافي) ---
        st.markdown("##### 📜 إدارة التنبيهات المنشورة")
        if not df_ex.empty:
            for index, row in df_ex.iloc[::-1].iterrows():
                with st.container(border=True):
                    st.markdown(f"**[{row.iloc[0]}]** - **{row.iloc[1]}**")
                    
                    # تجهيز رسالة احترافية لمجموعات الواتساب (ترميز آمن بدون ?)
                    group_msg = (
                        f"📢 *تنبيه جديد من منصة الأستاذ زياد*\n"
                        f"----------------------------------\n"
                        f"📝 *الموضوع:* {row.iloc[1]}\n"
                        f"📄 *التفاصيل:* {row.iloc[3] if len(row) > 3 else 'لا يوجد'}\n"
                        f"🗓️ *التاريخ:* {row.iloc[2]}\n"
                        f"----------------------------------\n"
                        f"🏛️ *تمنياتنا لكم بالتوفيق*"
                    )
                    encoded_group_msg = urllib.parse.quote(group_msg)
                    
                    c_wa, c_del = st.columns([2, 1])
                    
                    # زر الإرسال للمجموعات (يفتح الواتساب لتختار المجموعة)
                    wa_url = f"https://api.whatsapp.com/send?text={encoded_group_msg}"
                    c_wa.link_button("👥 إرسال لمجموعة واتساب", wa_url, use_container_width=True)
                    
                    # زر الحذف
                    if c_del.button("🗑️ حذف", key=f"del_ann_{index}", use_container_width=True):
                        sh.worksheet("exams").delete_rows(int(index) + 2)
                        st.cache_data.clear(); st.rerun()
        else:
            st.info("لا توجد تنبيهات سابقة.")
    
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
# 👨‍🎓 واجهة الطالب (النسخة الذهبية المكتملة)
# ==========================================
if st.session_state.role == "student":
    # 1. جلب البيانات بنظام التشفير الآمن والربط بالأسماء
    df_st = fetch_safe("students")
    df_grades = fetch_safe("grades") 
    df_beh = fetch_safe("behavior")
    df_ex = fetch_safe("exams")

    s_id = str(st.session_state.sid)

    try:
        s_row = df_st[df_st.iloc[:, 0].astype(str) == s_id].iloc[0]
        s_name = s_row['name'] if 'name' in s_row else s_row.iloc[1]
        s_class = s_row['class'] if 'class' in s_row else s_row.iloc[4]
        s_email = s_row['الإيميل'] if 'الإيميل' in s_row else "غير مسجل"
        s_phone = s_row['الجوال'] if 'الجوال' in s_row else "غير مسجل"
        
        # جلب النقاط من عمود "النقاط" حصراً لضمان الاستقرار
        p_col = "النقاط"
        raw_p = str(s_row[p_col]).strip() if p_col in s_row else "0"
        s_points = int(float(raw_p)) if raw_p.replace('.','',1).isdigit() else 0
        
    except Exception as e:
        st.error(f"⚠️ خطأ في مطابقة البيانات: يرجى التحقق من أسماء الأعمدة.")
        st.stop()

    # --- 📢 الهيدر العلوي ونظام النقاط (بدون تغيير حسب طلبك) ---
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 30px; border-radius: 25px; color: white; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0;">🎯 مرحباً بك: {s_name}</h2>
            <div style="margin-top: 10px; opacity: 0.9;">🏫 {s_class} | 🏆 النقاط: {s_points}</div>
        </div>
    """, unsafe_allow_html=True)

    # --- 📊 التبويبات المحدثة ---
    t_ex, t_grade, t_beh, t_lead, t_set = st.tabs(["📢 تنبيهات", "📊 درجاتي", "🎭 سجل سلوكي", "🏆 الأبطال", "⚙️ الإعدادات"])

    with t_ex: # 📢 تبويب التنبيهات المطور
        st.markdown("##### 📢 التعميمات والروابط الهامة")
        
        # التأكد من جلب أحدث البيانات من جدول التنبيهات
        df_ex = fetch_safe("exams")
        
        if not df_ex.empty:
            # فلترة التنبيهات حسب صف الطالب أو الإعلانات العامة
            f_ex = df_ex[(df_ex.iloc[:, 0] == s_class) | (df_ex.iloc[:, 0] == "الكل")]
            
            if not f_ex.empty:
                for _, r in f_ex.iloc[::-1].iterrows():
                    with st.container(border=True):
                        # عرض العنوان بخط عريض وأنيق
                        st.markdown(f"### 📍 {r[1]}")
                        st.caption(f"📅 تاريخ النشر: {r[2]}")
                        
                        # التأكد من وجود تفاصيل لعرضها
                        if len(r) > 3 and r[3]:
                            st.markdown("---")
                            # استخدام st.markdown يضمن أن أي رابط يبدأ بـ http أو https سيكون قابلاً للضغط تلقائياً
                            st.markdown(r[3]) 
                            
                            # ✨ لمسة إضافية: إذا كان النص يحتوي على رابط، نبه الطالب
                            if "http" in str(r[3]):
                                st.info("ℹ️ هذا الإعلان يحتوي على رابط تفاعلي، يمكنك الضغط عليه مباشرة.")
            else:
                st.info("💡 لا توجد تعميمات جديدة لصفك في الوقت الحالي.")
        else:
            st.info("📭 صندوق التنبيهات فارغ حالياً.")

    with t_grade: # 📊 درجاتي (تطوير: عرض البطاقة العرضية)
        st.markdown("##### 📚 ملخص النتائج الأكاديمية")
        my_g = df_grades[df_grades.iloc[:, 0].astype(str) == s_id]
        if not my_g.empty:
            # بطاقة الدرجات العرضية الأنيقة
            st.markdown(f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 15px; padding: 20px; display: flex; justify-content: space-around; align-items: center; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                    <div style="flex: 1; border-left: 1px solid #eee;">
                        <span style="color: #64748b; font-size: 0.9rem; display: block;">المشاركة والمهام</span>
                        <b style="font-size: 1.5rem; color: #1e3a8a;">{my_g.iloc[0, 1]} / 60</b>
                    </div>
                    <div style="flex: 1; border-left: 1px solid #eee;">
                        <span style="color: #64748b; font-size: 0.9rem; display: block;">اختبار قصير</span>
                        <b style="font-size: 1.5rem; color: #1e3a8a;">{my_g.iloc[0, 2]} / 40</b>
                    </div>
                    <div style="flex: 1;">
                        <span style="color: #f59e0b; font-size: 0.9rem; display: block;">المجموع الكلي</span>
                        <b style="font-size: 2rem; color: #f59e0b;">{my_g.iloc[0, 3]}%</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if len(my_g.columns) > 5 and my_g.iloc[0, 5]:
                st.success(f"💬 ملاحظة المعلم: {my_g.iloc[0, 5]}")
        else: st.info("لم يتم رصد درجاتك بعد.")

    with t_beh: # سجل سلوكي
        my_b = df_beh[df_beh.iloc[:, 0].astype(str) == s_id]
        if not my_b.empty:
            for _, r in my_b.iloc[::-1].iterrows():
                st.warning(f"🏷️ {r[2]} | {r[3]} (📅 {r[1]})")
        else: st.success("سجلك نظيف ومتميز! ✨")

    with t_lead: # الأبطال
        df_st[p_col] = pd.to_numeric(df_st[p_col], errors='coerce').fillna(0)
        top_10 = df_st.sort_values(by=p_col, ascending=False).head(10)
        for i, row in top_10.iterrows():
            is_me = str(row.iloc[0]) == s_id
            st.markdown(f"<div style='padding:10px; border-bottom:1px solid #eee;'>{'🥇' if i==top_10.index[0] else '👤'} {row.iloc[1]} - <b>{int(row[p_col])} نقطة</b> {'(أنت)' if is_me else ''}</div>", unsafe_allow_html=True)

    with t_set: # ⚙️ الإعدادات (تطوير: إعادة تحديث البيانات وزر الخروج الموحد)
        st.markdown("##### ⚙️ تحديث بيانات التواصل")
        with st.form("st_settings_update"):
            new_mail = st.text_input("📧 البريد الإلكتروني الحالي", value=str(s_email))
            new_phone = st.text_input("📱 جوال ولي الأمر (بدون 0)", value=str(s_phone).replace('966',''))
            
            if st.form_submit_button("✅ حفظ التعديلات"):
                # تنسيق الهاتف تلقائياً قبل الحفظ
                phone = new_phone.strip()
                if phone.startswith("0"): phone = phone[1:]
                if not phone.startswith("966") and phone: phone = "966" + phone
                
                ws = sh.worksheet("students")
                row_idx = df_st[df_st.iloc[:, 0].astype(str) == s_id].index[0] + 2
                
                # التحديث الديناميكي باستخدام أسماء الأعمدة
                col_mail_idx = get_col_idx(df_st, "الإيميل")
                col_phone_idx = get_col_idx(df_st, "الجوال")
                
                if col_mail_idx: ws.update_cell(row_idx, col_mail_idx, new_mail)
                if col_phone_idx: ws.update_cell(row_idx, col_phone_idx, phone)
                
                st.success("✅ تم تحديث بياناتك بنجاح!"); st.cache_data.clear(); st.rerun()
        
        st.divider()
        if st.button("🚪 تسجيل الخروج من المنصة", use_container_width=True, type="primary"):
            st.session_state.role = None; st.rerun()
