import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
from google.oauth2.service_account import Credentials
import urllib.parse

# --- 1. إعدادات الصفحة (يجب أن يكون أول أمر) ---
st.set_page_config(page_title="منصة زياد الذكية", layout="wide", initial_sidebar_state="collapsed")

# --- 2. دوال الاتصال الآمن وقاعدة البيانات ---
@st.cache_resource
def get_client():
    """الاتصال بجوجل شيت باستخدام الأسرار المرفوعة"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    """جلب البيانات كجدول بيانات مع ربط العناوين تلقائياً لمنع الانهيار"""
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records() # تجلب البيانات كقاموس يعتمد على أسماء الأعمدة
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def get_col_idx(ws, col_name):
    """إيجاد رقم العمود بناءً على اسمه لضمان استقرار الكود حتى لو تغير ترتيب الجدول"""
    try:
        headers = ws.row_values(1)
        return headers.index(col_name) + 1
    except:
        return None

# --- 3. التصميم الاحترافي (CSS) المستقر ---
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    /* منع الشاشة البيضاء عبر التأكد من ظهور الحاوية الأساسية */
    .stApp { visibility: visible !important; }
    
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px; border-radius: 0 0 30px 30px;
        color: white; text-align: center; margin: -60px -20px 20px -20px;
    }
    .badge-card {
        background: white; padding: 20px; border-radius: 15px;
        border: 2px solid #e2e8f0; text-align: center; margin-bottom: 15px;
    }
    </style>
    <div class="header-section">
        <h1 style="color:white; font-size:24px;">منصة زياد الذكية</h1>
        <p style="color:white; opacity:0.8;">نظام متابعة الطلاب والتحفيز الذكي</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. إدارة الحالة والدخول ---
if "role" not in st.session_state:
    st.session_state.role = None

# --- واجهة تسجيل الدخول ---
if st.session_state.role is None:
    tab1, tab2 = st.tabs(["🎓 بوابة الطالب", "🔐 بوابة الإدارة"])
    
    with tab1:
        with st.form("student_login"):
            sid = st.text_input("🆔 الرقم الأكاديمي", placeholder="أدخل رقم الهوية")
            if st.form_submit_button("دخول"):
                df_st = fetch_safe("students")
                # البحث في عمود 'الرقم الأكاديمي' تحديداً
                if not df_st.empty and str(sid) in df_st['الرقم الأكاديمي'].astype(str).values:
                    st.session_state.role = "student"
                    st.session_state.sid = str(sid)
                    st.rerun()
                else: st.error("عذراً، الرقم غير مسجل")

    with tab2:
        with st.form("admin_login"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("دخول الإدارة"):
                df_u = fetch_safe("users")
                if not df_u.empty:
                    row = df_u[df_u['username'] == u.strip()]
                    if not row.empty:
                        # التحقق من كلمة المرور (Hash)
                        if hashlib.sha256(str.encode(p)).hexdigest() == row.iloc[0]['password_hash']:
                            st.session_state.role = "teacher"
                            st.rerun()
                        else: st.error("كلمة المرور خاطئة")

    st.stop() # منع استكمال الكود إلا بعد تسجيل الدخول

# --- 5. واجهة المعلم (Teacher Dashboard) ---
if st.session_state.role == "teacher":
    st.markdown("### 👨‍🏫 لوحة تحكم المعلم")
    t1, t2, t3, t4 = st.tabs(["👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "🚗 خروج"])

    df_st = fetch_safe("students")

    with t1:
        st.markdown("#### إدارة السجلات")
        st.dataframe(df_st, use_container_width=True, hide_index=True)
        # ميزة الحذف الآمن بالاسم
        del_name = st.selectbox("اختر طالب للحذف:", [""] + df_st['الاسم الثلاثي'].tolist())
        if st.button("🗑️ حذف الطالب نهائياً"):
            if del_name:
                ws = sh.worksheet("students")
                cell = ws.find(del_name)
                if cell:
                    ws.delete_rows(cell.row)
                    st.success("تم الحذف"); time.sleep(1); st.rerun()

    with t2:
        st.markdown("#### رصد الدرجات (p1, p2, perf)")
        with st.form("grade_entry"):
            s_name = st.selectbox("الطالب:", df_st['الاسم الثلاثي'].tolist())
            c1, c2, c3 = st.columns(3)
            p1 = c1.number_input("المشاركة (p1)", 0, 20)
            p2 = c2.number_input("الواجبات (p2)", 0, 20)
            perf = c3.number_input("الاختبار (perf)", 0, 20)
            if st.form_submit_button("حفظ الدرجات"):
                s_id = df_st[df_st['الاسم الثلاثي'] == s_name]['الرقم الأكاديمي'].values[0]
                ws_g = sh.worksheet("grades")
                ws_g.append_row([str(s_id), p1, p2, perf, str(datetime.date.today())])
                st.success("تم الحفظ")

    with t3:
        st.markdown("#### تحديث النقاط السلوكية")
        target = st.selectbox("اختر الطالب للرصد:", df_st['الاسم الثلاثي'].tolist(), key="beh")
        b_type = st.radio("نوع السلوك:", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)"])
        if st.button("🚀 تحديث الرصيد الآن"):
            ws = sh.worksheet("students")
            p_col = get_col_idx(ws, "النقاط") # البحث عن عمود النقاط بالاسم
            cell = ws.find(target)
            if cell and p_col:
                current = int(ws.cell(cell.row, p_col).value or 0)
                points_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5}
                new_total = current + points_map.get(b_type, 0)
                ws.update_cell(cell.row, p_col, str(new_total))
                st.success(f"تم تحديث نقاط {target} إلى {new_total}"); time.sleep(1); st.rerun()

    with t4:
        if st.button("تسجيل خروج"):
            st.session_state.role = None; st.rerun()

# --- 6. واجهة الطالب (Student Dashboard) ---
if st.session_state.role == "student":
    df_st = fetch_safe("students")
    # البحث عن الطالب بالرقم الأكاديمي المخزن في الجلسة
    s_row = df_st[df_st['الرقم الأكاديمي'].astype(str) == st.session_state.sid]
    
    if not s_row.empty:
        s_data = s_row.iloc[0]
        s_name = s_data['الاسم الثلاثي']
        # معالجة النقاط لتجنب خطأ الشاشة البيضاء
        try:
            s_points = int(float(str(s_data['النقاط'] or 0)))
        except:
            s_points = 0
            
        # تصميم الأوسمة التفاعلي
        st.markdown(f"### مرحباً بك يا {s_name} 👋")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="badge-card"><h3>رصيد النقاط</h3><h1 style="color:#1e40af;">{s_points}</h1></div>', unsafe_allow_html=True)
        
        with c2:
            badge = "🌱 مبتدئ"
            if s_points >= 100: badge = "🥇 الذهبي"
            elif s_points >= 50: badge = "🥈 الفضي"
            elif s_points >= 10: badge = "🥉 البرونزي"
            st.markdown(f'<div class="badge-card"><h3>وسامك الحالي</h3><h1>{badge}</h1></div>', unsafe_allow_html=True)

        st.markdown("---")
        # عرض الدرجات المسجلة في شيت grades
        st.markdown("#### 📊 سجل درجاتي")
        df_g = fetch_safe("grades")
        if not df_g.empty:
            my_g = df_g[df_g['student_id'].astype(str) == st.session_state.sid]
            st.dataframe(my_g, use_container_width=True, hide_index=True)

    if st.button("تسجيل الخروج"):
        st.session_state.role = None; st.rerun()
