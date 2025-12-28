import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. إعداد الاتصال بقاعدة البيانات ---
def get_gspread_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return gspread.authorize(creds)
    except Exception:
        return None

# محاولة الاتصال وفتح الملف
gc = get_gspread_client()
sh = None
if gc:
    try:
        # استبدل YOUR_SHEET_ID_HERE بمعرف ملفك الحقيقي
        sh = gc.open_by_key("1Xf_B-YOUR_ACTUAL_ID_HERE") 
    except Exception:
        sh = None

# --- 2. نظام إدارة الجلسة والدخول ---
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if st.session_state.user_role is None:
    st.title("🔐 نظام المدرسة الرقمي")
    choice = st.radio("اختر نوع المستخدم", ["👨‍🏫 معلم", "🎓 طالب"], horizontal=True)
    
    if choice == "👨‍🏫 معلم":
        pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": # كلمة مرورك
                st.session_state.user_role = "teacher"
                st.rerun()
            else: st.error("كلمة المرور خاطئة")
    else:
        std_id = st.text_input("أدخل رقم الطالب الخاص بك")
        if st.button("دخول الطالب"):
            if std_id:
                st.session_state.user_role = "student"
                st.session_state.student_id = std_id
                st.rerun()
    st.stop()

# زر خروج عام في الشريط الجانبي
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.user_role = None
    st.rerun()

# --- 3. واجهة المعلم (رصد السلوك) ---
if st.session_state.user_role == "teacher":
    st.sidebar.button("🚪 تسجيل الخروج", on_click=lambda: st.session_state.update({"user_role": None}))
    st.title("👨‍🏫 لوحة تحكم المعلم")
    
    # إضافة تبويب الإدارة الذي أرسلته
    tab1, tab2, tab3, tab4 = st.tabs(["🎭 رصد السلوك", "📊 لوحة الدرجات", "🔍 معاينة الطلاب", "👥 إدارة الطلاب"])
    
    # --- التبويب الرابع: إدارة الطلاب (الكود الذي أرسلته) ---
    with tab4:
        st.markdown("<h3>👥 إدارة شؤون الطلاب</h3>", unsafe_allow_html=True)
        t_sub1, t_sub2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with t_sub1:
            with st.form("add_student", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sphase = st.selectbox("المرحلة", ["الابتدائية", "المتوسطة", "الثانوية"])
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                
                if st.form_submit_button("حفظ"):
                    try:
                        # الإضافة لورقة sheet1 (الرقم، الاسم، 0، 0، 0)
                        ws_students = sh.worksheet("sheet1")
                        ws_students.append_row([str(sid), sname, "0", "0", "0", sphase, sclass])
                        st.success("✅ تم حفظ الطالب الجديد في السجلات")
                        st.rerun()
                    except: st.error("فشل الاتصال بـ Google Sheets")

        with t_sub2:
            try:
                ws_students = sh.worksheet("sheet1")
                data = ws_students.get_all_records()
                if data:
                    import pandas as pd
                    df = pd.DataFrame(data)
                    for i, r in df.iterrows():
                        student_name = r.get("الاسم", r.get("name", "؟؟"))
                        st.markdown(f"**{student_name}** (ID: {r.get('رقم الطالب', i)})")
                        
                        if st.button(f"🗑️ حذف {student_name}", key=f"del_{i}"):
                            # 1. حذف من ورقة الطلاب الرئيسية
                            ws_students.delete_rows(i + 2)
                            
                            # 2. الحذف الذكي من ورقة السلوك (behavior)
                            try:
                                ws_b = sh.worksheet("behavior")
                                b_data = ws_b.get_all_values()
                                for r_idx in range(len(b_data), 1, -1):
                                    if b_data[r_idx-1][0] == student_name:
                                        ws_b.delete_rows(r_idx)
                            except: pass
                            
                            st.warning(f"تم حذف {student_name} وكافة سجلاته")
                            st.rerun()
            except: st.info("لا توجد بيانات طلاب لعرضها حالياً.")
    st.title("👨‍🏫 لوحة تحكم المعلم")
    t1, t2 = st.tabs(["🎭 رصد السلوك", "📊 لوحة الدرجات"])
    
    with t1:
        with st.form("behavior_form", clear_on_submit=True):
            st.subheader("إضافة موقف سلوكي")
            # جلب الأسماء تلقائياً من العمود B في ورقة sheet1
            names = ["تحميل الأسماء..."]
            if sh:
                try:
                    ws_gr = sh.worksheet("sheet1")
                    names = ws_gr.col_values(2)[1:] # العمود B يتخطى العنوان
                except: names = ["خطأ في الاتصال"]

            s_name = st.selectbox("اسم الطالب", names)
            b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
            b_desc = st.selectbox("وصف السلوك", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
            
            if st.form_submit_button("🚀 حفظ الرصد"):
                if sh:
                    try:
                        ws_bh = sh.worksheet("behavior")
                        ws_bh.append_row([s_name, str(datetime.now().date()), b_type, b_desc])
                        st.success(f"تم الحفظ لـ {s_name}")
                    except: st.error("فشل الحفظ في ورقة behavior")

# --- 4. واجهة الطالب (بحث برقم الطالب في العمود A) ---
elif st.session_state.user_role == "student":
    st.title("🎓 بوابة الطالب")
    if sh:
        try:
            ws_gr = sh.worksheet("sheet1")
            all_data = ws_gr.get_all_values()
            # البحث عن الرقم في العمود A (index 0)
            row = next((r for r in all_data if r[0] == st.session_state.student_id), None)
            
            if row:
                st.success(f"👋 مرحباً بك يا: {row[1]}") # العمود B: الاسم
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("الفترة 1", row[2]) # العمود C
                with c2: st.metric("الفترة 2", row[3]) # العمود D
                with c3: st.metric("الأداء", row[4])   # العمود E
                
                # إحصائيات سلوك الطالب
                ws_bh = sh.worksheet("behavior")
                bh_list = [r for r in ws_bh.get_all_values() if r[0] == row[1]]
                st.divider()
                st.subheader("📊 إحصائيات سلوكك")
                col_p, col_n = st.columns(2)
                col_p.info(f"✅ إيجابي: {sum(1 for r in bh_list if 'إيجابي' in r[2])}")
                col_n.warning(f"❌ سلبي: {sum(1 for r in bh_list if 'سلبي' in r[2])}")
            else:
                st.error("❌ رقم الطالب غير مسجل في العمود A.")
        except Exception:
            st.info("🔄 جاري تحديث البيانات من السجلات...")
