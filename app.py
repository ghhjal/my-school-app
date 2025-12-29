import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد المتكاملة", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except: return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 منصة الأستاذ زياد المعمري</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 دخول المعلم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 دخول الطالب")
        sid = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# --- 3. واجهة الطالب (إعلانات مخصصة + تحديث بيانات + نتائج) ---
if st.session_state.role == "student":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    student_data = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    
    st.title(f"مرحباً بك: {student_data['name']}")
    
    # 📢 الإعلانات المخصصة للصف الدراسي
    st.markdown(f"#### 📢 إعلانات الصف: {student_data['class']}")
    df_ann = fetch_safe("announcements")
    if not df_ann.empty:
        my_ann = df_ann[df_ann['target_class'] == student_data['class']]
        for m in my_ann['message']: st.info(m)

    st.divider()
    t1, t2, t3 = st.tabs(["📊 نتيجتي وتقييمي", "📧 تحديث بياناتي", "📝 الاختبارات"])
    
    with t1:
        df_g = fetch_safe("grades")
        st.dataframe(df_g[df_g.iloc[:,0] == student_data['name']], use_container_width=True, hide_index=True)
        st.metric("رصيد نقاط التميز ⭐", student_data['النقاط'] if 'النقاط' in student_data else 0)
    
    with t2:
        st.subheader("تحديث البريد الإلكتروني والجوال")
        with st.form("update_contact"):
            new_mail = st.text_input("البريد الإلكتروني", value=student_data.get('الإيميل', ''))
            new_phone = st.text_input("رقم الجوال", value=student_data.get('الجوال', ''))
            if st.form_submit_button("تحديث"):
                ws_st = sh.worksheet("students"); cell = ws_st.find(st.session_state.sid)
                ws_st.update_cell(cell.row, 7, new_mail) # عمود الإيميل
                ws_st.update_cell(cell.row, 8, new_phone) # عمود الجوال
                st.success("تم التحديث ✅"); time.sleep(1); st.rerun()

# --- 4. واجهة المعلم (الإدارة + السلوك + الدرجات + الإعلانات) ---
elif st.session_state.role == "teacher":
    st.sidebar.button("تسجيل خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب", "📢 نشر إعلان مخصص"])

    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        tab_b, tab_g = st.tabs(["🎭 السلوك (مع فلترة تلقائية)", "📝 رصد الدرجات"])
        
        with tab_b:
            st.subheader("رصد السلوك")
            with st.form("b_form"):
                sel_st = st.selectbox("اختر الطالب", df_st['name'].tolist())
                b_type = st.radio("النوع", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                if st.form_submit_button("حفظ"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([sel_st, str(datetime.now().date()), b_type, ""])
                    ws_st = sh.worksheet("students"); c = ws_st.find(sel_st)
                    old = int(ws_st.cell(c.row, 9).value or 0); ws_st.update_cell(c.row, 9, old + pts)
                    st.success("تم الحفظ"); st.rerun()
            st.divider()
            st.subheader(f"📋 سجل الطالب: {sel_st}")
            df_b = fetch_safe("behavior")
            st.dataframe(df_b[df_b.iloc[:,0] == sel_st], use_container_width=True)

        with tab_g:
            st.subheader("رصد ف1، ف2، والمشاركة")
            df_g = fetch_safe("grades")
            target = st.selectbox("الطالب", df_st['name'].tolist())
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1"); f2 = c2.number_input("ف2"); part = c3.number_input("المشاركة والمهام")
                if st.form_submit_button("تحديث الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try: fnd = ws_g.find(target); ws_g.update(f'B{fnd.row}:D{fnd.row}', [[f1, f2, part]])
                    except: ws_g.append_row([target, f1, f2, part])
                    st.success("✅ تم التحديث"); st.rerun()
            st.divider()
            st.subheader("📋 كشف الدرجات العام")
            st.dataframe(df_g, use_container_width=True)

    elif menu == "👥 إدارة الطلاب":
        st.header("إدارة الطلاب والحذف النهائي")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True)
        st.divider()
        c_del, c_add = st.columns([1, 2])
        with c_del:
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اختر للحذف", [""] + df_st['name'].tolist())
            if st.button("تأكيد الحذف الشامل"):
                for s in ["students", "grades", "behavior"]:
                    try: ws = sh.worksheet(s); ws.delete_rows(ws.find(to_del).row)
                    except: pass
                st.error("تم الحذف"); st.rerun()
        with c_add:
            st.subheader("📝 إضافة طالب جديد")
            with st.form("add_st"):
                id_v = st.text_input("الرقم")
                name_v = st.text_input("الاسم")
                col1, col2, col3 = st.columns(3)
                cls_v = col1.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                yr_v = col2.text_input("العام", value="1446هـ")
                lev_v = col3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                sub_v = st.text_input("المادة الدراسية")
                if st.form_submit_button("إضافة"):
                    sh.worksheet("students").append_row([id_v, name_v, cls_v, yr_v, sub_v, lev_v, "", "", 0])
                    st.success("تمت الإضافة"); st.rerun()

    elif menu == "📢 نشر إعلان مخصص":
        st.header("📢 إعلانات الصفوف")
        with st.form("ann"):
            t_cls = st.selectbox("الصف المستهدف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            msg = st.text_area("نص الإعلان")
            if st.form_submit_button("نشر"):
                sh.worksheet("announcements").append_row([t_cls, msg])
                st.success("تم النشر ✅")
