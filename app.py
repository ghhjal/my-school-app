import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الصفحة والاتصال ---
st.set_page_config(page_title="منصة الأستاذ زياد", layout="wide")

@st.cache_resource(ttl=300)
def get_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key("1_GSVxCKCamdoydymH6Nt5NQ0C_mmQfGTNrnb9ilUD_c")
    except Exception:
        return None

sh = get_db()

def fetch_safe(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [c.strip() for c in df.columns] # تنظيف المسافات
        return df
    except Exception:
        return pd.DataFrame()

# --- 2. التنسيق الجمالي (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; direction: rtl; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-right: 5px solid #1e3a8a; }
    .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; text-align: right; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center;'>🏛️ مرحباً بك في منصة الأستاذ زياد</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        choice = st.radio("نوع الدخول", ["👨‍🏫 معلم", "🎓 طالب"], horizontal=True)
        if choice == "👨‍🏫 معلم":
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول المعلم"):
                if pwd == "1234": st.session_state.role = "teacher"; st.rerun()
        else:
            sid = st.text_input("الرقم الأكاديمي")
            if st.button("دخول الطالب"):
                df_st = fetch_safe("students")
                if not df_st.empty and str(sid) in df_st.iloc[:,0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = str(sid); st.rerun()
                else: st.error("الرقم غير مسجل")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. واجهة المعلم ---
if st.session_state.role == "teacher":
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["📊 الدرجات والسلوك", "👥 إدارة الطلاب"])

    if menu == "📊 الدرجات والسلوك":
        df_st = fetch_safe("students")
        if df_st.empty: st.warning("لا يوجد طلاب مسجلين"); st.stop()
        
        name_col = df_st.columns[1]
        t1, t2 = st.tabs(["🎭 رصد السلوك والتحفيز", "📝 رصد الدرجات"])

        with t1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            with st.form("behavior_form"):
                st.subheader("🎭 إضافة سلوك ونقاط تميز")
                st_name = st.selectbox("اختر الطالب", df_st[name_col].tolist())
                b_type = st.radio("نوع السلوك (يؤثر على النقاط)", ["⭐ متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (-5)", "❌ سلبي (-10)"], horizontal=True)
                note = st.text_input("ملاحظة إضافية")
                if st.form_submit_button("📌 حفظ ورصد"):
                    pts = 10 if "⭐" in b_type else 5 if "✅" in b_type else -5 if "⚠️" in b_type else -10
                    sh.worksheet("behavior").append_row([st_name, str(datetime.now().date()), b_type, note])
                    ws_st = sh.worksheet("students"); c = ws_st.find(st_name)
                    old_pts = int(ws_st.cell(c.row, 9).value or 0)
                    ws_st.update_cell(c.row, 9, old_pts + pts)
                    st.success(f"تم تحديث نقاط {st_name}"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.dataframe(fetch_safe("behavior"), use_container_width=True)

        with t2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📝 تحديث درجات الطالب (منع التكرار)")
            df_g = fetch_safe("grades")
            target = st.selectbox("اختر الطالب لتعديل درجته", df_st[name_col].tolist())
            curr = df_g[df_g.iloc[:,0] == target]
            v1, v2, v3 = (float(curr.iloc[0,1]), float(curr.iloc[0,2]), float(curr.iloc[0,3])) if not curr.empty else (0.0, 0.0, 0.0)

            with st.form("grade_form"):
                c1, c2, c3 = st.columns(3)
                f1 = c1.number_input("ف1", value=v1); f2 = c2.number_input("ف2", value=v2); wrk = c3.number_input("مشاركة", value=v3)
                if st.form_submit_button("🔄 تحديث الدرجات"):
                    ws_g = sh.worksheet("grades")
                    try:
                        found = ws_g.find(target)
                        ws_g.update(f'B{found.row}:D{found.row}', [[f1, f2, wrk]])
                    except: ws_g.append_row([target, f1, f2, wrk])
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.dataframe(df_g, use_container_width=True)

    elif menu == "👥 إدارة الطلاب":
        st.markdown("<h2>👥 شاشة إدارة الطلاب</h2>", unsafe_allow_html=True)
        df_st = fetch_safe("students")
        st.dataframe(df_st, use_container_width=True, hide_index=True)

        st.divider()
        c_add, c_del = st.columns([2, 1])

        with c_add:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📝 إضافة طالب (بيانات كاملة)")
            with st.form("add_student_full"):
                ca, cb = st.columns(2)
                id_val = ca.text_input("الرقم الأكاديمي")
                name_val = cb.text_input("الاسم الثلاثي")
                cc, cd = st.columns(2)
                class_val = cc.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                year_val = cd.text_input("العام الدراسي", value="1446هـ")
                ce, cf = st.columns(2)
                sub_val = ce.text_input("المادة", value="اللغة الإنجليزية")
                level_val = cf.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
                if st.form_submit_button("🚀 حفظ الطالب"):
                    if id_val and name_val:
                        sh.worksheet("students").append_row([id_val, name_val, class_val, year_val, sub_val, level_val, "", "", 0])
                        st.success("تمت الإضافة بنجاح"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with c_del:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("🗑️ حذف طالب")
            to_del = st.selectbox("اختر الاسم للحذف", [""] + df_st.iloc[:,1].tolist())
            if st.button("تأكيد الحذف"):
                if to_del:
                    for s in ["students", "behavior", "grades"]:
                        try:
                            ws = sh.worksheet(s); cell = ws.find(to_del); ws.delete_rows(cell.row)
                        except: continue
                    st.success("تم الحذف"); time.sleep(1); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 5. واجهة الطالب ---
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    me = df_st[df_st.iloc[:,0].astype(str) == st.session_state.sid].iloc[0]
    st.markdown(f"<div class='card'><h2>🎓 الطالب: {me.iloc[1]}</h2></div>", unsafe_allow_html=True)
    st.metric("رصيد نقاط التميز 🌟", f"{me.iloc[8]} نقطة")
    st.subheader("📊 تقرير درجاتك")
    st.dataframe(fetch_safe("grades").query(f"الطالب == '{me.iloc[1]}'"), use_container_width=True, hide_index=True)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None; st.rerun()
