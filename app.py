import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. إعدادات الصفحة والاتصال ---
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

# --- وظائف مساعدة ---
def update_or_append_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update_cell(cell.row, 2, p1)
        ws.update_cell(cell.row, 3, p2)
        ws.update_cell(cell.row, 4, pf)
        return "✅ تم تحديث الدرجات"
    except:
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "✅ تم رصد درجات جديدة"

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="l_pwd")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي", key="l_sid")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

if st.sidebar.button("🚪 تسجيل الخروج", key="logout_main"):
    st.session_state.role = None; st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_new, tab_list = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with tab_new:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                    # إضافة المرحلة الدراسية كما طلبت
                    sphase = st.selectbox("المرحلة الدراسية", ["ابتدائي", "متوسط", "ثانوي"])
                with c2:
                    sclass = st.text_input("الصف (مثلاً: الأول)", value="الأول")
                    syear = st.selectbox("السنة", ["1446هـ", "1447هـ"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                
                if st.form_submit_button("حفظ البيانات"):
                    if sh and sname:
                        # حفظ المرحلة في عمود إضافي
                        sh.worksheet("students").append_row([str(sid), sname, sclass, syear, ssub, sphase])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success(f"✅ تم تسجيل الطالب {sname} بمرحلة {sphase}")
                        st.rerun()

        with tab_list:
            st.subheader("📋 كشف الطلاب (مع الحذف الشامل)")
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                if not data: st.info("القائمة فارغة")
                else:
                    for idx, row in enumerate(data):
                        col_i, col_d = st.columns([4, 1])
                        col_i.write(f"👤 **{row['name']}** | الرقم: `{row['id']}` | المرحلة: {row.get('sem', 'غير محدد')}")
                        # حل مشكلة رسالة الخطأ عند الحذف
                        if col_d.button("🗑️ حذف", key=f"del_st_{row['id']}_{idx}"):
                            with st.spinner("جاري الحذف..."):
                                ws_st.delete_rows(idx + 2)
                                # حذف السجلات المرتبطة
                                for sn in ["grades", "behavior", "sheet1"]:
                                    try:
                                        target_ws = sh.worksheet(sn)
                                        # البحث بالاسم أو الرقم للحذف الشامل
                                        search_term = str(row['name']) if sn != "sheet1" else str(row['id'])
                                        cells = target_ws.findall(search_term)
                                        for cell in reversed(cells): target_ws.delete_rows(cell.row)
                                    except: pass
                                st.success(f"تم حذف {row['name']} بنجاح")
                                st.rerun()
            except Exception as e: st.error(f"خطأ في التحميل: {e}")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        # جلب الجداول للجلسة لمنع الوميض
        if 'g_df' not in st.session_state: st.session_state.g_df = pd.DataFrame(sh.worksheet("grades").get_all_records())
        if 'b_df' not in st.session_state: st.session_state.b_df = pd.DataFrame(sh.worksheet("behavior").get_all_records())
        
        try:
            names = [r[1] for r in sh.worksheet("students").get_all_values()[1:]]
            t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with t_g:
                with st.form("g_update"):
                    sel = st.selectbox("الطالب", names)
                    g1, g2, pf = st.columns(3)
                    v1, v2, vp = g1.number_input("P1", 0.0), g2.number_input("P2", 0.0), pf.number_input("Perf", 0.0)
                    if st.form_submit_button("تحديث الدرجات"):
                        st.success(update_or_append_grades(sel, v1, v2, vp))
                        st.session_state.g_df = pd.DataFrame(sh.worksheet("grades").get_all_records())
                        st.rerun()
                st.dataframe(st.session_state.g_df, use_container_width=True, hide_index=True)

            with t_b:
                with st.form("b_form"):
                    bs = st.selectbox("الطالب", names, key="bs_f")
                    bt = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    bn = st.text_input("الملاحظة")
                    if st.form_submit_button("رصد"):
                        sh.worksheet("behavior").append_row([bs, str(datetime.now().date()), bt, bn])
                        st.session_state.b_df = pd.DataFrame(sh.worksheet("behavior").get_all_records())
                        st.success("تم الرصد"); st.rerun()
                st.dataframe(st.session_state.b_df, use_container_width=True, hide_index=True)
        except: st.warning("أضف طلاباً أولاً")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("P1", res[2]); c2.metric("P2", res[3]); c3.metric("الأداء", res[4])
        else: st.error("غير مسجل")
    except: st.info("تحميل...")
