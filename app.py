import streamlit as st
from gspread_streamlit import GSpreadSt
from datetime import datetime

# 1. إعداد الاتصال بـ Google Sheets
# تأكد من وضع مفاتيح الربط الخاصة بك هنا
# sh = gc.open_by_key("YOUR_SHEET_ID") 

# --- نظام إدارة الجلسة (تسجيل الدخول) ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'student_id' not in st.session_state:
    st.session_state.student_id = None

# --- شاشة تسجيل الدخول الرئيسية ---
if st.session_state.role is None:
    st.title("🔐 نظام المدرسة الذكي")
    t_login1, t_login2 = st.tabs(["👨‍🏫 بوابة المعلم", "🎓 بوابة الطالب"])
    
    with t_login1:
        pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": # غير كلمة السر هنا
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("كلمة المرور خاطئة")
                
    with t_login2:
        s_id = st.text_input("أدخل رقم الطالب")
        if st.button("دخول الطالب"):
            if s_id:
                st.session_state.role = "student"
                st.session_state.student_id = s_id
                st.rerun()
            else:
                st.warning("يرجى إدخال الرقم")
    st.stop()

# --- واجهة المعلم (رصد وإدارة) ---
if st.session_state.role == "teacher":
    st.sidebar.button("🚪 خروج", on_click=lambda: st.session_state.update({"role": None}))
    st.title("👨‍🏫 لوحة تحكم المعلم")
    
    tab1, tab2 = st.tabs(["📊 إدارة الدرجات", "🎭 رصد السلوك"])
    
    with tab1:
        st.info("هنا تضع كود إدارة الدرجات الخاص بك")
        
    with tab2:
        with st.form("behavior_form", clear_on_submit=True):
            st.subheader("رصد سلوك جديد")
            # استبدل names_list بقائمة أسمائك من Sheet1
            student = st.selectbox("اسم الطالب", ["محمد", "أحمد", "فهد"]) 
            b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
            b_desc = st.selectbox("الوصف", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
            
            if st.form_submit_button("🚀 حفظ الرصد"):
                try:
                    # ws = sh.worksheet("behavior")
                    # ws.append_row([student, str(datetime.now().date()), b_type, b_desc])
                    st.success(f"تم الرصد لـ {student}")
                except:
                    st.error("خطأ في الاتصال")

# --- واجهة الطالب (استعلام فقط) ---
elif st.session_state.role == "student":
    st.sidebar.button("🚪 خروج", on_click=lambda: st.session_state.update({"role": None}))
    st.title("🎓 ملف الطالب")
    st.success(f"مرحباً بك، رقمك الأكاديمي: {st.session_state.student_id}")
    
    try:
        # هنا يتم جلب البيانات وتصفيتها بناءً على st.session_state.student_id
        # ws_bh = sh.worksheet("behavior")
        # ws_gr = sh.worksheet("Sheet1")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ السلوك الإيجابي", "5")
        with col2:
            st.metric("❌ السلوك السلبي", "1")
            
        st.divider()
        st.subheader("📝 درجاتك الحالية")
        st.write("الفترة الأولى: 18/20")
    except:
        st.info("🔄 جاري تحميل بياناتك من السجلات...") # حل مشكلة Syntax بالكامل هنا
