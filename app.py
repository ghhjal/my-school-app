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
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) > 0:
            # معالجة ذكية للأعمدة المكررة لمنع الانهيار
            raw_headers = data[0]
            clean_headers = []
            for i, h in enumerate(raw_headers):
                name = h.strip() if h.strip() else f"col_{i}"
                if name in clean_headers: name = f"{name}_{i}"
                clean_headers.append(name)
            df = pd.DataFrame(data[1:], columns=clean_headers)
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
# 🛠️ واجهة المعلم
# ==========================================
if st.session_state.role == "teacher":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    menu = st.sidebar.selectbox("القائمة", ["👥 إدارة الطلاب", "📝 شاشة الدرجات", "🎭 رصد السلوك", "📢 شاشة الاختبارات"])

    # 1. إدارة الطلاب [إصلاح الحقول المفقودة]
    if menu == "👥 إدارة الطلاب":
        st.header("👥 إدارة سجلات الطلاب")
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        
        with st.form("add_student_form"):
            st.subheader("➕ إضافة طالب جديد")
            c1, c2, c3 = st.columns(3)
            nid = c1.text_input("الرقم الأكاديمي")
            nname = c2.text_input("الاسم الثلاثي")
            nclass = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            if st.form_submit_button("حفظ الطالب"):
                if nid and nname:
                    sh.worksheet("students").append_row([nid, nname, nclass, "1447", "1", "لغة إنجليزية", "ابتدائي", "", "", "0"])
                    st.success("تمت إضافة الطالب"); st.rerun()
        
        st.divider()
        st.subheader("🗑️ حذف طالب")
        del_target = st.selectbox("اختر الطالب للحذف", [""] + df_st.iloc[:, 1].tolist())
        if st.button("⚠️ حذف الطالب نهائياً"):
            if del_target:
                ws = sh.worksheet("students")
                cell = ws.find(del_target)
                ws.delete_rows(cell.row)
                st.warning(f"تم حذف {del_target}"); time.sleep(1); st.rerun()

    # 2. شاشة الدرجات [إصلاح الاختفاء]
    elif menu == "📝 شاشة الدرجات":
        st.header("📝 رصد الدرجات")
        df_st = fetch_safe("students")
        df_g = fetch_safe("grades")
        
        target_name = st.selectbox("اختر الطالب للرصد", [""] + df_st.iloc[:, 1].tolist())
        if target_name:
            curr = df_g[df_g.iloc[:, 0] == target_name]
            v1 = int(curr.iloc[0, 1]) if not curr.empty else 0
            v2 = int(curr.iloc[0, 2]) if not curr.empty else 0
            v3 = int(curr.iloc[0, 3]) if not curr.empty else 0
            
            with st.form("grading"):
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("الفترة 1", 0, 100, value=v1)
                p2 = c2.number_input("الفترة 2", 0, 100, value=v2)
                pf = c3.number_input("المشاركة", 0, 100, value=v3)
                if st.form_submit_button("حفظ الدرجات"):
                    ws = sh.worksheet("grades")
                    try:
                        cell = ws.find(target_name)
                        ws.update(f'B{cell.row}:D{cell.row}', [[p1, p2, pf]])
                    except: ws.append_row([target_name, p1, p2, pf])
                    st.success("تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("grades"), use_container_width=True)

    # 3. رصد السلوك [تفعيل الفلتر والحالة التلقائية]
    elif menu == "🎭 رصد السلوك":
        st.header("🎭 سجل السلوك")
        df_st = fetch_safe("students")
        with st.form("behavior_entry"):
            c1, c2 = st.columns(2)
            b_name = c1.selectbox("الطالب", [""] + df_st.iloc[:, 1].tolist())
            b_type = c2.selectbox("النوع", ["إيجابي", "سلبي", "تنبيه"])
            b_note = st.text_area("الملاحظة")
            if st.form_submit_button("رصد"):
                # الحالة عند الرصد هي دائماً "⏳ لم يتم القراءة"
                sh.worksheet("behavior").append_row([b_name, str(datetime.now().date()), b_type, b_note, "⏳ لم يتم القراءة"])
                st.success("تم الرصد"); st.rerun()
        
        st.divider()
        # طلب 3: تفعيل الفلتر ليعمل على الجدول بالأسفل
        f_name = st.selectbox("🔍 فلتر الجدول حسب اسم الطالب", ["الكل"] + df_st.iloc[:, 1].tolist())
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            view_df = df_b if f_name == "الكل" else df_b[df_b.iloc[:, 0] == f_name]
            st.table(view_df)

# ==========================================
# 👨‍🎓 واجهة الطالب [زر شكرا أستاذي يختفي فوراً]
# ==========================================
elif st.session_state.role == "student":
    st.sidebar.button("🚗 خروج", on_click=lambda: st.session_state.update({"role": None}))
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == st.session_state.sid].iloc[0]
    s_name = s_row.iloc[1]

    st.markdown(f"<h2 style='text-align: center;'>👋 مرحباً بك يا بطل: {s_name}</h2>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📊 نتيجتي الدراسية", "🎭 ملاحظاتي السلوكية"])
    
    with t2:
        df_b = fetch_safe("behavior")
        if not df_b.empty:
            my_b = df_b[df_b.iloc[:, 0] == s_name]
            for i, row in my_b.iterrows():
                # التحقق من الحالة الحالية
                status = row.iloc[4] if len(row) > 4 else "⏳ لم يتم القراءة"
                
                with st.container(border=True):
                    st.write(f"📅 {row.iloc[1]} | {row.iloc[2]}")
                    st.info(row.iloc[3])
                    
                    # طلب 1 و 2: الزر يختفي فوراً بعد الضغط ويحدث الحالة
                    if "✅ تمت القراءة" not in status:
                        if st.button(f"❤️ شكراً أستاذي", key=f"thanks_{i}"):
                            ws_b = sh.worksheet("behavior")
                            # البحث عن الصف بدقة لتحديثه
                            all_rows = ws_b.get_all_values()
                            for idx, r in enumerate(all_rows):
                                if r[0] == s_name and r[3] == row.iloc[3]:
                                    ws_b.update_cell(idx + 1, 5, "✅ تمت القراءة")
                                    st.success("شكراً لك!")
                                    time.sleep(1)
                                    st.rerun() # هذا الأمر سيخفي الزر فوراً
                    else:
                        st.markdown("<span style='color: green;'>✅ تمت القراءة</span>", unsafe_allow_html=True)
