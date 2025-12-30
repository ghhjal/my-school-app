import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

# --- إعداد الصفحة ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

# --- دالة الإرسال المستقرة ---
def send_email_notification(to_email, student_name, note_type, note_text, note_date):
    if not to_email or "@" not in str(to_email): return False
    try:
        sender = "ziyadalamri30@gmail.com"
        password = "your_app_password" # ضع الكود المكون من 16 حرفاً هنا
        body = f"ولي أمر الطالب/ة: {student_name}\nرصد ملاحظة سلوكية جديدة:\n📅 التاريخ: {note_date}\n🏷️ النوع: {note_type}\n📝 الملاحظة: {note_text}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"إشعار من الأستاذ زياد المعمري", 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except: return False

# --- الاتصال بقاعدة البيانات ---
@st.cache_resource(ttl=5)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

# إدارة حالة الدخول
if 'role' not in st.session_state: st.session_state.role = None
if 'confirmed' not in st.session_state: st.session_state.confirmed = set()

# ==========================================
# 🚪 شاشة الدخول المزدوجة
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري التعليمية</h1>", unsafe_allow_html=True)
    col_t, col_s = st.columns(2)
    
    with col_t:
        st.markdown("### 🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": # يمكنك تغيير كلمة المرور هنا
                st.session_state.role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
            
    with col_s:
        st.markdown("### 👨‍🎓 منطقة الطالب")
        s_id = st.text_input("أدخل الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch("students")
            if not df_st.empty and str(s_id) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"
                st.session_state.sid = str(s_id)
                st.rerun()
            else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (الشاشات المستقلة)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 تسجيل الخروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 رصد الدرجات", "🎭 رصد السلوك", "📢 الاختبارات"])
    
    df_st = fetch("students")

    # --- شاشة إدارة الطلاب الاحترافية ---
    if menu == "👥 إدارة الطلاب":
        st.markdown("<h2 style='text-align: right;'>👥 إدارة سجلات الطلاب</h2>", unsafe_allow_html=True)
        
        # 1. جلب البيانات بطريقة مرنة (تعتمد على ترتيب الأعمدة وليس أسمائها)
        try:
            ws_s = sh.worksheet("students")
            raw_data = ws_s.get_all_values()
            
            if len(raw_data) > 1: # التأكد من وجود بيانات غير العنوان
                # تحويل البيانات إلى DataFrame وتسمية الأعمدة يدوياً لضمان استقرار الكود
                df_st = pd.DataFrame(raw_data[1:], columns=[
                    "ID", "الاسم", "الصف", "العام الدراسي", "الفصل", 
                    "المادة", "المرحلة", "الإيميل", "الجوال", "النقاط"
                ])
                st.success(f"✅ تم العثور على {len(df_st)} طلاب في القاعدة")
                st.dataframe(df_st, use_container_width=True, hide_index=True)
            else:
                df_st = pd.DataFrame()
                st.warning("⚠️ الجدول فارغ حالياً، ابدأ بإضافة أول طالب أدناه")
        except Exception as e:
            st.error(f"❌ خطأ في الاتصال بالبيانات: {e}")
            df_st = pd.DataFrame()

        st.divider()

        # 2. تصميم نماذج الإضافة والحذف بشكل جانبي
        col_add, col_del = st.columns([1.2, 0.8], gap="large")
        
        with col_add:
            st.markdown("#### ➕ إضافة طالب جديد")
            with st.container(border=True):
                with st.form("form_pro_add", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st_id = st.text_input("الرقم الأكاديمي (ID)")
                        st_stage = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                    with c2:
                        st_name = st.text_input("اسم الطالب الثلاثي")
                        st_class = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    
                    st_year = st.text_input("العام الدراسي", value="1447هـ")
                    
                    if st.form_submit_button("حفظ الطالب في النظام"):
                        if st_id and st_name:
                            # إضافة البيانات بالترتيب الصحيح للأعمدة
                            ws_s.append_row([
                                st_id, st_name, st_class, st_year, 
                                "الفصل الأول", "اللغة الإنجليزية", st_stage, 
                                "", "", 0 # الإيميل والجوال يتركان فارغين ليضيفهما الطالب
                            ])
                            st.balloons()
                            st.success("تم الحفظ بنجاح! جاري تحديث القائمة...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("يرجى إكمال البيانات الأساسية")

        with col_del:
            st.markdown("#### 🗑️ حذف طالب نهائياً")
            with st.container(border=True):
                if not df_st.empty:
                    # نستخدم العمود الثاني (الاسم) في قائمة الاختيار
                    delete_name = st.selectbox("اختر الطالب المراد إزالته", [""] + df_st["الاسم"].tolist())
                    
                    if st.button("❌ حذف شامل ومؤكد"):
                        if delete_name:
                            with st.spinner("جاري تنظيف كافة السجلات..."):
                                try:
                                    # حذف من جدول الطلاب
                                    cell = ws_s.find(delete_name)
                                    ws_s.delete_rows(cell.row)
                                    
                                    # حذف من الدرجات والسلوك (إضافي)
                                    for sheet in ["grades", "behavior"]:
                                        try:
                                            ws_temp = sh.worksheet(sheet)
                                            matches = ws_temp.findall(delete_name)
                                            for m in sorted(matches, key=lambda x: x.row, reverse=True):
                                                ws_temp.delete_rows(m.row)
                                        except: pass
                                    
                                    st.warning(f"تم حذف سجلات {delete_name} بالكامل")
                                    time.sleep(1)
                                    st.rerun()
                                except:
                                    st.error("فشل الحذف، الطالب قد لا يكون موجوداً في الصف المحدد")
                else:
                    st.info("لا يوجد طلاب مسجلون حالياً.")

    # --- 2. شاشة رصد الدرجات (المطورة) ---
    if menu == "📝 رصد الدرجات":
        st.markdown("<h2 style='text-align: right;'>📝 رصد وتحديث درجات الطلاب</h2>", unsafe_allow_html=True)
        
        # جلب البيانات لضمان وجود الطلاب
        df_st = fetch("students")
        
        if df_st.empty:
            st.warning("⚠️ لا توجد بيانات طلاب. يرجى إضافتهم من شاشة إدارة الطلاب أولاً.")
        else:
            # حل مشكلة الاختيار: نحدد عمود الأسماء بدقة (العمود الثاني عادة)
            student_list = df_st.iloc[:, 1].tolist() 
            
            # تصميم منطقة الاختيار والرصد
            with st.container(border=True):
                sel_student = st.selectbox("🎯 اختر الطالب المراد رصد درجاته", [""] + student_list)
                
                if sel_student:
                    # محاولة جلب الدرجات الحالية للطالب إذا وجدت
                    df_grades = fetch("grades")
                    current_val = [0, 0, 0]
                    if not df_grades.empty and sel_student in df_grades.iloc[:, 0].values:
                        row = df_grades[df_grades.iloc[:, 0] == sel_student].iloc[0]
                        current_val = [int(row.iloc[1]), int(row.iloc[2]), int(row.iloc[3])]

                    with st.form("grade_update_form"):
                        c1, c2, c3 = st.columns(3)
                        with c1: f1 = st.number_input("فترة 1", 0, 100, value=current_val[0])
                        with c2: f2 = st.number_input("فترة 2", 0, 100, value=current_val[1])
                        with c3: pt = st.number_input("مشاركة", 0, 100, value=current_val[2])
                        
                        if st.form_submit_button("💾 حفظ الدرجات"):
                            ws_g = sh.worksheet("grades")
                            try:
                                # البحث عن الطالب لتحديثه أو إضافته كجديد
                                cell = ws_g.find(sel_student)
                                ws_g.update(f'B{cell.row}:D{cell.row}', [[f1, f2, pt]])
                            except:
                                ws_g.append_row([sel_student, f1, f2, pt])
                            
                            st.success(f"✅ تم تحديث درجات الطالب: {sel_student}")
                            time.sleep(1)
                            st.rerun()

            st.divider()
            st.subheader("📊 جدول الدرجات العام")
            st.dataframe(fetch("grades"), use_container_width=True, hide_index=True)

    # --- 1. شاشة إدارة الطلاب (التصميم الاحترافي المصحح) ---
    elif menu == "👥 إدارة الطلاب":
        st.markdown("<h2 style='text-align: right;'>👥 إدارة سجلات الطلاب</h2>", unsafe_allow_html=True)
        
        # جلب أحدث البيانات
        ws_s = sh.worksheet("students")
        data = ws_s.get_all_values()
        df_st = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()

        if not df_st.empty:
            st.dataframe(df_st, use_container_width=True, hide_index=True)
        else:
            st.info("الجدول فارغ، أضف طلاباً جدد.")

        col_add, col_del = st.columns([1.2, 0.8], gap="medium")
        
        with col_add:
            with st.form("pro_add_student"):
                st.markdown("#### ➕ إضافة طالب")
                nid = st.text_input("الرقم الأكاديمي")
                nname = st.text_input("الاسم الثلاثي")
                nclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                nstage = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                nyear = st.text_input("العام الدراسي", value="1447هـ")
                
                if st.form_submit_button("حفظ الطالب"):
                    if nid and nname:
                        ws_s.append_row([nid, nname, nclass, nyear, "الأول", "إنجليزي", nstage, "", "", 0])
                        st.success("تم الحفظ!"); time.sleep(1); st.rerun()

        with col_del:
            if not df_st.empty:
                st.markdown("#### 🗑️ حذف طالب")
                target = st.selectbox("اختر للحذف", [""] + df_st.iloc[:, 1].tolist())
                if st.button("❌ حذف نهائي"):
                    if target:
                        cell = ws_s.find(target)
                        ws_s.delete_rows(cell.row)
                        st.warning("تم الحذف"); time.sleep(1); st.rerun()

    elif menu == "🎭 رصد السلوك":
        st.header("🎭 رصد السلوك")
        sel_b = st.selectbox("اختر الطالب", [""] + df_st['name'].tolist() if not df_st.empty else [])
        if sel_b:
            with st.form("b_form"):
                b_date = st.date_input("التاريخ", datetime.now())
                b_type = st.radio("التقييم", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                b_note = st.text_input("الملاحظة")
                if st.form_submit_button("رصد وإرسال إشعار"):
                    with st.spinner("جاري الرصد..."):
                        pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note, "🕒 لم تقرأ"])
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        old_p = int(ws_s.cell(c.row, 10).value or 0) # العمود العاشر هو النقاط
                        ws_s.update_cell(c.row, 10, old_p + pts)
                        email = ws_s.cell(c.row, 8).value # العمود الثامن هو الإيميل
                        send_email_notification(email, sel_b, b_type, b_note, b_date)
                        st.success("تم الرصد بنجاح"); st.rerun()
        st.dataframe(fetch("behavior").iloc[::-1], use_container_width=True)

# ==========================================
# 👨‍🎓 واجهة الطالب
# ==========================================
if st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_data.iloc[1]

    st.markdown(f"<h1 style='text-align:center;'>👋 أهلاً بك: {s_name}</h1>", unsafe_allow_html=True)
    st.info(f"المرحلة: {s_data.iloc[6]} | العام: {s_data.iloc[3]} | النقاط: {s_data.iloc[9]}")

    t1, t2, t3, t4 = st.tabs(["📊 نتيجتي", "🎭 سلوكي", "📅 الاختبارات", "⚙️ بياناتي"])
    # (هنا يتم وضع كود عرض البيانات للطالب كما في النسخ السابقة لضمان التنسيق)
