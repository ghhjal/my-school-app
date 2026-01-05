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
st.set_page_config(page_title="منصة زياد الذكية v2.0", layout="wide")

@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except:
        return None

sh = get_client()

def fetch_safe(worksheet_name):
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame()

# ==========================================
# 2. التصميم الاحترافي المحسن (CSS)
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
    .stMetric {
        background: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
    }
    .badge-gold { background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .badge-silver { background: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .stButton>button {
        border-radius: 12px !important; font-weight: bold !important; transition: 0.3s;
    }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-rocket-takeoff" style="font-size:35px; color:white;"></i></div>
        <h1 style="font-size:24px; font-weight:700; margin:0;">منصة الأستاذ زياد التعليمية</h1>
        <p style="opacity:0.8; font-size:14px; margin-top:5px;">الإصدار الاحترافي للتحليل والرصد الذكي</p>
    </div>
""", unsafe_allow_html=True)

# دالة لتحديد الوسام بناءً على النقاط
def get_badge(points):
    p = int(float(str(points or 0)))
    if p >= 100: return "🏆 القائد الذهبي"
    if p >= 50: return "🌟 الطالب المتميز"
    if p >= 20: return "✨ المتفاعل"
    if p < 0: return "⚠️ يحتاج توجيه"
    return "🌱 برعم صاعد"

def send_auto_email_silent(to_email, student_name, b_type, b_note, b_date):
    try:
        set = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = set["sender_email"]; msg['To'] = to_email
        msg['Subject'] = f"🔔 إشعار من منصة أ. زياد: {student_name}"
        body = f"تحية طيبة،\nتم رصد ملاحظة: {b_type}\nالتفاصيل: {b_note}\nالتاريخ: {b_date}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(set["sender_email"], set["sender_password"])
            s.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. واجهة الدخول
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 بوابة الطلاب", "🔐 الإدارة"])
    with t1:
        with st.form("l1"):
            sid = st.text_input("🔢 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول"):
                df = fetch_safe("students")
                if not df.empty and sid in df.iloc[:, 0].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid; st.rerun()
                else: st.error("الرقم غير صحيح")
    with t2:
        with st.form("l2"):
            u, p = st.text_input("المستخدم"), st.text_input("المرور", type="password")
            if st.form_submit_button("دخول"):
                df = fetch_safe("users")
                if not df.empty and u == df.iloc[0, 0] and hashlib.sha256(p.encode()).hexdigest() == df.iloc[0, 1]:
                    st.session_state.role = "teacher"; st.rerun()
                else: st.error("خطأ في البيانات")
    st.stop()

# ==========================================
# 4. واجهة المعلم الاحترافية
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["📊 الإحصائيات", "👥 الطلاب", "📈 الدرجات", "🥇 السلوك", "📢 الإعلانات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- تبويب الإحصائيات (الجديد كلياً) ---
    with menu[0]:
        st.markdown("### 📊 نظرة عامة على الأداء")
        df_s = fetch_safe("students"); df_g = fetch_safe("grades"); df_b = fetch_safe("behavior")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الطلاب", len(df_s))
        avg_g = pd.to_numeric(df_g.iloc[:, 3], errors='coerce').mean() if not df_g.empty else 0
        c2.metric("متوسط الدرجات", f"{avg_g:.1f}")
        c3.metric("ملاحظات السلوك", len(df_b))
        top_student = df_s.iloc[pd.to_numeric(df_s.iloc[:, 8], errors='coerce').idxmax(), 1] if not df_s.empty else "---"
        c4.metric("الأول على الصف", top_student)

        st.markdown("---")
        st.write("📈 **أعلى 5 طلاب في النقاط**")
        if not df_s.empty:
            df_s['pts_n'] = pd.to_numeric(df_s.iloc[:, 8], errors='coerce').fillna(0)
            st.bar_chart(df_s.nlargest(5, 'pts_n').set_index(df_s.columns[1])['pts_n'])

    # --- تبويب الطلاب ---
    with menu[1]:
        st.markdown("### 👥 إدارة الطلاب")
        with st.expander("➕ إضافة طالب جديد"):
            with st.form("f_add", clear_on_submit=True):
                c = st.columns(3)
                nid = c[0].text_input("الرقم الأكاديمي"); nname = c[1].text_input("الاسم الثلاثي"); nclass = c[2].selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                m1, m2 = st.columns(2); nmail = m1.text_input("الإيميل"); nphone = m2.text_input("الجوال")
                if st.form_submit_button("حفظ الطالب"):
                    if nid and nname:
                        sh.worksheet("students").append_row([nid, nname, nclass, "1447هـ", "ابتدائي", "لغة إنجليزية", nmail, "966"+nphone.lstrip("0"), "0"])
                        st.success("تم الحفظ"); st.rerun()
        st.dataframe(fetch_safe("students"), use_container_width=True)

    # --- تبويب الدرجات ---
    with menu[2]:
        st.markdown("### 📈 رصد الدرجات")
        df_st = fetch_safe("students"); df_gr = fetch_safe("grades")
        if not df_st.empty:
            with st.container(border=True):
                sel_st = st.selectbox("👤 ابحث عن طالب لرصد درجته:", options=df_st.iloc[:, 1].tolist())
                c1, c2 = st.columns(2)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0)
                total = p1 + p2
                st.info(f"المجموع: {total} | الحالة: {'✅ ناجح' if total >= 50 else '❌ متابعة'}")
                if st.button("💾 اعتماد الدرجة"):
                    ws = sh.worksheet("grades"); cell = ws.find(sel_st)
                    row = [sel_st, p1, p2, total, str(datetime.date.today()), ""]
                    if cell: ws.update(f"B{cell.row}:F{cell.row}", [row[1:]])
                    else: ws.append_row(row)
                    st.success("تم الحفظ"); st.rerun()
        st.dataframe(df_gr, use_container_width=True)

    # --- تبويب السلوك (احترافي بالأزرار) ---
    with menu[3]:
        st.markdown("### 🥇 إدارة السلوك")
        df_st = fetch_safe("students")
        if not df_st.empty:
            sel_b = st.selectbox("🎯 اختر الطالب:", options=df_st.iloc[:, 1].tolist())
            s_row = df_st[df_st.iloc[:, 1] == sel_b].iloc[0]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("نوع السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_note = st.text_area("الملاحظة")
                
                col = st.columns(4)
                if col[0].button("💾 حفظ"):
                    sh.worksheet("behavior").append_row([sel_b, str(datetime.date.today()), b_type, b_note])
                    # تحديث النقاط
                    ws_s = sh.worksheet("students"); c = ws_s.find(sel_b)
                    pts_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                    old_p = int(s_row.iloc[8] or 0)
                    ws_s.update_cell(c.row, 9, old_p + pts_map.get(b_type, 0))
                    st.success("تم الحفظ"); st.rerun()
                
                if col[1].button("📧 إيميل"):
                    if send_auto_email_silent(s_row.iloc[6], sel_b, b_type, b_note, datetime.date.today()): st.success("تم")
                
                if col[2].button("💬 واتساب"):
                    msg = f"إشعار سلوكي للطالب: {sel_b}\nالنوع: {b_type}\n{b_note}"
                    st.markdown(f'<script>window.open("https://wa.me/{s_row.iloc[7]}?text={urllib.parse.quote(msg)}", "_blank");</script>', unsafe_allow_html=True)
                
                if col[3].button("🗑️ حذف طالب"):
                    sh.worksheet("students").delete_rows(sh.worksheet("students").find(sel_b).row); st.rerun()

    with menu[5]:
        st.markdown("### ⚙️ الإعدادات")
        if st.button("🔴 تصفير كافة النقاط"):
            ws = sh.worksheet("students"); all_v = ws.get_all_values()
            if len(all_v) > 1:
                cells = ws.range(f'I2:I{len(all_v)}')
                for c in cells: c.value = '0'
                ws.update_cells(cells); st.success("تم التصفير")

    with menu[6]:
        if st.button("خروج"): st.session_state.role = None; st.rerun()

# ==========================================
# 5. واجهة الطالب (النسخة الذكية بالأوسمة)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_safe("students")
    s_row = df_st[df_st.iloc[:, 0].astype(str) == str(st.session_state.sid)].iloc[0]
    points = int(float(s_row.iloc[8] or 0))
    
    # واجهة الترحيب مع الوسام
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; text-align: center; border: 1px solid #e2e8f0;">
            <h2 style="margin:0;">مرحباً، {s_row.iloc[1]} 👋</h2>
            <div style="margin: 15px 0;">
                <span class="badge-gold" style="font-size: 18px;">{get_badge(points)}</span>
            </div>
            <h4 style="color: #1e40af;">رصيدك الحالي: {points} نقطة</h4>
        </div>
    """, unsafe_allow_html=True)

    t = st.tabs(["📢 الإعلانات", "📊 درجاتي", "🏆 لوحة الشرف"])
    
    with t[1]:
        df_g = fetch_safe("grades")
        my_g = df_g[df_g.iloc[:, 0] == s_row.iloc[1]]
        if not my_g.empty:
            g = my_g.iloc[0]
            st.metric("مجموع درجاتك", f"{g.iloc[3]} / 100")
            st.progress(float(g.iloc[3])/100)
            if float(g.iloc[3]) >= 90: st.balloons()
        else: st.info("لا توجد درجات مرصودة حالياً")

    with t[2]:
        st.markdown("🏆 **العشرة الأوائل على مستوى المنصة**")
        df_st['p_val'] = pd.to_numeric(df_st.iloc[:, 8], errors='coerce').fillna(0)
        top = df_st.nlargest(10, 'p_val')
        for i, r in enumerate(top.values):
            st.write(f"{i+1}. {r[1]} — {int(r[8])} نقطة — {get_badge(r[8])}")

    if st.button("تسجيل الخروج"): st.session_state.role = None; st.rerun()
