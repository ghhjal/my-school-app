import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الصفحة والاتصال المحسن (لحل مشكلة Quota) ---
st.set_page_config(page_title="نظام المدرسة الرقمي المتكامل", layout="wide")

# استخدام التخزين المؤقت لتقليل الطلبات على جوجل
@st.cache_resource(ttl=600)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except:
        return None

sh = get_db()

# دالة تحديث الدرجات بطلب واحد (Batch Update)
def safe_update_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
        return "✅ تم تحديث الدرجات بنجاح"
    except:
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "✅ تم رصد درجات جديدة"

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="pwd_t")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي", key="sid_s")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with tab_reg:
            with st.form("reg_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.text_input("الصف", value="الأول")
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ الطالب"):
                    sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                    sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                    st.success("✅ تم التسجيل"); time.sleep(1); st.rerun()

        with tab_view:
            st.subheader("📋 كشف الطلاب (مع الحذف الشامل)")
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                if not data:
                    st.info("القائمة فارغة.")
                else:
                    for idx, row in enumerate(data):
                        col_i, col_d = st.columns([4, 1])
                        col_i.write(f"👤 **{row['name']}** | الرقم: `{row['id']}`")
                        # منطق الحذف الشامل لجميع الجداول
                        if col_d.button("🗑️ حذف", key=f"del_{row['id']}"):
                            with st.spinner(f"جاري حذف {row['name']}..."):
                                ws_st.delete_rows(idx + 2)
                                for sn in ["grades", "behavior", "sheet1"]:
                                    try:
                                        target = sh.worksheet(sn)
                                        term = str(row['name']) if sn != "sheet1" else str(row['id'])
                                        for cell in reversed(target.findall(term)):
                                            target.delete_rows(cell.row)
                                    except: continue
                                st.success("تم الحذف بنجاح"); time.sleep(1); st.rerun()
            except: st.error("خطأ في تحميل القائمة")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            # جلب الأسماء بشكل آمن لضمان عدم ظهور "أضف طلاباً أولاً"
            all_st_data = sh.worksheet("students").get_all_values()
            if len(all_st_data) <= 1:
                st.warning("⚠️ يرجى إضافة طلاب أولاً")
            else:
                names = [r[1] for r in all_st_data[1:]]
                t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
                
                with t_g:
                    with st.form("g_form"):
                        sel = st.selectbox("الطالب", names)
                        c1, c2, c3 = st.columns(3)
                        v1, v2, vp = c1.number_input("P1", 0.0), c2.number_input("P2", 0.0), c3.number_input("Perf", 0.0)
                        if st.form_submit_button("حفظ الدرجات"):
                            st.success(safe_update_grades(sel, v1, v2, vp))
                            time.sleep(1); st.rerun()
                    st.dataframe(pd.DataFrame(sh.worksheet("grades").get_all_records()), use_container_width=True, hide_index=True)

                with t_b:
                    with st.form("b_form"):
                        bs = st.selectbox("الطالب", names, key="bs_s")
                        bt = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                        bn = st.text_input("الملاحظة")
                        if st.form_submit_button("رصد السلوك"):
                            # إضافة السلوك بطلب واحد لتقليل الضغط
                            sh.worksheet("behavior").append_row([bs, str(datetime.now().date()), bt, bn])
                            st.success("✅ تم الرصد بنجاح"); time.sleep(1); st.rerun()
                    # عرض الجدول بالأسفل كما طلبت
                    st.dataframe(pd.DataFrame(sh.worksheet("behavior").get_all_records()), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"⚠️ خطأ (Quota): {e}")
