import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الاتصال الآمن وقاعدة البيانات ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال: {e}")
        return None

sh = get_db()

# وظيفة التحديث الذكي لمنع التكرار
def update_or_append_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update_cell(cell.row, 2, p1)
        ws.update_cell(cell.row, 3, p2)
        ws.update_cell(cell.row, 4, pf)
        return "✅ تم تحديث درجات الطالب بنجاح"
    except:
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "✅ تم رصد درجات جديدة للطالب"

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="l_p")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي", key="l_s")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

if st.sidebar.button("🚪 تسجيل الخروج", key="logout"):
    st.session_state.role = None; st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with tab_reg:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.text_input("الصف", value="الأول")
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ"):
                    sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                    sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                    st.success(f"✅ تم تسجيل {sname}")
                    st.rerun()

        with tab_view:
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                for idx, row in enumerate(data):
                    col_info, col_del = st.columns([4, 1])
                    col_info.write(f"👤 **{row['name']}** | الرقم: `{row['id']}` | المرحلة: {row.get('sem', '---')}")
                    if col_del.button("🗑️ حذف", key=f"del_{idx}"):
                        ws_st.delete_rows(idx + 2)
                        for sn in ["grades", "behavior", "sheet1"]:
                            try:
                                target = sh.worksheet(sn)
                                term = str(row['name']) if sn != "sheet1" else str(row['id'])
                                for cell in reversed(target.findall(term)): target.delete_rows(cell.row)
                            except: pass
                        st.rerun()
            except: st.info("القائمة فارغة")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            # إصلاح مشكلة جلب الأسماء لضمان عدم ظهور "أضف طلاباً أولاً" بالخطأ
            ws_students = sh.worksheet("students")
            all_student_data = ws_students.get_all_values()
            
            if len(all_student_data) <= 1:
                st.warning("⚠️ لا يوجد طلاب مسجلون. يرجى إضافة طلاب من شاشة 'إدارة الطلاب' أولاً.")
            else:
                student_names = [row[1] for row in all_student_data[1:]]
                t_grades, t_behavior = st.tabs(["📝 الدرجات", "🎭 السلوك"])
                
                with t_grades:
                    with st.form("g_form"):
                        target_name = st.selectbox("اختر الطالب", student_names)
                        c1, c2, c3 = st.columns(3)
                        p1 = c1.number_input("P1", 0.0); p2 = c2.number_input("P2", 0.0); pf = c3.number_input("Perf", 0.0)
                        if st.form_submit_button("تحديث الدرجات"):
                            st.success(update_or_append_grades(target_name, p1, p2, pf))
                            st.rerun()
                    # عرض الجدول تحت النموذج مباشرة
                    st.subheader("📋 كشف الدرجات المرصودة")
                    st.dataframe(pd.DataFrame(sh.worksheet("grades").get_all_records()), use_container_width=True, hide_index=True)

                with t_behavior:
                    with st.form("b_form"):
                        b_name = st.selectbox("اسم الطالب", student_names)
                        b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                        b_note = st.text_input("الملاحظة")
                        if st.form_submit_button("رصد السلوك"):
                            sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note])
                            st.success("✅ تم الرصد")
                            st.rerun()
                    # عرض الجدول تحت نموذج السلوك
                    st.subheader("📋 سجل السلوكيات")
                    st.dataframe(pd.DataFrame(sh.worksheet("behavior").get_all_records()), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"حدث خطأ في جلب البيانات: {e}")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("P1", res[2]); c2.metric("P2", res[3]); c3.metric("الأداء", res[4])
        else: st.error("رقم أكاديمي غير مسجل")
    except: st.info("🔄 جاري تحميل النتائج...")
