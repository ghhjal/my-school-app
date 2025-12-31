import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الربط: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 1:
            # تنظيف وتوحيد أسماء الأعمدة لمنع الأخطاء
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            return pd.DataFrame(data[1:], columns=clean_headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("عذراً، الرقم غير مسجل")
    st.stop()

# ==========================================
# ==========================================
# 🛠️ واجهة المعلم (إدارة متكاملة)
# ==========================================
# --- بداية قسم المعلم ---
if st.session_state.role == "teacher":
    # زر الخروج في القائمة الجانبية
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    
    # تعريف القائمة الرئيسية (تأكد من مطابقة الإيموجي والاسم تماماً)
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

   if menu == "👥 إدارة الطلاب":
        # تصميم عنوان احترافي في أعلى الصفحة
        st.markdown("""
            <div style="background-color: #1E3A8A; padding: 20px; border-radius: 15px; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h1 style="color: white; margin: 0; font-family: 'Arial';">👥 مركز التحكم بالطلاب</h1>
                <p style="color: #d1d5db; margin-top: 10px;">أهلاً بك يا أستاذي.. هنا يمكنك تأسيس وإدارة بيانات طلابك بكل سهولة</p>
            </div>
        """, unsafe_allow_html=True)
        
        # جلب البيانات
        df_st = fetch_safe("students")
        
        # 1. عرض الجدول بداخل حاوية أنيقة
        with st.container(border=True):
            st.markdown("<h3 style='color: #1E3A8A;'>📋 قائمة الطلاب الحالية</h3>", unsafe_allow_html=True)
            if not df_st.empty:
                st.dataframe(df_st, use_container_width=True, hide_index=True)
            else:
                st.info("لا يوجد طلاب مسجلون حالياً.")
        
        st.write("") # مسافة جمالية

        # 2. تصميم نموذج الإضافة كبطاقة (Card)
        st.markdown("""
            <div style="background-color: #f8fafc; padding: 15px; border-right: 5px solid #10b981; border-radius: 10px; margin-bottom: 10px;">
                <h3 style="color: #065f46; margin: 0;">➕ تأسيس حساب طالب جديد</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_st_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("🔢 الرقم الأكاديمي (ID)")
            nname = c2.text_input("👤 الاسم الثلاثي")
            nclass = c3.selectbox("🏫 الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            
            c4, c5, c6 = st.columns(3)
            nstage = c4.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            nyear = c5.text_input("🗓️ العام الدراسي", value="1447هـ")
            nsub = c6.text_input("📚 المادة", value="لغة إنجليزية")
            
            # زر الإضافة بتصميم streamlit الافتراضي داخل الفورم
            submit = st.form_submit_button("✅ اعتماد التأسيس وإضافة الطالب")
            
            if submit:
                if nid and nname:
                    # الترتيب: ID, Name, Class, Year, Status, Sub, Stage, Email, Phone, Points
                    new_student = [nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"]
                    sh.worksheet("students").append_row(new_student)
                    st.balloons() # إضافة تأثير احتفالي عند النجاح
                    st.success(f"🎉 تم تأسيس حساب الطالب {nname} بنجاح")
                    st.rerun()
                else:
                    st.error("⚠️ يرجى تعبئة الرقم الأكاديمي والاسم لضمان صحة البيانات")

        st.write("")

        # 3. قسم الحذف بتصميم تحذيري
        st.markdown("""
            <div style="background-color: #fff1f2; padding: 15px; border-right: 5px solid #e11d48; border-radius: 10px; margin-bottom: 10px;">
                <h3 style="color: #9f1239; margin: 0;">🗑️ منطقة الحذف النهائي</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            if not df_st.empty:
                del_target = st.selectbox("اختر الطالب المراد حذفه نهائياً من كافة السجلات", [""] + df_st.iloc[:, 1].tolist())
                if st.button("⚠️ تنفيذ الحذف الشامل"):
                    if del_target:
                        with st.spinner('جاري تنظيف السجلات...'):
                            for sn in ["students", "grades", "behavior"]:
                                try:
                                    ws = sh.worksheet(sn)
                                    cell = ws.find(del_target)
                                    ws.delete_rows(cell.row)
                                except: pass
                        st.warning(f"تم حذف {del_target} بنجاح من النظام")
                        st.rerun()
            else:
                st.info("القائمة فارغة، لا يوجد ما يمكن حذفه.")

    # 2. شاشة الدرجات
    elif menu == "📝 شاشة الدرجات":
        st.header("📝 رصد الدرجات الدراسية")
        df_st = fetch_safe("students")
        target = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if target:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == target]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة الأولى", 0, 100, value=v1)
                p2 = c2.number_input("الفترة الثانية", 0, 100, value=v2)
                part = c3.number_input("درجة المشاركة", 0, 100, value=v3)
                if st.form_submit_button("حفظ وتحديث الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([target, p1, p2, part])
                    st.success("تم التحديث"); st.rerun()
        st.subheader("📋 جدول الدرجات العام")
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. شاشة رصد السلوك (تم إعادتها داخل نطاق شرط المعلم)
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 سجل السلوك والملاحظات")
        df_st = fetch_safe("students")
        
        with st.form("behavior_form"):
            c1, c2, c3 = st.columns(3)
            b_name = c1.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
            b_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه"])
            b_date = c3.date_input("التاريخ")
            b_note = st.text_area("نص الملاحظة")
            if st.form_submit_button("رصد الملاحظة"):
                # إضافة السلوك مع عمود خامس للحالة "لم تُقرأ بعد" لربطها بشاشة الطالب
                sh.worksheet("behavior").append_row([b_name, str(b_date), b_type, b_note, "لم تُقرأ بعد"])
                st.success("تم الرصد بنجاح"); st.rerun()

        st.divider()
        st.subheader("🔍 استعراض الفلتر الذكي")
        f_name = st.selectbox("اختر اسم الطالب لعرض سجلاته فقط", ["الكل"] + df_st.iloc[:, 1].unique().tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_df = df_b if f_name == "الكل" else df_b[df_b.iloc[:, 0] == f_name]
            # استخدام dataframe لضمان التوافق مع الجوال
            st.dataframe(view_df, use_container_width=True, hide_index=True)

    # 4. شاشة الاختبارات (تم إعادتها داخل نطاق شرط المعلم)
    elif menu == "📢 شاشة الاختبارات":
        st.header("📢 إدارة إعلانات الاختبارات")
        with st.form("ex_form"):
            c1, c2, c3 = st.columns(3)
            e_class = c1.selectbox("الصف المستهدف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_date = c2.date_input("موعد الاختبار")
            e_title = c3.text_input("موضوع الاختبار")
            if st.form_submit_button("نشر الإعلان"):
                sh.worksheet("exams").append_row([str(e_date), e_title, e_class])
                st.success("تم النشر بنجاح"); st.rerun()
        
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            for i, row in df_ex.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    # عرض الإعلان بشكل أنيق
                    c1.write(f"📢 **{row.iloc[1]}** | 📅 {row.iloc[0]} | 👥 {row.iloc[2]}")
                    if c2.button("🗑️ حذف", key=f"del_ex_{i}"):
                        sh.worksheet("exams").delete_rows(i + 2); st.rerun()
# ==========================================
# 👨‍🎓 واجهة الطالب (تصميم احترافي وفعال)
# ==========================================
# --- شاشة الطالب (مستقلة تماماً لمنع الأخطاء) ---
if st.session_state.role == "student":
    # 1. جلب البيانات الأساسية
    df_st = fetch_safe("students")
    s_data = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid]
    
    if not s_data.empty:
        s_row = s_data.iloc[0]
        s_name = s_row.iloc[1]
        s_email = s_row.iloc[7]
        s_phone = s_row.iloc[8]
        s_points = s_row.iloc[9]
        s_class = s_row.iloc[2]

        # 2. قسم الإعلانات (أعلى الشاشة - وضوح تام للجوال)
        df_ex = fetch_safe("exams")
        if not df_ex.empty:
            my_ex = df_ex[(df_ex.iloc[:, 2] == s_class) | (df_ex.iloc[:, 2] == "الكل")]
            for _, ex in my_ex.iterrows():
                st.warning(f"🔔 **إعلان هام:** {ex.iloc[1]} \n\n 📅 التاريخ: {ex.iloc[0]}")

        # 3. واجهة الهوية والأوسمة (تصميم عمودي للجوال)
        st.markdown(f"""
            <div style="text-align: center; background-color: #ffffff; padding: 15px; border-radius: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); border-top: 5px solid #1E3A8A; margin-top: 10px;">
                <h3 style="color: #1E3A8A; margin-bottom: 5px;">مرحباً: {s_name}</h3>
                <p style="font-size: 13px; color: #666;">📧 {s_email} | 📱 {s_phone}</p>
                <div style="display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #eee; padding-top: 10px;">
                    <div style="text-align: center;">
                        <div style="font-size: 35px;">🏆</div>
                        <div style="font-weight: bold; color: #1E3A8A; font-size: 18px;">{s_points}</div>
                        <div style="font-size: 11px; color: #888;">نقطة</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 35px;">🥇</div>
                        <div style="font-weight: bold; color: #1E3A8A; font-size: 18px;">متميز</div>
                        <div style="font-size: 11px; color: #888;">وسام</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("") 

        # 4. التبويبات (النتائج والملاحظات)
        # تم استخدام metric بدلاً من جداول لمنع أخطاء DeltaGenerator
        t1, t2 = st.tabs(["📊 نتيجتي الدراسية", "🎭 سجل ملاحظاتي"])
        
        with t1:
            df_g = fetch_safe("grades")
            if not df_g.empty:
                my_g = df_g[df_g.iloc[:, 0] == s_name]
                if not my_g.empty:
                    st.metric("الفترة الأولى", f"{my_g.iloc[0, 1]}")
                    st.metric("الفترة الثانية", f"{my_g.iloc[0, 2]}")
                    st.metric("درجة المشاركة", f"{my_g.iloc[0, 3]}")
                else:
                    st.info("لا توجد درجات مرصودة حالياً.")

        with t2:
            df_b = fetch_safe("behavior")
            if not df_b.empty:
                my_b = df_b[df_b.iloc[:, 0] == s_name]
                if not my_b.empty:
                    for _, row in my_b.iterrows():
                        # استخدام expander لسهولة القراءة من الجوال
                        with st.expander(f"🗓️ {row.iloc[1]} | {row.iloc[2]}", expanded=True):
                            st.info(f"📝 {row.iloc[3]}")
                else:
                    st.info("سجلك السلوكي نظيف.")

    # زر الخروج في أسفل القائمة الجانبية بعيداً عن كود الشاشة
    st.sidebar.markdown("---")
    st.sidebar.button("🚗 تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
