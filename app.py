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

# --- 2. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 بوابة الدخول")
    t_m, t_s = st.tabs(["👨‍🏫 المعلم", "🎓 الطالب"])
    with t_m:
        pwd = st.text_input("كلمة المرور", type="password", key="p_t")
        if st.button("دخول المعلم"):
            if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with t_s:
        sid_l = st.text_input("الرقم الأكاديمي", key="s_l")
        if st.button("دخول الطالب"):
            if sid_l: st.session_state.role = "student"; st.session_state.student_id = sid_l; st.rerun()
    st.stop()

if st.sidebar.button("🚪 تسجيل الخروج", key="lg_btn"):
    st.session_state.role = None; st.rerun()

# --- 3. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.radio("القائمة الرئيسية", ["👥 إدارة الطلاب", "📊 الدرجات والسلوك"])

    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة شؤون الطلاب")
        t1, t2 = st.tabs(["📝 تسجيل جديد", "📋 قائمة الطلاب"])
        
        with t1:
            with st.form("reg", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    sid = st.number_input("الرقم الأكاديمي", min_value=1, step=1)
                    sname = st.text_input("اسم الطالب")
                with c2:
                    sclass = st.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                    ssub = st.text_input("المادة", value="اللغة الإنجليزية")
                if st.form_submit_button("حفظ"):
                    if sh and sname:
                        sh.worksheet("students").append_row([str(sid), sname, sclass, "1446هـ", ssub])
                        sh.worksheet("sheet1").append_row([str(sid), sname, "0", "0", "0"])
                        st.success(f"✅ تم حفظ {sname}")
                        st.rerun()

        with t2:
            st.subheader("📋 كشف الطلاب المسجلين")
            try:
                ws_st = sh.worksheet("students")
                data = ws_st.get_all_records()
                if data:
                    for index, row in enumerate(data):
                        c_info, c_del = st.columns([4, 1])
                        name = row.get('name', '؟؟')
                        id_val = str(row.get('id', ''))
                        
                        c_info.markdown(f"👤 **{name}** | الرقم: `{id_val}`")
                        
                        if c_del.button("🗑️ حذف", key=f"d_{id_val}_{index}"):
                            with st.spinner(f"جاري حذف {name} وجميع سجلاته..."):
                                # 1. الحذف من ورقة الطلاب
                                ws_st.delete_rows(index + 2)
                                
                                # 2. الحذف الشامل من الأوراق الأخرى (الدرجات، السلوك، sheet1)
                                for sheet_name in ["grades", "behavior", "sheet1"]:
                                    try:
                                        curr_ws = sh.worksheet(sheet_name)
                                        cells = curr_ws.findall(name if sheet_name != "sheet1" else id_val)
                                        # الحذف من الأسفل للأعلى لضمان عدم تغير أرقام الصفوف أثناء المسح
                                        for cell in reversed(cells):
                                            curr_ws.delete_rows(cell.row)
                                    except: pass
                                
                                st.success(f"تم حذف {name} وكافة بياناته بنجاح")
                                st.rerun()
                else: st.info("القائمة فارغة")
            except Exception as e: st.error(f"خطأ في تحميل البيانات: {e}")

    elif menu == "📊 الدرجات والسلوك":
        st.header("📊 رصد الدرجات والسلوك")
        try:
            ws_st = sh.worksheet("students")
            names = [r[1] for r in ws_st.get_all_values()[1:]]
            tg, tb = st.tabs(["📝 الدرجات", "🎭 السلوك"])
            
            with tg:
                with st.form("gf"):
                    sn = st.selectbox("الطالب", names)
                    g1, g2, pf = st.columns(3)
                    v1 = g1.number_input("P1", 0.0)
                    v2 = g2.number_input("P2", 0.0)
                    vp = pf.number_input("Perf", 0.0)
                    if st.form_submit_button("حفظ الدرجات"):
                        sh.worksheet("grades").append_row([sn, v1, v2, vp])
                        st.success("✅ تم الحفظ")
            
            with tb:
                with st.form("bf"):
                    bn = st.selectbox("الطالب", names, key="bs")
                    bt = st.radio("النوع", ["✅ إيجابي", "❌ سلبي"], horizontal=True)
                    bnote = st.selectbox("الوصف", ["🌟 تميز", "📚 واجب", "⚠️ إزعاج", "➕ أخرى..."])
                    if st.form_submit_button("رصد"):
                        sh.worksheet("behavior").append_row([bn, str(datetime.now().date()), bt, bnote])
                        st.success("✅ تم الرصد")
        except: st.warning("أضف طلاباً أولاً")

# --- 4. واجهة الطالب ---
elif st.session_state.role == "student":
    st.title(f"🎓 نتائج الطالب")
    try:
        res = next((r for r in sh.worksheet("sheet1").get_all_values() if r[0] == st.session_state.student_id), None)
        if res:
            st.success(f"مرحباً {res[1]}")
            c1, c2, c3 = st.columns(3)
            c1.metric("P1", res[2]); c2.metric("P2", res[3]); c3.metric("الأداء", res[4])
        else: st.error("رقم غير مسجل")
    except: st.info("🔄 تحميل...")
