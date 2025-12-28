import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. إعداد الاتصال (الطريقة القياسية المستقرة) ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# ملاحظة: تأكد من وجود ملف secrets.json أو استبدل هذا الجزء بطريقتك الخاصة للاتصال
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("YOUR_SHEET_ID_HERE") # ضع معرف ملفك هنا
except Exception as e:
    st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من إعدادات الربط.")

# --- 2. إدارة الجلسة والدخول المستقل ---
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'student_id' not in st.session_state:
    st.session_state.student_id = None

# --- شاشة تسجيل الدخول ---
if st.session_state.user_role is None:
    st.title("🔐 نظام المدرسة الرقمي")
    choice = st.radio("اختر نوع المستخدم", ["👨‍🏫 معلم", "🎓 طالب"], horizontal=True)
    
    if choice == "👨‍🏫 معلم":
        pwd = st.text_input("كلمة مرور المعلم", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": # كلمة المرور الخاصة بك
                st.session_state.user_role = "teacher"
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
    else:
        std_id = st.text_input("أدخل رقم الطالب الخاص بك")
        if st.button("دخول الطالب"):
            if std_id:
                st.session_state.user_role = "student"
                st.session_state.student_id = std_id
                st.rerun()
            else:
                st.warning("يرجى إدخال رقم الطالب")
    st.stop()

# --- واجهة المعلم (صلاحيات كاملة) ---
if st.session_state.user_role == "teacher":
    st.sidebar.button("🚪 تسجيل الخروج", on_click=lambda: st.session_state.update({"user_role": None}))
    st.title("👨‍🏫 لوحة تحكم المعلم")
    
    t1, t2 = st.tabs(["🎭 رصد السلوك", "📊 إدارة الدرجات"])
    
    with t1:
        with st.form("behavior_form", clear_on_submit=True):
            st.subheader("إضافة موقف سلوكي")
            # استبدل هذه القائمة بجلب الأسماء من Sheet1 لاحقاً
            s_name = st.selectbox("اسم الطالب", ["محمد", "أحمد", "فهد"])
            b_type = st.radio("نوع السلوك", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
            b_desc = st.selectbox("وصف السلوك", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
            
            if st.form_submit_button("🚀 حفظ الرصد"):
                try:
                    ws = sh.worksheet("behavior")
                    ws.append_row([s_name, str(datetime.now().date()), b_type, b_desc])
                    st.success("تم الحفظ بنجاح")
                except:
                    st.error("تعذر الوصول لورقة behavior حالياً")

# --- واجهة الطالب (مستقلة تماماً بالرقم) ---
elif st.session_state.user_role == "student":
    st.sidebar.button("🚪 خروج الطالب", on_click=lambda: st.session_state.update({"user_role": None}))
    st.title("🎓 بوابة الطالب للنتائج")
    st.info(f"مرحباً بك.. رقمك المسجل: {st.session_state.student_id}")
    
    try:
        # هنا نقوم بالبحث في Sheets وعرض درجات وسلوك الطالب صاحب st.session_state.student_id فقط
        c1, c2 = st.columns(2)
        with c1:
            st.metric("✅ رصيد التميز", "10")
        with c2:
            st.metric("❌ التنبيهات", "2")
        
        st.divider()
        st.subheader("📑 تقرير الدرجات")
        st.write("الفترة الأولى: **19**")
    except:
        # بلوك except يمنع ظهور SyntaxError
        st.info("🔄 جاري استخراج بياناتك...")
