import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الاتصال ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_data_safe(sheet_name, expected_cols):
    try:
        if sh:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df.columns = expected_cols[:len(df.columns)]
                return df
    except: pass
    return pd.DataFrame(columns=expected_cols)

# --- 2. نظام الدخول والخروج ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("🔐 بوابة الدخول الموحدة")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="login_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_in = st.text_input("الرقم الأكاديمي للطالب", key="login_sid")
        if st.button("دخول الطالب"):
            if sid_in:
                # التحقق من وجود الطالب
                df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
                # تحويل الرقم لنص للمقارنة الصحيحة
                student_match = df_st[df_st["الرقم"].astype(str) == str(sid_in)]
                if not student_match.empty:
                    st.session_state.role = "student"
                    st.session_state.student_id = str(sid_in)
                    st.session_state.student_name = student_match.iloc[0]["الاسم"]
                    st.rerun()
                else: st.error("الرقم الأكاديمي غير مسجل")
    st.stop()

# زر الخروج الجانبي
with st.sidebar:
    st.write(f"👤 مرحباً: {st.session_state.role}")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
    st.divider()

# --- 3. واجهة المعلم (بدون أي تعديل على الحقول) ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t_reg, t_view = st.tabs(["📝 تسجيل جديد", "📋 البحث والحذف الشامل"])
        with t_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    syear = st.selectbox("العام الدراسي", ["1446هـ", "1447هـ", "1448هـ", "1449هـ", "1450هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ البيانات"):
                    if sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        st.success(f"✅ تم حفظ {sname}"); time.sleep(1); st.rerun()
        with t_view:
            df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            st.divider()
            del_target = st.selectbox("حذف طالب نهائياً", [""] + df_st["الاسم"].tolist())
            if st.button("تأكيد الحذف الشامل"):
                if del_target:
                    target_name = del_target.strip()
                    with st.spinner("جاري تنظيف كافة السجلات..."):
                        for sn in ["students", "behavior", "grades"]:
                            ws = sh.worksheet(sn)
                            while True:
                                try:
                                    cell = ws.find(target_name); ws.delete_rows(cell.row)
                                except: break
                    st.success(f"🗑️ تم المسح بنجاح"); time.sleep(1); st.rerun()

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        df_all = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
        if not df_all.empty:
            t_grad, t_beh = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            with t_grad:
                with st.form("grade_form"):
                    sel_st = st.selectbox("اختر الطالب", df_all["الاسم"].tolist())
                    c1, c2, c3 = st.columns(3)
                    p1, p2, work = c1.number_input("الفترة 1"), c2.number_input("الفترة 2"), c3.number_input("المشاركة والمهام")
                    if st.form_submit_button("تحديث"):
                        ws_g = sh.worksheet("grades")
                        try:
                            cell = ws_g.find(sel_st.strip())
                            ws_g.update(f'B{cell.row}:D{cell.row}', [[p1, p2, work]])
                        except: ws_g.append_row([sel_st.strip(), p1, p2, work])
                        st.success("✅ تم التحديث"); time.sleep(1); st.rerun()
                df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
                st.dataframe(df_g, use_container_width=True, hide_index=True)
            with t_beh:
                with st.form("beh_form"):
                    b_st = st.selectbox("اسم الطالب", df_all["الاسم"].tolist())
                    b_date = st.date_input("التاريخ", datetime.now())
                    b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    b_note = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد"):
                        sh.worksheet("behavior").append_row([b_st, str(b_date), b_type, b_note])
                        st.success("✅ تم الرصد"); time.sleep(1); st.rerun()
                df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
                st.dataframe(df_b, use_container_width=True, hide_index=True)

# --- 4. واجهة الطالب المطورة (بيانات كاملة) ---
elif st.session_state.role == "student":
    st.title(f"🎓 لوحة تحكم الطالب: {st.session_state.student_name}")
    
    # جلب البيانات
    df_st = fetch_data_safe("students", ["الرقم", "الاسم", "الصف", "السنة", "المادة", "المرحلة"])
    df_g = fetch_data_safe("grades", ["الطالب", "ف1", "ف2", "مشاركة"])
    df_b = fetch_data_safe("behavior", ["الاسم", "التاريخ", "النوع", "الملاحظة"])
    
    # 1. المعلومات الأساسية
    my_info = df_st[df_st["الرقم"].astype(str) == st.session_state.student_id].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("الصف", my_info["الصف"])
    c2.metric("المرحلة", my_info["المرحلة"])
    c3.metric("المادة", my_info["المادة"])
    
    st.divider()
    
    # 2. عرض الدرجات
    st.subheader("📊 نتائج التقييم الدراسي")
    my_grades = df_g[df_g["الطالب"] == st.session_state.student_name]
    if not my_grades.empty:
        st.table(my_grades)
    else:
        st.info("لم يتم رصد درجاتك بعد.")
        
    st.divider()
    
    # 3. عرض السلوك
    st.subheader("🎭 سجل السلوك والملاحظات")
    my_beh = df_b[df_b["الاسم"] == st.session_state.student_name]
    if not my_beh.empty:
        for i, row in my_beh.iterrows():
            color = "green" if "إيجابي" in row["النوع"] else "red"
            st.markdown(f"""
            <div style="padding:10px; border-radius:10px; border-right: 5px solid {color}; background-color: #f9f9f9; margin-bottom:10px">
                <strong>التاريخ:</strong> {row['التاريخ']} | <strong>النوع:</strong> {row['النوع']}<br>
                <strong>الملاحظة:</strong> {row['الملاحظة']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("سجلك السلوكي نظيف، واصل تميزك!")
