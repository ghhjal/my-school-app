import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. إعدادات الاتصال والتحكم في الحصص (Quota) ---
st.set_page_config(page_title="نظام المدرسة الرقمي", layout="wide")

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

# دالة تحديث الدرجات بطلب واحد لتقليل استهلاك Quota
def safe_update_grades(student_name, p1, p2, pf):
    try:
        ws = sh.worksheet("grades")
        cell = ws.find(student_name)
        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
        return "✅ تم تحديث الدرجات بنجاح"
    except:
        sh.worksheet("grades").append_row([student_name, p1, p2, pf])
        return "✅ تم رصد درجات جديدة"

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state: st.session_state.role = None

# إضافة زر الخروج في الشريط الجانبي إذا كان المستخدم مسجلاً [إصلاح طلبك]
if st.session_state.role:
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.role = None
        st.session_state.student_id = None
        st.rerun()

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t1, t2 = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t1:
        pwd = st.text_input("كلمة المرور", type="password", key="p_teacher")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t2:
        sid_l = st.text_input("الرقم الأكاديمي", key="s_student")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        tab_reg, tab_view = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب والبحث"])
        
        with tab_reg:
            with st.form("main_reg_form", clear_on_submit=True):
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
            st.subheader("🔍 البحث السريع")
            search_query = st.text_input("ابحث بالاسم أو الرقم الأكاديمي...", placeholder="اكتب للفلترة...")
            
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                if not data:
                    st.info("لا يوجد طلاب مسجلون.")
                else:
                    df = pd.DataFrame(data)
                    # تصفية الجدول بناءً على البحث
                    filtered_df = df[df.apply(lambda row: search_query.lower() in str(row['name']).lower() or search_query in str(row['id']), axis=1)]
                    
                    # عرض النتائج في جدول منظم [إصلاح طلبك]
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.subheader("🗑️ إجراءات الحذف")
                    # عرض أزرار الحذف بشكل منفصل للحفاظ على ترتيب الجدول
                    for idx, row in filtered_df.iterrows():
                        c_name, c_btn = st.columns([4, 1])
                        c_name.write(f" الطالب: **{row['name']}** (ID: {row['id']})")
                        if c_btn.button("حذف السجلات", key=f"del_{row['id']}"):
                            with st.spinner(f"جاري الحذف الشامل لـ {row['name']}..."):
                                for sn in ["behavior", "grades", "sheet1"]:
                                    try:
                                        target = sh.worksheet(sn)
                                        search = str(row['name']) if sn != "sheet1" else str(row['id'])
                                        for cell in reversed(target.findall(search)): target.delete_rows(cell.row)
                                    except: continue
                                # حذف من القائمة الرئيسية
                                ws_st.delete_rows(idx + 2)
                                st.success("تم الحذف بنجاح"); time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"⚠️ خطأ في تحميل البيانات: {e}")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            all_st = sh.worksheet("students").get_all_values()
            if len(all_st) <= 1:
                st.warning("⚠️ يرجى إضافة طلاب أولاً")
            else:
                names = [r[1] for r in all_st[1:]]
                t_g, t_b = st.tabs(["📝 الدرجات", "🎭 السلوك"])
                
                with t_g:
                    with st.form("g_update_form"):
                        sel_st = st.selectbox("الطالب", names)
                        c1, c2, c3 = st.columns(3)
                        p1, p2, pf = c1.number_input("P1", 0.0), c2.number_input("P2", 0.0), c3.number_input("Perf", 0.0)
                        if st.form_submit_button("تحديث الدرجات"):
                            st.success(safe_update_grades(sel_st, p1, p2, pf))
                            time.sleep(1); st.rerun()
                    st.dataframe(pd.DataFrame(sh.worksheet("grades").get_all_records()), use_container_width=True, hide_index=True)

                with t_b:
                    with st.form("b_add_form"):
                        b_st = st.selectbox("اسم الطالب", names, key="bs_key")
                        b_type = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                        b_note = st.text_input("الملاحظة")
                        if st.form_submit_button("رصد السلوك"):
                            sh.worksheet("behavior").append_row([b_st, str(datetime.now().date()), b_type, b_note])
                            st.success("✅ تم الرصد بنجاح"); time.sleep(1); st.rerun()
                    st.dataframe(pd.DataFrame(sh.worksheet("behavior").get_all_records()), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"⚠️ مشكلة في الاتصال (Quota): يرجى الانتظار قليلاً")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title("🎓 نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("P1", res[2]); c2.metric("P2", res[3]); c3.metric("الأداء", res[4])
        else: st.error("رقم غير مسجل")
    except: st.info("🔄 جاري التحميل...")
