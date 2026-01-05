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
# 1. إعدادات الصفحة والاتصال المحترف
# ==========================================
st.set_page_config(page_title="منصة زياد الذكية", layout="wide")

@st.cache_resource
def get_gsheet_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

client = get_gsheet_client()

def fetch_data(worksheet_name):
    """جلب البيانات وتحويلها لقاموس لضمان استقرار الأعمدة"""
    if not client: return pd.DataFrame()
    try:
        ws = client.worksheet(worksheet_name)
        data = ws.get_all_records() # جلب البيانات كـ List of Dicts
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def get_row_number(worksheet, id_val, col_name="الرقم"):
    """دالة احترافية لإيجاد رقم الصف بناءً على المعرف الفريد"""
    try:
        cells = worksheet.col_values(1) # نفترض أن الرقم الأكاديمي في العمود الأول
        return cells.index(str(id_val)) + 1
    except ValueError:
        return None

# ==========================================
# 2. التصميم (CSS) - الحفاظ على الهوية البصرية
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
        padding: 45px 20px; border-radius: 0 0 40px 40px;
        color: white; text-align: center; margin: -80px -20px 30px -20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .logo-container {
        background: rgba(255, 255, 255, 0.1);
        width: 75px; height: 75px; border-radius: 20px;
        margin: 0 auto 15px; display: flex; 
        justify-content: center; align-items: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stButton>button {
        border-radius: 12px !important; font-weight: bold !important;
        transition: all 0.3s ease;
    }
    /* تحسين ألوان الأزرار التفاعلية */
    div[data-testid="stForm"] .stButton>button { background: #2563eb !important; color: white !important; }
    .btn-wa { background-color: #16a34a !important; color: white !important; }
    .btn-auto { background-color: #dc2626 !important; color: white !important; }
    
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div class="header-section">
        <div class="logo-container"><i class="bi bi-graph-up-arrow" style="font-size:38px; color:white;"></i></div>
        <h1 style="font-size:26px; font-weight:700; margin:0; color:white;">منصة زياد الذكية</h1>
        <p style="opacity:0.9; font-size:15px; margin-top:8px; color:white;">نظام رصد أكاديمي وسلوكي متطور</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. الدوال المساعدة
# ==========================================
def get_formatted_msg(name, b_type, b_note, b_date, prefix=""):
    return (
        f"{prefix}تحية طيبة، إشعار ملاحظة سلوكية للطالب: {name}\n"
        f"----------------------------------------\n"
        f"🏷️ النوع: {b_type}\n"
        f"📝 الملاحظة: {b_note}\n"
        f"📅 التاريخ: {b_date}\n"
        f"----------------------------------------\n"
        f"🏛️ منصة الأستاذ زياد الذكية"
    )

def send_auto_email(to_email, student_name, b_type, b_note, b_date):
    try:
        conf = st.secrets["email_settings"]
        msg = MIMEMultipart()
        msg['From'] = conf["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = f"🔔 إشعار سلوكي: {student_name}"
        body = get_formatted_msg(student_name, b_type, b_note, b_date)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(conf["sender_email"], conf["sender_password"])
            server.send_message(msg)
        return True
    except: return False

# ==========================================
# 4. نظام الدخول وحماية الجلسة
# ==========================================
if "role" not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    t1, t2 = st.tabs(["🎓 دخول الطلاب", "🔐 بوابة الإدارة"])
    with t1:
        with st.form("st_log"):
            sid = st.text_input("🆔 الرقم الأكاديمي").strip()
            if st.form_submit_button("دخول 🚀"):
                df = fetch_data("students")
                if not df.empty and sid in df['الرقم'].astype(str).values:
                    st.session_state.role = "student"; st.session_state.sid = sid
                    st.rerun()
                else: st.error("رقم أكاديمي غير مسجل")
    with t2:
        with st.form("admin_log"):
            u, p = st.text_input("👤 المستخدم"), st.text_input("🔑 المرور", type="password")
            if st.form_submit_button("دخول"):
                df = fetch_data("users")
                if not df.empty:
                    user_row = df[df['username'] == u.strip()]
                    if not user_row.empty and hashlib.sha256(p.encode()).hexdigest() == user_row.iloc[0]['password_hash']:
                        st.session_state.role = "teacher"; st.rerun()
                    else: st.error("بيانات الدخول غير صحيحة")
    st.stop()

# ==========================================
# 5. واجهة المعلم الاحترافية
# ==========================================
if st.session_state.role == "teacher":
    menu = st.tabs(["👥 إدارة الطلاب", "📈 الدرجات", "🔍 البحث", "🥇 السلوك", "📢 الاختبارات", "⚙️ الإعدادات", "🚗 خروج"])

    # --- 1. إدارة الطلاب ---
    with menu[0]:
        st.subheader("👥 تسجيل وإدارة الطلاب")
        with st.expander("➕ إضافة طالب جديد", expanded=False):
            with st.form("new_student_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3); nid = c1.text_input("الرقم الأكاديمي")
                nname = c2.text_input("الاسم الثلاثي"); nclass = c3.selectbox("الصف", ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
                c4, c5, c6 = st.columns(3); nyear = c4.text_input("العام", "1447هـ")
                nstage = c5.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"]); nsub = c6.text_input("المادة", "لغة إنجليزية")
                c7, c8 = st.columns(2); nmail = c7.text_input("البريد الإلكتروني"); nphone = c8.text_input("جوال ولي الأمر")
                
                if st.form_submit_button("حفظ البيانات"):
                    if nid and nname:
                        phone_fixed = "966" + nphone.lstrip("0") if nphone else ""
                        new_row = [nid, nname, nclass, nyear, nstage, nsub, nmail, phone_fixed, "0"]
                        client.worksheet("students").append_row(new_row)
                        st.success("تم الحفظ بنجاح"); time.sleep(1); st.rerun()

        st.markdown("---")
        df_st = fetch_data("students")
        st.dataframe(df_st, use_container_width=True)

        if not df_st.empty:
            with st.expander("🗑️ منطقة الحذف الآمن"):
                to_del = st.selectbox("اختر الطالب للحذف النهائي", options=df_st['الاسم'].tolist())
                if st.button("🚨 تأكيد الحذف النهائي"):
                    # الحذف يعتمد على مطابقة الاسم في جدول الطلاب
                    ws_st = client.worksheet("students")
                    cell = ws_st.find(to_del)
                    if cell:
                        ws_st.delete_rows(cell.row)
                        st.success("تم الحذف بنجاح"); time.sleep(1); st.rerun()

    # --- 2. الدرجات (منطق التحديث الذكي) ---
    with menu[1]:
        st.subheader("📝 رصد وتحديث الدرجات")
        df_st = fetch_data("students")
        df_gr = fetch_data("grades")
        
        if not df_st.empty:
            with st.form("grade_form"):
                st_choice = st.selectbox("اختر الطالب", options=df_st['الاسم'].tolist())
                # جلب الرقم الأكاديمي للطالب المختار
                st_id = df_st[df_st['الاسم'] == st_choice].iloc[0]['الالرقم'] if 'الالرقم' in df_st.columns else df_st[df_st['الاسم'] == st_choice].iloc[0][0]
                
                c1, c2, c3 = st.columns(3)
                p1 = c1.number_input("المهام (P1)", 0.0, 100.0)
                p2 = c2.number_input("الاختبار (P2)", 0.0, 100.0)
                total = p1 + p2
                c3.metric("المجموع", total)
                note = st.text_input("ملاحظات الدرجة")
                
                if st.form_submit_button("اعتماد الدرجة"):
                    ws_gr = client.worksheet("grades")
                    # البحث عن الاسم في جدول الدرجات للتحديث أو الإضافة
                    existing_cell = ws_gr.find(str(st_choice))
                    row_data = [st_choice, p1, p2, total, str(datetime.date.today()), note]
                    
                    if existing_cell:
                        ws_gr.update(f"B{existing_cell.row}:F{existing_cell.row}", [row_data[1:]])
                        st.success("تم تحديث الدرجة")
                    else:
                        ws_gr.append_row(row_data)
                        st.success("تم رصد درجة جديدة")
                    time.sleep(1); st.rerun()
            st.dataframe(df_gr, use_container_width=True)

    # --- 3. البحث ---
    with menu[2]:
        st.subheader("🔍 استعلام سريع")
        q = st.text_input("ابحث بالاسم أو الرقم الأكاديمي...")
        if q:
            df_st = fetch_data("students")
            res = df_st[df_st.astype(str).apply(lambda x: x.str.contains(q)).any(axis=1)]
            for _, r in res.iterrows():
                with st.container(border=True):
                    st.write(f"👤 **{r['الاسم']}** | 🆔 {r['الرقم']} | 🏫 {r['الصف']}")
                    st.write(f"📱 {r['جوال ولي الأمر']} | 📧 {r['البريد الإلكتروني']}")

    # --- 4. السلوك ---
    with menu[3]:
        st.subheader("🎭 سجل الانضباط والسلوك")
        df_st = fetch_data("students")
        if not df_st.empty:
            sel_st = st.selectbox("الطالب المستهدف:", options=df_st['الاسم'].tolist(), key="beh_sel")
            s_data = df_st[df_st['الاسم'] == sel_st].iloc[0]
            
            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_type = c1.selectbox("فئة السلوك", ["🌟 متميز (+10)", "✅ إيجابي (+5)", "⚠️ تنبيه (0)", "❌ سلبي (-5)", "🚫 مخالفة (-10)"])
                b_date = c2.date_input("تاريخ الرصد")
                b_note = st.text_area("تفاصيل الملاحظة")
                
                col1, col2, col3 = st.columns(3)
                if col1.button("💾 حفظ السجل", use_container_width=True):
                    client.worksheet("behavior").append_row([sel_st, str(b_date), b_type, b_note])
                    # تحديث نقاط الطالب في جدول الطلاب
                    ws_st = client.worksheet("students")
                    cell = ws_st.find(sel_st)
                    p_map = {"🌟 متميز (+10)": 10, "✅ إيجابي (+5)": 5, "⚠️ تنبيه (0)": 0, "❌ سلبي (-5)": -5, "🚫 مخالفة (-10)": -10}
                    current_pts = int(s_data['النقاط'] if s_data['النقاط'] else 0)
                    ws_st.update_cell(cell.row, 9, current_pts + p_map[b_type])
                    st.success("تم الحفظ وتحديث النقاط"); st.rerun()

                if col2.button("💬 واتساب", use_container_width=True):
                    msg = get_formatted_msg(sel_st, b_type, b_note, b_date)
                    url = f"https://api.whatsapp.com/send?phone={s_data['جوال ولي الأمر']}&text={urllib.parse.quote(msg)}"
                    st.markdown(f'<script>window.open("{url}", "_blank");</script>', unsafe_allow_html=True)
                
                if col3.button("⚡ إيميل تلقائي", use_container_width=True):
                    if send_auto_email(s_data['البريد الإلكتروني'], sel_st, b_type, b_note, b_date):
                        st.success("تم الإرسال")
                    else: st.error("فشل الإرسال")

    # --- 5. الاختبارات ---
    with menu[4]:
        st.subheader("📢 إدارة التنبيهات")
        with st.form("ex_form"):
            c1, c2 = st.columns([1,2])
            e_cls = c1.selectbox("الفئة المستهدفة", ["الكل", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"])
            e_ttl = c2.text_input("موضوع التنبيه")
            e_dt = st.date_input("موعد الاختبار/الحدث")
            e_lnk = st.text_input("رابط مرجعي (اختياري)")
            if st.form_submit_button("نشر الآن"):
                client.worksheet("exams").append_row([str(e_cls), str(e_ttl), str(e_dt), str(e_lnk)])
                st.success("تم النشر"); st.rerun()

    # --- 6. الإعدادات ---
    with menu[5]:
        st.subheader("⚙️ التحكم بالنظام")
        if st.button("🔴 تصفير كافة النقاط لكافة الطلاب"):
            ws = client.worksheet("students")
            rows = len(ws.get_all_values())
            if rows > 1:
                cells = ws.range(f"I2:I{rows}")
                for c in cells: c.value = "0"
                ws.update_cells(cells)
                st.success("تم تصفير النقاط")

    with menu[6]:
        if st.button("تسجيل الخروج"):
            st.session_state.role = None; st.rerun()

# ==========================================
# 6. واجهة الطالب (مستقرة وسريعة)
# ==========================================
elif st.session_state.role == "student":
    df_st = fetch_data("students")
    s_id = str(st.session_state.sid)
    student_info = df_st[df_st['الرقم'].astype(str) == s_id].iloc[0]
    s_name = student_info['الاسم']
    
    st.markdown(f"<div style='text-align:center; padding:20px; background:#f8fafc; border-radius:15px; border-right:5px solid #1e40af;'>"
                f"<h3>مرحباً: {s_name}</h3>"
                f"<h4 style='color:#1e40af;'>رصيد نقاطك: {student_info['النقاط']}</h4></div>", unsafe_allow_html=True)
    
    st_tabs = st.tabs(["📢 الإعلانات", "📊 درجاتي", "🎭 سلوكي", "🏆 الأوائل"])
    
    with st_tabs[0]:
        df_ex = fetch_data("exams")
        if not df_ex.empty:
            relevant = df_ex[(df_ex['الصف'] == student_info['الصف']) | (df_ex['الصف'] == "الكل")]
            for _, r in relevant.iloc[::-1].iterrows():
                st.info(f"**{r['العنوان']}** \n📅 التاريخ: {r['التاريخ']}  \n🔗 {r['رابط']}")

    with st_tabs[1]:
        df_gr = fetch_data("grades")
        my_gr = df_gr[df_gr['الاسم'] == s_name]
        if not my_gr.empty:
            g = my_gr.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("المهام", g['P1']); c2.metric("الاختبار", g['P2']); c3.metric("المجموع", g['المجموع'])
        else: st.warning("لم يتم رصد درجاتك بعد")

    with st_tabs[3]:
        st.write("🏆 قائمة العشرة الأوائل:")
        top_10 = df_st.nlargest(10, 'النقاط')[['الاسم', 'النقاط']]
        st.table(top_10)

    if st.button("خروج"): st.session_state.role = None; st.rerun()
