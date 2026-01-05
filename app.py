import streamlit as st
import gspread
import pandas as pd
import hashlib
import time
import datetime
import urllib.parse
import io
import smtplib
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. إعدادات المنصة والاتصال
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except: return None

sh = get_client()

def fetch_safe(worksheet_name):
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data or len(data) < 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
    except: return pd.DataFrame()

# ==========================================
# 2. التصميم (CSS) - الحفاظ الكامل على الهوية
# ==========================================
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL; text-align: right;
    }
    .header-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 40px 20px; border-radius: 0 0 40px 40px;
        color: white; text-align: center; margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 70px; height: 70px; border-radius: 20px;
        margin: 0 auto 10px; display: flex; justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stButton>button {
        background: #2563eb !important; color: white !important;
        border-radius: 12px !important; font-weight: bold !important;
        height: 3.5em !important; width: 100% !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    .badge-info { background: #e0f2fe; color: #0369a1; padding: 5px 15px; border-radius: 10px; font-weight: bold; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-rocket-takeoff" style="font-size:35px; color:white;"></i></div>
        <h1 style="font-size:24px; font-weight:700; margin:0;">منصة الأستاذ زياد التعليمية</h1>
        <p style="opacity:0.8; font-size:14px; margin-top:5px;">نظام الرصد الذكي والتواصل الفعال</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. إدارة الدخول
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 الإدارة"])
    with t1:
        with st.form("l_st"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول للمنصة"):
                df = fetch_safe("students")
                if not df.empty and sid in df.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("رقم غير مسجل")
    with t2:
        with st.form("l_te"):
            u, p = st.text_input("اسم المستخدم"), st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                df = fetch_safe("users")
                if not df.empty and u == df.iloc[0, 0] and hashlib.sha256(p.encode()).hexdigest() == df.iloc[0, 1]:
                    st.session_state.role = "teacher"; st.rerun()
                else: st.error("بيانات خاطئة")
    st.stop()

# ==========================================
# 4. واجهة المعلم (حل مشكلة النموذج الفارغ)
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "📢 الإعلانات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- تبويب الإحصائيات ---
    with menu[0]:
        df_s = fetch_safe("students"); df_g = fetch_safe("grades")
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الطلاب", len(df_s))
        avg_v = pd.to_numeric(df_g.iloc[:, 3], errors='coerce').mean() if not df_g.empty else 0
        c2.metric("متوسط الدرجات", f"{avg_v:.1f}")
        c3.metric("الطلاب المرصودين", len(df_g))

    # --- تبويب الدرجات (الإصلاح الجذري هنا) ---
    with menu[2]:
        st.markdown("### 📈 رصد وتحديث الدرجات")
        df_st = fetch_safe("students")
        df_gr = fetch_safe("grades")
        
        if not df_st.empty:
            # 1. قائمة اختيار الطالب (خارج النموذج للتفاعل الفوري)
            sel_student = st.selectbox("👤 اختر الطالب للبدء:", options=df_st.iloc[:, 1].tolist())
            
            # جلب بيانات الطالب المختار فوراً
            st_info = df_st[df_st.iloc[:, 1] == sel_student].iloc[0]
            st_id = st_info.iloc[0]
            
            with st.container(border=True):
                st.markdown(f"**الرقم الأكاديمي:** <span class='badge-info'>{st_id}</span>", unsafe_allow_html=True)
                
                # التحقق من وجود درجة سابقة
                prev_row = df_gr[df_gr.iloc[:, 0] == sel_student]
                is_update = not prev_row.empty
                if is_update:
                    st.warning(f"⚠️ الطالب لديه درجة سابقة: {prev_row.iloc[0, 3]}")
                else:
                    st.info("✨ طالب جديد - لم تُرصد له درجة بعد.")

                # 2. نموذج إدخال الدرجات
                with st.form("grade_submit_form", clear_on_submit=False):
                    c1, c2 = st.columns(2)
                    p1 = c1.number_input("📝 المهام (P1)", 0.0, 100.0, value=float(prev_row.iloc[0, 1]) if is_update else 0.0)
                    p2 = c2.number_input("📄 الاختبار (P2)", 0.0, 100.0, value=float(prev_row.iloc[0, 2]) if is_update else 0.0)
                    
                    note = st.text_input("💬 ملاحظة", value=str(prev_row.iloc[0, 5]) if is_update else "")
                    
                    btn_label = "🔄 تحديث الدرجة الحالية" if is_update else "💾 حفظ واعتماد الدرجة"
                    if st.form_submit_button(btn_label):
                        ws = sh.worksheet("grades")
                        total = p1 + p2
                        new_data = [sel_student, p1, p2, total, str(datetime.date.today()), note]
                        
                        cell = ws.find(sel_student)
                        if cell:
                            ws.update(f"B{cell.row}:F{cell.row}", [new_data[1:]])
                        else:
                            ws.append_row(new_data)
                        
                        st.success(f"تم حفظ درجة {sel_student} بنجاح!")
                        time.sleep(1)
                        st.rerun()

            st.markdown("---")
            st.write("📋 **سجل الدرجات الحالي**")
            st.dataframe(df_gr, use_container_width=True)

    # --- تبويب السلوك (بنفس منطق التفاعل الفوري) ---
    with menu[3]:
        st.markdown("### 🥇 إدارة السلوك والنقاط")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_b = st.selectbox("🎯 اختر الطالب لتسجيل سلوك:", options=df_st.iloc[:, 1].tolist())
            s_data = df_st[df_st.iloc[:, 1] == sel_b].iloc[0]
            
            with st.container(border=True):
                st.write(f"النقاط الحالية: **{s_data.iloc[8]}**")
                with st.form("beh_form"):
                    c1, c2 = st.columns(2)
                    b_type = c1.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                    b_date = c2.date_input("التاريخ", datetime.date.today())
                    b_note = st.text_area("الملاحظة")
                    
                    if st.form_submit_button("💾 رصد السلوك"):
                        sh.worksheet("behavior").append_row([sel_b, str(b_date), b_type, b_note])
                        # تحديث النقاط في ورقة الطلاب
                        ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                        p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                        old_p = int(s_data.iloc[8] or 0)
                        ws_s.update_cell(c.row, 9, old_p + p_map.get(b_type, 0))
                        st.success("تم التحديث"); time.sleep(1); st.rerun()

    # --- بقية التبويبات (إدارة الطلاب والإعدادات) ---
    with menu[1]:
        st.dataframe(fetch_safe("students"), use_container_width=True)
    
    with menu[5]:
        if st.button("🔴 تصفير كافة النقاط"):
            ws = sh.worksheet("students"); all_v = ws.get_all_values()
            if len(all_v) > 1:
                cells = ws.range(f'I2:I{len(all_v)}')
                for c in cells: c.value = '0'
                ws.update_cells(cells); st.success("تم التصفير")

    with menu[6]:
        if st.button("تسجيل الخروج"):
            st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)].iloc[0]
    st.markdown(f"<h2 style='text-align:center;'>مرحباً {s_row.iloc[1]} 👋</h2>", unsafe_allow_html=True)
    st.metric("رصيد نقاطك", f"{s_row.iloc[8]} نقطة")
    
    t1, t2 = st.tabs(["📊 درجاتي", "🏆 لوحة الشرف"])
    with t1:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_row.iloc[1]]
        if not my_g.empty:
            st.metric("المجموع", f"{my_g.iloc[0, 3]} / 100")
        else: st.info("لا توجد درجات حالياً")
    
    if st.button("خروج"): st.session_state.role = None; st.rerun()
