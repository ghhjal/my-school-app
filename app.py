import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المعمري", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. إدارة الجلسة والدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with col_r:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي (id)")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st['id'].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة الطالب (نتائج + تحديث بيانات + إعلانات) ---
if st.session_state.role == "student":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    student_data = df_st[df_st['id'].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"مرحباً بك: {student_data['name']}")
    
    # قسم الإعلانات (يظهر حسب الصف)
    st.info(f"📢 إعلانات الصف: {student_data['class']}")
    df_ann = fetch_safe("announcements")
    if not df_ann.empty:
        my_ann = df_ann[df_ann['target_class'] == student_data['class']]
        for msg in my_ann['message']: st.warning(msg)

    tab1, tab2, tab3 = st.tabs(["📊 نتيجتي", "📧 تحديث بياناتي", "🗓️ جدول الاختبارات"])
    
    with tab1: # عرض الدرجات
        df_g = fetch_safe("grades")
        my_g = df_g[df_g['student_id'] == student_data['name']]
        st.table(my_g)
        st.metric("رصيد نقاط التميز ⭐", student_data['النقاط'])

    with tab2: # تحديث الإيميل والجوال من قبل الطالب
        st.subheader("تحديث بيانات التواصل")
        with st.form("update_info"):
            new_mail = st.text_input("البريد الإلكتروني", value=student_data['الإيميل'])
            new_phone = st.text_input("رقم الجوال", value=student_data['الجوال'])
            if st.form_submit_button("حفظ التعديلات"):
                ws_st = sh.worksheet("students"); cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 6, new_mail) # العمود F
                ws_st.update_cell(cell.row, 7, new_phone) # العمود G
                st.success("تم التحديث ✅"); time.sleep(1); st.rerun()

    with tab3: # جدول الاختبارات
        df_ex = fetch_safe("exams")
        st.dataframe(df_ex[df_ex['الصف'] == student_data['class']], use_container_width=True)

# --- 4. واجهة المعلم الكاملة ---
elif st.session_state.role == "teacher":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 الإعلانات والاختبارات"])

    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        tab_g, tab_b = st.tabs(["📝 رصد الدرجات", "🎭 رصد السلوك"])
        
        with tab_g: # تحديث درجات p1, p2, perf
            st.subheader("تحديث درجات الطالب")
            target = st.selectbox("اختر الطالب", df_st['name'].tolist())
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                v_p1 = c1.number_input("درجة p1")
                v_p2 = c2.number_input("درجة p2")
                v_perf = c3.number_input("المشاركة (perf)")
                if st.form_submit_button("تحديث"):
                    ws_g = sh.worksheet("grades")
                    try: 
                        fnd = ws_g.find(target)
                        ws_g.update(f'B{fnd.row}:D{fnd.row}', [[v_p1, v_p2, v_perf]])
                    except: ws_g.append_row([target, v_p1, v_p2, v_perf])
                    st.success("تم التحديث ✅"); st.rerun()
            st.dataframe(fetch_safe("grades"), use_container_width=True)

        with tab_b: # رصد السلوك
            with st.form("b_form"):
                sel_st = st.selectbox("اسم الطالب", df_st['name'].tolist())
                b_type = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("ملاحظة إضافية")
                if st.form_submit_button("حفظ الرصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old = int(ws_st.cell(c.row, 8).value or 0) # عمود النقاط H
                    ws_st.update_cell(c.row, 8, old + pts)
                    st.success("تم الحفظ ✅"); st.rerun()

    elif menu == "👥 إدارة الطلاب": # شاشة إدارة الطلاب الشاملة
        st.header("إدارة بيانات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        
        st.divider()
        col_del, col_add = st.columns([1, 2])
        with col_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اختر للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف النهائي"):
                for s in ["students", "grades", "behavior"]:
                    try: ws = sh.worksheet(s); ws.delete_rows(ws.find(to_del).row)
                    except: pass
                st.error("تم حذف الطالب من كافة السجلات"); st.rerun()
        
        with col_add: # إضافة طالب مع كافة الحقول
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_st"):
                c1, c2 = st.columns(2)
                ni_id = c1.text_input("الرقم (id)")
                ni_name = c2.text_input("الاسم الثلاثي")
                c3, c4, c5 = st.columns(3)
                ni_cls = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث"])
                ni_yr = c4.text_input("العام", value="1446هـ")
                ni_sem = c5.text_input("المادة (sem)", value="اللغة الإنجليزية")
                if st.form_submit_button("إضافة"):
                    sh.worksheet("students").append_row([ni_id, ni_name, ni_cls, ni_yr, ni_sem, "", "", 0])
                    st.success("تمت الإضافة بنجاح ✅"); st.rerun()

    elif menu == "📢 الإعلانات والاختبارات":
        st.subheader("نشر إعلان مخصص لصف")
        with st.form("ann_f"):
            t_cls = st.selectbox("الصف المستهدف", ["الأول", "الثاني", "الثالث"])
            t_msg = st.text_area("نص الإعلان")
            if st.form_submit_button("نشر الآن"):
                sh.worksheet("announcements").append_row([t_cls, t_msg])
                st.success("تم النشر ✅")
