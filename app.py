import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# 1. تهيئة حالة الجلسة (لحل مشاكل AttributeError)
if 'role' not in st.session_state:
    st.session_state.role = None
if 'sid' not in st.session_state:
    st.session_state.sid = None

# 2. تحسين مظهر التطبيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .error-box { background-color: #ffebee; border: 1px solid #ffcdd2; padding: 10px; border-radius: 5px; color: #c62828; }
    </style>
""", unsafe_allow_html=True)

# 3. دالة الاتصال (تم تعديلها لضمان مطابقة الرابط)
def get_sh():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # ⚠️ تأكد أن هذا الرابط هو الرابط الفعلي لملف جوجل شيت الخاص بك
        # جرب نسخ الرابط مباشرة من المتصفح ولصقه هنا
        url = "https://docs.google.com/spreadsheets/d/1vA5W0Tq7Bv9K5G_xK8e8Tq_pWv_Y-L-2/edit"
        
        return client.open_by_url(url)
    except Exception as e:
        return None

sh = get_sh()

# --- واجهة تسجيل الدخول ---
if st.session_state.role is None:
    st.markdown("<h2 style='text-align: center;'>🌟 منصة الأستاذ زياد العمري</h2>", unsafe_allow_html=True)
    
    login_type = st.radio("دخول بصفتي:", ["طالب", "معلم"], horizontal=True)
    user_id = st.text_input("أدخل الكود الخاص بك (ID)").strip()
    
    if st.button("🚀 دخول للمنصة", type="primary"):
        if login_type == "معلم":
            if user_id == "1234":
                st.session_state.role = "teacher"
                st.rerun()
            else:
                st.error("❌ كود المعلم غير صحيح")
        else:
            if sh:
                try:
                    # تأكد أن اسم الورقة في جوجل شيت هو students بالضبط
                    ws = sh.worksheet("students")
                    df = pd.DataFrame(ws.get_all_records())
                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    
                    if user_id in df.iloc[:, 0].values:
                        st.session_state.role = "student"
                        st.session_state.sid = user_id
                        st.rerun()
                    else:
                        st.error(f"❌ الكود ({user_id}) غير مسجل")
                except Exception as e:
                    st.error(f"❌ فشل في قراءة الورقة: تأكد من تسميتها 'students'")
            else:
                st.error("❌ لا يوجد اتصال بقاعدة البيانات (خطأ 404)")

# --- واجهة المعلم ---
elif st.session_state.role == "teacher":
    st.title("👨‍🏫 إدارة الطلاب")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    
    if sh:
        try:
            ws = sh.worksheet("students")
            st.success("✅ متصل بقاعدة البيانات")
            
            # قسم إضافة طالب (كما في صورتك)
            with st.expander("➕ إضافة طالب جديد"):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("الكود (ID)")
                nname = c2.text_input("الاسم")
                nclass = c3.selectbox("الصف", ["الثاني", "الثالث", "الرابع"])
                
                if st.button("إضافة"):
                    ws.append_row([nid, nname, nclass, "1447", "نشط", "English", "ابتدائي", "", "", "0"])
                    st.success("تمت الإضافة بنجاح")
                    st.rerun()
        except:
            st.error("❌ الورقة 'students' غير موجودة في ملف الإكسل")

# --- واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 صفحة الطالب")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.role = None
        st.rerun()
    
    if sh:
        df = pd.DataFrame(sh.worksheet("students").get_all_records())
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        data = df[df.iloc[:, 0] == st.session_state.sid].iloc[0]
        st.write(f"أهلاً بك يا {data.iloc[1]}")
        st.metric("رصيد نقاطك 🌟", data.iloc[8])
