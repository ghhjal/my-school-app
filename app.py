import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام الأستاذ زياد المعمري", layout="wide")

# دالة الاتصال بجوجل شيت باستخدام المفتاح السري
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

st.title("👨‍🏫 نظام الأستاذ زياد - الإدارة الذكية")

try:
    # الاتصال بالملف (تأكد أن اسم الورقة هو students)
    client = get_gspread_client()
    sh = client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    worksheet = sh.worksheet("students")
    
    # قراءة البيانات الحالية
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # عرض الجدول
    st.subheader("📋 قائمة الطلاب الحالية")
    st.dataframe(df, use_container_width=True)

    st.divider()

    # نموذج إضافة طالب (حفظ داخلي مباشر)
    st.subheader("➕ إضافة طالب جديد")
    with st.form("add_student", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_id = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
            new_name = st.text_input("اسم الطالب")
        with col2:
            new_class = st.text_input("الصف")
            # قيم افتراضية
            new_year = "1447هـ"
            new_sem = "الأول"
        
        submit_btn = st.form_submit_button("✅ حفظ البيانات فوراً")

        if submit_btn:
            if new_name:
                # الحفظ الصامت في السطر التالي
                worksheet.append_row([new_id, new_name, new_class, new_year, new_sem])
                st.success(f"تم حفظ الطالب {new_name} بنجاح!")
                st.balloons()
                st.rerun() # لتحديث الجدول فوراً
            else:
                st.warning("يرجى كتابة الاسم.")

except Exception as e:
    st.error("تأكد من وضع الـ Secrets بشكل صحيح ومشاركة الملف مع إيميل الخدمة.")
    st.info(f"تفاصيل الخطأ: {e}")
