import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time

# --- 1. الإعدادات والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد العمري", layout="wide")

@st.cache_resource(ttl=1)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 0:
            df = pd.DataFrame(data[1:], columns=[h.strip() for h in data[0]])
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# إدارة الجلسة
if 'role' not in st.session_state: st.session_state.role = None
if 'sid' not in st.session_state: st.session_state.sid = None

# ==========================================
# 🚪 شاشة الدخول
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎓 منصة الأستاذ زياد العمري التعليمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔐 منطقة المعلم")
        t_pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول المعلم"):
            if t_pwd == "1234": st.session_state.role = "teacher"; st.rerun()
    with c2:
        st.subheader("👨‍🎓 منطقة الطالب")
        sid_in = st.text_input("الرقم الأكاديمي")
        if st.button("دخول الطالب"):
            df_st = fetch_safe("students")
            if not df_st.empty and str(sid_in) in df_st.iloc[:, 0].astype(str).values:
                st.session_state.role = "student"; st.session_state.sid = str(sid_in); st.rerun()
            else: st.error("الرقم غير مسجل")
    st.stop()

# ==========================================
# 🛠️ واجهة المعلم (إصلاح الشاشات الأربع)
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    # 1. إدارة الطلاب
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        with st.form("add_st"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nstage = c3.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            c4, c5, c6 = st.columns(3)
            nclass = c4.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            nyear = c5.text_input("العام الدراسي", value="1447هـ")
            nsub = c6.text_input("المادة الدراسية", value="لغة إنجليزية")
            if st.form_submit_button("حفظ الطالب"):
                sh.worksheet("students").append_row([nid, nname, nclass, nyear, "1", nsub, nstage, "", "", "0"])
                st.success("تم الحفظ"); st.rerun()
        
        st.divider()
        st.subheader("🗑️ حذف شامل")
        del_target = st.selectbox("اختر الطالب للحذف النهائي", [""] + df_st.iloc[:, 1].tolist())
        if st.button("⚠️ حذف الطالب من كافة السجلات"):
            if del_target:
                for sn in ["students", "grades", "behavior"]:
                    try:
                        ws = sh.worksheet(sn)
                        cell = ws.find(del_target)
                        ws.delete_rows(cell.row)
                    except: pass
                st.warning(f"تم حذف {del_target} بنجاح"); time.sleep(1); st.rerun()

    # 2. شاشة الدرجات
    elif menu == "📝 شاشة الدرجات":
        st.header("📝 رصد وتحديث الدرجات")
        df_st = fetch_safe("students")
        sel_name = st.selectbox("اختر الطالب", [""] + df_st.iloc[:, 1].tolist())
        if sel_name:
            df_g = fetch_safe("grades")
            curr = df_g[df_g.iloc[:, 0] == sel_name]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            with st.form("g_form"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة 1", 0, 100, value=v1)
                p2 = c2.number_input("الفترة 2", 0, 100, value=v2)
                part = c3.number_input("المشاركة", 0, 100, value=v3)
                if st.form_submit_button("تحديث"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(sel_name)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, part]])
                    except: ws.append_row([sel_name, p1, p2, part])
                    st.success("تم التحديث"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. رصد السلوك
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 سجل السلوك")
        df_st = fetch_safe("students")
        with st.form("b_form"):
            c1, c2, c3 = st.columns(3)
            sb_name = c1.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
            sb_type = c2.selectbox("نوع السلوك", ["إيجابي", "سلبي", "تنبيه", "أخرى"])
            sb_date = c3.date_input("تاريخ الملاحظة")
            sb_note = st.text_area("الملاحظة")
            if st.form_submit_button("رصد الملاحظة"):
                sh.worksheet("behavior").append_row([sb_name, str(sb_date), sb_type, sb_note, "لم يتم القراءة"])
                st.success("تم الرصد"); st.rerun()
        
        st.divider()
        f_name = st.selectbox("🔍 فلتر حسب الطالب", ["الكل"] + df_st.iloc[:, 1].tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_b = df_b if f_name == "الكل" else df_b[df_b.iloc[:, 0] == f_name]
            st.table(view_b)

    # 4. شاشة الاختبارات
    elif menu == "📢 شاشة الاختبارات":
        st.header("📢 إعلانات الاختبارات")
        with st.form("ex"):
            c1, c2, c3 = st.columns(3)
            e_class = c1.selectbox("الصف", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_date = c2.date_input("التاريخ")
            e_title = c3.text_input("الموضوع")
            if st.form_submit_button("نشر"):
                sh.worksheet("exams").append_row([str(e_date), e_title, e_class])
                st.rerun()
        df_ex = fetch_safe("exams")
        for i, r in df_ex.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.info(f"📅 {r.iloc[0]} | 📢 {r.iloc[1]} | 👥 {r.iloc[2]}")
            if c2.button("🗑️ حذف", key=f"ex_{i}"):
                sh.worksheet("exams").delete_rows(i + 2); st.rerun()

# ==========================================
# 👨‍🎓 واجهة الطالب (التصميم الفعال)
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    # إعلانات في الأعلى
    df_ex = fetch_safe("exams")
    if not df_ex.empty:
        my_ex = df_ex[(df_ex.iloc[:, 2] == s_row.iloc[2]) | (df_ex.iloc[:, 2] == "الكل")]
        for _, ex in my_ex.iterrows():
            st.warning(f"🔔 **إعلان:** {ex.iloc[1]} بتاريخ {ex.iloc[0]}")

    # تصميم الهوية والأوسمة
    st.markdown(f"""
        <div style="text-align: center; background-color: #f0f2f6; padding: 20px; border-radius: 15px; border: 2px solid #1E3A8A;">
            <h2 style="color: #1E3A8A;">👋 مرحباً بالبطل: {s_name}</h2>
            <div style="display: flex; justify-content: center; gap: 20px;">
                <div style="background: white; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px #ccc; width: 100px;">
                    <span style="font-size: 30px;">🏆</span><br><b>{s_row.iloc[9]} نقطة</b>
                </div>
                <div style="background: white; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px #ccc; width: 100px;">
                    <span style="font-size: 30px;">🎖️</span><br><b>متميز</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.tabs(["📊 درجاتي الدراسية", "🎭 ملاحظاتي السلوكية"])
    
    with t1:
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g.iloc[:, 0] == s_name]
            if not my_g.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("الفترة 1", my_g.iloc[0, 1])
                c2.metric("الفترة 2", my_g.iloc[0, 2])
                c3.metric("المشاركة", my_g.iloc[0, 3])
            else: st.info("لا توجد درجات مرصودة")

    with t2:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for i, row in my_b.iterrows():
                status = row.iloc[4]
                with st.container(border=True):
                    st.write(f"📅 {row.iloc[1]} | {row.iloc[2]}")
                    st.info(row.iloc[3])
                    # زر الشكر الذكي
                    if "✅ تمت القراءة" not in status:
                        if st.button("❤️ شكراً أستاذي (تأكيد القراءة)", key=f"btn_{i}"):
                            ws = sh.worksheet("behavior")
                            # تحديث الحالة في جوجل شيت
                            all_v = ws.get_all_values()
                            for idx, r in enumerate(all_v):
                                if r[0] == s_name and r[3] == row.iloc[3]:
                                    ws.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                    st.success("تم إبلاغ المعلم"); time.sleep(1); st.rerun()
                    else:
                        st.success("✅ تمت القراءة")
