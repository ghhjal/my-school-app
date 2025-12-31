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

   # تأكد أن هذا الكود يقع داخل شرط (if st.session_state.role == "teacher":)
if menu == "👥 إدارة الطلاب":
    # 1. هيدر احترافي بتصميم عريض
    st.markdown("""
        <style>
            .main-header {
                background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
                padding: 25px;
                border-radius: 15px;
                color: white;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            .sub-card {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 12px;
                border-right: 8px solid #1E3A8A;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                margin-bottom: 20px;
            }
        </style>
        <div class="main-header">
            <h1 style="margin:0;">👥 إدارة شؤون الطلاب</h1>
            <p style="margin:5px 0 0 0; opacity: 0.8;">تأسيس الحسابات والتحكم الشامل بالسجلات</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. عرض جدول البيانات في حاوية مخصصة
    st.markdown('<div class="sub-card"><h3>📋 سجل الطلاب الحالي</h3></div>', unsafe_allow_html=True)
    df_st = fetch_safe("students")
    if not df_st.empty:
        # عرض الجدول مع تلوين الصفوف تلقائياً من Streamlit
        st.dataframe(df_st, use_container_width=True, hide_index=True)
    else:
        st.info("لم يتم تسجيل أي طلاب في النظام حتى الآن.")

    # 3. نموذج الإضافة بتصميم البطاقات
    st.write("")
    st.markdown('<div class="sub-card" style="border-right-color: #10B981;"><h3>➕ تأسيس طالب جديد</h3></div>', unsafe_allow_html=True)
    
    with st.form("professional_add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nid = st.text_input("🔢 الرقم الأكاديمي")
        with col2:
            nname = st.text_input("👤 اسم الطالب الثلاثي")
        with col3:
            nclass = st.selectbox("🏫 الصف الدراسي", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
        
        col4, col5, col6 = st.columns(3)
        with col4:
            nstage = st.selectbox("🎓 المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
        with col5:
            nyear = st.text_input("🗓️ العام", value="1447هـ")
        with col6:
            nsub = st.text_input("📚 المادة", value="لغة إنجليزية")
        
        # زر الإضافة بتنسيق عريض
        if st.form_submit_button("✅ اعتماد التأسيس وإضافة السجل"):
            if nid and nname:
                # الترتيب المتفق عليه: الطالب يكمل بيانات التواصل لاحقاً
                new_row = [nid, nname, nclass, nyear, "نشط", nsub, nstage, "", "", "0"]
                sh.worksheet("students").append_row(new_row)
                st.balloons()
                st.success(f"تم تأسيس حساب الطالب {nname} بنجاح!")
                st.rerun()
            else:
                st.error("يرجى التأكد من إدخال الرقم الأكاديمي والاسم.")

    # 4. منطقة الحذف (Safety Zone)
    st.write("")
    st.markdown('<div class="sub-card" style="border-right-color: #EF4444;"><h3>🗑️ منطقة الحذف النهائي</h3></div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        if not df_st.empty:
            target = st.selectbox("اختر الطالب المراد إزالته نهائياً", [""] + df_st.iloc[:, 1].tolist())
            if st.button("⚠️ تنفيذ الحذف الشامل"):
                if target:
                    with st.spinner('جاري مسح البيانات من كافة السجلات...'):
                        for sheet in ["students", "grades", "behavior"]:
                            try:
                                ws = sh.worksheet(sheet)
                                cell = ws.find(target)
                                ws.delete_rows(cell.row)
                            except: pass
                    st.warning(f"تم حذف الطالب {target} وكل بياناته المرتبطة.")
                    st.rerun()

    # 2. شاشة الدرجات - تم إصلاح المسافات (Indentation) ومعالجة SyntaxError
    elif menu == "📝 شاشة الدرجات":
        # تصميم هيدر احترافي للشاشة باللون البنفسجي لتمييزها
        st.markdown("""
            <div style="background: linear-gradient(90deg, #6366f1 0%, #4338ca 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <h1 style="margin:0;">📝 بوابة رصد النتائج</h1>
                <p style="margin:5px 0 0 0; opacity: 0.8;">توثيق درجات الفترات والمشاركة في السجل الأكاديمي</p>
            </div>
        """, unsafe_allow_html=True)

        # جلب بيانات الطلاب الأساسية لعمل قائمة الاختيار
        df_st = fetch_safe("students")
        
        # حاوية الاختيار والبحث
        with st.container(border=True):
            target_student = st.selectbox("🎯 اختر الطالب المراد تحديث درجاته", [""] + df_st.iloc[:, 1].tolist())
            
            if target_student:
                # جلب سجل الدرجات الحالي
                df_grades_db = fetch_safe("grades")
                current_record = df_grades_db[df_grades_db.iloc[:, 0] == target_student]
                
                # جلب القيم الحالية أو وضع 0 كقيمة افتراضية
                val1 = int(current_record.iloc[0, 1]) if not current_record.empty else 0
                val2 = int(current_record.iloc[0, 2]) if not current_record.empty else 0
                val3 = int(current_record.iloc[0, 3]) if not current_record.empty else 0
                
                st.markdown(f"#### ✍️ رصد الدرجات لـ: <span style='color:#4338ca;'>{target_student}</span>", unsafe_allow_html=True)
                
                # نموذج الرصد الاحترافي
                with st.form("grade_entry_form", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    p1_score = c1.number_input("📉 الفترة الأولى", 0, 100, value=val1)
                    p2_score = c2.number_input("📉 الفترة الثانية", 0, 100, value=val2)
                    participation = c3.number_input("⭐ المشاركة", 0, 100, value=val3)
                    
                    if st.form_submit_button("💾 اعتماد وحفظ الدرجات"):
                        worksheet_grades = sh.worksheet("grades")
                        try:
                            # محاولة العثور على الطالب لتحديث بياناته
                            found_cell = worksheet_grades.find(target_student)
                            worksheet_grades.update(f'B{found_cell.row}:D{found_cell.row}', [[p1_score, p2_score, participation]])
                        except:
                            # إذا كان الطالب جديداً في سجل الدرجات
                            worksheet_grades.append_row([target_student, p1_score, p2_score, participation])
                        
                        st.balloons()
                        st.success(f"🎉 تم رصد وتحديث درجات {target_student} بنجاح")
                        st.rerun()

        # 📊 استعراض الجدول العام للنتائج
        st.write("")
        st.markdown("<h3 style='color: #4338ca;'>📋 السجل العام لدرجات الطلاب</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            df_display = fetch_safe("grades")
            if not df_display.empty:
                # عرض البيانات بتنسيق تفاعلي
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("لا توجد بيانات مرصودة في سجل الدرجات حالياً.")

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
